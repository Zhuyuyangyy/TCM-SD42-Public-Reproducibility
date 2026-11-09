#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Figure 4 v3 - two-route comparison plate with matched-protocol annotations.

Changes vs v2:
  - input blocks now state the shared frozen splits (4,186 train / 420 dev)
  - denser panel A (models and head block enlarged, dead space removed)
  - 'Prompt / QLoRA / LoRA adapters' corrected to 'QLoRA / LoRA adapters'
  - shared rail tab now carries the full split counts
"""
import math
import os

W, H = 2000, 1000
INK = "#222222"
MUT = "#666666"
RULE = "#B9C2CA"
SOFT = "#E7EBEF"
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


def tab(x, y, w, text, size=20):
    R(x, y, w, 46, fill="#FFFFFF", stroke=RULE, sw=1.2, rx=4)
    T(x + w / 2, y + 30, text, size, "#111111", 700, "middle")


def box(x, y, w, h, seq, stroke=INK, fill="#FFFFFF", sw=1.3, rx=4,
        size=18, weight=400, color=INK, lh=24, dash=None):
    R(x, y, w, h, fill=fill, stroke=stroke, sw=sw, rx=rx, dash=dash)
    total = (len(seq) - 1) * lh
    top = y + h / 2 - total / 2 + size * 0.36
    for i, s in enumerate(seq):
        T(x + w / 2, top + i * lh, s, size, color, weight, "middle")


def input_block(x, y):
    """Shared-entry block: same record format, same frozen splits."""
    R(x, y, 880, 62, fill="#F7F9FA", stroke=SOFT, sw=1.2, rx=4)
    T(x + 440, y + 26, "Same standardized clinical record (input_text)", 17, INK, 400, "middle")
    T(x + 440, y + 48, "same frozen splits \u00b7 4,186 train / 420 dev", 14, MUT, 400, "middle")


S.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
S.append(f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>')

# ------------------------------------------------------------------ frames
R(40, 90, 940, 550, fill="#FFFFFF", stroke=RULE, sw=1.4, rx=18)
R(1020, 90, 940, 550, fill="#FFFFFF", stroke=RULE, sw=1.4, rx=18)
T(40, 72, "A", 34, "#111111", 700)
T(1020, 72, "B", 34, "#111111", 700)
tab(240, 67, 540, "Discriminative route \u00b7 ~1/15\u20131/25 parameters")
tab(1220, 67, 540, "Generative route \u00b7 8B-class")

# ------------------------------------------------------------------ A
input_block(70, 122)
arrow(340, 184, 340, 214, sw=1.8)
arrow(720, 184, 720, 214, sw=1.8)

R(90, 214, 380, 122, fill=P_BLUE, stroke=BLUE, sw=2, rx=8)
T(108, 254, "ZY-BERT", 26, BLUE, 700)
T(108, 284, "TCM-domain encoder \u00b7 seeds 42 / 2026 / 7", 15, SLATE, 400)
T(108, 310, "pretrained on TCM text \u00b7 fine-tuned head", 14, MUT, 400)

R(510, 214, 380, 122, fill=P_GREEN, stroke=GREEN, sw=1.6, rx=8)
T(528, 254, "MacBERT", 24, "#006B54", 700)
T(528, 284, "general-domain \u00b7 historical seed-42", 15, SLATE, 400)
T(528, 310, "same head architecture, no TCM pretraining", 14, MUT, 400)

arrow(280, 336, 280, 382, sw=1.8)
arrow(700, 336, 700, 382, sw=1.8)
box(120, 382, 760, 92,
    ["Fine-tuned 42-class heads (one per model)", "closed-set argmax \u00b7 no free text",
     "trained on 4,186 \u00b7 validated on 420"],
    size=19, lh=26, fill="#F4F8FB", stroke=NAVY, sw=1.4)

T(120, 512, "100% format-valid by construction", 16, NAVY, 600)
T(120, 538, "\u2192 class index, no parsing step", 15, MUT, 400)
T(520, 512, "Frozen label order, identical for all systems", 15, MUT, 400)

arrow(500, 474, 500, 690, sw=2.2)

# ------------------------------------------------------------------ B
input_block(1050, 122)
arrow(1320, 184, 1320, 214, sw=1.8)
arrow(1700, 184, 1700, 214, sw=1.8)

R(1070, 214, 380, 122, fill=P_ORANGE, stroke=ORANGE, sw=2, rx=8)
T(1088, 252, "InternLM3-8B-Instruct", 19, "#A4400A", 700)
T(1088, 282, "4-bit NF4 QLoRA \u00b7 seeds 42 / 2026 / 7", 14, SLATE, 400)
T(1088, 308, "8B-class \u00b7 4.98B recorded", 14, MUT, 400)

R(1490, 214, 380, 122, fill=P_MAGENTA, stroke=MAGENTA, sw=1.6, rx=8)
T(1508, 252, "Qwen3-8B", 24, "#9C3D74", 700)
T(1508, 282, "LoRA-SFT \u00b7 historical seed-42", 15, SLATE, 400)
T(1508, 308, "8B-class", 14, MUT, 400)

arrow(1260, 336, 1260, 382, sw=1.8)
arrow(1680, 336, 1680, 382, sw=1.8)
box(1100, 382, 760, 64, ["QLoRA / LoRA adapters (per model)"], size=19, fill="#F4F6F8", stroke=SLATE, sw=1.4)

arrow(1290, 446, 1290, 484, sw=1.8)
box(1100, 484, 330, 92, ["Generated label +", "templated rationale"], size=17, lh=24, fill="#FFFFFF", stroke=SLATE, sw=1.4)
arrow(1430, 530, 1466, 530, sw=1.8)
box(1466, 484, 394, 92, ["Frozen parser v18", "99.95% format-valid"], size=18, lh=24, fill="#FFFFFF", stroke=SLATE, sw=1.4)
T(1466, 604, "two empty outputs (0.05%)", 15, MUT, 400)

arrow(1660, 576, 1660, 690, sw=2.2)

# ------------------------------------------------------------------ shared rail
R(40, 690, 1920, 260, fill="#FBFCFD", stroke=RULE, sw=1.4, rx=18)
T(66, 724, "C", 34, "#111111", 700)
tab(520, 667, 960, "Common frozen 42-class evaluation \u00b7 N = 4,218", 20)

for r in range(3):
    for c in range(14):
        fill = "#DCE8F2" if (r + c) % 4 == 0 else "#EDF3F8"
        R(88 + c * 50, 752 + r * 40, 42, 32, fill=fill, stroke="#FFFFFF", sw=1)

T(830, 782, "42 classes \u00b7 identical order \u00b7 identical evaluation target", 18, INK, 600)
T(830, 816, "paired bootstrap, 2,000 resamples \u00b7 Holm\u2013McNemar", 16, MUT, 400)
T(830, 850, "ZY-BERT vs InternLM3-8B: \u0394Accuracy +6.19 pp (95% CI 4.93\u20137.44)", 16, MUT, 400)
T(830, 884, "ZY-BERT 75.77 / 66.51  \u00b7  InternLM3-8B 69.58 / 60.74", 15, MUT, 400)

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
