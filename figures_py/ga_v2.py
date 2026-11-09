#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Graphical abstract v3 - scientific workflow diagram.

Style contract: white canvas, dashed module frames, thin black outlines and
arrows, square corners, no fills except light shading for data marks.  Colour
only marks model identity.  All quantitative values come from figure_data.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figure_data as fd

W, H = 2400, 1640
INK = "#1A1A1A"
MUT = "#555555"
DASH = "#7A7A7A"
RULE = "#D8DEE3"
NAVY = "#1B4F72"
SLATE = "#5D6D7E"

BLUE = "#0072B2"
ORANGE = "#D55E00"
GREEN = "#009E73"
MAGENTA = "#CC79A7"

FONT = "Arial, Helvetica, sans-serif"
OUT = os.path.dirname(os.path.abspath(__file__))
S = []


def T(x, y, s, size=20, fill=INK, weight=400, anchor="start"):
    st = (f'font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
          f'fill="{fill}" text-anchor="{anchor}"')
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    S.append(f'<text x="{x}" y="{y}" {st}>{s}</text>')


def R(x, y, w, h, fill="none", stroke=INK, sw=1.2, rx=0, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    S.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
             f'stroke="{stroke}" stroke-width="{sw}"{d}/>')


def L(x1, y1, x2, y2, stroke=INK, sw=1.2, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    S.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
             f'stroke-width="{sw}"{d} stroke-linecap="round"/>')


def P(pts, fill="none", stroke=INK, sw=1.2):
    p = " ".join(f"{a:.2f},{b:.2f}" for a, b in pts)
    S.append(f'<polygon points="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"/>')


def C(cx, cy, r, fill=INK, stroke="none", sw=1):
    S.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')


def arrow(x1, y1, x2, y2, color=INK, sw=1.5, hs=7, dash=None):
    dx, dy = x2 - x1, y2 - y1
    ln = math.hypot(dx, dy)
    if ln == 0:
        return
    ux, uy = dx / ln, dy / ln
    d = f' stroke-dasharray="{dash}"' if dash else ""
    S.append(f'<line x1="{x1}" y1="{y1}" x2="{x2 - ux * hs * 1.3:.2f}" y2="{y2 - uy * hs * 1.3:.2f}" '
             f'stroke="{color}" stroke-width="{sw}"{d} stroke-linecap="round"/>')
    p2 = (x2 - ux * hs - uy * hs * 0.5, y2 - uy * hs + ux * hs * 0.5)
    p3 = (x2 - ux * hs + uy * hs * 0.5, y2 - uy * hs - ux * hs * 0.5)
    P([(x2, y2), p2, p3], fill=color, stroke=color, sw=0.8)


def marker(x, y, col, s=12):
    R(x, y, s, s, fill=col, stroke=col, sw=0.8)


S.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
S.append(f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>')

# ============================================================ module frames
R(40, 86, 2320, 300, stroke=DASH, sw=1.2, dash="7 6")
R(40, 452, 1280, 588, stroke=DASH, sw=1.2, dash="7 6")
R(1380, 452, 980, 588, stroke=DASH, sw=1.2, dash="7 6")
R(40, 1100, 2320, 460, stroke=DASH, sw=1.2, dash="7 6")
T(40, 72, "A", 32, INK, 700)
T(40, 438, "B", 32, INK, 700)
T(1380, 438, "C", 32, INK, 700)
T(40, 1086, "D", 32, INK, 700)
T(64, 122, "Data source and task construction", 20, INK, 700)
T(64, 488, "Four systems, one frozen label space", 20, INK, 700)
T(1404, 488, "Common evaluation", 20, INK, 700)
T(64, 1136, "Long tail, efficiency and clinical use", 20, INK, 700)

# ============================================================ A
for i, (dx, dy) in enumerate([(0, 0), (12, 10), (24, 20)]):
    R(80 + dx, 160 + dy, 96, 116, fill="#FFFFFF", stroke=INK, sw=1)
for i in range(4):
    L(112, 186 + i * 10, 152, 186 + i * 10, stroke="#AAB4BC", sw=2)
T(218, 206, "TCM-SD public corpus", 20, INK, 400)
T(218, 246, "54,152 records", 28, INK, 700)

# decontamination
R(450, 160, 410, 180, fill="#FFFFFF", stroke=INK, sw=1.1)
T(468, 188, "held-out pool 4,452", 18, MUT, 400)
T(468, 222, "SHA-256 exact match", 21, INK, 400)
T(842, 222, "\u22126", 22, INK, 700, "end")
L(468, 234, 842, 234, stroke=RULE, sw=1)
T(468, 264, "TF-IDF cosine \u2265 0.95", 21, INK, 400)
T(842, 264, "\u2212228", 22, INK, 700, "end")
L(468, 276, 842, 276, stroke=RULE, sw=1)
T(468, 314, "234 excluded \u00b7 4,218 retained", 21, INK, 700)

# partitions
R(940, 160, 450, 180, fill="#FFFFFF", stroke=INK, sw=1.1)
R(960, 180, 396, 32, fill="#E4E9ED", stroke=INK, sw=1)
T(972, 203, "Train 4,186", 19, INK, 400)
R(960, 222, 40, 32, fill="#E4E9ED", stroke=INK, sw=1)
T(1016, 245, "Dev 420", 19, INK, 400)
R(960, 264, 400, 32, fill=INK, stroke=INK, sw=1)
T(972, 287, "Clean test 4,218", 19, "#FFFFFF", 700)

# frozen classes
R(1470, 160, 370, 180, fill="#FFFFFF", stroke=INK, sw=1.1)
T(1655, 198, "42 frozen syndrome classes", 20, INK, 700, "middle")
for r in range(6):
    for c in range(7):
        R(1500 + c * 48, 216 + r * 17, 40, 13, fill="#E7ECEF", stroke="#FFFFFF", sw=1)

# audit
R(1900, 160, 380, 180, fill="#FFFFFF", stroke=INK, sw=1.1)
T(1918, 196, "Label audit", 20, INK, 700)
x = 1918
for i in range(40):
    w = 8.6 if i < 38 else 12.4
    R(x, 210, w - 1.4, 14, fill="#C6D1D9" if i < 38 else "#1A1A1A", stroke="none", sw=0)
    x += w
T(1918, 264, "38 KEEP + 4 MERGE", 20, INK, 400)
T(1918, 298, "\u2192 40 normalized categories", 20, INK, 400)

arrow(414, 250, 450, 250, sw=1.8)
arrow(860, 250, 940, 250, sw=1.8)
arrow(1390, 250, 1470, 250, sw=1.8)

# ============================================================ B
T(64, 540, "Discriminative encoders \u00b7 ~1/15\u20131/25 parameters", 21, INK, 700)
marker(64, 560, BLUE)
T(84, 571, "ZY-BERT", 21, INK, 700)
T(64, 600, "TCM domain \u00b7 seeds 42/2026/7", 18, MUT, 400)
marker(64, 628, GREEN)
T(84, 639, "MacBERT", 21, INK, 700)
T(64, 668, "general domain \u00b7 seed-42", 18, MUT, 400)

L(330, 566, 360, 566, stroke=INK, sw=1.2)
L(330, 634, 360, 634, stroke=INK, sw=1.2)
L(360, 566, 360, 634, stroke=INK, sw=1.2)
arrow(360, 600, 420, 600)
R(420, 554, 250, 92, fill="#FFFFFF", stroke=INK, sw=1.1)
T(545, 590, "42-class head", 19, INK, 700, "middle")
T(545, 616, "argmax \u00b7 no free text", 17, MUT, 400, "middle")
arrow(670, 600, 980, 600)

T(64, 780, "Generative LLMs \u00b7 8B-class", 21, INK, 700)
marker(64, 800, ORANGE)
T(84, 811, "InternLM3-8B-Instruct", 20, INK, 700)
T(64, 840, "4-bit NF4 QLoRA \u00b7 4.98B", 18, MUT, 400)
marker(64, 868, MAGENTA)
T(84, 879, "Qwen3-8B", 21, INK, 700)
T(64, 908, "LoRA-SFT \u00b7 seed 42", 18, MUT, 400)

L(330, 806, 360, 806, stroke=INK, sw=1.2)
L(330, 874, 360, 874, stroke=INK, sw=1.2)
L(360, 806, 360, 874, stroke=INK, sw=1.2)
arrow(360, 840, 420, 840)
R(420, 770, 520, 140, fill="#FFFFFF", stroke=INK, sw=1.1)
L(420, 840, 940, 840, stroke=INK, sw=1)
T(680, 812, "Generated label + templated rationale", 18, INK, 400, "middle")
T(680, 882, "parser v18 \u00b7 99.95% format-valid", 18, MUT, 400, "middle")
arrow(940, 840, 980, 840)

# shared label space
T(1124, 530, "42 frozen syndrome classes", 19, INK, 700, "middle")
for r in range(7):
    for c in range(6):
        R(980 + c * 48, 550 + r * 56, 44, 50, fill="#FFFFFF", stroke="#9FB0BC", sw=0.9)

# ============================================================ C
C(1700, 514, 5, BLUE)
T(1712, 520, "Accuracy", 16, MUT, 400)
R(1790, 508, 9, 9, fill="#FFFFFF", stroke=INK, sw=1.1)
T(1806, 520, "Macro-F1", 16, MUT, 400)

CY0, CY1 = 744, 534
def cy(v): return CY0 - v / 100 * (CY0 - CY1)
L(1700, CY0, 2140, CY0, stroke=INK, sw=1)
for v in (0, 20, 40, 60, 80, 100):
    L(1700 + v / 100 * 440, CY0, 1700 + v / 100 * 440, CY0 + 6, stroke=INK, sw=1)
    T(1700 + v / 100 * 440, CY0 + 22, str(v), 16, MUT, 400, "middle")

_m = fd.metrics()
rows = [(n, _m[n]["acc"], _m[n]["mf1"], c, y) for n, c, y in
        (("ZY-BERT", BLUE, 570), ("InternLM3-8B", ORANGE, 616),
         ("MacBERT", GREEN, 662), ("Qwen3-8B", MAGENTA, 708))]
for nm, acc, f1, col, yy in rows:
    T(1680, yy + 6, nm, 18, INK, 600 if nm == "ZY-BERT" else 400, "end")
    C(1700 + acc / 100 * 440, yy - 6, 6, col)
    R(1700 + f1 / 100 * 440 - 5, yy + 1, 10, 10, fill="#FFFFFF", stroke=col, sw=1.6)
    T(2160, yy + 6, f"{acc:.2f} / {f1:.2f}", 18, col, 600)

# paired differences
L(1400, 790, 2340, 790, stroke=RULE, sw=1)
T(1400, 812, "ZY-BERT \u2212 InternLM3-8B", 19, INK, 700)

DX0, DX1 = 1700, 2140
def dx(v): return DX0 + v / 10 * (DX1 - DX0)
L(DX0, 830, DX0, 878, stroke=SLATE, sw=1, dash="3 4")
_d = fd.primary_pair()
for lab, val, lo, hi, yy in (("\u0394Accuracy", _d[0], _d[1], _d[2], 838),
                             ("\u0394Macro-F1", _d[3], _d[4], _d[5], 868)):
    T(1400, yy + 6, lab, 17, INK, 400)
    L(dx(lo), yy, dx(hi), yy, stroke=INK, sw=1.6)
    L(dx(lo), yy - 6, dx(lo), yy + 6, stroke=INK, sw=1.6)
    L(dx(hi), yy - 6, dx(hi), yy + 6, stroke=INK, sw=1.6)
    R(dx(val) - 4, yy - 4, 8, 8, fill=INK, stroke=INK, sw=0)
    T(2160, yy + 6, f"+{val:.2f} pp", 18, INK, 700)
T(1400, 900, f"95% CI {_d[1]:.2f}\u2013{_d[2]:.2f} \u00b7 p < 0.001 (Holm)", 16, MUT, 400)

# seeds
L(1400, 920, 2340, 920, stroke=RULE, sw=1)
T(1400, 942, "Seeds 42 \u00b7 2026 \u00b7 7", 19, INK, 700)
SX0, SX1 = 1700, 2140
def sx(v): return SX0 + (v - 66) / 12 * (SX1 - SX0)
L(SX0, 1006, SX1, 1006, stroke=INK, sw=1)
for v in (66, 70, 74, 78):
    L(sx(v), 1006, sx(v), 1012, stroke=INK, sw=1)
    T(sx(v), 1028, str(v), 15, MUT, 400, "middle")
for nm, (m, sd), col, yy in (("ZY-BERT", fd.seed_mean_sd("ZY-BERT"), BLUE, 964),
                             ("InternLM3-8B", fd.seed_mean_sd("InternLM3-8B"), ORANGE, 988)):
    T(1400, yy + 5, nm, 17, INK, 400)
    L(sx(m - sd), yy, sx(m + sd), yy, stroke=col, sw=2)
    C(sx(m), yy, 5, col)
    T(2160, yy + 5, f"{m:.2f} \u00b1 {sd:.2f}", 17, INK, 700)

# ============================================================ D
GX0, GX1 = 120, 820
GY0, GY1 = 1190, 1500
LO, HI = 4.0, 1600.0
def gy(v): return GY1 - (math.log10(max(v, LO)) - math.log10(LO)) / (math.log10(HI) - math.log10(LO)) * (GY1 - GY0)
T(64, 1168, "Test records (log scale)", 18, MUT, 400)
L(GX0, GY1, GX1, GY1, stroke=INK, sw=1)
L(GX0, GY0, GX0, GY1, stroke=INK, sw=1)
for gv, gl in ((10, "10"), (100, "100"), (1000, "1,000")):
    L(GX0, gy(gv), GX1, gy(gv), stroke="#EEEEEE", sw=0.9)
    T(GX0 - 12, gy(gv) + 6, gl, 17, MUT, 400, "end")
pitch = (GX1 - GX0) / 42.0
sup = fd.support()
for i, v in enumerate(sup):
    R(GX0 + i * pitch + 1.5, gy(v), 11, GY1 - gy(v), fill=INK if i == 0 else "#9FB0BC", stroke="none", sw=0)
L(GX0, gy(95), GX1, gy(95), stroke=MUT, sw=1, dash="5 5")
L(GX0, gy(10), GX1, gy(10), stroke=MUT, sw=1, dash="2 4")
T(GX1 + 12, gy(95) + 6, "train 91\u2013100", 16, MUT, 400)
T(GX1 + 12, gy(10) + 18, "dev 10 / class", 16, MUT, 400)
T(GX0 + pitch + 6, gy(sup[0]) + 7, "860", 18, INK, 700)
T(GX0 + 41 * pitch + pitch / 2, gy(sup[-1]) - 8, "6", 18, INK, 600, "middle")
T(120, 1536, "42 frozen classes \u00b7 support 6\u2013860 (clean held-out test)", 18, INK, 400)

# efficiency
_par = fd.params()
_rat = fd.param_ratios()
T(960, 1170, "Parameter scale", 20, INK, 700)
T(960, 1244, f"1 : {_rat[0]:.1f}", 40, INK, 700)
T(960, 1278, f"recorded vs InternLM3-8B \u00b7 nominal 1 : {_rat[1]:.0f}", 17, MUT, 400)
T(960, 1352, f"+{_d[0]:.2f} pp accuracy at ~1/15\u20131/25 parameters", 19, INK, 700)
T(960, 1384, f"{_par['ZY-BERT'] / 1e9:.2f}B vs {_par['InternLM3-8B'] / 1e9:.2f}B recorded parameters", 17, MUT, 400)

# hybrid workflow
T(1640, 1170, "Proposed hybrid clinical workflow", 20, INK, 700)
R(1640, 1200, 250, 78, fill="#FFFFFF", stroke=INK, sw=1.1)
marker(1656, 1218, BLUE)
T(1678, 1231, "ZY-BERT", 19, INK, 700)
T(1656, 1256, "precise syndrome label", 17, INK, 400)
R(1640, 1324, 250, 78, fill="#FFFFFF", stroke=INK, sw=1.1)
T(1656, 1355, "LLM", 19, INK, 700)
T(1656, 1380, "interactive rationale", 17, INK, 400)
R(2000, 1246, 220, 96, fill="#FFFFFF", stroke=INK, sw=1.1)
T(2110, 1284, "Clinician", 19, INK, 700, "middle")
T(2110, 1310, "decision", 19, INK, 700, "middle")
arrow(1890, 1239, 2000, 1272, sw=1.8)
arrow(1890, 1363, 2000, 1316, sw=1.7, dash="3 5")
T(1902, 1228, "decides", 16, INK, 700)
T(1902, 1404, "explains", 16, MUT, 700)

S.append("</svg>")
svg = "\n".join(S)
with open(os.path.join(OUT, "Figure1.svg"), "w", encoding="utf-8") as f:
    f.write(svg)
html = ('<!doctype html><html><head><meta charset="utf-8"><style>'
        'html,body{margin:0;padding:0;background:#fff}svg{display:block}'
        f'</style></head><body>{svg}</body></html>')
with open(os.path.join(OUT, "Figure1.html"), "w", encoding="utf-8") as f:
    f.write(html)
print("ok", len(svg))
