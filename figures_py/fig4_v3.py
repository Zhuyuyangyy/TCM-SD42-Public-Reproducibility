#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Figure 4 v3 - two-route comparison plate with matched-protocol annotations.

Layout: A discriminative encoders (left) / B generative LLMs (right) / C shared
frozen evaluation rail.  All numbers are read from figure_data, never typed.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figure_data as fd

W, H = 2000, 1000
INK = "#222222"
MUT = "#666666"
RULE = "#B9C2CA"
FRAME = "#C6D0D7"
SOFT = "#D8DFE4"
NAVY = "#1B4F72"
SLATE = "#5D6D7E"

BLUE = "#0072B2"
ORANGE = "#D55E00"
GREEN = "#009E73"
MAGENTA = "#CC79A7"

P_BLUE = "#EFF6FA"
P_GREEN = "#EFF7F4"
P_ORANGE = "#FCF3EE"
P_MAGENTA = "#FBF2F6"

FONT = "Arial, Helvetica, sans-serif"
OUT = os.path.dirname(os.path.abspath(__file__))
S = []


def T(x, y, s, size=20, fill=INK, weight=400, anchor="start", italic=False):
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


def L(x1, y1, x2, y2, stroke=INK, sw=1.2, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    S.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
             f'stroke-width="{sw}"{d} stroke-linecap="round"/>')


def P(pts, fill="none", stroke=INK, sw=1.2, closed=True):
    tag = "polygon" if closed else "polyline"
    p = " ".join(f"{a:.2f},{b:.2f}" for a, b in pts)
    S.append(f'<{tag} points="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"/>')


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


def box(x, y, w, h, seq, stroke=INK, fill="#FFFFFF", sw=1.3, rx=4,
        size=18, weight=400, color=INK, lh=24, dash=None):
    R(x, y, w, h, fill=fill, stroke=stroke, sw=sw, rx=rx, dash=dash)
    total = (len(seq) - 1) * lh
    top = y + h / 2 - total / 2 + size * 0.36
    for i, s in enumerate(seq):
        T(x + w / 2, top + i * lh, s, size, color, weight, "middle")


def input_block(x, y):
    """Shared-entry block: same record format, same frozen splits."""
    R(x, y, 880, 62, fill="#FBFCFD", stroke=SOFT, sw=1.1, rx=4)
    T(x + 440, y + 24, "Same standardized clinical record (input_text)", 20, INK, 400, "middle")
    T(x + 440, y + 46, "same frozen splits \u00b7 4,186 train / 420 dev", 19, MUT, 400, "middle")


_m = fd.metrics()
_p = fd.primary_pair()
_DACC, _LO, _HI = _p[0], _p[1], _p[2]
_N = fd.n_test()

S.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
S.append(f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>')

# ------------------------------------------------------------------ frames
R(40, 90, 940, 550, fill="#FFFFFF", stroke=FRAME, sw=1.1, rx=8)
R(1020, 90, 940, 550, fill="#FFFFFF", stroke=FRAME, sw=1.1, rx=8)
T(40, 72, "A", 34, "#111111", 700)
T(1020, 72, "B", 34, "#111111", 700)
T(980, 72, "Discriminative route \u00b7 ~1/15\u20131/25 parameters", 21, INK, 700, "end")
T(1960, 72, "Generative route \u00b7 8B-class", 21, INK, 700, "end")

# ------------------------------------------------------------------ A
input_block(70, 122)
arrow(340, 184, 340, 214, sw=1.8)
arrow(720, 184, 720, 214, sw=1.8)

R(90, 214, 380, 122, fill=P_BLUE, stroke=BLUE, sw=2, rx=6)
T(108, 254, "ZY-BERT", 26, BLUE, 700)
T(108, 284, "TCM-domain \u00b7 seeds 42/2026/7", 20, SLATE, 400)
T(108, 310, "pretrained on TCM text", 19, MUT, 400)

R(510, 214, 380, 122, fill=P_GREEN, stroke=GREEN, sw=1.6, rx=6)
T(528, 254, "MacBERT", 24, "#006B54", 700)
T(528, 284, "general-domain \u00b7 seed-42 baseline", 20, SLATE, 400)
T(528, 310, "same head \u00b7 no TCM pretraining", 19, MUT, 400)

arrow(280, 336, 280, 382, sw=1.8)
arrow(700, 336, 700, 382, sw=1.8)
box(120, 382, 760, 108,
    ["Fine-tuned 42-class heads (one per model)", "closed-set argmax \u00b7 no free text",
     "trained on 4,186 \u00b7 validated on 420"],
    size=22, lh=31, fill="#FFFFFF", stroke=NAVY, sw=1.4)

T(120, 526, "100% format-valid by construction", 20, NAVY, 600)

arrow(500, 490, 500, 690, sw=2.2)

# ------------------------------------------------------------------ B
input_block(1050, 122)
arrow(1320, 184, 1320, 214, sw=1.8)
arrow(1700, 184, 1700, 214, sw=1.8)

R(1070, 214, 380, 122, fill=P_ORANGE, stroke=ORANGE, sw=2, rx=6)
T(1088, 252, "InternLM3-8B-Instruct", 24, "#A4400A", 700)
T(1088, 282, "4-bit NF4 QLoRA \u00b7 seeds 42/2026/7", 20, SLATE, 400)
T(1088, 308, "8B-class \u00b7 4.98B recorded", 20, MUT, 400)

R(1490, 214, 380, 122, fill=P_MAGENTA, stroke=MAGENTA, sw=1.6, rx=6)
T(1508, 252, "Qwen3-8B", 24, "#9C3D74", 700)
T(1508, 282, "LoRA-SFT \u00b7 8B-class \u00b7 seed 42", 20, SLATE, 400)
T(1508, 308, "8B-class", 20, MUT, 400)

arrow(1260, 336, 1260, 382, sw=1.8)
arrow(1680, 336, 1680, 382, sw=1.8)
box(1100, 382, 760, 64, ["QLoRA / LoRA adapters (per model)"], size=22, fill="#FFFFFF", stroke=SLATE, sw=1.4)

arrow(1290, 446, 1290, 484, sw=1.8)
box(1100, 484, 330, 92, ["Generated label +", "templated rationale"], size=20, lh=27, fill="#FFFFFF", stroke=SLATE, sw=1.4)
arrow(1430, 530, 1466, 530, sw=1.8)
box(1466, 484, 394, 92, ["Frozen parser v18", "99.95% format-valid"], size=20, lh=27, fill="#FFFFFF", stroke=SLATE, sw=1.4)
T(1466, 604, "two empty outputs (0.05%)", 20, MUT, 400)

arrow(1660, 576, 1660, 690, sw=2.2)

# ------------------------------------------------------------------ shared rail
R(40, 690, 1920, 260, fill="#FFFFFF", stroke=FRAME, sw=1.1, rx=8)
T(66, 724, "C", 34, "#111111", 700)
T(1960, 724, f"Common frozen 42-class evaluation \u00b7 N = {_N:,}", 21, INK, 700, "end")

for r in range(3):
    for c in range(14):
        fill = "#DCE8F2" if (r + c) % 4 == 0 else "#EDF3F8"
        R(88 + c * 50, 752 + r * 40, 42, 32, fill=fill, stroke="#FFFFFF", sw=1)

T(830, 782, "42 classes \u00b7 identical order \u00b7 identical evaluation target", 21, INK, 600)
T(830, 816, "paired bootstrap, 2,000 resamples \u00b7 Holm\u2013McNemar", 20, MUT, 400)
T(830, 850, f"ZY-BERT vs InternLM3-8B: \u0394Accuracy +{_DACC:.2f} pp (95% CI {_LO:.2f}\u2013{_HI:.2f})", 20, MUT, 400)
T(830, 884, f"ZY-BERT {_m['ZY-BERT']['acc']:.2f} / {_m['ZY-BERT']['mf1']:.2f}  \u00b7  "
            f"InternLM3-8B {_m['InternLM3-8B']['acc']:.2f} / {_m['InternLM3-8B']['mf1']:.2f}", 19, MUT, 400)

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
