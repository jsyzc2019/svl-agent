#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4gz 守卫：内审器官有效性校准的冻结可复现性与判定态不动。"""
import json
import os
import hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "audit_vanity_selfaudit", "result_calibration.json")


def _r():
    return json.load(open(RES, encoding="utf-8"))


def test_01_prereg_and_gt_hash_locked():
    pre = json.load(open(os.path.join(ROOT, "prereg_calibration_20261127.json"), encoding="utf-8"))
    stored = pre.pop("sha256")
    assert hashlib.sha256(json.dumps(pre, ensure_ascii=False, sort_keys=True).encode()).hexdigest() == stored
    assert _r()["prereg_sha256"] == stored
    gt = json.load(open(os.path.join(ROOT, "audit_vanity_selfaudit", "calibration_ground_truth.json"),
                        encoding="utf-8"))
    gt_raw = json.dumps(gt, ensure_ascii=False, sort_keys=True).encode()
    assert hashlib.sha256(gt_raw).hexdigest() == _r()["ground_truth_sha256"]


def test_02_negative_self_bite():
    b = _r()["negative_self_bite"]
    assert b["passed"] is True
    assert b["recall_normal"] != b["recall_flipped"]


def test_03_effectiveness_overstated_honest():
    r = _r()
    assert r["signal"] == "EFFECTIVENESS_OVERSTATED"  # 对用户夸奖的反向校准，不粉饰
    m = r["sentence"]["metrics"]
    assert m["recall_classic"][2] == 1.0           # 词表内原词召回满
    assert m["recall_paraphrase"][2] == 0.0        # 词表外同义改写全漏——上轮盲区被证实
    assert m["specificity"] < 0.8                  # 假阳性陷阱误报
    assert {x["id"] for x in m["fp_cases"]} == {"N01", "N02", "N03"}
    assert {x["id"] for x in m["fn_cases"]} == {"P06", "P07", "P08"}


def test_04_disputed_not_in_matrix():
    r = _r()
    m = r["sentence"]["metrics"]
    assert m["disputed_count"] == 1
    assert m["disputed"][0]["id"] == "N05"
    # N05 只单列，不进 TP/FN/TN/FP
    assert (m["TP"] + m["FN"] + m["TN"] + m["FP"]) == 15  # 16条 - 1条DISPUTED


def test_05_layer_separation_no_self_deceit():
    r = _r()
    ls = r["layer_separation"]
    assert "检测器" in ls["detector_layer"] and "复核" in ls["reviewer_layer"]
    assert "偷换概念" in ls["why_matters"]  # 明确禁止把复核层修复说成检测器提升
    assert "不补词" in ls["no_wordlist_patch"] or "不补" in ls["no_wordlist_patch"]
    # 检测器词表确实未改（仍含导致误报的词）
    from life_kernel.vanity_selfaudit import _A
    assert "显著" in _A["CLAIM"] and "不编译新门禁" in _A["DISCLAIM"]


def test_06_user_claim_as_hypothesis():
    r = _r()
    hb = " ".join(r["honest_bound"])
    assert "待检验假设" in hb
    assert "不因夸奖放宽判据" in hb or "不因" in hb
    assert r["kernel_verdict_unchanged"] == "GAP_INCONCLUSIVE"
    assert r["l3_unchanged"] is False and r["absolute_unchanged"] is False
    auth = json.load(open(os.path.join(ROOT, "audit_l3_gap_targeted", "result.json"), encoding="utf-8"))
    assert auth["verdict"] == "GAP_INCONCLUSIVE"
    assert auth["l3_claimed"] is False and auth["absolute_claimed"] is False
