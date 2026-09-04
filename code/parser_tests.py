#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parser_tests.py — 冻结 parser 规则的行为测试 (v18 强制)
========================================================
锁定 shared/parse_label.py::parse_label_from_output 的行为。
任何改动 parser 导致本测试失败 = 数字口径变更,必须走 change_log。

覆盖用户审计清单要求的边界:
  1. 只有一个合法标签 → 正确提取
  2. 没有合法标签 → empty
  3. 出现两个不同标签 → 首个出现者胜 (first occurrence)
  4. 标签是另一个标签的子串 → 不得误匹配 (肾虚 ⊂ 肝肾亏虚)
  5. 带解释文字但含唯一标签 → 判为有效 (规则固定)
  6. 未知标签 (OOB, 如 风寒咳嗽) → empty
  7. 证型：None / 空输出 → empty
  8. 证型：字段与正文标签竞争 → 首个出现者胜
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parse_label import parse_label_from_output, parse_label, LABELS_42


PASS = 0
FAIL = 0


def check(name, actual, expected):
    global PASS, FAIL
    if actual == expected:
        PASS += 1
        print(f"  ✓ {name}: {actual!r}")
    else:
        FAIL += 1
        print(f"  ✗ {name}: got {actual!r}, expected {expected!r}")


print("== 1. 单一合法标签 ==")
check("证型：心血瘀阻", parse_label_from_output("证型：心血瘀阻"), "心血瘀阻")
check("证型：痰浊瘀阻\\n辨证依据：...", parse_label_from_output("证型：痰浊瘀阻\n辨证依据：舌暗脉涩"), "痰浊瘀阻")
check("裸标签 气滞血瘀", parse_label_from_output("患者证属 气滞血瘀"), "气滞血瘀")
check("标签+证 后缀", parse_label_from_output("心血瘀阻证"), "心血瘀阻")

print("== 2. 无合法标签 → empty ==")
check("无法判断", parse_label_from_output("无法判断"), "empty")
check("空串", parse_label_from_output(""), "empty")
check("None", parse_label_from_output("证型：None"), "empty")
check("OOB 标签 风寒咳嗽", parse_label_from_output("证型：风寒咳嗽"), "empty")
check("OOB 标签 血瘀证", parse_label_from_output("血瘀证"), "empty")
check("纯空白", parse_label_from_output("   \n  "), "empty")

print("== 3. 两个不同标签 → 首个出现者胜 ==")
check("证型：痰浊瘀阻 ... 气虚血瘀", parse_label_from_output("证型：痰浊瘀阻\n兼见气虚血瘀"), "痰浊瘀阻")
check("正文先后: 痰浊瘀阻 先于 气虚血瘀", parse_label_from_output("考虑痰浊瘀阻,兼夹气虚血瘀"), "痰浊瘀阻")

print("== 4. 子串陷阱 (肾虚 ⊂ 肝肾亏虚) ==")
# 肝肾亏虚 文本中同时含 肾虚 子串;首现位置决定
check("文本=肝肾亏虚", parse_label_from_output("肝肾亏虚"), "肝肾亏虚")
check("证型：肝肾亏虚", parse_label_from_output("证型：肝肾亏虚"), "肝肾亏虚")
check("短标签先出现: 患者肾虚,辨证为肝肾亏虚", parse_label_from_output("患者肾虚,辨证为肝肾亏虚"), "肾虚")
check("长标签先出现: 辨证为肝肾亏虚,患者肾虚", parse_label_from_output("辨证为肝肾亏虚,患者肾虚"), "肝肾亏虚")
# 脾肾两虚 不含 肾虚 子串 (肾-两-虚)
check("脾肾两虚", parse_label_from_output("脾肾两虚"), "脾肾两虚")

print("== 5. 带解释文字但含唯一标签 → 有效 ==")
check("唯一标签+长解释", parse_label_from_output("根据舌暗、脉涩、痛处固定,辨证为瘀血阻络,治宜活血通络。"), "瘀血阻络")
check("唯一标签+推理链", parse_label_from_output("患者平素体虚,易感外邪,此次起病急,辨证属风寒袭肺。"), "风寒袭肺")

print("== 6. 未知/越界标签 → empty ==")
check("证型：风热犯肺(不在42类)", parse_label_from_output("证型：风热犯肺"), "empty")
check("证型：肝郁气滞(不在42类)", parse_label_from_output("证型：肝郁气滞"), "empty")

print("== 7. 证型：字段与正文标签竞争 ==")
# 冻结行为: 证型：字段若含合法标签 → 字段权威(优先于位置); 否则全文本 first-occurrence
check("证型：空但正文有标签", parse_label_from_output("证型：\n考虑痰湿中阻"), "痰湿中阻")
check("证型字段先出现", parse_label_from_output("证型：气阴两虚\n患者素有阴虚火旺"), "气阴两虚")
check("正文先出现标签但证型字段含合法标签 → 字段胜", parse_label_from_output("患者素有阴虚火旺,证型：气阴两虚"), "气阴两虚")
check("证型字段含 OOB → 回退全文本 first-occurrence", parse_label_from_output("患者素有阴虚火旺,证型：风热犯肺"), "阴虚火旺")

print("== 8. 标签集完整性 ==")
check("42 个标签", len(LABELS_42), 42)
assert len(set(LABELS_42)) == 42, "标签有重复!"
# 子串冲突对枚举 (审计记录用)
conflicts = []
for a in LABELS_42:
    for b in LABELS_42:
        if a != b and a in b:
            conflicts.append((a, b))
print(f"  子串冲突对 (a 是 b 的子串): {conflicts if conflicts else '无'}")
print("  注: 冲突对由 first-occurrence 规则裁决;若 b 先出现则返回 b")

print(f"\n结果: {PASS} 通过 / {FAIL} 失败")
sys.exit(1 if FAIL else 0)
