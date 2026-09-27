#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_leakage.py — v18 四层泄漏审计 (任务7)
==========================================
L1 完全重复: raw / normalized / clinical-content 三类哈希, 全跨划分对比
L2 近重复:   char n-gram TF-IDF cosine, 阈值带 0.95+ / 0.90-0.95 / 0.85-0.90
L3 患者级:   可用标识审计 (预期: 无稳定患者 ID → 诚实声明)
L4 标签泄漏: gold 标签在输入中的直现率 + 诊断短语 + 模型准确率分层
输出: dataset_audit/reports/ 下
  exact_duplicate_summary.csv / exact_duplicate_pairs.csv
  near_duplicate_pairs.csv / near_duplicate_summary.md / near_duplicate_review.xlsx
  patient_overlap.csv
  label_leakage_summary.md / label_leakage_examples.csv
"""
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]  # v18_working
DATA = ROOT / "dataset_audit/data"
REP = ROOT / "dataset_audit/reports"
PRED = ROOT / "predictions"
sys.path.insert(0, str(ROOT / "evaluation"))
from parse_label import LABELS_42  # noqa: E402
from parse_label import parse_label_from_output  # noqa: E402

LABEL_SET = set(LABELS_42)

SPLITS = {
    "train": DATA / "train_4186.json",
    "dev": DATA / "dev_420.json",
    "pilot": DATA / "pilot_test_420.json",
    "full": DATA / "full_test_4452.json",
}

TEMPLATE_PREFIXES = [
    "疾病名称：", "主诉：", "四诊信息：", "患者", "现病史：", "既往史：",
    "查体：", "辅助检查：", "症状：", "病史：", "体格检查：",
]
PUNCT_RE = re.compile(r"[\s，。、；：:（）()【】\[\]「」『』“”\"'《》,.?!\-—…%％+·/\\|]+")
DIGIT_RE = re.compile(r"\d+")
CASEID_RE = re.compile(r"tcm_sd_(train|test)_\d+")


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def norm_text(t):
    t = CASEID_RE.sub("", t)
    t = DIGIT_RE.sub("", t)
    t = PUNCT_RE.sub("", t)
    for pfx in TEMPLATE_PREFIXES:
        t = t.replace(pfx, "")
    return t


def sha(t):
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def input_text(it):
    return it.get("input_text", "") or ""


# ── 载入 ─────────────────────────────────────────────
data = {k: load(p) for k, p in SPLITS.items()}
print("载入:", {k: len(v) for k, v in data.items()})

for name, items in data.items():
    for it in items:
        it["_raw"] = input_text(it)
        it["_norm"] = norm_text(it.get("description", "") + it.get("detection", ""))
        it["_norm_input"] = norm_text(input_text(it))

# ══════════════════════════════════════════════════════
# L1 完全重复
# ══════════════════════════════════════════════════════
print("\n== L1 完全重复 ==")
HASH_TYPES = {"raw": "_raw", "norm_input": "_norm_input", "clinical": "_norm"}
summary_rows = []
pair_rows = []
for a in SPLITS:
    for b in SPLITS:
        if a > b:  # 只算一次 (a<b 字典序)
            continue
        counts = {}
        for hname, attr in HASH_TYPES.items():
            ha = Counter(h for it in data[a] if (h := it[attr]))  # 排除空文本
            hb = Counter(h for it in data[b] if (h := it[attr]))
            overlap = sum(min(ha.get(h, 0), hb.get(h, 0)) for h in set(ha) & set(hb))
            counts[hname] = overlap
        summary_rows.append([a, b, counts["raw"], counts["norm_input"], counts["clinical"]])
        # 收集具体配对 (clinical 重复的最严重)
        ha = defaultdict(list)
        for it in data[a]:
            if it["_norm"]:
                ha[it["_norm"]].append(it)
        hb = defaultdict(list)
        for it in data[b]:
            if it["_norm"]:
                hb[it["_norm"]].append(it)
        for h in set(ha) & set(hb):
            for x in ha[h][:3]:
                for y in hb[h][:3]:
                    pair_rows.append([a, b, x["id"], y["id"], x["syndrome_canonical"],
                                      y["syndrome_canonical"], "clinical", h[:16]])
        print(f"  {a} vs {b}: raw={counts['raw']} norm_input={counts['norm_input']} clinical={counts['clinical']}", flush=True)

with open(REP / "exact_duplicate_summary.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["split_a", "split_b", "raw_dup", "norm_input_dup", "clinical_dup"])
    w.writerows(summary_rows)
with open(REP / "exact_duplicate_pairs.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["split_a", "split_b", "id_a", "id_b", "gold_a", "gold_b", "hash_type", "hash_prefix"])
    w.writerows(pair_rows)

# ══════════════════════════════════════════════════════
# L2 近重复 (char n-gram TF-IDF cosine, 分块计算防 cgroup 2GB OOM)
# ══════════════════════════════════════════════════════
print("\n== L2 近重复 (TF-IDF char 2-4gram, chunked) ==", flush=True)
from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
from sklearn.metrics.pairwise import cosine_similarity  # noqa: E402

all_texts = []
meta = []  # (split, idx)
for name in ("train", "dev", "pilot", "full"):
    for i, it in enumerate(data[name]):
        all_texts.append(it["_norm_input"])
        meta.append((name, i))

vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=2,
                      sublinear_tf=True, norm="l2", max_features=200_000)
X = vec.fit_transform(all_texts)
print(f"  TF-IDF 矩阵: {X.shape} nnz={X.nnz}", flush=True)
import gc  # noqa: E402

# 按划分切分索引
idx_of = defaultdict(list)
for pos, (name, i) in enumerate(meta):
    idx_of[name].append(pos)

CROSS_PAIRS = [("train", "full"), ("dev", "full"), ("pilot", "full"),
               ("train", "dev"), ("train", "pilot"), ("dev", "pilot")]
BANDS = [(0.95, 1.01, ">=0.95"), (0.90, 0.95, "0.90-0.95"), (0.85, 0.90, "0.85-0.90")]
near_rows = []
band_counts = defaultdict(Counter)
CHUNK = 512

for a, b in CROSS_PAIRS:
    ia, ib = idx_of[a], idx_of[b]
    Xa = X[ia]
    Xb = X[ib]
    n_pairs = 0
    for start in range(0, len(ib), CHUNK):
        Xb_chunk = Xb[start:start + CHUNK]
        sim = cosine_similarity(Xb_chunk, Xa)  # dense |chunk| x |a|
        hits = np.argwhere(sim >= 0.85)
        for r, c in hits:
            s = float(sim[r, c])
            band = next(bn for lo, hi, bn in BANDS if lo <= s < hi)
            band_counts[(a, b)][band] += 1
            n_pairs += 1
            item_b = data[b][start + r]   # Xb_chunk 第 r 行 = split b 第 (start+r) 条
            item_a = data[a][c]
            near_rows.append([
                a, b, item_a["id"], item_b["id"], item_a["syndrome_canonical"],
                item_b["syndrome_canonical"], f"{s:.4f}", band,
                item_a["_norm_input"][:200], item_b["_norm_input"][:200],
            ])
        del sim, hits
        gc.collect()
    print(f"  {a}×{b}: {n_pairs} 对 >=0.85 (chunked)", flush=True)

with open(REP / "near_duplicate_pairs.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["split_a", "split_b", "id_a", "id_b", "gold_a", "gold_b",
                "similarity", "band", "text_a", "text_b"])
    w.writerows(near_rows)

near_summary = ["# 近重复摘要 (L2)"]
near_summary.append("| 对比 | >=0.95 | 0.90-0.95 | 0.85-0.90 | 合计 |")
near_summary.append("|------|--------|-----------|-----------|------|")
total_hi = 0
for a, b in CROSS_PAIRS:
    c = band_counts[(a, b)]
    s = sum(c.values())
    total_hi += c[">=0.95"]
    near_summary.append(f"| {a} vs {b} | {c['>=0.95']} | {c['0.90-0.95']} | {c['0.85-0.90']} | {s} |")
near_summary.append(f"\n>=0.95 跨划分近重复总数: {total_hi}")
with open(REP / "near_duplicate_summary.md", "w", encoding="utf-8") as f:
    f.write("\n".join(near_summary))

try:
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "near_duplicates"
    ws.append(["split_a", "split_b", "id_a", "id_b", "gold_a", "gold_b",
               "similarity", "band", "text_a", "text_b"])
    for row in near_rows:
        ws.append(row)
    wb.save(REP / "near_duplicate_review.xlsx")
    print(f"  xlsx: {len(near_rows)} 对")
except Exception as e:
    print(f"  xlsx 跳过: {e}")
print(f"  近重复对总数: {len(near_rows)} (>=0.85)")

# ══════════════════════════════════════════════════════
# L3 患者级重叠
# ══════════════════════════════════════════════════════
print("\n== L3 患者级 ==")
candidate_fields = ["id", "patient_id", "性别", "年龄", "birth", "visit_date", "就诊日期", "病历号"]
with open(REP / "patient_overlap.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["field", "present", "notes"])
    sample = data["train"][0]
    for field in candidate_fields:
        w.writerow([field, field in sample, "id 是病例号而非患者号" if field == "id" else ""])
    w.writerow(["conclusion", "no_stable_patient_identifier",
                "仅能保证病例级 id 零重叠; 患者级重叠无法排除 (见 Methods Limitations 声明模板)"])
print("  结论: 无稳定患者标识 → 患者级重叠无法排除, 按用户给定模板声明")

# ══════════════════════════════════════════════════════
# L4 标签泄漏
# ══════════════════════════════════════════════════════
print("\n== L4 标签泄漏 ==")
DIAG_PHRASES = re.compile(r"辨证为|证属|中医诊断|证型[：:]|西医诊断|诊断为")

def gold_in(text, gold):
    return gold in text if gold else False

leak_rows = []
per_split = {}
for name, items in data.items():
    n = len(items)
    gold_in_input = 0
    gold_in_desc = 0
    gold_in_det = 0
    any_label_in_input = 0
    diag_phrase = 0
    examples = []
    for it in items:
        gold = it["syndrome_canonical"]
        inp = it["_raw"]
        desc = it.get("description", "")
        det = it.get("detection", "")
        gi = gold_in(inp, gold)
        gd = gold_in(desc, gold)
        gdt = gold_in(det, gold)
        al = any(lab in inp for lab in LABELS_42)
        dp = bool(DIAG_PHRASES.search(inp + desc))
        gold_in_input += gi
        gold_in_desc += gd
        gold_in_det += gdt
        any_label_in_input += al
        diag_phrase += dp
        if gi or gd or gdt:
            examples.append([name, it["id"], gold, int(gi), int(gd), int(gdt),
                             inp[:150], desc[:150]])
    per_split[name] = {
        "n": n, "gold_in_input": gold_in_input, "gold_in_desc": gold_in_desc,
        "gold_in_det": gold_in_det, "any_label_in_input": any_label_in_input,
        "diag_phrase": diag_phrase,
    }
    print(f"  {name}: n={n} gold_in_input={gold_in_input} ({gold_in_input/n*100:.2f}%) "
          f"gold_in_desc={gold_in_desc} gold_in_det={gold_in_det} "
          f"any_label_in_input={any_label_in_input} diag_phrase={diag_phrase}")
    leak_rows.extend(examples[:50])  # 每划分最多 50 条示例

with open(REP / "label_leakage_examples.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["split", "id", "gold", "in_input", "in_description", "in_detection",
                "input_text_excerpt", "description_excerpt"])
    w.writerows(leak_rows)

# 准确率分层 (gold 在输入中出现 vs 不出现)
def load_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]

def acc(golds, preds):
    return sum(1 for g, p in zip(golds, preds) if g == p) / len(golds)

strat_rows = []
# pilot: MacBERT + SFT
pilot_items = data["pilot"]
mac_pilot = load_jsonl(PRED / "pilot420/macbert.jsonl")
sft_pilot = load_jsonl(PRED / "pilot420/sft_clean_v3_bnb_nf4.jsonl")
for model, preds in [("macbert", mac_pilot), ("sft_clean_v3", sft_pilot)]:
    g, p = [], []
    for it, pr in zip(pilot_items, preds):
        if it["syndrome_canonical"] != pr.get("gold", pr.get("gt_sx")):
            print(f"  ⚠️ pilot 对齐错位: {it['id']}")
        g.append(it["syndrome_canonical"])
        p.append(pr["pred"] if "pred" in pr else parse_label_from_output(pr.get("output", "")))
    mask = [gold_in(it["_raw"], it["syndrome_canonical"]) for it in pilot_items]
    strat_rows.append(["pilot420", model, "gold_in_input",
                       f"{acc(g, p)*100:.2f}", f"{acc([gg for gg, m in zip(g, mask) if m], [pp for pp, m in zip(p, mask) if m])*100:.2f}" if any(mask) else "n/a",
                       f"{acc([gg for gg, m in zip(g, mask) if not m], [pp for pp, m in zip(p, mask) if not m])*100:.2f}" if any(not m for m in mask) else "n/a",
                       f"{sum(mask)}/{len(mask)}"])
# heldout4452: MacBERT + SFT
full_items = data["full"]
mac_full = load_jsonl(PRED / "heldout4452/macbert.jsonl")
sft_full = load_jsonl(PRED / "heldout4452/sft_clean_v3.jsonl")
for model, preds in [("macbert", mac_full), ("sft_clean_v3", sft_full)]:
    g, p = [], []
    for it, pr in zip(full_items, preds):
        g.append(it["syndrome_canonical"])
        p.append(pr["pred"] if "pred" in pr else parse_label_from_output(pr.get("raw_output", "")))
    mask = [gold_in(it["_raw"], it["syndrome_canonical"]) for it in full_items]
    strat_rows.append(["heldout4452", model, "gold_in_input",
                       f"{acc(g, p)*100:.2f}",
                       f"{acc([gg for gg, m in zip(g, mask) if m], [pp for pp, m in zip(p, mask) if m])*100:.2f}" if any(mask) else "n/a",
                       f"{acc([gg for gg, m in zip(g, mask) if not m], [pp for pp, m in zip(p, mask) if not m])*100:.2f}" if any(not m for m in mask) else "n/a",
                       f"{sum(mask)}/{len(mask)}"])

lines = ["# 标签泄漏摘要 (L4)", "",
         "| split | n | gold_in_input | gold_in_desc | gold_in_det | any_label_in_input | diag_phrase |",
         "|-------|---|---------------|--------------|--------------|--------------------|-------------|"]
for name, s in per_split.items():
    lines.append(f"| {name} | {s['n']} | {s['gold_in_input']} ({s['gold_in_input']/s['n']*100:.2f}%) | "
                 f"{s['gold_in_desc']} | {s['gold_in_det']} | {s['any_label_in_input']} | {s['diag_phrase']} |")
lines += ["", "## 准确率分层 (gold 标签在输入中出现 vs 不出现)", "",
          "| dataset | model | cond | acc_all% | acc_label_present% | acc_label_absent% | n_present |",
          "|---------|-------|------|----------|--------------------|-------------------|-----------|"]
for r in strat_rows:
    lines.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {r[6]} |")
with open(REP / "label_leakage_summary.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("\n全部完成。输出目录:", REP)
