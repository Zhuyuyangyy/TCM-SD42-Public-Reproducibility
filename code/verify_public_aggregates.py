#!/usr/bin/env python3
"""Read-only PUBLIC AGGREGATE consistency checks. Not an end-to-end replication."""
import csv, json, math, statistics
from pathlib import Path
R=Path(__file__).resolve().parents[1]
N=4218
M=("zybert","internlm3","macbert","qwen3")
def rows(p):
    with (R/p).open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def eq(g,e,k,t=5e-5):
    assert abs(g-e)<=t,(k,g,e)
def matrix(model,labels):
    with (R/"results"/f"confusion_matrix_{model}.csv").open(encoding="utf-8-sig",newline="") as f:
        data=list(csv.reader(f))
    assert data[0][0]=="gold\\pred" and data[0][1:]==labels
    assert [r[0] for r in data[1:]]==labels
    mat=[[int(x) for x in r[1:]] for r in data[1:]]
    assert len(mat)==42 and all(len(r)==42 and min(r)>=0 for r in mat)
    return mat
def mcnemar(a,b):
    n=a+b
    return min(1.0,2*sum(math.comb(n,k) for k in range(min(a,b)+1))/2**n)
def main():
    labels=(R/"code/labels_42.txt").read_text(encoding="utf-8").splitlines()
    assert len(labels)==len(set(labels))==42
    assert labels==json.loads((R/"label_space/syndrome_label_list.json").read_text(encoding="utf-8"))
    mats={m:matrix(m,labels) for m in M}
    gold=[sum(r) for r in mats["zybert"]]
    assert sum(gold)==N and [sum(r) for r in mats["macbert"]]==gold
    published={r["model"]:r for r in rows("results/clean4218_seed42.csv")}
    assert set(published)==set(M)
    for m,mat in mats.items():
        observed=[sum(r) for r in mat]
        omitted=[a-b for a,b in zip(gold,observed)]
        assert min(omitted)>=0 and sum(observed)+sum(omitted)==N
        tp=[mat[i][i] for i in range(42)]
        col=[sum(mat[j][i] for j in range(42)) for i in range(42)]
        f1=[2*tp[i]/(gold[i]+col[i]) for i in range(42)]
        recall=[tp[i]/gold[i] for i in range(42)]
        computed={"syn_acc@1":sum(tp)/N,"macro_f1":sum(f1)/42,
                  "weighted_f1":sum(gold[i]*f1[i] for i in range(42))/N,
                  "balanced_accuracy":sum(recall)/42,
                  "format_validity":sum(observed)/N,
                  "empty_pred_rate":sum(omitted)/N}
        for k,v in computed.items():eq(v,float(published[m][k]),m+"."+k)
        print(f"{m}: PASS / included {sum(observed)} / omitted {sum(omitted)} / correct {sum(tp)}")
    summary=rows("results/three_seed_summary.csv")
    assert len(summary)==8
    aliases={"ZY-BERT":"zybert","InternLM3-8B":"internlm3"}
    keys={"accuracy":"acc","macro_f1":"macro","weighted_f1":"wf1","balanced_accuracy":"bal"}
    for row in summary:
        data=json.loads((R/"results"/f"{aliases[row['model']]}_3seed_metrics.json").read_text(encoding="utf-8"))
        vals=[data[s][keys[row["metric"]]] for s in ("42","2026","7")]
        eq(statistics.mean(vals),float(row["mean_percent"]),"seed mean",1e-4)
        eq(statistics.stdev(vals),float(row["sd_percent"]),"seed sd",1e-4)
    print("three-seed means and sample SD: PASS")
    pairs=rows("results/pairwise_significance_seed42.csv")
    assert len(pairs)==6
    raw=[]
    for i,r in enumerate(pairs):
        a,b=int(r["a_correct_b_wrong"]),int(r["a_wrong_b_correct"])
        p=mcnemar(a,b);raw.append((i,p))
        eq(100*(a-b)/N,float(r["delta_accuracy_pp"]),"paired delta",0.0051)
        assert abs(p/float(r["mcnemar_exact_p"])-1)<0.01
    prev=0
    for rank,(i,p) in enumerate(sorted(raw,key=lambda x:x[1])):
        prev=max(prev,(6-rank)*p)
        assert abs(prev/float(pairs[i]["holm_adjusted_p"])-1)<0.01
    print("six McNemar exact p-values and Holm corrections: PASS")
    print("PUBLIC AGGREGATE CHECK PASS; NOT original-record, checkpoint, or bootstrap replication.")
if __name__=="__main__":main()
