#!/usr/bin/env python3
"""Recompute MacBERT clean-test metrics from frozen positional predictions.

Prints aggregate metrics and hashes only; no clinical text or case IDs are emitted.
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
def load_json(path):
    with Path(path).open(encoding="utf-8") as f:obj=json.load(f)
    if isinstance(obj,list):return obj
    if isinstance(obj,dict):
        for k in ("data","records","examples","items"):
            if isinstance(obj.get(k),list):return obj[k]
    raise ValueError(f"{path}: expected a list of records")
def load_jsonl(path):
    with Path(path).open(encoding="utf-8") as f:return [json.loads(x) for x in f if x.strip()]
def load_ids(path,field):
    with Path(path).open(encoding="utf-8-sig",newline="") as f:return {str(r[field]) for r in csv.DictReader(f)}
def score(gold,pred,labels):
    n=len(gold);valid=set(labels);correct=sum(g==p for g,p in zip(gold,pred))
    tp=Counter();fp=Counter();fn=Counter();support=Counter()
    for g,p in zip(gold,pred):
        support[g]+=1
        if p in valid:
            if g==p:tp[g]+=1
            else:fp[p]+=1;fn[g]+=1
        else:fn[g]+=1
    f1=[];recall=[];weighted=0.0
    for lab in labels:
        den=2*tp[lab]+fp[lab]+fn[lab]
        v=2*tp[lab]/den if den else 0.0
        f1.append(v);weighted+=support[lab]*v
        recall.append(tp[lab]/support[lab] if support[lab] else 0.0)
    return {"n":n,"correct":correct,"accuracy":correct/n,"macro_f1":sum(f1)/len(labels),
        "weighted_f1":weighted/n,"balanced_accuracy":sum(recall)/len(labels),
        "valid_prediction_rate":sum(p in valid for p in pred)/n,
        "invalid_predictions":sum(p not in valid for p in pred),"empty_predictions":sum(p=="empty" for p in pred)}
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--full-test",required=True,type=Path)
    ap.add_argument("--clean-test",required=True,type=Path)
    ap.add_argument("--excluded-ids",required=True,type=Path)
    ap.add_argument("--predictions",required=True,type=Path)
    ap.add_argument("--labels",required=True,type=Path)
    ap.add_argument("--id-field",default="id")
    ap.add_argument("--gold-field",default="syndrome_canonical")
    ap.add_argument("--prediction-index-field",default="index")
    ap.add_argument("--prediction-gold-field",default="gold")
    ap.add_argument("--prediction-field",default="pred")
    ap.add_argument("--excluded-id-field",default="id")
    ap.add_argument("--out",required=True,type=Path)
    a=ap.parse_args()
    full=load_json(a.full_test);clean=load_json(a.clean_test);preds=load_jsonl(a.predictions)
    labels=[x.strip() for x in a.labels.read_text(encoding="utf-8").splitlines() if x.strip()]
    assert len(labels)==len(set(labels))==42,"expected 42 unique frozen labels"
    full_ids=[str(r[a.id_field]) for r in full];full_gold=[str(r[a.gold_field]) for r in full]
    clean_ids=[str(r[a.id_field]) for r in clean];clean_gold=[str(r[a.gold_field]) for r in clean]
    assert len(full)==4452 and len(set(full_ids))==4452,"full test must have 4,452 unique IDs"
    assert len(clean)==4218 and len(set(clean_ids))==4218,"clean test must have 4,218 unique IDs"
    assert set(clean_ids).issubset(set(full_ids)),"clean IDs are not a subset of full test"
    excluded=load_ids(a.excluded_ids,a.excluded_id_field)
    assert set(full_ids)-set(clean_ids)==excluded,"excluded IDs must equal full-test IDs minus clean-test IDs"
    assert len(preds)==len(full),"prediction file must have 4,452 rows"
    ordered=[None]*len(full)
    for row in preds:
        idx=int(row[a.prediction_index_field])
        if idx<1 or idx>len(full) or ordered[idx-1] is not None:raise ValueError("prediction indices must be unique 1-based 1..4452")
        ordered[idx-1]=row
    assert all(r is not None for r in ordered),"missing prediction index"
    assert [str(r[a.prediction_gold_field]) for r in ordered]==full_gold,"prediction gold sequence differs from frozen full-test order"
    full_index={rid:i for i,rid in enumerate(full_ids)}
    assert [full_gold[full_index[rid]] for rid in clean_ids]==clean_gold,"clean-test ID/gold order mismatch"
    selected=[full_index[rid] for rid in clean_ids]
    clean_pred=[str(ordered[i][a.prediction_field]) for i in selected]
    result={"model":"MacBERT","evidence_scope":"metrics recomputed from frozen predictions; does not recreate training/checkpoint provenance",
        "input_sha256":{"full_test":sha256(a.full_test),"clean_test":sha256(a.clean_test),"excluded_ids":sha256(a.excluded_ids),
                        "predictions":sha256(a.predictions),"labels":sha256(a.labels)},
        "alignment":{"full_rows":len(full),"prediction_rows":len(preds),"gold_sequence_matches_full":True,
                     "clean_rows":len(clean),"clean_gold_sequence_matches":True,"excluded_count":len(excluded)},
        "metrics":score(clean_gold,clean_pred,labels),
        "reported_reference_percent":{"accuracy":62.78,"macro_f1":56.81,"weighted_f1":63.94,"balanced_accuracy":72.63}}
    result["metrics_percent"]={k:100*v for k,v in result["metrics"].items() if k in ("accuracy","macro_f1","weighted_f1","balanced_accuracy","valid_prediction_rate")}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
