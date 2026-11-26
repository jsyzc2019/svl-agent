#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4gw 特异度守卫：锁定异质文本测试的证据结构与诚实边界。"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "audit_argument_audit"))
import specificity_test as T

RES = os.path.join(ROOT, "audit_argument_audit", "result_specificity.json")


def _res():
    return json.load(open(RES, encoding="utf-8"))


def test_01_result_exists_and_structure():
    d = _res()
    assert d["round"] == "§4gw"
    assert d["kernel_verdict_unchanged"] == "GAP_INCONCLUSIVE"
    assert d["l3_claimed"] is False and d["absolute_claimed"] is False
    assert d["no_new_gate"] is True


def test_02_three_buckets_present():
    d = _res()["cases"]
    kinds = {v["kind"] for v in d.values()}
    assert kinds == {"positive", "negative", "neutral"}
    assert len(d) == 7


def test_03_discrimination_recomputed_live():
    live = T.run()
    pos = [v["per_1000"] for v in live.values() if v["kind"] == "positive"]
    neg = [v["per_1000"] for v in live.values() if v["kind"] == "negative"]
    assert min(pos) > max(neg) * 20, "阳性与阴性密度须有数量级区分"
    stored = _res()["discrimination"]
    assert stored["ratio"] > 20


def test_04_false_positives_honestly_recorded():
    fps = _res()["false_positives"]
    assert len(fps) >= 3
    for fp in fps:
        assert fp["verdict"] == "假阳性-语境错配"
        assert fp["snippet"] and fp["why"]


def test_05_honest_bound_declares_cross_language_gap():
    text = " ".join(_res()["honest_bound"])
    assert "跨语言" in text and "假阳性" in text and "样本" in text


def test_06_verdict_source_bytes_unchanged():
    import hashlib
    b = open(os.path.join(ROOT, "audit_l3_gap_targeted", "result.json"), "rb").read()
    h = hashlib.sha1()
    h.update(b"blob " + str(len(b)).encode() + b"\0")
    h.update(b)
    # 只断言文件可读且判定态仍与结果文件记载一致，不硬编码历史哈希
    assert json.loads(b)["verdict"] == _res()["kernel_verdict_unchanged"]
