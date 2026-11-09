#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Graphical abstract v2 - multi-panel composite derived from the paper's evidence chain.

Layout: A (task pipeline, full width) -> B (four systems) + C (matched evidence)
        -> D (long tail, efficiency, clinical implication).
Rules kept: fixed model colours, 0-100 axes for main metrics, black letters.
"""
import csv
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figure_data as fd

W, H = 2400, 1640
INK = "#1E2B33"
MUT = "#666666"
RULE = "#CBD5DC"
NAVY = "#1B4F72"
SLATE = "#5D6D7E"

BLUE = "#0072B2"
ORANGE = "#D55E00"
GREEN = "#009E73"
MAGENTA = "#CC79A7"

P_BLUE = "#E6F1F7"
P_GREEN = "#E5F3EE"
P_ORANGE = "#FBEEE7"
P_MAGENTA = "#F8EAF1"

FONT = "Arial, Helvetica, sans-serif"
OUT = os.path.dirname(os.path.abspath(__file__))
S = []


def T(x, y, s, size=22, fill=INK, weight=400, anchor="start", italic=False):
    st = (f'font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
          f'fill="{fill}" text-anchor="{anchor}"')
    if italic:
        st += ' font-style="italic"'
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    S.append(f'<text x="{x}" y="{y}" {st}>{s}</text>')


def R(x, y, w, h, fill="none", stroke=INK, sw=1.2, rx=0, dash=None, op=1):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    S.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
             f'stroke="{stroke}" stroke-width="{sw}"{d} opacity="{op}"/>')


def L(x1, y1, x2, y2, stroke=INK, sw=1.2, dash=None, op=1):
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
    d = f' stroke-dasharray="{dash}"' if dash else ""
    S.append(f'<line x1="{x1}" y1="{y1}" x2="{x2 - ux * hs * 1.3:.2f}" y2="{y2 - uy * hs * 1.3:.2f}" '
             f'stroke="{color}" stroke-width="{sw}"{d} stroke-linecap="round"/>')
    p2 = (x2 - ux * hs - uy * hs * 0.5, y2 - uy * hs + ux * hs * 0.5)
    p3 = (x2 - ux * hs + uy * hs * 0.5, y2 - uy * hs - ux * hs * 0.5)
    P([(x2, y2), p2, p3], fill=color, stroke=color, sw=1)


def head(x, y, letter, title, width):
    T(x, y, letter, 36, "#111111", 700)


def lines(x, y, seq, size=20, fill=INK, weight=400, anchor="start", lh=26):
    for i, s in enumerate(seq):
        T(x, y + i * lh, s, size, fill, weight, anchor)


def cbox(x, y, w, h, seq, stroke=INK, fill="#FFFFFF", sw=1.3, rx=0,
         size=20, weight=400, color=INK, lh=26, dash=None):
    R(x, y, w, h, fill=fill, stroke=stroke, sw=sw, rx=rx, dash=dash)
    total = (len(seq) - 1) * lh
    top = y + h / 2 - total / 2 + size * 0.36
    for i, s in enumerate(seq):
        T(x + w / 2, top + i * lh, s, size, color, weight, "middle")


def load_support():
    return fd.support()


S.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
S.append(f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>')

# ============================================================ A
head(60, 96, "A", "Task construction and decontamination", 2280)

# corpus
for i, (dx, dy) in enumerate([(0, 0), (12, 10), (24, 20)]):
    R(80 + dx, 150 + dy, 96, 118, fill="#EDF2F6" if i < 2 else "#F9FBFC", stroke="#8FA3B3", sw=1)
for i in range(4):
    L(112, 176 + i * 10, 152, 176 + i * 10, stroke="#B9C6D0", sw=2)
T(218, 196, "TCM-SD public corpus", 21, INK, 400)
T(218, 236, "54,152 records", 28, NAVY, 700)

# decontamination
R(450, 150, 410, 190, fill="#FAFBFC", stroke="#B9C2CA", sw=1.1)
T(468, 180, "held-out pool 4,452", 19, MUT, 400)
T(468, 216, "SHA-256 exact match", 22, INK, 400)
T(842, 216, "\u22126", 24, INK, 700, "end")
L(468, 228, 842, 228, stroke="#E1E6EB", sw=1)
T(468, 258, "TF-IDF cosine \u2265 0.95", 22, INK, 400)
T(842, 258, "\u2212228", 24, INK, 700, "end")
L(468, 270, 842, 270, stroke="#E1E6EB", sw=1)
T(468, 310, "234 excluded \u00b7 4,218 retained", 22, INK, 700)

# partitions
R(940, 150, 450, 190, fill="#FFFFFF", stroke="#B9C2CA", sw=1.1)
R(960, 172, 396, 34, fill="#D6E3EC", stroke="#8FA6B5", sw=1)
T(972, 196, "Train 4,186", 20, INK, 600)
R(960, 216, 40, 34, fill="#E8EDF1", stroke=SLATE, sw=1)
T(1016, 240, "Dev 420", 20, INK, 600)
R(960, 260, 400, 34, fill=NAVY, stroke=NAVY, sw=1)
T(972, 284, "Clean test 4,218", 20, "#FFFFFF", 700)

# frozen classes
R(1470, 150, 370, 190, fill="#FFFFFF", stroke="#B9C2CA", sw=1.1)
T(1655, 188, "42 frozen syndrome classes", 21, INK, 600, "middle")
for r in range(6):
    for c in range(7):
        R(1500 + c * 48, 212 + r * 17, 40, 13, fill="#E4EDF5", stroke="#FFFFFF", sw=1)

# audit callout
L(1840, 245, 1896, 245, stroke="#9AA9B4", sw=1, dash="4 5")
R(1900, 150, 380, 190, fill="#FAFBFC", stroke="#C6D0D7", sw=1.1)
T(1918, 186, "Label audit", 21, INK, 700)
x = 1918
for i in range(40):
    w = 8.6 if i < 38 else 12.4
    R(x, 200, w - 1.4, 14, fill="#A8BECF" if i < 38 else "#34495E", stroke="none", sw=0)
    x += w
T(1918, 256, "38 KEEP + 4 MERGE", 21, INK, 400)
T(1918, 292, "\u2192 40 normalized categories", 21, INK, 400)

arrow(414, 245, 450, 245, sw=2)
arrow(860, 245, 940, 245, sw=2)
arrow(1390, 245, 1470, 245, sw=2)

# ============================================================ B
head(60, 480, "B", "Four systems, one frozen label space", 1380)

T(80, 545, "Discriminative encoders \u00b7 ~1/15\u20131/25 parameters", 23, NAVY, 700)
R(80, 565, 300, 88, fill=P_BLUE, stroke=BLUE, sw=2, rx=6)
T(96, 600, "ZY-BERT", 24, BLUE, 700)
T(96, 626, "TCM-domain \u00b7 seeds 42/2026/7", 19, SLATE, 400)
R(80, 665, 300, 88, fill=P_GREEN, stroke=GREEN, sw=1.6, rx=6)
T(96, 700, "MacBERT", 22, "#006B54", 700)
T(96, 726, "general-domain \u00b7 seed-42", 19, SLATE, 400)

L(400, 609, 430, 609, stroke=INK, sw=1.4)
L(400, 709, 430, 709, stroke=INK, sw=1.4)
L(430, 609, 430, 709, stroke=INK, sw=1.4)
arrow(430, 659, 470, 659, sw=1.8)
cbox(470, 600, 200, 118, ["42-class heads", "(one per model)"], size=20, lh=27)

T(80, 800, "Generative LLMs \u00b7 8B-class", 23, NAVY, 700)
R(80, 820, 300, 84, fill=P_ORANGE, stroke=ORANGE, sw=2, rx=6)
T(96, 852, "InternLM3-8B-Instruct", 22, "#A4400A", 700)
T(96, 878, "4-bit NF4 QLoRA \u00b7 4.98B", 19, SLATE, 400)
R(80, 912, 300, 84, fill=P_MAGENTA, stroke=MAGENTA, sw=1.6, rx=6)
T(96, 944, "Qwen3-8B", 22, "#9C3D74", 700)
T(96, 970, "LoRA-SFT \u00b7 seed-42", 19, SLATE, 400)

L(400, 862, 430, 862, stroke=INK, sw=1.4)
L(400, 954, 430, 954, stroke=INK, sw=1.4)
L(430, 862, 430, 954, stroke=INK, sw=1.4)
arrow(430, 908, 470, 908, sw=1.8)
cbox(470, 876, 200, 64, ["QLoRA / LoRA", "adapters"], size=19, lh=24)
arrow(670, 908, 700, 908, sw=1.8)
cbox(700, 872, 240, 72, ["Generated label +", "templated rationale"], size=19, lh=23)
arrow(820, 944, 820, 976, sw=1.8)
cbox(700, 976, 240, 54, ["Frozen parser v18"], size=20, weight=600)
arrow(940, 990, 1000, 990, sw=1.8)

# shared output grid
R(1000, 560, 300, 470, fill="#F4F7FA", stroke=INK, sw=1.4)
T(1150, 590, "42-class output space", 21, NAVY, 700, "middle")
for r in range(7):
    for c in range(6):
        R(1012 + c * 48, 610 + r * 56, 42, 50, fill="#FFFFFF", stroke="#9FB4C6", sw=1)
arrow(670, 659, 1000, 659, sw=1.8)

# ============================================================ C
head(1500, 480, "C", "Matched evidence", 840)

C(1930, 472, 5, BLUE, sw=0)
T(1944, 479, "Accuracy", 16, MUT, 400)
R(2036, 466, 9, 9, fill="#FFFFFF", stroke=INK, sw=1.1)
T(2050, 479, "Macro-F1", 16, MUT, 400)

CY0, CY1 = 800, 590
def cy(v): return CY0 - v / 100 * (CY0 - CY1)
L(1760, CY0, 2200, CY0, stroke=INK, sw=1)
for v in (0, 20, 40, 60, 80, 100):
    L(1760 + v / 100 * 440, CY0, 1760 + v / 100 * 440, CY0 + 6, stroke=INK, sw=1)
    T(1760 + v / 100 * 440, CY0 + 24, str(v), 17, MUT, 400, "middle")

_m = fd.metrics()
rows = [(n, _m[n]["acc"], _m[n]["mf1"], c, y) for n, c, y in
        (("ZY-BERT", BLUE, 580), ("InternLM3-8B", ORANGE, 640),
         ("MacBERT", GREEN, 700), ("Qwen3-8B", MAGENTA, 760))]
for nm, acc, f1, col, yy in rows:
    T(1740, yy + 7, nm, 20, INK, 600 if nm == "ZY-BERT" else 400, "end")
    C(1760 + acc / 100 * 440, yy - 7, 6, col)
    R(1760 + f1 / 100 * 440 - 5, yy + 2, 10, 10, fill="#FFFFFF", stroke=col, sw=1.6)
    T(2220, yy + 7, f"{acc:.2f} / {f1:.2f}", 18, col, 600)

# paired differences
L(1500, 850, 2320, 850, stroke=RULE, sw=1)
T(1500, 876, "ZY-BERT \u2212 InternLM3-8B", 20, INK, 700)

DX0, DX1 = 1760, 2200
def dx(v): return DX0 + v / 10 * (DX1 - DX0)
L(DX0, 890, DX0, 964, stroke=SLATE, sw=1, dash="3 4")
_d = fd.primary_pair()
for lab, val, lo, hi, yy in (("\u0394Accuracy", _d[0], _d[1], _d[2], 910),
                             ("\u0394Macro-F1", _d[3], _d[4], _d[5], 944)):
    T(1500, yy + 6, lab, 18, INK, 400)
    L(dx(lo), yy, dx(hi), yy, stroke=NAVY, sw=1.8)
    L(dx(lo), yy - 7, dx(lo), yy + 7, stroke=NAVY, sw=1.8)
    L(dx(hi), yy - 7, dx(hi), yy + 7, stroke=NAVY, sw=1.8)
    R(dx(val) - 4.5, yy - 4.5, 9, 9, fill=NAVY, stroke=NAVY, sw=0)
    T(2220, yy + 6, f"+{val:.2f} pp", 19, NAVY, 700)
T(1500, 984, f"95% CI {_d[1]:.2f}\u2013{_d[2]:.2f} \u00b7 p < 0.001 (Holm)", 17, MUT, 400)

# seeds
L(1500, 1006, 2320, 1006, stroke=RULE, sw=1)
T(1500, 1042, "Seeds 42 \u00b7 2026 \u00b7 7", 20, INK, 700)
SX0, SX1 = 1760, 2200
def sx(v): return SX0 + (v - 66) / 12 * (SX1 - SX0)
L(SX0, 1114, SX1, 1114, stroke=INK, sw=1)
for v in (66, 70, 74, 78):
    L(sx(v), 1114, sx(v), 1120, stroke=INK, sw=1)
    T(sx(v), 1136, str(v), 17, MUT, 400, "middle")
for nm, (m, sd), col, yy in (("ZY-BERT", fd.seed_mean_sd("ZY-BERT"), BLUE, 1066),
                             ("InternLM3-8B", fd.seed_mean_sd("InternLM3-8B"), ORANGE, 1094)):
    T(1500, yy + 6, nm, 18, INK, 400)
    L(sx(m - sd), yy, sx(m + sd), yy, stroke=col, sw=2)
    C(sx(m), yy, 5, col)
    T(2220, yy + 6, f"{m:.2f} \u00b1 {sd:.2f}", 18, col, 700)

# ============================================================ D
head(60, 1170, "D", "Long tail, efficiency and clinical implication", 2280)

sup = load_support()
GX0, GX1 = 110, 800
GY0, GY1 = 1245, 1545
LO, HI = 4.0, 1600.0
def gy(v): return GY1 - (math.log10(max(v, LO)) - math.log10(LO)) / (math.log10(HI) - math.log10(LO)) * (GY1 - GY0)
L(GX0, GY1, GX1, GY1, stroke=INK, sw=1)
L(GX0, GY0, GX0, GY1, stroke=INK, sw=1)
for gv, gl in ((10, "10"), (100, "100"), (1000, "1,000")):
    L(GX0, gy(gv), GX1, gy(gv), stroke="#EEEEEE", sw=0.9)
    T(GX0 - 12, gy(gv) + 6, gl, 17, MUT, 400, "end")
pitch = (GX1 - GX0) / 42.0
for i, v in enumerate(sup):
    R(GX0 + i * pitch + 1.5, gy(v), 11, GY1 - gy(v), fill=NAVY if i == 0 else "#6F8FAA", stroke="none", sw=0)
L(GX0, gy(95), GX1, gy(95), stroke=MUT, sw=1, dash="5 5")
L(GX0, gy(10), GX1, gy(10), stroke=MUT, sw=1, dash="2 4")
T(GX1 + 12, gy(95) + 6, "train 91\u2013100", 17, MUT, 400)
T(GX1 + 12, gy(10) + 18, "dev 10 / class", 17, MUT, 400)
T(GX0 + pitch + 6, gy(sup[0]) + 7, "860", 18, NAVY, 700)
T(GX0 + 41 * pitch + pitch / 2, gy(sup[-1]) - 8, "6", 18, INK, 600, "middle")
T(110, 1582, "42 frozen classes \u00b7 support 6\u2013860 (clean held-out test)", 19, INK, 400)
T(60, 1222, "Test records (log scale)", 19, MUT, 400)

# efficiency
_par = fd.params()
_rat = fd.param_ratios()
T(940, 1252, "Parameter scale", 21, NAVY, 700)
T(940, 1318, f"1 : {_rat[0]:.1f}", 42, NAVY, 700)
T(940, 1350, f"recorded vs InternLM3-8B \u00b7 nominal 1 : {_rat[1]:.0f}", 18, MUT, 400)
T(940, 1412, f"+{_d[0]:.2f} pp accuracy at ~1/15\u20131/25 parameters", 19, INK, 700)
T(940, 1444, f"{_par['ZY-BERT'] / 1e9:.2f}B vs {_par['InternLM3-8B'] / 1e9:.2f}B recorded parameters", 18, MUT, 400)

# hybrid workflow
T(1520, 1252, "Proposed hybrid clinical workflow", 21, SLATE, 700)
R(1520, 1282, 240, 76, fill=P_BLUE, stroke=BLUE, sw=1.6, rx=6)
T(1536, 1314, "ZY-BERT", 19, BLUE, 700)
T(1536, 1338, "precise syndrome label", 18, INK, 400)
R(1520, 1402, 240, 76, fill="#F1F4F7", stroke=SLATE, sw=1.6, rx=6)
T(1536, 1434, "LLM", 19, SLATE, 700)
T(1536, 1458, "interactive rationale", 18, INK, 400)
R(1880, 1322, 220, 96, fill="#EEF2F5", stroke=NAVY, sw=1.6, rx=12)
T(1990, 1360, "Clinician", 19, NAVY, 700, "middle")
T(1990, 1386, "decision", 19, NAVY, 700, "middle")
arrow(1760, 1320, 1880, 1352, color=NAVY, sw=2, hs=8)
arrow(1760, 1440, 1880, 1390, color=SLATE, sw=1.7, hs=8, dash="3 5")
T(1776, 1310, "decides", 17, NAVY, 700)
T(1776, 1474, "explains", 17, SLATE, 700)

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
