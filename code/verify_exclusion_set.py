#!/usr/bin/env python3
"""Verify the frozen held-out exclusion ID set using authorized private inputs.

No raw text, IDs, or per-case predictions are printed. Inputs are not distributed
in this public repository. This check validates set equality, not patient-level
independence or the appropriateness of the historical similarity threshold.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path
SPLITS={"train":"train_4186.json","dev":"dev_420.json","pilot":"pilot_test_420.json","full":"full_test_4452.json"}
def raw_hash(row):return hashlib.sha256(row["input_text"].encode("utf-8")).hexdigest()
def load_csv(p):
    with open(p,encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--splits",required=True,help="authorized private split directory")
    ap.add_argument("--pairs",required=True,help="private near_duplicate_pairs.csv")
    ap.add_argument("--excluded",required=True,help="private excluded_heldout_ids.csv")
    ap.add_argument("--threshold",type=float,default=0.95)
    a=ap.parse_args();root=Path(a.splits)
    splits={k:json.load(open(root/f,encoding="utf-8")) for k,f in SPLITS.items()}
    # Keep every ID per raw hash; do not collapse repeated records to one ID.
    hashes={}
    for name,rows in splits.items():
        buckets={}
        for row in rows:buckets.setdefault(raw_hash(row),[]).append(str(row["id"]))
        hashes[name]=buckets
    other_hashes=set().union(*(set(hashes[k]) for k in ("train","dev","pilot")))
    raw_ids={i for h,items in hashes["full"].items() if h in other_hashes for i in items}
    pairs=load_csv(a.pairs)
    full_pairs=[r for r in pairs if r.get("split_b")=="full"]
    near_ids={str(r["id_b"]) for r in full_pairs if float(r["similarity"])>=a.threshold}
    derived=raw_ids|near_ids
    excluded={str(r["id"]) for r in load_csv(a.excluded)}
    result={"n_full":len(splits["full"]),"n_raw_exact_excluded":len(raw_ids),
        "n_near_duplicate_ids":len(near_ids),"n_union":len(derived),"n_archived_excluded":len(excluded),
        "set_equal":derived==excluded,"missing":len(excluded-derived),"extra":len(derived-excluded),
        "threshold":a.threshold,"pairs_rows":len(pairs),
        "pairs_sha256":hashlib.sha256(Path(a.pairs).read_bytes()).hexdigest(),
        "clinical_records_printed":False}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result["set_equal"] else 1
if __name__=="__main__":raise SystemExit(main())
