#!/usr/bin/env python3
"""Recompute raw and canonical TCM-SD42 label support from public source splits.

The script deliberately separates raw source strings from the frozen canonical
label vocabulary. It emits aggregate support tables and input hashes only.
It cannot prove that the same implementation ran in the historical May 2026
pipeline, and it does not recreate the missing historical deduplication stage.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from collections import Counter,defaultdict
from pathlib import Path

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def load_records(path):
    path=Path(path)
    if path.suffix.lower()==".jsonl":
        with path.open(encoding="utf-8") as f: rows=[json.loads(x) for x in f if x.strip()]
    elif path.suffix.lower()==".csv":
        with path.open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
    else:
        with path.open(encoding="utf-8") as f: obj=json.load(f)
        if isinstance(obj,list): rows=obj
        elif isinstance(obj,dict):
            rows=next((obj[k] for k in ("data","records","examples","items") if isinstance(obj.get(k),list)),None)
            if rows is None: raise ValueError(f"{path}: expected a list or list under data/records/examples/items")
        else: raise ValueError(f"{path}: unsupported top-level JSON type")
    if not rows or not all(isinstance(r,dict) for r in rows): raise ValueError(f"{path}: expected non-empty records")
    return rows

def label_counts(rows,field,path):
    missing=sum(field not in r or r[field] is None or not str(r[field]).strip() for r in rows)
    if missing: raise ValueError(f"{path}: {missing} records lack non-empty label field {field!r}")
    return Counter(str(r[field]).strip() for r in rows)

def canonicalize(label):
    # The independently reconstructed frozen mapping removes one trailing Chinese character 证.
    return label[:-1] if label.endswith("证") else label

def write_csv(path,rows):
    if not rows: raise ValueError(f"no rows to write: {path}")
    with Path(path).open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--train",required=True,type=Path); ap.add_argument("--dev",required=True,type=Path); ap.add_argument("--test",required=True,type=Path)
    ap.add_argument("--label-field",default="syndrome")
    ap.add_argument("--frozen-labels",type=Path); ap.add_argument("--frozen-support-csv",type=Path)
    ap.add_argument("--support-label-field",default="auto")
    ap.add_argument("--support-train-field",default="auto")
    ap.add_argument("--support-dev-field",default="auto")
    ap.add_argument("--support-test-field",default="auto")
    ap.add_argument("--train-cap",type=int,default=1000); ap.add_argument("--top-k",type=int,default=50)
    ap.add_argument("--out-dir",required=True,type=Path)
    ap.add_argument("--expected-train",type=int,default=43180); ap.add_argument("--expected-dev",type=int,default=5486); ap.add_argument("--expected-test",type=int,default=5486)
    ap.add_argument("--reported-final-train",type=int,default=19125); ap.add_argument("--reported-final-dev",type=int,default=4411); ap.add_argument("--reported-final-test",type=int,default=4452)
    a=ap.parse_args()
    paths={"train":a.train,"dev":a.dev,"test":a.test}
    records={k:load_records(v) for k,v in paths.items()}
    expected={"train":a.expected_train,"dev":a.expected_dev,"test":a.expected_test}
    counts={}
    for split,rows in records.items():
        if len(rows)!=expected[split]: print(f"WARNING: {split} rows={len(rows)}, expected={expected[split]}")
        counts[split]=label_counts(rows,a.label_field,paths[split])
    raw_union=set().union(*(set(v) for v in counts.values()))
    canonical_union={canonicalize(x) for x in raw_union}
    raw_table=[]
    for label in sorted(raw_union):
        tr,dv,te=(counts[k].get(label,0) for k in ("train","dev","test"))
        raw_table.append({"raw_label":label,"train":tr,"dev":dv,"test":te,"total":tr+dv+te,
            "eligible_raw_string":tr>=100 and dv>=10 and te>=10,"canonical_label":canonicalize(label)})
    eligible=[r for r in raw_table if r["eligible_raw_string"]]
    eligible.sort(key=lambda r:(-r["total"],r["raw_label"]))
    selected_raw=eligible[:a.top_k]
    selected_canonical={r["canonical_label"] for r in selected_raw}
    # Aggregate only selected eligible raw strings into canonical labels, then apply the training cap per canonical label.
    grouped=defaultdict(lambda:{"selected_raw_forms":[],"train_before_cap":0,"dev":0,"test":0})
    for r in selected_raw:
        g=grouped[r["canonical_label"]]
        g["selected_raw_forms"].append(r["raw_label"])
        g["train_before_cap"]+=r["train"];g["dev"]+=r["dev"];g["test"]+=r["test"]
    canonical_table=[]
    for label,g in sorted(grouped.items()):
        canonical_table.append({"canonical_label":label,"selected_raw_forms":"; ".join(sorted(g["selected_raw_forms"])),
            "train_before_cap":g["train_before_cap"],"train_after_cap":min(g["train_before_cap"],a.train_cap),
            "dev":g["dev"],"test":g["test"],"total_before_cap":g["train_before_cap"]+g["dev"]+g["test"]})
    final={"train_before_cap":sum(r["train_before_cap"] for r in canonical_table),
        "train_after_cap":sum(r["train_after_cap"] for r in canonical_table),
        "dev":sum(r["dev"] for r in canonical_table),"test":sum(r["test"] for r in canonical_table)}
    # Compare two plausible cap orders explicitly; do not silently choose whichever matches.
    raw_cap_train=sum(min(r["train"],a.train_cap) for r in selected_raw)
    raw_cap_dev=sum(r["dev"] for r in selected_raw)
    raw_cap_test=sum(r["test"] for r in selected_raw)
    frozen_support=None
    if a.frozen_support_csv:
        with a.frozen_support_csv.open(encoding="utf-8-sig",newline="") as f:
            fr=list(csv.DictReader(f))
        if not fr: raise ValueError("frozen support CSV has no data rows")
        fields=list(fr[0])
        def choose_field(requested,candidates,kind):
            if requested!="auto":
                if requested not in fields: raise ValueError(f"support CSV missing requested {kind} field {requested!r}; available={fields}")
                return requested
            for candidate in candidates:
                if candidate in fields:return candidate
            raise ValueError(f"cannot infer support CSV {kind} field from {fields}; pass the corresponding --support-*-field")
        lab_field=choose_field(a.support_label_field,("syndrome","label","canonical_label","syndrome_canonical","label_name"),"label")
        tr_field=choose_field(a.support_train_field,("train_count","train","train_support","n_train"),"train")
        dv_field=choose_field(a.support_dev_field,("dev_count","dev","dev_support","n_dev","development_count"),"dev")
        te_field=choose_field(a.support_test_field,("test_count","test","test_support","n_test"),"test")
        by_label={canonicalize(str(r[lab_field]).strip()):r for r in fr}
        frozen_support={"rows":len(fr),"fields":{"label":lab_field,"train":tr_field,"dev":dv_field,"test":te_field},
            "train_total":sum(int(r[tr_field]) for r in fr),"dev_total":sum(int(r[dv_field]) for r in fr),
            "test_total":sum(int(r[te_field]) for r in fr),"canonical_train_support_mismatches":[]}
        for r in canonical_table:
            old=by_label.get(r["canonical_label"])
            if old is None or int(old[tr_field])!=int(r["train_after_cap"]):
                frozen_support["canonical_train_support_mismatches"].append({
                    "canonical_label":r["canonical_label"],
                    "reconstructed_train_after_canonical_cap":int(r["train_after_cap"]),
                    "frozen_train_count":None if old is None else int(old[tr_field])})
        frozen_support["canonical_train_support_match"]=not frozen_support["canonical_train_support_mismatches"]
    frozen=None
    if a.frozen_labels:
        labs=[x.strip() for x in a.frozen_labels.read_text(encoding="utf-8").splitlines() if x.strip()]
        frozen={"count":len(labs),"unique_count":len(set(labs)),"missing":sorted(set(labs)-selected_canonical),
            "extra":sorted(selected_canonical-set(labs)),"exact_set_match":set(labs)==selected_canonical}
    a.out_dir.mkdir(parents=True,exist_ok=True)
    write_csv(a.out_dir/"label_selection_raw_support.csv",raw_table)
    write_csv(a.out_dir/"label_selection_canonical_support.csv",canonical_table)
    reported={"train":a.reported_final_train,"dev":a.reported_final_dev,"test":a.reported_final_test}
    result={"evidence_scope":"independent recomputation on supplied public source splits; not proof of the exact historical run",
        "label_field":a.label_field,"source_files":{k:{"basename":p.name,"sha256":sha256(p),"rows":len(records[k])} for k,p in paths.items()},
        "label_counts":{"train_raw_unique":len(counts["train"]),"three_split_raw_union_unique":len(raw_union),
            "three_split_canonical_union_unique":len(canonical_union),"eligible_raw_strings":len(eligible),
            "selected_raw_strings":len(selected_raw),"selected_canonical_labels":len(selected_canonical)},
        "criteria":{"train_min":100,"dev_min":10,"test_min":10,"top_k":a.top_k,"top_k_binding":len(eligible)>a.top_k,
            "canonicalization":"remove one trailing Chinese character 证 from each selected eligible raw label",
            "training_cap":"apply min(count, train_cap) per canonical label after selected raw strings are grouped"},
        "recomputed_selected_support_before_historical_dedup":final,
        "cap_order_comparison":{
            "cap_each_raw_label_then_merge":{"train":raw_cap_train,"dev":raw_cap_dev,"test":raw_cap_test},
            "merge_eligible_raw_labels_then_cap_each_canonical_label":{"train":final["train_after_cap"],"dev":final["dev"],"test":final["test"]},
            "train_difference_between_cap_orders":raw_cap_train-final["train_after_cap"],
            "canonical_cap_train_equals_reported_frozen_train":final["train_after_cap"]==a.reported_final_train,
            "raw_cap_train_equals_reported_frozen_train":raw_cap_train==a.reported_final_train,
            "interpretation":"Compare both explicit operation orders against retained per-class support and historical records; do not infer which order ran historically from a total match alone."
        },
        "frozen_support_csv_comparison":frozen_support,
        "reported_internal_summary_counts":reported,
        "delta_recomputed_minus_reported":{"train_after_canonical_cap":final["train_after_cap"]-reported["train"],
            "train_after_raw_cap":raw_cap_train-reported["train"],
            "dev":final["dev"]-reported["dev"],"test":final["test"]-reported["test"]},
        "frozen_label_comparison":frozen,
        "outputs":["label_selection_raw_support.csv","label_selection_canonical_support.csv"],
        "warning":"A match of canonical labels validates this reconstructed rule on the supplied public splits. The historical preprocessing/deduplication script and complete original frequency table are unavailable, so historical post-processing counts are not independently reproduced."}
    (a.out_dir/"label_selection_recompute.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
