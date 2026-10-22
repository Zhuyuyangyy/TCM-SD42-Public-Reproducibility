#!/usr/bin/env python3
"""Recompute paired correctness and exact McNemar/Holm on frozen predictions.
Private clinical inputs and case-level predictions are not distributed here.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,re,sys
from itertools import combinations
from pathlib import Path
from scipy.stats import binomtest

TEMPLATE_LABELS=["疾病名称：","疾病名称:","主诉：","主诉:","四诊信息：","四诊信息:","现病描述摘要：","现病描述摘要:","病史：","病史:","舌脉：","舌脉:","中医证型：","中医证型:","证型：","证型:"]
PUNCT=re.compile(r"[\s\u3000-\u303f\uff00-\uff0f\uff1a-\uff20\uff3b-\uff40\uff5b-\uff65!-/:-@\[\x60{-~]")

def norm_text(t):
    s=t.strip().lower()
    for lab in TEMPLATE_LABELS:s=s.replace(lab,"")
    s=re.sub(r"tcm_sd_(?:train|test)_\d+","",s)
    s=re.sub(r"(病例|病案|编号|序号|记录|id)\s*[:：]?\s*[0-9a-z\-]+","",s)
    return PUNCT.sub("",re.sub(r"\d+","",s))

def sha(s):return hashlib.sha256(s.encode("utf-8")).hexdigest()
def keep_first(keys):
    seen=set();keep=[]
    for i,k in enumerate(keys):
        if k not in seen:keep.append(i);seen.add(k)
    return keep
def load_jsonl(path):
    with open(path,encoding="utf-8") as f:return [json.loads(x) for x in f if x.strip()]
def holm(raw):
    names=list(raw);order=sorted(range(len(names)),key=lambda i:raw[names[i]])
    out=[0.0]*len(names);prev=0.0;m=len(names)
    for rank,i in enumerate(order):
        prev=max(prev,(m-rank)*raw[names[i]]);out[i]=min(prev,1.0)
    return {names[i]:out[i] for i in range(len(names))}
def pair_cells(idx,ca,cb):
    n11=n10=n01=n00=0
    for i in idx:
        a,b=ca[i],cb[i]
        if a and b:n11+=1
        elif a:n10+=1
        elif b:n01+=1
        else:n00+=1
    correct_a=n11+n10;correct_b=n11+n01
    assert n11+n10+n01+n00==len(idx)
    assert n10-n01==correct_a-correct_b,"McNemar identity violated"
    p=float(binomtest(n10,n10+n01,0.5).pvalue) if n10+n01 else 1.0
    return {"n":len(idx),"n11":n11,"n10":n10,"n01":n01,"n00":n00,"correct_a":correct_a,"correct_b":correct_b,
            "acc_a":correct_a/len(idx),"acc_b":correct_b/len(idx),"delta_pp":(correct_a-correct_b)/len(idx)*100,"p":p}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--clean",required=True,help="authorized private clean 4218 JSON")
    ap.add_argument("--preds",required=True,help="comma-separated name=path[:index][:raw]")
    ap.add_argument("--gold-field",default="syndrome_canonical")
    ap.add_argument("--pairs",default="")
    ap.add_argument("--out-csv",required=True)
    a=ap.parse_args()
    clean=json.load(open(a.clean,encoding="utf-8"));ids=[str(r["id"]) for r in clean]
    gold=[r[a.gold_field] for r in clean];texts=[r["input_text"] for r in clean]
    assert len(set(ids))==len(ids),"duplicate clean IDs"
    pred={}
    for spec in a.preds.split(","):
        name,path=spec.split("=",1);flags=set()
        while path.endswith(":index") or path.endswith(":raw"):path,flag=path.rsplit(":",1);flags.add(flag)
        rows=load_jsonl(path)
        if "index" in flags:
            by={int(r["index"]):r for r in rows};ordered=[by[int(i.rsplit("_",1)[1])+1] for i in ids]
        else:
            by={str(r["id"]):r for r in rows};assert set(by)==set(ids),f"{name}: ID set mismatch";ordered=[by[i] for i in ids]
        obs=[r.get("gold",r.get("gold_syndrome")) for r in ordered]
        assert all(g is None or g==gg for g,gg in zip(obs,gold)),f"{name}: gold mismatch"
        if "raw" in flags:
            sys.path.insert(0,str(Path(__file__).resolve().parent))
            from parse_label import parse_label_from_output
            pred[name]=[parse_label_from_output(r.get("raw_output","")) for r in ordered]
        else:pred[name]=[r["pred"] for r in ordered]
    corr={m:[g==p for g,p in zip(gold,pred[m])] for m in pred}
    subsets={"S0_full":list(range(len(ids))),"S1_raw_dedup":keep_first([sha(t) for t in texts]),
             "S2_norm_dedup":keep_first([sha(norm_text(t)) for t in texts])}
    pairs=[tuple(x.split(":")) for x in a.pairs.split(",")] if a.pairs else list(combinations(sorted(pred),2))
    out=[]
    for sub,idx in subsets.items():
        rawp={};current={}
        for x,y in pairs:
            r=pair_cells(idx,corr[x],corr[y]);current[(x,y)]=r;rawp[f"{x}-vs-{y}"]=r["p"]
        adj=holm(rawp)
        for (x,y),r in current.items():
            out.append({"subset":sub,"n":r["n"],"pair":f"{x}-vs-{y}","n10_A_right_B_wrong":r["n10"],
                "n01_A_wrong_B_right":r["n01"],"n11":r["n11"],"n00":r["n00"],"acc_A":f'{r["acc_a"]:.6f}',
                "acc_B":f'{r["acc_b"]:.6f}',"delta_acc_pp":f'{r["delta_pp"]:+.4f}',
                "p_exact_mcnemar":f'{r["p"]:.6e}',"p_holm":f'{adj[f"{x}-vs-{y}"]:.6e}'})
    with open(a.out_csv,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
    print(json.dumps({"rows":len(out),"subsets":{k:len(v) for k,v in subsets.items()},"models":sorted(pred),
        "clinical_inputs_not_printed":True},ensure_ascii=False,indent=2))
if __name__=="__main__":main()
