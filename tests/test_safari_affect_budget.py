#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4S2 Safari 守卫：拿 A 级一手打 §4hi 前提的裁决必须可复现、可证伪。"""
import os
import json
import hashlib

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from audit_safari_affect_budget import engine as E

RESULT = os.path.join(ROOT, "audit_safari_affect_budget", "result.json")
HERE = os.path.join(ROOT, "audit_safari_affect_budget")
PREREG = os.path.join(ROOT, "prereg_safari_affect_budget_20261127.json")


def _result():
    return json.load(open(RESULT, encoding="utf-8"))


def test_01_verdict_refine_deep():
    r = _result()
    assert r["verdict"] == "REFINE_DEEP"
    assert r["all_evidence_ok"] is True
    assert r["verified_hits"] == 3


def test_02_three_questions_covered():
    r = _result()
    assert set(r["questions"]) == {"F1_core", "F2_anchor", "F3_backfire"}
    for q in r["questions"].values():
        assert q["ok"] is True
        assert q["misses"] == []


def test_03_evidence_manifest_sha256():
    """落盘的每篇证据 sha256 必须与现场文件一致（防证据被偷换）。"""
    r = _result()
    for e in r["evidence_manifest"]:
        p = os.path.join(HERE, e["file"])
        assert hashlib.sha256(open(p, "rb").read()).hexdigest() == e["sha256"]


def test_04_f1_effect_sizes_verbatim():
    """F1 效应量逐字锚必须真在原文：跨零 CI + 不显著 + 贝叶斯偏向零。"""
    q = E.check_question("F1_core")
    assert q["ok"] is True
    flat = [x["quote"] for s in q["sources"] for x in s["quotes_ok"] if x["hit"]]
    assert any("d = 0.04" in f and "0.15" in f for f in flat)
    assert any("nonsignificant result (d = 0.06)" in f for f in flat)
    assert any("4 times more likely under the null" in f for f in flat)


def test_05_f2_capacity_verbatim():
    q = E.check_question("F2_anchor")
    assert q["ok"] is True
    assert any("four chunks" in x["quote"] for s in q["sources"] for x in s["quotes_ok"] if x["hit"])


def test_06_f3_switch_cost_verbatim():
    q = E.check_question("F3_backfire")
    assert q["ok"] is True
    flat = [x["quote"] for s in q["sources"] for x in s["quotes_ok"] if x["hit"]]
    assert any("switch cost" in f or "overhead" in f for f in flat)
    assert any("residual component" in f for f in flat)


def test_07_refined_claim_reanchors_capacity():
    """REFINE 必须把有限性改锚容量瓶颈、不再宣称意志力耗尽。"""
    r = _result()
    c = r["refined_claim"]
    assert "容量瓶颈" in c and "four chunks" not in c  # 叙事提容量，不逐字抄论文数
    assert "意志力会耗尽" in c  # 明确点出被打穿的旧叙事
    assert "不越权" in c


def test_08_against_me_recorded():
    """对我不利的两条必须如实记，不粉饰成 DEFENDED。"""
    r = _result()
    assert "打穿" in r["honest_layer"]["against_me"]
    assert "反噬" in r["honest_layer"]["against_me"]
    assert "两条都对我不利" in r["honest_layer"]["against_me"]


def test_09_analogy_bounded():
    """人→Agent 类比必须有界，不能写成直接等号。"""
    r = _result()
    assert r["analogy_guarded"] is True
    assert "人类心理学效应 ≠ Agent 机制" in r["honest_layer"]["bounded_analogy"]


def test_10_no_overreach_boundaries():
    r = _result()
    b = r["hard_boundaries"]
    assert b["verdict_l3_absolute"] == "GAP_INCONCLUSIVE/false/false 未动"
    assert b["constitution"] == "fe56291b 未动"
    assert b["result_sha"] == "0f3ccb13 未动"
    assert b["no_new_gate"] and b["no_l3_raise"] and b["no_spawn"]


def test_11_prereg_before_evidence():
    """预注册文件真实存在且哈希落 result（先锁后取证）。"""
    r = _result()
    pr = json.load(open(PREREG, encoding="utf-8"))
    assert pr["round"] == "§4S2"
    assert set(pr["three_questions"]) == {"F1_core", "F2_anchor", "F3_backfire"}
    assert r["prereg_sha256"] and len(r["prereg_sha256"]) == 64


def test_12_evidence_missing_fails_gracefully():
    """若证据文件缺失，check_question 应报 ok=False 而非崩溃（判据不放宽、如实 EVIDENCE_MISS）。"""
    saved = dict(E.EVIDENCE["F2_anchor"])
    try:
        E.EVIDENCE["F2_anchor"] = {"pmid_missing": {
            "file": "nonexistent.txt", "sha256": "0000", "quotes": ["x"]}}
        q = E.check_question("F2_anchor")
        assert q["ok"] is False
        assert any("FILE_MISSING" in m for m in q["misses"])
    finally:
        E.EVIDENCE["F2_anchor"] = saved
