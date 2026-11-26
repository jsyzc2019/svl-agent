#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4gj 测试：认错台账四链闭环 + 双向校准 + 历史失效真实回放。"""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from life_kernel import correction_ledger as cl  # noqa: E402
from life_kernel import numeric_honesty as nh  # noqa: E402


def _good():
    return cl._good_case()


def test_c01_good_chain_closed():
    g = _good()
    assert cl.channel_status(g["detect"], g["records"], True).status == "CORRECTION_CLOSED"


def test_c02_no_error_no_fabrication():
    # 无失败信号不得硬造认错
    assert cl.channel_status([], [], True).status == "NO_CORRECTION_NEEDED"


def test_c03_detected_but_unrecorded():
    assert cl.channel_status(["kb_count"], [], False).status == "DETECTED_BUT_UNRECORDED"


def test_c04_record_without_propagation():
    g = _good()
    assert cl.channel_status(g["detect"], g["records"], False).status == "RECORD_WITHOUT_PROPAGATION"


def test_c05_tamper_caught():
    g = _good()
    bad = [{**g["records"][0], "truth": "999"}]
    assert cl.channel_status(g["detect"], bad, True).status == "RECORD_TAMPER"


def test_c06_broken_chain_caught():
    r = cl.make_correction({"x": "y"}, "a", "b", "numeric_honesty.check_handoff",
                           "CORR-X", "2026-11-26T06:02:00Z", prev_hash="WRONG")
    assert cl.channel_status(["x"], [r], True).status == "RECORD_TAMPER"


def test_c07_self_hash_recomputable():
    g = _good()
    assert cl._self_hash(g["records"][0]) == g["records"][0]["self_hash"]


def test_c08_blind_spot_permissive():
    assert cl.blind_spot_check(lambda c: True)["status"] == "OVERREJECT"


def test_c09_blind_spot_strict():
    assert cl.blind_spot_check(lambda c: False)["status"] == "BLIND_SPOT"


def test_c10_real_judge_calibrated():
    assert cl.blind_spot_check(cl.is_bad_chain)["status"] == "ALL_KNOWN_BAD_CHAINS_RECOGNIZED"


def test_c11_wiring_self_check():
    assert cl.wiring_self_check(["tests/test_correction_ledger.py::test_c01_good_chain_closed"])
    assert not cl.wiring_self_check(["tests/test_unrelated.py::t"])


def test_c12_live_regression_all_green():
    lr = cl.live_regression()
    assert all(lr.values()), [k for k, v in lr.items() if not v]


def test_c13_prereg_locked():
    import hashlib
    p = os.path.join(ROOT, "prereg_correction_ledger_20261126.json")
    s = os.path.join(ROOT, "prereg_correction_ledger_20261126.sha256")
    assert hashlib.sha256(open(p, "rb").read()).hexdigest() == open(s).read().split()[0]
    assert json.load(open(p, encoding="utf-8"))["written_at_utc"] == "2026-11-26T06:00:09Z"


def test_c14_h01_historical_replay_471_470():
    """H01 真实回放：§4gf 报告KB=471现场470。
    用真的 check_handoff 产生 detect 信号→认错记录→权威行修正→check ok。
    证明通道能逼出'我错了'并机械驱动权威行，非人肉自觉。"""
    truth = {"kb_count": 470, "safari_rounds": 133, "constitution_prefix": "fe56291b",
             "verdict": "GAP_INCONCLUSIVE", "l3_claimed": False, "absolute_claimed": False,
             "test_count": None}
    bad_line = ("- **权威现状**：全量测试 **1593**、知识库 **471** 条、"
                "Safari 台账 **133** 轮、宪法锁 SHA256 `fe56291b…` 一致；"
                "`verdict=GAP_INCONCLUSIVE`、`l3=false`、`absolute=false`。")
    # L1 detect：真的判据抓错
    detected = nh.check_handoff(bad_line, truth)
    assert not detected["ok"] and "kb_count" in detected["failed"]
    # L1.5 当时状态：抓到了但没落记录 → 通道判 DETECTED_BUT_UNRECORDED
    v0 = cl.channel_status(detected["failed"], [], False)
    assert v0.status == "DETECTED_BUT_UNRECORDED"
    # L2 机械生成认错记录
    rec = cl.make_correction({"kb_count": "declared471_vs_truth470"}, "471", "470",
                             "numeric_honesty.check_handoff", "CORR-H01",
                             "2026-11-26T06:01:00Z")
    # L3 驱动权威行修正（471→470）
    fixed_line = bad_line.replace("知识库 **471** 条", "知识库 **470** 条")
    after = nh.check_handoff(fixed_line, truth)
    assert after["ok"]
    # L4 四链闭合
    v1 = cl.channel_status(detected["failed"], [rec], after["ok"])
    assert v1.status == "CORRECTION_CLOSED"
    assert v1.detail["chain"]["links_ok"] and v1.detail["chain"]["order_ok"]


def test_c15_h02_fake_sync_replay():
    """H02 F07：旧记忆声称GitHub已同步c446e01现场未推。
    存在性判据抓到无句柄→认错记录→撤销假声明→闭合。"""
    from life_kernel import claim_honesty as ch
    claims = [{"text": "GitHub同步已成功", "is_existence": True}]  # 无句柄
    verdicts = ch.existence_claim_guard(claims)
    assert verdicts[0].status == "UNVERIFIED_CLAIM"
    detected = ["github_sync_unverified"]
    rec = cl.make_correction({"github_sync": "claimed_but_unverified"},
                             "已同步c446e01", "未推", "claim_honesty.existence_claim_guard",
                             "CORR-H02", "2026-11-26T06:01:30Z")
    # 撤销假声明后权威行 ok（此处用合成 authority_ok=True 表示假声明已撤）
    v = cl.channel_status(detected, [rec], True)
    assert v.status == "CORRECTION_CLOSED"
    # 对照：不撤假声明(authority_ok=False)→未传播，不放行
    assert cl.channel_status(detected, [rec], False).status == "RECORD_WITHOUT_PROPAGATION"
