#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Figure 4 - two-route architecture plate in scientific-workflow style.

Style contract: white canvas, dashed module frames, thin black outlines and
arrows, square corners, no shadows or gradients.  Colour appears only as a
small model-identity marker.  All numbers are read from figure_data.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figure_data as fd

W, H = 2000, 1000
INK = "#1A1A1A"
MUT = "#555555"
DASH = "#7A7A7A"
GRID = "#E6EBEF"

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


def arrow(x1, y1, x2, y2, color=INK, sw=1.5, hs=7):
    dx, dy = x2 - x1, y2 - y1
    ln = math.hypot(dx, dy)
    if ln == 0:
        return
    ux, uy = dx / ln, dy / ln
    S.append(f'<line x1="{x1}" y1="{y1}" x2="{x2 - ux * hs * 1.3:.2f}" y2="{y2 - uy * hs * 1.3:.2f}" '
             f'stroke="{color}" stroke-width="{sw}" stroke-linecap="round"/>')
    p2 = (x2 - ux * hs - uy * hs * 0.5, y2 - uy * hs + ux * hs * 0.5)
    p3 = (x2 - ux * hs + uy * hs * 0.5, y2 - uy * hs - ux * hs * 0.5)
    P([(x2, y2), p2, p3], fill=color, stroke=color, sw=0.8)


def input_block(x, y):
    R(x, y, 880, 56, fill="#FFFFFF", stroke=INK, sw=1.1)
    T(x + 440, y + 24, "Standardized clinical record (input_text)", 19, INK, 400, "middle")
    T(x + 440, y + 44, "same frozen splits \u00b7 4,186 train / 420 dev", 17, MUT, 400, "middle")


_m = fd.metrics()
_p = fd.primary_pair()
_DACC, _LO, _HI = _p[0], _p[1], _p[2]
_DMF1 = _p[3]
_N = fd.n_test()

S.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
S.append(f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>')

# ------------------------------------------------------------------ frames
R(40, 92, 940, 548, stroke=DASH, sw=1.2, dash="7 6")
R(1020, 92, 940, 548, stroke=DASH, sw=1.2, dash="7 6")
R(40, 710, 1920, 250, stroke=DASH, sw=1.2, dash="7 6")
T(40, 78, "A", 32, INK, 700)
T(1020, 78, "B", 32, INK, 700)
T(40, 696, "C", 32, INK, 700)

# ------------------------------------------------------------------ A
T(62, 132, "Discriminative route \u00b7 ~1/25 parameters", 20, INK, 700)
input_block(70, 152)
arrow(300, 208, 300, 240)
arrow(700, 208, 700, 240)

R(150, 240, 300, 86, stroke=BLUE, sw=1.4)
R(166, 258, 12, 12, fill=BLUE, stroke=BLUE, sw=0.8)
T(188, 270, "ZY-BERT", 21, INK, 700)
T(166, 304, "TCM domain \u00b7 seeds 42/2026/7", 18, MUT)

R(550, 240, 300, 86, stroke=GREEN, sw=1.4)
R(566, 258, 12, 12, fill=GREEN, stroke=GREEN, sw=0.8)
T(588, 270, "MacBERT", 21, INK, 700)
T(566, 304, "general domain \u00b7 seed-42 baseline", 18, MUT)

arrow(300, 326, 300, 362)
arrow(700, 326, 700, 362)
R(140, 362, 720, 84, stroke=INK, sw=1.1)
T(500, 394, "Fine-tuned 42-class classification head", 20, INK, 700, "middle")
T(500, 420, "closed-set argmax \u00b7 no free text", 18, MUT, 400, "middle")
T(140, 486, "valid label guaranteed by construction", 19, INK, 700)

arrow(500, 446, 500, 710, sw=1.5)

# ------------------------------------------------------------------ B
T(1042, 132, "Generative route \u00b7 8B-class", 20, INK, 700)
input_block(1050, 152)
arrow(1320, 208, 1320, 240)
arrow(1700, 208, 1700, 240)

R(1070, 240, 380, 86, stroke=ORANGE, sw=1.4)
R(1086, 258, 12, 12, fill=ORANGE, stroke=ORANGE, sw=0.8)
T(1108, 270, "InternLM3-8B-Instruct", 20, INK, 700)
T(1086, 304, "4-bit NF4 QLoRA \u00b7 4.98B", 18, MUT)

R(1490, 240, 380, 86, stroke=MAGENTA, sw=1.4)
R(1506, 258, 12, 12, fill=MAGENTA, stroke=MAGENTA, sw=0.8)
T(1528, 270, "Qwen3-8B", 21, INK, 700)
T(1506, 304, "LoRA-SFT \u00b7 seed 42", 18, MUT)

arrow(1260, 326, 1260, 362)
arrow(1680, 326, 1680, 362)
R(1100, 362, 760, 60, stroke=INK, sw=1.1)
T(1480, 398, "QLoRA / LoRA adapters (per model)", 19, INK, 400, "middle")

arrow(1290, 422, 1290, 458)
R(1100, 458, 760, 132, stroke=INK, sw=1.1)
L(1100, 524, 1860, 524, stroke=INK, sw=1)
T(1480, 492, "Generated label + templated rationale", 18, INK, 400, "middle")
T(1480, 566, f"Frozen parser v18 \u00b7 99.95% labels extracted", 18, MUT, 400, "middle")
T(1100, 620, "two empty outputs (0.05%)", 18, MUT)

arrow(1660, 590, 1660, 710, sw=1.5)

# ------------------------------------------------------------------ shared evaluation
for r in range(3):
    for c in range(14):
        fill = GRID if (r + c) % 4 == 0 else "#F4F6F8"
        R(70 + c * 48, 770 + r * 36, 44, 28, fill=fill, stroke="#C9D2D8", sw=0.7)

T(790, 796, "42 frozen syndrome classes \u00b7 identical order", 20, INK, 700)
T(790, 828, f"N = {_N:,} clean held-out records", 18, MUT)
T(790, 860, "paired bootstrap, 2,000 resamples \u00b7 Holm\u2013McNemar", 18, MUT)
T(790, 892, f"\u0394Accuracy +{_DACC:.2f} pp (95% CI {_LO:.2f}\u2013{_HI:.2f})", 18, MUT)
T(790, 924, f"\u0394Macro-F1 +{_DMF1:.2f} pp", 18, MUT)

# compact metric table (right of the class grid)
T(1830, 786, "Accuracy", 17, MUT, 400, "end")
T(1930, 786, "Macro-F1", 17, MUT, 400, "end")
L(1436, 796, 1930, 796, stroke="#C9D2D8", sw=0.9)
for i, (nm, col) in enumerate((("ZY-BERT", BLUE), ("InternLM3-8B", ORANGE),
                              ("MacBERT", GREEN), ("Qwen3-8B", MAGENTA))):
    yy = 826 + i * 30
    R(1436, yy - 10, 8, 8, fill=col, stroke=col, sw=0.6)
    T(1454, yy, nm, 18, INK)
    T(1830, yy, f"{_m[nm]['acc']:.2f}", 18, INK, 600, "end")
    T(1930, yy, f"{_m[nm]['mf1']:.2f}", 18, INK, 600, "end")

S.append("</svg>")
svg = "\n".join(S)
with open(os.path.join(OUT, "Figure4.svg"), "w", encoding="utf-8") as f:
    f.write(svg)
html = ('<!doctype html><html><head><meta charset="utf-8"><style>'
        'html,body{margin:0;padding:0;background:#fff}svg{display:block}'
        f'</style></head><body>{svg}</body></html>')
with open(os.path.join(OUT, "Figure4.html"), "w", encoding="utf-8") as f:
    f.write(html)
print("ok", len(svg))
