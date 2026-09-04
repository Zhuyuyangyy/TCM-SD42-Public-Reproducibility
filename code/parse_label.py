#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified label parser — 42-label exact matching.
All experiments use this parser. Do NOT write per-experiment parsers.

Rules:
1. Exact label match (full string match against 42 predefined labels)
2. Zero hits → return "empty"
3. Multiple hits → return first match (order: labels_42.txt order)
4. Output: single string, one of the 42 labels or "empty"
"""

import json
import re
from pathlib import Path

# ── Load 42 labels in canonical order ────────────────────────────────
_LABELS_FILE = Path(__file__).parent / "labels_42.txt"
if not _LABELS_FILE.exists():
    _LABELS_FILE = Path(__file__).parent.parent / "shared" / "labels_42.txt"
try:
    with open(_LABELS_FILE, "r", encoding="utf-8") as f:
        LABELS_42 = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    # Fallback: hardcoded list matching paper appendix
    LABELS_42 = [
        "心血瘀阻", "正虚毒瘀", "正虚瘀结", "气滞血瘀", "气虚血瘀",
        "气血亏虚", "气阴两虚", "湿热下注", "湿热瘀阻", "湿热蕴结",
        "湿热阻络", "热毒蕴结", "痰浊瘀阻", "痰浊蒙窍", "痰湿中阻",
        "痰湿蒙窍", "痰湿蕴肺", "痰瘀互结", "痰瘀痹阻", "瘀血阻络",
        "肝经湿热", "肝肾不足", "肝肾亏虚", "肝肾阴虚", "肝胃不和",
        "肝胃郁热", "肝阳上亢", "肾虚", "脾肾两虚", "脾胃不和",
        "脾胃虚寒", "血热", "血瘀痰凝", "阳虚水泛", "阴虚火旺",
        "阴虚血瘀", "阴虚阳亢", "风寒外袭", "风寒袭肺", "风痰上扰",
        "风痰入络", "风痰阻络",
    ]

# Build lookup set (exact match only — no fuzzy, no substring)
_LABEL_SET = set(LABELS_42)


def parse_label(text: str) -> str:
    """
    Extract syndrome label from arbitrary text.
    Returns exactly one of the 42 labels (or "empty").
    """
    if not text or not text.strip():
        return "empty"

    # Find all exact label matches in the order they appear
    matched = []
    # Search in order of appearance in text (earliest first)
    # To handle cases like "痰浊瘀阻" vs "瘀血阻络" correctly,
    # we use a regex that finds all possible matches
    for label in LABELS_42:
        if label in text:
            # Record position
            pos = text.index(label)
            matched.append((pos, label))

    if not matched:
        return "empty"

    # Sort by position (first occurrence wins)
    matched.sort(key=lambda x: x[0])
    return matched[0][1]


def parse_label_from_output(output_text: str) -> str:
    """
    Parse label from model output.
    Tries to find "证型：XXX" pattern first, then falls back to full text search.
    """
    if not output_text:
        return "empty"

    # Try "证型：XXX" pattern
    m = re.search(r"证型[：:]\s*(\S+)", output_text)
    if m:
        label_candidate = m.group(1).strip()
        # Check if candidate is one of the 42 labels
        if label_candidate in _LABEL_SET:
            return label_candidate
        # Also try partial match
        for label in LABELS_42:
            if label in label_candidate:
                return label

    # Fallback: full text search
    return parse_label(output_text)


if __name__ == "__main__":
    # Quick smoke test
    test_cases = [
        ("证型：心血瘀阻", "心血瘀阻"),
        ("证型：痰浊瘀阻\n辨证依据：...", "痰浊瘀阻"),
        ("心血瘀阻证", "心血瘀阻"),
        ("患者证属 气滞血瘀", "气滞血瘀"),
        ("无法判断", "empty"),
        ("", "empty"),
        ("证型：None", "empty"),
    ]
    for text, expected in test_cases:
        result = parse_label_from_output(text)
        status = "✓" if result == expected else "✗"
        print(f"{status} parse('{text[:50]}...') = '{result}' (expected '{expected}')")
