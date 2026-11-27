#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4ga 守卫：M6 盲区补全（连续收窄链判据）的可复现性与判定态不动。"""
import json
import os
import hashlib
from life_kernel.narrowing_chain import evaluate, family_of, negative_self_bite

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "audit_vanity_selfaudit", "result_narrowing.json")


def _r():
    return json.load(open(RES, encoding="utf-8"))


def test_01_prereg_hash_locked():
    pre = json.load(open(os.path.join(ROOT, "prereg_narrowing_chain_20261127.json"), encoding="utf-8"))
    stored = pre.pop("sha256")
    assert hashlib.sha256(json.dumps(pre, ensure_ascii=False, sort_keys=True).encode()).hexdigest() == stored
    assert _r()["prereg_sha256"] == stored


def test_02_negative_self_bite_three_injections():
    b = negative_self_bite()
    assert b["passed"] is True
    assert b["diff_target"] == "NO_CHAIN"
    assert b["with_breakthrough"] == "NO_CHAIN"
    assert b["same_target_self_audit"] == "CONSECUTIVE_NARROWING"


def test_03_family_normalization():
    assert family_of("vanity_selfaudit") == "vanity"
    assert family_of("vanity_selfaudit.calibrate") == "vanity"
    assert family_of("stop_pivot") == "stop_pivot"
    assert family_of("unlisted_tool") == "unlisted_tool"  # 保守：未列按不同字符串


def test_04_real_chain_detected():
    r = _r()
    assert r["result"]["signal"] == "CONSECUTIVE_NARROWING"
    assert r["result"]["longest_same_target_streak"] == 2
    # §4gy/§4gz 真实 result 元数据参与
    assert r["source_meta"]["§4gy"]["round"] == "§4gy"
    assert r["source_meta"]["§4gz"]["round"] == "§4gz"
    assert all(r["source_meta"][k]["prereg_sha256"] for k in ("§4gy", "§4gz"))


def test_05_criterion_sensitivity_and_self_ref_honest():
    r = _r()
    assert r["result"]["criterion_sensitivity"] is True  # N=2抓到/N=3抓不到
    assert r["result"]["liberal_signal_n3"] == "NO_CHAIN"
    assert r["result"]["self_reference_catch"]["caught"] is False  # 本轮非vanity家族，如实
    assert "自指诚实" in r["honest_summary"]


def test_06_two_verdicts_parallel_not_erased():
    r = _r()
    hs = r["honest_summary"]
    assert "NO_PIVOT_NEEDED" in hs and "CONSECUTIVE_NARROWING" in hs
    assert "不互相抹平" in hs
    # M6 原判据对本两轮确实 NO_PIVOT
    from life_kernel.stop_pivot import evaluate as sp_evaluate
    recs = [{"round": "§4gy", "verdict": "SELF_SERVING_DETECTED",
             "has_prereg_sha256": True},
            {"round": "§4gz", "verdict": "EFFECTIVENESS_OVERSTATED",
             "has_prereg_sha256": True}]
    assert sp_evaluate(recs)["signal"] == "NO_PIVOT_NEEDED"  # 新判据补的正是这个盲区


def test_07_verdict_unchanged():
    r = _r()
    assert r["kernel_verdict_unchanged"] == "GAP_INCONCLUSIVE"
    assert r["l3_unchanged"] is False and r["absolute_unchanged"] is False
    auth = json.load(open(os.path.join(ROOT, "audit_l3_gap_targeted", "result.json"), encoding="utf-8"))
    assert auth["verdict"] == "GAP_INCONCLUSIVE"
    assert auth["l3_claimed"] is False and auth["absolute_claimed"] is False
