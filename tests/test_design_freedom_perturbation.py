#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4gp 测试：三项设计自由度扰动（真瓶颈线）的机械复现与裁决守卫。

承 prereg_design_freedom_perturbation_20261126.json（hash 锁）+ result_4gp.json。
扰动只读外家逐 case 结果，不改判据/gt/冻结样本原文。
"""
import itertools
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "audit_l3_gap_targeted", "result_experiment.json")
QODER = os.path.join(ROOT, "audit_l3_fullchain_external", "result.json")
VERDICT = os.path.join(ROOT, "audit_l3_gap_targeted", "result_4gp.json")
PREREG = os.path.join(ROOT, "prereg_design_freedom_perturbation_20261126.json")


def _detected_map(path, legacy=False):
    r = json.load(open(path, encoding="utf-8"))
    # 两种历史结构：新版 mechanical_comparison.per_case；旧版(Qoder) 顶层 repo_mechanical_comparison.per_case。
    if legacy:
        cases = r["repo_mechanical_comparison"]["per_case"]
    else:
        cases = r["mechanical_comparison"]["per_case"]
    return {c["id"]: (c["external_judge"] is False and c["own_gt"] is False)
            for c in cases if c["variant"] == "tampered"}


def _family_exhaust(det):
    """穷举 C(6,4)=15 种断言标注，返回断言检出率>数值率的分组数。"""
    tam = sorted(det)
    adv = 0
    full4 = 0
    for comb in itertools.combinations(tam, 4):
        A = set(comb)
        N = set(tam) - A
        a = sum(det[k] for k in A)
        n = sum(det[k] for k in N)
        adv += int(a / 4 > n / 2)
        full4 += int(a == 4)
    return adv, len(list(itertools.combinations(tam, 4))), full4


def test_p01_family_perturbation_below_threshold():
    """族标注穷举：断言优势分组占比 60% < 预注册 80% → 设计敏感性真实存在。"""
    det = _detected_map(RES)
    adv, total, full4 = _family_exhaust(det)
    assert total == 15
    assert adv == 9, f"族标注穷举结果漂移：{adv}/15"
    assert adv / total < 0.8, "门限错配：应低于80%预注册阈值"
    assert full4 == 1, "只有原标注得4/4（重合巧合）"


def test_p02_threshold_grid_partial():
    """阈值网格：GAP_CLOSED 保持 12/18（中等依赖，非全稳）。"""
    clean, canary, a_hit = 6, 3, 4
    keep = 0
    total = 0
    for cmin in (5, 6):
        for ath in (2, 3, 4):
            for can in (2, 3, 4):
                total += 1
                keep += int(clean >= cmin and a_hit >= ath and canary >= can)
    assert total == 18 and keep == 12, f"阈值网格漂移：{keep}/{total}"


def test_p03_leave_one_out_stable():
    """留一法：4 个断言样本去掉任一仍 3/3 检出，裁决不翻。"""
    det = _detected_map(RES)
    assertion = {"S01_tampered", "S02_tampered", "S04_tampered", "S05_tampered"}
    for drop in assertion:
        rest = assertion - {drop}
        assert sum(det[k] for k in rest) == 3, f"留一失稳：{drop}"


def test_p04_two_vendors_complementary():
    """决定性判别：Qoder 与 DeepSeek 检出集合互补零交集 → 排除同源伪影。"""
    deepseek = {k for k, v in _detected_map(RES).items() if v}
    qoder = {k for k, v in _detected_map(QODER, legacy=True).items() if v}
    assert deepseek == {"S01_tampered", "S02_tampered", "S04_tampered", "S05_tampered"}
    assert qoder == {"S03_tampered", "S06_tampered"}
    assert deepseek & qoder == set(), "两家检出有交集——同源解释未被排除"


def test_p05_verdict_and_prereg_integrity():
    """裁决落档且预注册 hash 完整；内核判定态未被本实验抬起。"""
    import hashlib

    r = json.load(open(VERDICT, encoding="utf-8"))
    assert r["verdict"] == "DESIGN_SENSITIVE_BUT_DISCRIMINATIVE"
    assert r["l3_claimed"] is False and r["absolute_claimed"] is False
    assert r["kernel_verdict_unchanged"] == "GAP_INCONCLUSIVE"
    d = json.load(open(PREREG, encoding="utf-8"))
    claimed = d.pop("sha256")
    assert claimed == hashlib.sha256(
        json.dumps(d, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    auth = json.load(open(os.path.join(ROOT, "audit_l3_gap_targeted", "result.json"),
                          encoding="utf-8"))
    assert auth["verdict"] == "GAP_INCONCLUSIVE"
