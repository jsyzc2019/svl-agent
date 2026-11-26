#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4gt · M6 内生 stop/pivot 器官守卫（预注册 prereg_stop_pivot_20261126.json）。
固化：verdict 分类 / 三贡献位 / 双口径 / 负向自咬 / 真实序列结论 / 判定态不动。"""
import hashlib
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "life_kernel"))
import stop_pivot as sp  # noqa: E402


def test_01_prereg_hash_locked():
    """预注册 sha256 锁未被篡改。"""
    p = os.path.join(ROOT, "prereg_stop_pivot_20261126.json")
    d = json.load(open(p, encoding="utf-8"))
    stored = d.pop("sha256")
    raw = json.dumps(d, ensure_ascii=False, sort_keys=True)
    assert hashlib.sha256(raw.encode()).hexdigest() == stored
    assert stored == "2667a24e311d4e0af5535099b37bf0ab397feb6b0741e84549a1b77b0471ddfd"


def test_02_verdict_classification_locked():
    """verdict 分类按预注册锁定；未知落 GAP。"""
    assert sp.classify("GAP_CLOSED") == "BREAKTHROUGH"
    assert sp.classify("SPECIALIZED_SYNTAX") == "NARROW"
    assert sp.classify("ISOMORPHIC_CONFIRMED") == "NARROW"
    assert sp.classify("GAP_INCONCLUSIVE") == "GAP"
    assert sp.classify("TOTALLY_UNKNOWN_VERDICT") == "GAP"


def test_03_nutritive_three_flags():
    """营养轮=三贡献位全 false；任一为真即非营养轮。"""
    base = {"verdict": "GAP_INCONCLUSIVE", "has_prereg_sha256": False,
            "changed_criterion": False, "round": "X"}
    assert sp._is_nutritive(base, liberal=False) is True
    assert sp._is_nutritive({**base, "has_prereg_sha256": True}, liberal=False) is False
    assert sp._is_nutritive({**base, "changed_criterion": True}, liberal=False) is False
    assert sp._is_nutritive({**base, "verdict": "GAP_CLOSED"}, liberal=False) is False
    # NARROW 在保守口径非营养，宽口径仍非营养（GAP 类才两者都营养）
    assert sp._is_nutritive({**base, "verdict": "SPECIALIZED_SYNTAX"}, liberal=False) is True
    assert sp._is_nutritive({**base, "verdict": "SPECIALIZED_SYNTAX"}, liberal=True) is False


def test_04_streak_threshold():
    """连续营养轮计数与阈值触发。"""
    two = [{"round": str(i), "verdict": "GAP_INCONCLUSIVE",
            "has_prereg_sha256": False, "changed_criterion": False} for i in range(2)]
    assert sp.longest_nutritive_streak(two, liberal=False) == 2
    assert sp.evaluate(two)["signal"] == "NO_PIVOT_NEEDED"
    three = two + [{"round": "2", "verdict": "GAP_INCONCLUSIVE",
                    "has_prereg_sha256": False, "changed_criterion": False}]
    assert sp.evaluate(three)["signal"] == "PIVOT_ADVISED"


def test_05_negative_self_bite_must_trigger():
    """负向自咬：全营养轮序列两种口径都必须触发 PIVOT_ADVISED。"""
    r = sp.self_bite_check()
    assert r["passed"] is True
    assert r["conservative"] == "PIVOT_ADVISED"
    assert r["liberal"] == "PIVOT_ADVISED"


def test_06_real_sequence_result_persisted():
    """首用真实序列结果与落档文件一致；未伪造 pivot。"""
    p = os.path.join(ROOT, "audit_l3_gap_targeted", "result_4gt.json")
    d = json.load(open(p, encoding="utf-8"))
    assert d["prereg_sha256"] == "2667a24e311d4e0af5535099b37bf0ab397feb6b0741e84549a1b77b0471ddfd"
    assert d["self_bite_passed"] is True
    assert d["signal"] == "NO_PIVOT_NEEDED"
    assert d["longest_nutritive_streak_conservative"] == 1
    assert d["kernel_verdict_unchanged"] == "GAP_INCONCLUSIVE"
    assert d["l3_claimed"] is False and d["absolute_claimed"] is False


def test_07_criterion_sensitivity_exposed():
    """口径翻转若改变信号必须显式暴露，不得隐藏。"""
    # 构造只在宽口径翻转变的序列：NARROW verdict 且无 prereg
    recs = [{"round": str(i), "verdict": "SPECIALIZED_SYNTAX",
             "has_prereg_sha256": False, "changed_criterion": False} for i in range(3)]
    r = sp.evaluate(recs)
    assert r["signal"] == "PIVOT_ADVISED"          # 保守：NARROW 不算推翻→营养
    assert r["liberal_counter_signal"] == "NO_PIVOT_NEEDED"  # 宽：算推翻→非营养
    assert r["criterion_sensitivity"] is True      # 敏感性被显式暴露


def test_08_no_verdict_state_mutation():
    """器官运行不触碰内核判定态权威源。"""
    p = os.path.join(ROOT, "audit_l3_gap_targeted", "result.json")
    before = open(p, "rb").read()
    sp.evaluate([{"round": "X", "verdict": "GAP_CLOSED"}])
    sp.self_bite_check()
    after = open(p, "rb").read()
    assert before == after
