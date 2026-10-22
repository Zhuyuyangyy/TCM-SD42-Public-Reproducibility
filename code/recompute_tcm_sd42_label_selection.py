#!/usr/bin/env python3
"""Recompute TCM-SD42 label eligibility from official public source splits.

Outputs aggregate counts only; never writes clinical text or full records.
A matching recomputation verifies the rule on the supplied downloaded splits,
not that the same code was used in the historical May 2026 run.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from collections import Counter
from pathlib import Path

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
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
            if rows is None:raise ValueError(f"{path}: expected a list or a list under data/records/examples/items")
        else:raise ValueError(f"{path}: unsupported top-level JSON type")
    if not rows or not all(isinstance(r,dict) for r in rows):raise ValueError(f"{path}: expected non-empty records")
    return rows

def counts(rows,field,path):
    missing=sum(field not in r or r[field] is None or not str(r[field]).strip() for r in rows)
    if missing:raise ValueError(f"{path}: {missing} records lack non-empty label field {field!r}")
    return Counter(str(r[field]).strip() for r in rows)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--train",required=True,type=Path)
    ap.add_argument("--dev",required=True,type=Path)
    ap.add_argument("--test",required=True,type=Path)
    ap.add_argument("--label-field",default="syndrome",help="exact raw source-label field")
    ap.add_argument("--frozen-labels",type=Path,help="optional newline-delimited 42-label vocabulary")
    ap.add_argument("--train-cap",type=int,default=1000)
    ap.add_argument("--top-k",type=int,default=50)
    ap.add_argument("--out-dir",required=True,type=Path)
    ap.add_argument("--expected-train",type=int,default=43180)
    ap.add_argument("--expected-dev",type=int,default=5486)
    ap.add_argument("--expected-test",type=int,default=5486)
    ap.add_argument("--expected-final-train",type=int,default=19125)
    ap.add_argument("--expected-final-dev",type=int,default=4411)
    ap.add_argument("--expected-final-test",type=int,default=4452)
    a=ap.parse_args()
    paths={"train":a.train,"dev":a.dev,"test":a.test}
    records={k:load_records(v) for k,v in paths.items()}
    expected={"train":a.expected_train,"dev":a.expected_dev,"test":a.expected_test}
    raw={}
    for split,rows in records.items():
        if len(rows)!=expected[split]:print(f"WARNING: {split} rows={len(rows)}, expected={expected[split]}")
        raw[split]=counts(rows,a.label_field,paths[split])
    universe=sorted(set().union(*(set(c) for c in raw.values())))
    table=[]
    for label in universe:
        tr,dv,te=(raw[k].get(label,0) for k in ("train","dev","test"))
        eligible=tr>=100 and dv>=10 and te>=10
        table.append({"label_raw":label,"train_raw":tr,"dev_raw":dv,"test_raw":te,"total_raw":tr+dv+te,
                      "eligible_by_thresholds":eligible,"train_after_cap":min(tr,a.train_cap) if a.train_cap>0 else tr})
    eligible=[r for r in table if r["eligible_by_thresholds"]]
    # Tie break is explicit; if >top-k qualify, compare this ordering with the historical rule.
    eligible.sort(key=lambda r:(-r["total_raw"],r["label_raw"]))
    selected=eligible[:a.top_k];selected_labels={r["label_raw"] for r in selected}
    for r in table:r["selected_by_recompute"]=r["label_raw"] in selected_labels
    final={"train":sum(r["train_after_cap"] for r in selected),"dev":sum(r["dev_raw"] for r in selected),"test":sum(r["test_raw"] for r in selected)}
    frozen=None
    if a.frozen_labels:
        labels=[x.strip() for x in a.frozen_labels.read_text(encoding="utf-8").splitlines() if x.strip()]
        frozen={"count":len(labels),"unique_count":len(set(labels)),"missing":sorted(set(labels)-selected_labels),
                "extra":sorted(selected_labels-set(labels)),"exact_set_match":set(labels)==selected_labels}
    a.out_dir.mkdir(parents=True,exist_ok=True)
    with (a.out_dir/"label_selection_support.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(table[0]));w.writeheader();w.writerows(table)
    result={"evidence_scope":"independent recomputation on supplied source splits; not proof of historical execution",
        "label_field":a.label_field,
        "source_files":{k:{"basename":p.name,"sha256":sha256(p),"rows":len(records[k])} for k,p in paths.items()},
        "raw_label_count_union":len(universe),"eligible_label_count":len(eligible),"selected_label_count":len(selected),
        "top_k":a.top_k,"top_k_cap_binding":len(eligible)>a.top_k,
        "criteria":{"train_min":100,"dev_min":10,"test_min":10,"ranking":"descending total support; ties broken by raw label ascending"},
        "final_counts_after_train_cap":final,
        "reported_final_counts":{"train":a.expected_final_train,"dev":a.expected_final_dev,"test":a.expected_final_test},
        "final_count_match":final=={"train":a.expected_final_train,"dev":a.expected_final_dev,"test":a.expected_final_test},
        "frozen_label_comparison":frozen,"support_csv":"label_selection_support.csv",
        "warning":"Do not manually adjust mismatches. A match verifies this downloaded source split and code path, not the exact historical May 2026 execution."}
    (a.out_dir/"label_selection_recompute.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
