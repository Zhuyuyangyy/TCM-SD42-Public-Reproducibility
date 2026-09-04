#!/usr/bin/env python3
"""Paired accuracy comparison for standardized prediction JSONL files.

Expected JSONL fields per row: id, gold, pred.
All prediction files must contain the same IDs and gold labels.
"""
import argparse, json, random
from pathlib import Path
from scipy.stats import binomtest


def load_jsonl(path):
    rows={}
    with open(path, encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            r=json.loads(line)
            rows[str(r['id'])]=(r['gold'], r['pred'])
    return rows


def paired_compare(a, b, n_boot=2000, seed=20260516):
    ids=sorted(set(a) & set(b))
    if set(a) != set(b):
        raise ValueError('Prediction files do not contain identical ID sets.')
    gold=[]; pa=[]; pb=[]
    for i in ids:
        ga, xa=a[i]; gb, xb=b[i]
        if ga != gb: raise ValueError(f'Gold mismatch for id={i}')
        gold.append(ga); pa.append(xa); pb.append(xb)
    n=len(ids)
    ca=[g==p for g,p in zip(gold,pa)]
    cb=[g==p for g,p in zip(gold,pb)]
    diff=sum(ca)/n-sum(cb)/n
    rng=random.Random(seed)
    ds=[]
    for _ in range(n_boot):
        idx=[rng.randrange(n) for _ in range(n)]
        ds.append(sum(ca[i]-cb[i] for i in idx)/n)
    ds.sort()
    lo=ds[int(n_boot*0.025)]
    hi=ds[int(n_boot*0.975)-1]
    n10=sum(x and not y for x,y in zip(ca,cb))
    n01=sum((not x) and y for x,y in zip(ca,cb))
    p=binomtest(n10, n10+n01, p=0.5).pvalue if n10+n01 else 1.0
    return {'n':n,'acc_diff':diff,'ci_lower':lo,'ci_upper':hi,'n10':n10,'n01':n01,'mcnemar_exact_p':float(p)}


def holm(pairs):
    ordered=sorted(pairs.items(), key=lambda kv: kv[1])
    m=len(ordered); prev=0.0; out={}
    for i,(k,p) in enumerate(ordered):
        adj=max(prev,(m-i)*p); prev=adj; out[k]=min(adj,1.0)
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--pred', action='append', required=True, help='NAME=path.jsonl; repeat for >=2 models')
    ap.add_argument('--bootstrap', type=int, default=2000)
    ap.add_argument('--seed', type=int, default=20260516)
    ap.add_argument('--output', default='pairwise_stats.json')
    args=ap.parse_args()
    models={}
    for spec in args.pred:
        name,path=spec.split('=',1); models[name]=load_jsonl(path)
    names=list(models); results={}; raw={}
    for i in range(len(names)):
        for j in range(i+1,len(names)):
            key=f'{names[i]}_vs_{names[j]}'
            r=paired_compare(models[names[i]],models[names[j]],args.bootstrap,args.seed)
            results[key]=r; raw[key]=r['mcnemar_exact_p']
    adjusted=holm(raw)
    for k,v in adjusted.items(): results[k]['holm_p']=v
    Path(args.output).write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(results,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
