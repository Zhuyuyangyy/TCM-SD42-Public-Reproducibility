#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TCM-SD42 Figures 2-8: deterministic vector rebuild (BMC/journal style).

Rules: white ground, Arial, thin grey/black rules, plain black bold panel
letters, no panel titles, Okabe-Ito model colours, despined axes.
"""
import csv
import math
import os

import figure_data as fd

INK = "#222222"
MUT = "#666666"
RULE = "#B8B8B8"
SOFT = "#EAEAEA"
NAVY = "#1B4F72"

BLUE = "#0072B2"
ORANGE = "#D55E00"
GREEN = "#009E73"
MAGENTA = "#CC79A7"

FONT = "Arial, Helvetica, sans-serif"
OUT = os.path.dirname(os.path.abspath(__file__))

W = H = 0
NAME = ""
S = []


def begin(w, h, name):
    global W, H, NAME, S
    W, H, NAME, S = w, h, name, []
    S.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
    S.append(f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>')


def T(x, y, s, size=24, fill=INK, weight=400, anchor="start", italic=False):
    st = (f'font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
          f'fill="{fill}" text-anchor="{anchor}"')
    if italic:
        st += ' font-style="italic"'
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    S.append(f'<text x="{x}" y="{y}" {st}>{s}</text>')


def R(x, y, w, h, fill="none", stroke=INK, sw=1.3, rx=0, dash=None, op=1):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    S.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
             f'stroke="{stroke}" stroke-width="{sw}"{d} opacity="{op}"/>')


def L(x1, y1, x2, y2, stroke=RULE, sw=1, dash=None, op=1):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    S.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
             f'stroke-width="{sw}"{d} opacity="{op}" stroke-linecap="round"/>')


def P(pts, fill="none", stroke=INK, sw=1.2, closed=True, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    tag = "polygon" if closed else "polyline"
    p = " ".join(f"{a:.2f},{b:.2f}" for a, b in pts)
    S.append(f'<{tag} points="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d} stroke-linejoin="round"/>')


def C(cx, cy, r, fill=INK, stroke="none", sw=1):
    S.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')


def arrow(x1, y1, x2, y2, color=INK, sw=1.8, hs=8, dash=None):
    dx, dy = x2 - x1, y2 - y1
    ln = math.hypot(dx, dy)
    if ln == 0:
        return
    ux, uy = dx / ln, dy / ln
    if dash is None:
        L(x1, y1, x2 - ux * hs * 1.25, y2 - uy * hs * 1.25, stroke=color, sw=sw, dash=dash)
    S.append(f'<line x1="{x1}" y1="{y1}" x2="{x2 - ux * hs * 1.25:.2f}" y2="{y2 - uy * hs * 1.25:.2f}" '
             f'stroke="{color}" stroke-width="{sw}"' + (f' stroke-dasharray="{dash}"' if dash else "") + ' stroke-linecap="round"/>')
    p2 = (x2 - ux * hs - uy * hs * 0.5, y2 - uy * hs + ux * hs * 0.5)
    p3 = (x2 - ux * hs + uy * hs * 0.5, y2 - uy * hs - ux * hs * 0.5)
    P([(x2, y2), p2, p3], fill=color, stroke=color, sw=1)


def panel(x, y, letter):
    T(x, y, letter, 40, "#111111", 700)


def lines(x, y, seq, size=24, fill=INK, weight=400, anchor="start", lh=30):
    for i, s in enumerate(seq):
        T(x, y + i * lh, s, size, fill, weight, anchor)


def cbox(x, y, w, h, seq, stroke=INK, fill="#FFFFFF", sw=1.4, rx=0,
         size=24, weight=400, color=INK, lh=30, dash=None):
    R(x, y, w, h, fill=fill, stroke=stroke, sw=sw, rx=rx, dash=dash)
    total = (len(seq) - 1) * lh
    top = y + h / 2 - total / 2 + size * 0.36
    for i, s in enumerate(seq):
        T(x + w / 2, top + i * lh, s, size, color, weight, "middle")


def save():
    svg = "\n".join(S) + "\n</svg>"
    with open(os.path.join(OUT, f"{NAME}.svg"), "w", encoding="utf-8") as f:
        f.write(svg)
    html = ('<!doctype html><html><head><meta charset="utf-8"><style>'
            'html,body{margin:0;padding:0;background:#fff}svg{display:block}'
            f'</style></head><body>{svg}</body></html>')
    with open(os.path.join(OUT, f"{NAME}.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(NAME, "ok", len(svg))


# ---------------------------------------------------------------- data
def load_support():
    p = os.path.join(OUT, "source_data", "classwise_metrics.csv")
    with open(p, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return {int(r["label_id"]): r for r in rows}


# ================================================================= FIG 2
def fig2():
    begin(2000, 620, "Figure2")
    L(980, 60, 980, 560, stroke="#8A8A8A", sw=1.1, dash="6 6")
    panel(46, 96, "A")

    steps = [
        (170, 150, 560, 84, ["54,152 clinical records"], 26, True),
        (210, 286, 480, 84, ["43 eligible source forms",
                             "train \u2265 100 \u00b7 dev \u2265 10 \u00b7 test \u2265 10"], 25, True),
        (250, 422, 400, 84, ["42 frozen labels", "syndrome_canonical"], 26, True),
    ]
    for x, y, w, h, seq, size, _ in steps:
        R(x, y, w, h, fill="#F4F7FA", stroke=INK, sw=1.3)
        total = (len(seq) - 1) * 30
        top = y + h / 2 - total / 2 + size * 0.36
        T(x + w / 2, top, seq[0], size, INK, 600, "middle")
        if len(seq) > 1:
            T(x + w / 2, top + 30, seq[1], 20, MUT, 400, "middle")

    arrow(450, 234, 450, 286, sw=2)
    arrow(450, 370, 450, 422, sw=2)

    L(654, 452, 694, 446, stroke="#999999", sw=1)
    L(654, 476, 694, 478, stroke="#999999", sw=1)
    T(700, 452, "41 one-to-one mappings", 21, INK, 400)
    T(700, 484, "1 two-to-one collision", 21, INK, 400)

    panel(1030, 96, "B")
    cbox(1040, 210, 400, 86, ["38 identity-preserved", "labels (KEEP)"], size=23)
    cbox(1040, 350, 400, 86, ["4 MERGE/rename", "mappings"], size=23)
    cbox(1560, 268, 380, 110, ["40 distinct", "normalized categories"], size=24, weight=600)

    L(1440, 253, 1500, 253, stroke=INK, sw=1.4)
    L(1440, 393, 1500, 393, stroke=INK, sw=1.4)
    L(1500, 253, 1500, 393, stroke=INK, sw=1.4)
    arrow(1500, 323, 1560, 323, sw=1.8)

    T(1040, 500, "Audit-only correspondence; frozen 42-class target unchanged",
      21, MUT, 400, italic=True)
    T(1040, 540, "label-level audit \u00b7 no model target was altered", 20, MUT, 400)
    save()


# ================================================================= FIG 3
def fig3():
    begin(2000, 740, "Figure3")
    L(505, 60, 505, 720, stroke="#8A8A8A", sw=1.1, dash="6 6")
    L(1400, 60, 1400, 720, stroke="#8A8A8A", sw=1.1, dash="6 6")
    panel(46, 96, "A")

    blocks = [
        (60, 150, 410, 84, ["4,186 training records", "91\u2013100 per class"]),
        (60, 260, 410, 84, ["420 development records", "10 per class"]),
        (60, 370, 410, 84, ["4,452-record source test pool", "before decontamination"]),
        (60, 480, 410, 84, ["4,218 clean held-out test records", "primary evaluation"]),
    ]
    for i, (x, y, w, h, seq) in enumerate(blocks):
        fill = "#EAF1F7" if i == 3 else "#FFFFFF"
        sw = 2.0 if i == 2 else 1.3
        R(x, y, w, h, fill=fill, stroke=INK, sw=sw)
        T(x + 16, y + 34, seq[0], 24, INK, 600)
        T(x + 16, y + 64, seq[1], 20, MUT, 400)

    panel(520, 96, "B")
    arrow(470, 412, 540, 412, sw=2)
    C(540, 412, 4.5)
    L(540, 210, 540, 510, stroke=INK, sw=2)
    C(540, 510, 4)
    arrow(540, 210, 600, 210, sw=1.8)
    arrow(540, 510, 600, 510, sw=1.8)

    cbox(600, 160, 560, 100, ["SHA-256 exact match on raw input_text",
                              "6 exact duplicates (5 unique hashes)"],
         size=22, lh=30)
    cbox(600, 460, 560, 100, ["TF-IDF cosine \u2265 0.95 (char 2\u20134-gram)",
                              "228 near-duplicates excluded"],
         size=22, lh=30)

    L(1200, 210, 1240, 210, stroke=INK, sw=1.4)
    L(1200, 510, 1240, 510, stroke=INK, sw=1.4)
    L(1240, 210, 1240, 560, stroke=INK, sw=1.4)
    arrow(1240, 560, 1240, 600, sw=1.8)

    cbox(600, 600, 740, 90, ["234 excluded  \u00b7  4,452 \u2212 6 \u2212 228 = 4,218 clean records"],
         size=23, weight=600)

    panel(1450, 96, "C")
    cbox(1460, 150, 470, 66, ["420 development records"], size=23, weight=600)
    arrow(1695, 216, 1695, 258, sw=1.8)
    cbox(1460, 258, 470, 96, ["54 instances in train\u2013dev pairs",
                              "\u2265 0.95 (18 exact duplicates) excluded"],
         size=21, lh=28)
    arrow(1695, 354, 1695, 396, sw=1.8)
    cbox(1460, 396, 470, 60, ["366 development records remaining"], size=22, weight=600)

    R(1460, 486, 470, 240, fill="#F7F9FB", stroke="#D5DCE3", sw=1.1)
    T(1478, 518, "ZY-BERT development Macro-F1", 22, BLUE, 700)

    T(1478, 542, "record-level audit", 18, MUT, 400)
    ax0, ax1 = 1700, 1900
    def mx(v): return ax0 + (v - 0.76) / 0.06 * (ax1 - ax0)
    L(ax0, 642, ax1, 642, stroke=INK, sw=1.2)
    for v in (0.76, 0.78, 0.80):
        L(mx(v), 642, mx(v), 648, stroke=INK, sw=1)
        T(mx(v), 668, f"{v:.2f}", 19, MUT, 400, "middle")

    T(1478, 575, "Before exclusion", 21, INK, 400)
    T(1478, 611, "After exclusion", 21, INK, 400)
    T(mx(0.8056), 552, "0.8056", 21, INK, 700, "middle")
    T(mx(0.7742), 588, "0.7742", 21, INK, 700, "middle")
    C(mx(0.8056), 576, 6, BLUE)
    C(mx(0.7742), 612, 6, BLUE)
    L(mx(0.8056), 576, mx(0.7742), 612, stroke=BLUE, sw=1.2)

    T(1478, 706, "\u0394 \u22120.0314  (\u22123.9%)", 21, ORANGE, 700)
    save()


# ================================================================= FIG 4
def fig4():
    begin(2000, 1060, "Figure4")
    panel(46, 96, "A")

    cbox(60, 330, 300, 220, ["Same standardized", "clinical record", "(input_text)",
                             "", "Frozen label order", "42 syndrome classes"],
         size=23, lh=32)

    panel(440, 96, "B")

    R(440, 120, 1140, 410, fill="#FCFCFC", stroke="#B9C2CA", sw=1.1, dash="6 5")
    T(456, 150, "Discriminative systems", 22, MUT, 700)

    R(470, 176, 520, 90, fill="#FFFFFF", stroke=BLUE, sw=2)
    lines(486, 212, ["ZY-BERT (TCM-domain encoder;", "seeds 42, 2026, 7)"], 22, INK, 400, lh=28)
    cbox(1060, 176, 450, 90, ["Fine-tuned 42-class", "classification head"], size=22, lh=28)

    R(470, 344, 520, 90, fill="#FFFFFF", stroke=GREEN, sw=2)
    lines(486, 380, ["MacBERT (general-domain encoder;", "historical seed-42)"], 22, INK, 400, lh=28)
    cbox(1060, 344, 450, 90, ["42-class", "classification head"], size=22, lh=28)

    arrow(990, 221, 1060, 221, sw=1.8)
    arrow(990, 389, 1060, 389, sw=1.8)

    R(440, 570, 1140, 420, fill="#FCFCFC", stroke="#B9C2CA", sw=1.1, dash="6 5")
    T(456, 600, "Generative systems", 22, MUT, 700)

    R(470, 626, 420, 86, fill="#FFFFFF", stroke=ORANGE, sw=2)
    lines(486, 660, ["InternLM3-8B (4-bit NF4 QLoRA;", "seeds 42, 2026, 7)"], 21, INK, 400, lh=28)
    R(470, 742, 420, 86, fill="#FFFFFF", stroke=MAGENTA, sw=2)
    lines(486, 776, ["Qwen3-8B (LoRA-SFT;", "historical seed-42)"], 21, INK, 400, lh=28)

    L(890, 669, 940, 669, stroke=INK, sw=1.4)
    L(890, 785, 940, 785, stroke=INK, sw=1.4)
    L(940, 669, 940, 785, stroke=INK, sw=1.4)
    C(940, 727, 4)
    arrow(940, 727, 1000, 727, sw=1.8)

    cbox(1000, 684, 240, 86, ["Prompt /", "LoRA adapter"], size=22, lh=28)
    arrow(1240, 727, 1276, 727, sw=1.8)
    cbox(1276, 684, 280, 86, ["Generated label +", "templated rationale"], size=21, lh=28)
    arrow(1416, 770, 1416, 806, sw=1.8)
    cbox(1276, 806, 280, 60, ["Frozen parser v18"], size=22, weight=600)

    panel(1620, 96, "C")
    R(1620, 210, 320, 460, fill="#F4F7FA", stroke=INK, sw=1.5)
    T(1780, 246, "Frozen 42-class", 22, NAVY, 700, "middle")
    T(1780, 274, "output space", 22, NAVY, 700, "middle")
    for r in range(7):
        for c in range(6):
            R(1660 + c * 40, 300 + r * 46, 26, 32, fill="#FFFFFF", stroke="#9FB4C6", sw=1)

    arrow(1510, 221, 1620, 280, sw=1.6)
    arrow(1510, 389, 1620, 380, sw=1.6)
    arrow(1556, 836, 1620, 700, sw=1.6)

    arrow(360, 440, 400, 440, sw=2)
    C(400, 440, 4.5)
    L(400, 221, 400, 727, stroke=INK, sw=2)
    C(400, 221, 4)
    C(400, 727, 4)
    arrow(400, 221, 440, 221, sw=1.8)
    arrow(400, 727, 440, 727, sw=1.8)
    save()


# ================================================================= FIG 5
def fig5():
    begin(2000, 1360, "Figure5")
    panel(46, 96, "A")

    # legend
    lx = 1110
    for i, (nm, col) in enumerate([("ZY-BERT", BLUE), ("InternLM3-8B", ORANGE),
                                   ("MacBERT", GREEN), ("Qwen3-8B", MAGENTA)]):
        C(lx + i * 225, 90, 7, col)
        T(lx + i * 225 + 16, 99, nm, 20, INK, 400)

    X0, X1 = 170, 1930
    Y0, Y1 = 570, 150
    L(X0, Y0, X1, Y0, stroke=INK, sw=1.2)
    for v in range(0, 101, 20):
        yy = Y0 - v / 100 * (Y0 - Y1)
        L(X0, yy, X1, yy, stroke=SOFT, sw=0.9)
        T(X0 - 14, yy + 7, str(v), 21, MUT, 400, "end")
    T(40, 130, "Score (%)", 22, MUT, 400)

    groups = ["Accuracy", "Macro-F1", "Weighted-F1", "Balanced accuracy"]
    gx = [420, 880, 1340, 1800]
    data = fd.metric_matrix()
    cols = [BLUE, ORANGE, GREEN, MAGENTA]
    offs = [-105, -35, 35, 105]
    for gi, gname in enumerate(groups):
        T(gx[gi], Y0 + 44, gname, 24, INK, 600, "middle")
        for mi in range(4):
            v = data[mi][gi]
            xx = gx[gi] + offs[mi]
            yy = Y0 - v / 100 * (Y0 - Y1)
            C(xx, yy, 7, cols[mi])
            T(xx, yy - 16, f"{v:.2f}", 21, INK, 600, "middle")

    panel(46, 700, "B")
    pairs = fd.acc_pairs()
    FX0, FX1 = 470, 790
    def fx(v): return FX0 + v / 18 * (FX1 - FX0)
    L(fx(0), 770, fx(0), 1230, stroke=MUT, sw=1, dash="3 4")
    for i, (nm, d, lo, hi, dis, pv) in enumerate(pairs):
        yy = 800 + i * 78
        T(50, yy + 7, nm, 21, INK, 400)
        L(fx(lo), yy, fx(hi), yy, stroke=INK, sw=1.6)
        L(fx(lo), yy - 7, fx(lo), yy + 7, stroke=INK, sw=1.6)
        L(fx(hi), yy - 7, fx(hi), yy + 7, stroke=INK, sw=1.6)
        C(fx(d), yy, 5, INK)
        T(812, yy + 7, f"+{d:.2f} pp", 20, INK, 700)
        T(912, yy + 7, f"[{lo:.2f}, {hi:.2f}]", 19, MUT, 400)
        T(812, yy + 30, f"discordant {dis}  \u00b7  p {pv}", 15, MUT, 400)
    L(FX0, 1230, FX1, 1230, stroke=INK, sw=1.2)
    for v in (0, 5, 10, 15):
        L(fx(v), 1230, fx(v), 1236, stroke=INK, sw=1)
        T(fx(v), 1256, str(v), 20, MUT, 400, "middle")
    T(FX1, 1292, "Accuracy difference (pp)", 21, MUT, 400, "end")

    panel(1080, 700, "C")
    MACRO, BA = fd.mf1_forest(), fd.ba_forest()
    CX0, CX1 = 1380, 1780
    def cx(v): return CX0 + (v + 2.5) / 17.5 * (CX1 - CX0)
    L(cx(0), 800, cx(0), 1240, stroke=MUT, sw=1, dash="3 4")

    C(1120, 764, 6, INK)
    T(1134, 771, "Macro-F1", 19, MUT, 400)
    R(1250, 757, 10, 10, fill="#FFFFFF", stroke=INK, sw=1.2)
    T(1266, 771, "Balanced accuracy", 19, MUT, 400)
    names = ["ZY-BERT vs InternLM3-8B", "ZY-BERT vs MacBERT", "ZY-BERT vs Qwen3-8B",
             "InternLM3-8B vs MacBERT", "InternLM3-8B vs Qwen3-8B", "MacBERT vs Qwen3-8B"]

    for i in range(6):
        yy = 840 + i * 72
        if i == 3:
            R(1080, yy - 36, 820, 72, fill="#F9EBEA", stroke="none", sw=0)
        T(1340, yy + 7, names[i], 19, ORANGE if i == 3 else INK, 400, "end")

        mv, mlo, mhi = MACRO[i]
        L(cx(mlo), yy - 14, cx(mhi), yy - 14, stroke=INK, sw=1.3)
        C(cx(mv), yy - 14, 5, INK)

        bv, blo, bhi = BA[i]
        L(cx(blo), yy + 14, cx(bhi), yy + 14, stroke=INK, sw=1.3)
        R(cx(bv) - 5, yy + 9, 10, 10, fill="#FFFFFF", stroke=INK, sw=1.2)

    L(CX0, 1250, CX1, 1250, stroke=INK, sw=1.2)
    for v in (0, 5, 10, 15):
        L(cx(v), 1250, cx(v), 1256, stroke=INK, sw=1)
        T(cx(v), 1276, str(v), 20, MUT, 400, "middle")
    T(CX1, 1312, "Metric difference (pp)", 21, MUT, 400, "end")
    save()


# ================================================================= FIG 6
def fig6():
    begin(2000, 1360, "Figure6")
    panel(50, 96, "A")

    SX = [200, 370, 540]
    AY0, AY1 = 520, 190
    def ay(v): return AY0 - (v - 66) / 12.0 * (AY0 - AY1)
    L(140, AY0, 620, AY0, stroke=INK, sw=1.2)
    for v in (68, 70, 72, 74, 76):
        yy = ay(v)
        L(140, yy, 620, yy, stroke=SOFT, sw=0.9)
        T(128, yy + 7, str(v), 21, MUT, 400, "end")
    for xx in (150, 138):
        L(xx, AY0 - 14, xx + 14, AY0 + 6, stroke=INK, sw=1.2)
    T(40, 150, "Accuracy (%)", 22, MUT, 400)
    T(176, 510, "axis break \u00b7 range 66\u201378", 15, MUT, 400)

    _seeds = fd.seeds()
    ZY, ILM = _seeds["ZY-BERT"], _seeds["InternLM3-8B"]
    for vals, col in ((ZY, BLUE), (ILM, ORANGE)):
        P([(x, ay(v)) for x, v in zip(SX, vals)], stroke=col, sw=2.4, closed=False)
        for x, v in zip(SX, vals):
            C(x, ay(v), 6, col)
    for x, v in zip(SX, ZY):
        T(x, ay(v) - 14, f"{v:.2f}", 20, BLUE, 700, "middle")
    for x, v in zip(SX, ILM):
        T(x, ay(v) + 28, f"{v:.2f}", 20, ORANGE, 700, "middle")
    for x, lab in zip(SX, ("42", "2026", "7")):
        T(x, AY0 + 34, lab, 21, MUT, 400, "middle")
    T(380, AY0 + 68, "random seed", 20, MUT, 400, "middle")

    zm, zsd = fd.seed_mean_sd("ZY-BERT")
    im, isd = fd.seed_mean_sd("InternLM3-8B")
    T(660, ay(zm) - 10, f"{zm:.2f} \u00b1 {zsd:.2f}", 21, BLUE, 700)
    T(660, ay(im) - 10, f"{im:.2f} \u00b1 {isd:.2f}", 21, ORANGE, 700)
    L(635, ay(zm - zsd), 635, ay(zm + zsd), stroke=BLUE, sw=1.4)
    L(635, ay(im - isd), 635, ay(im + isd), stroke=ORANGE, sw=1.4)

    panel(800, 96, "B")
    PX = [900, 1230, 1560]
    BY0, BY1 = 520, 170
    def by(v): return (BY0 - BY1) / 33.0 * (v + 19) + BY1
    for v in (-15, -10, -5, 0, 5, 10):
        yy = by(v)
        L(860, yy, 1600, yy, stroke=MUT if v == 0 else SOFT, sw=1.2 if v == 0 else 0.9)
        T(846, yy + 7, ("%+d" % v).replace("-", "\u2212"), 20, MUT, 400, "end")
    T(800, 150, "Paired \u0394 accuracy (pp)", 22, MUT, 400)
    for x, lab in zip(PX, ("S0 (4,218)", "S1 (4,206)", "S2 (4,195)")):
        T(x, BY0 + 34, lab, 21, MUT, 400, "middle")
    T(1000, BY0 + 68, "record-level deduplication definition", 20, MUT, 400, "middle")

    PAIRS = fd.dedup_slopes()
    COLS = [MAGENTA, GREEN, ORANGE, "#777777", NAVY, BLUE]
    for (nm, a, b, c), col in zip(PAIRS, COLS):
        P([(x, by(v)) for x, v in zip(PX, (a, b, c))], stroke=col, sw=1.8, closed=False)
        for x, v in zip(PX, (a, b, c)):
            C(x, by(v), 4.5, col)
        T(1580, by(c) + 7, nm, 19, col, 600)

    panel(50, 620, "C")
    # legend
    C(700, 640, 6, BLUE); T(714, 647, "ordinary paired bootstrap", 19, MUT, 400)
    R(1000, 633, 10, 10, fill=BLUE, stroke=BLUE, sw=1); T(1016, 647, "class-stratified", 19, MUT, 400)

    CX0, CX1 = 900, 1500
    def cx(v): return CX0 + (v + 2.5) / 17.5 * (CX1 - CX0)
    L(cx(0), 690, cx(0), 1260, stroke=MUT, sw=1, dash="3 4")

    MACRO, BA = fd.bootstrap_forest()
    names = ["ZY-BERT vs InternLM3-8B", "ZY-BERT vs MacBERT", "ZY-BERT vs Qwen3-8B",
             "InternLM3-8B vs MacBERT", "InternLM3-8B vs Qwen3-8B", "MacBERT vs Qwen3-8B"]

    T(50, 706, "Macro-F1", 24, INK, 700)
    T(50, 1006, "Balanced accuracy", 24, INK, 700)

    def rowf(yy, vals, nm, shade=False):
        v, lo, hi, slo, shi = vals
        if shade:
            R(50, yy - 20, 1810, 40, fill="#F9EBEA", stroke="none", sw=0)
        T(870, yy + 7, nm, 19, INK if not shade else ORANGE, 400, "end")
        L(cx(lo), yy - 9, cx(hi), yy - 9, stroke=BLUE, sw=1.4)
        C(cx(v), yy - 9, 5, BLUE)
        L(cx(slo), yy + 9, cx(shi), yy + 9, stroke=BLUE, sw=1.4)
        R(cx(v) - 5, yy + 4, 10, 10, fill=BLUE, stroke=BLUE, sw=1)

    for i, vals in enumerate(MACRO):
        rowf(750 + i * 40, vals, names[i])
    for i, vals in enumerate(BA):
        rowf(1050 + i * 40, vals, names[i], shade=(i == 3))

    L(CX0, 1260, CX1, 1260, stroke=INK, sw=1.2)
    for v in (0, 5, 10, 15):
        L(cx(v), 1260, cx(v), 1266, stroke=INK, sw=1)
        T(cx(v), 1286, str(v), 20, MUT, 400, "middle")
    T(CX1, 1322, "Paired difference (pp)", 21, MUT, 400, "end")
    save()


# ================================================================= FIG 7
def fig7():
    inf = load_support()
    begin(2000, 960, "Figure7")
    panel(46, 96, "A")

    sup = sorted((int(inf[i]["support"]) for i in inf), reverse=True)
    GX0, GX1 = 150, 860
    GY0, GY1 = 140, 780
    LO, HI = 4.0, 1600.0
    def gyv(v): return GY1 - (math.log10(max(v, LO)) - math.log10(LO)) / (math.log10(HI) - math.log10(LO)) * (GY1 - GY0)

    L(GX0, GY1, GX1, GY1, stroke=INK, sw=1.2)
    L(GX0, GY0, GX0, GY1, stroke=INK, sw=1.2)
    for gv, gl in ((10, "10"), (100, "100"), (1000, "1,000")):
        L(GX0, gyv(gv), GX1, gyv(gv), stroke=SOFT, sw=0.9)
        T(GX0 - 12, gyv(gv) + 7, gl, 20, MUT, 400, "end")
    pitch = (GX1 - GX0) / 42.0
    for i, v in enumerate(sup):
        R(GX0 + i * pitch + 2, gyv(v), 12, GY1 - gyv(v), fill="#1F618D" if i == 0 else "#4A6572", stroke="none", sw=0)
    L(GX0, gyv(95), GX1, gyv(95), stroke=MUT, sw=1, dash="5 5")
    L(GX0, gyv(10), GX1, gyv(10), stroke=MUT, sw=1, dash="2 4")
    T(GX1 + 14, gyv(95) + 7, "train 91\u2013100 / class", 19, MUT, 400)
    T(GX1 + 14, gyv(10) - 10, "dev 10 / class", 19, MUT, 400)
    T(GX0 + pitch + 8, gyv(sup[0]) + 8, "860", 20, "#1F618D", 700)
    T(GX0 + 41 * pitch + pitch / 2, gyv(sup[-1]) - 10, "6", 20, INK, 700, "middle")
    T(150, GY1 + 36, "42 frozen classes, sorted by support", 20, MUT, 400)
    T(40, 120, "Test records (log scale)", 21, MUT, 400)

    panel(1070, 96, "B")
    key = [(5, "C05", 860), (23, "C23", 98), (2, "C02", 13),
           (11, "C11", 6), (33, "C33", 20), (32, "C32", 17)]
    BX0, BX1 = 1210, 1900
    def bx(v): return BX0 + v / 100 * (BX1 - BX0)

    C(1080, 128, 7, BLUE); T(1094, 135, "ZY-BERT", 19, MUT, 400)
    C(1225, 128, 7, ORANGE); T(1239, 135, "InternLM3-8B", 19, MUT, 400)
    C(1370, 128, 7, GREEN); T(1384, 135, "MacBERT", 19, MUT, 400)
    C(1500, 128, 7, MAGENTA); T(1514, 135, "Qwen3-8B", 19, MUT, 400)
    C(1080, 162, 6, INK); T(1094, 169, "Recall", 19, MUT, 400)
    R(1180, 156, 10, 10, fill="#FFFFFF", stroke=INK, sw=1.2); T(1196, 169, "F1", 19, MUT, 400)

    models = [("recall_zybert", "f1_zybert", BLUE), ("recall_internlm3", "f1_internlm3", ORANGE),
              ("recall_macbert", "f1_macbert", GREEN), ("recall_qwen3", "f1_qwen3", MAGENTA)]
    for ri, (lid, tag, supn) in enumerate(key):
        yy = 256 + ri * 96
        T(1190, yy + 7, f"{tag} (n = {supn})", 21, INK, 600, "end")
        for mi, (rk, fk, col) in enumerate(models):
            off = (mi - 1.5) * 16
            rv = float(inf[lid][rk]); fv = float(inf[lid][fk])
            C(bx(rv), yy + off - 6, 5, col)
            R(bx(fv) - 5, yy + off + 2, 10, 10, fill="#FFFFFF", stroke=col, sw=1.4)
    L(BX0, 830, BX1, 830, stroke=INK, sw=1.2)
    for v in (0, 20, 40, 60, 80, 100):
        L(bx(v), 830, bx(v), 836, stroke=INK, sw=1)
        T(bx(v), 856, str(v), 19, MUT, 400, "middle")
    T(BX1, 892, "Score (%)", 20, MUT, 400, "end")
    save()


# ================================================================= FIG 8
def fig8():
    begin(2000, 1260, "Figure8")
    panel(46, 96, "A")

    rows = fd.error_rows()
    models = ["ZY-BERT", "InternLM3-8B", "MacBERT", "Qwen3-8B"]

    HX0, HY0 = 380, 160
    cw, ch = 260, 44
    for j, nm in enumerate(models):
        T(HX0 + j * cw + cw / 2, HY0 - 18, nm, 20, INK, 600, "middle")

    def hcol(v):
        t = min(v / 140.0, 1.0)
        r = int(255 + (140 - 255) * t)
        g = int(247 + (74 - 247) * t)
        b = int(240 + (30 - 240) * t)
        return f"#{r:02X}{g:02X}{b:02X}"

    for i, (nm, vals, tot) in enumerate(rows):
        yy = HY0 + i * ch
        T(360, yy + 29, nm, 20, INK, 500, "end")
        for j, v in enumerate(vals):
            xx = HX0 + j * cw
            R(xx, yy, cw, ch, fill=hcol(v), stroke="#FFFFFF", sw=1.6)
            T(xx + cw / 2, yy + 29, str(v), 21, "#FFFFFF" if v > 80 else INK, 700, "middle")

    # colour bar
    cbx, cby, cbh = 1480, HY0, 10 * ch
    for k in range(100):
        v = 140 * k / 99
        yy = cby + cbh - (k + 1) * cbh / 100
        R(cbx, yy, 22, cbh / 100 + 1, fill=hcol(v), stroke="none", sw=0)
    R(cbx, cby, 22, cbh, fill="none", stroke="#999999", sw=0.8)
    for v in (0, 70, 140):
        yy = cby + cbh - v / 140 * cbh
        L(cbx + 22, yy, cbx + 28, yy, stroke=INK, sw=1)
        T(cbx + 34, yy + 6, str(v), 18, MUT, 400)
    T(cbx + 12, cby - 16, "errors", 18, MUT, 400, "middle")

    panel(46, 660, "B")
    SX0, SX1 = 330, 820
    def sx(v): return SX0 + v / 360 * (SX1 - SX0)
    for i, (nm, vals, tot) in enumerate(rows):
        yy = 730 + i * 46
        T(310, yy + 22, nm, 19, INK, 400, "end")
        x = SX0
        for v, col in zip(vals, (BLUE, ORANGE, GREEN, MAGENTA)):
            w = (SX1 - SX0) * v / 360.0
            R(x, yy, max(w, 0.6), 30, fill=col, stroke="none", sw=0)
            x += w
        T(SX1 + 12, yy + 22, str(tot), 19, INK, 700)
    T(SX1 + 12, 700, "pooled", 18, MUT, 600)
    L(SX0, 1180, SX1, 1180, stroke=INK, sw=1.2)
    for v in (0, 100, 200, 300):
        L(sx(v), 1180, sx(v), 1186, stroke=INK, sw=1)
        T(sx(v), 1206, str(v), 19, MUT, 400, "middle")
    T(SX1, 1240, "Pooled errors (model-record errors)", 20, MUT, 400, "end")

    panel(1020, 660, "C")
    VX0, VX1 = 1220, 1780
    def vx(v): return VX0 + v / 100 * (VX1 - VX0)
    V = fd.validity()
    vals = [(nm, V[nm][0], V[nm][1], col) for nm, col in
            (("ZY-BERT", BLUE), ("InternLM3-8B", ORANGE),
             ("MacBERT", GREEN), ("Qwen3-8B", MAGENTA))]
    for i, (nm, v, empty, col) in enumerate(vals):
        yy = 760 + i * 84
        T(1200, yy + 24, nm, 21, INK, 400, "end")
        L(VX0, yy + 20, VX0 + (v / 100) * (VX1 - VX0), yy + 20, stroke=col, sw=14)
        T(VX1 + 14, yy + 26, f"{v:.2f}%", 21, INK, 700)
        T(VX1 + 14, yy + 50, ("2 empty (0.05%)" if empty else "0 empty"), 18, MUT, 400)
    L(VX0, 1100, VX1, 1100, stroke=INK, sw=1.2)
    for v in (0, 50, 100):
        L(vx(v), 1100, vx(v), 1106, stroke=INK, sw=1)
        T(vx(v), 1126, str(v), 19, MUT, 400, "middle")
    T(VX1, 1160, "Format-valid outputs (%)", 20, MUT, 400, "end")
    save()


if __name__ == "__main__":
    # Figure4 is built by fig4_v3.py (two-route plate); do not call fig4() here,
    # otherwise it overwrites Figure4.svg with the retired single-panel layout.
    fig2(); fig3(); fig5(); fig6(); fig7(); fig8()
