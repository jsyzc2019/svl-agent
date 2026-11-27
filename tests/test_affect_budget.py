"""注意力预算终止器官守卫（§4hi，functional affect，预注册 80e7fc36）。"""
import os
import json
import hashlib
import pytest

from life_kernel import affect_budget as AB

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _file_sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def test_01_prereg_hash_locked():
    p = os.path.join(ROOT, "prereg_affect_budget_20261127.json")
    d = json.load(open(p, encoding="utf-8"))
    d.pop("sha256", None)
    h = hashlib.sha256(json.dumps(d, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    declared = open(os.path.join(ROOT, "prereg_affect_budget_20261127.sha256")).read().split()[0]
    assert h == declared and h.startswith("80e7fc36")


def test_02_counterfactual_orthogonality():
    """反事实：两旧器官不用停、本器官独立触发——非装饰的机械证据。"""
    r = AB.counterfactual_check()
    assert r["orthogonal_independent_trigger"] is True
    assert r["affect_budget_signal"] == "EXHAUSTION"
    assert r["old_organ_signals"]["stop_pivot"] == "NO_PIVOT_NEEDED"
    assert r["old_organ_signals"]["narrowing_chain"] == "NO_CHAIN"


def test_03_negative_selfbite_all_caught():
    r = AB.negative_self_bite()
    assert r["passed"] is True
    assert r["low_no_false_alarm"] == "WITHIN_BUDGET"
    assert r["target_satiety"] == "SATIETY_WARNING"
    assert r["global_exhaustion"] == "EXHAUSTION"


def test_04_budget_priority():
    """EXHAUSTION 优先于 SATIETY：全局耗尽时即使单猎场也达阈值，报 EXHAUSTION。"""
    recs = [
        {"round": "P1", "target_object": "a", "attention_units": 2},
        {"round": "P2", "target_object": "a", "attention_units": 2},
        {"round": "P3", "target_object": "a", "attention_units": 2},
    ]  # 单猎场 6>=3 且全局 6>=6
    r = AB.evaluate(recs)
    assert r["signal"] == "EXHAUSTION"
    assert r["forced_stop"] is True
    assert r["advice"] == "FORCED_STOP_AND_PITCH"


def test_05_contribution_does_not_exempt():
    """正交性核心：有认知贡献也不豁免预算耗尽。"""
    with_contrib = [{"round": f"X{i}", "target_object": f"t{i}",
                     "has_prereg_sha256": True, "changed_criterion": True,
                     "attention_units": 2} for i in range(3)]
    r = AB.evaluate(with_contrib)
    assert r["signal"] == "EXHAUSTION"
    assert all(p["has_contribution"] for p in r["per_round"])


def test_06_criterion_sensitivity_exposed():
    """双口径敏感性暴露：T_exh=6 触发、T_exh=8 不触发时 sensitivity=true。"""
    recs = [{"round": f"S{i}", "target_object": f"t{i}", "attention_units": 2} for i in range(3)]
    r = AB.evaluate(recs)  # global=6
    assert r["signal"] == "EXHAUSTION"
    assert r["liberal_signal"] == "SATIETY_WARNING" or r["liberal_signal"] == "WITHIN_BUDGET"
    assert r["criterion_sensitivity"] is True


def test_07_first_use_snapshot_immutable():
    """首用快照固化 EXHAUSTION，只读不随重跑改写。"""
    snap = json.load(open(os.path.join(ROOT, "audit_affect_budget", "first_use_snapshot.json")))
    assert snap["signal"] == "EXHAUSTION"
    assert snap["global_cost"] == 8.0
    assert snap["immutable"]  # 固化标记存在


def test_08_no_qualia_claim():
    """诚实边界：不宣称主观情感/qualia/生命力。"""
    r = AB.evaluate([{"round": "N", "target_object": "a", "attention_units": 1}])
    bound = " ".join(r["honest_bound"])
    assert "qualia" in bound
    assert "不宣称" in bound
    assert "用户裁定" in bound or "归用户" in bound


def test_09_verdict_bytes_unchanged():
    """运行不改判定态/宪法锁字节。"""
    before = _file_sha(os.path.join(ROOT, "audit_l3_gap_targeted", "result.json"))
    AB.evaluate([{"round": "V", "target_object": "a", "attention_units": 99}])
    AB.counterfactual_check()
    after = _file_sha(os.path.join(ROOT, "audit_l3_gap_targeted", "result.json"))
    assert before == after and before.startswith("0f3ccb13")


def test_10_negative_cannot_false_alarm_on_empty():
    """空输入 / 低消耗不误报疲劳。"""
    assert AB.evaluate([])["signal"] == "WITHIN_BUDGET"
    assert AB.evaluate([{"round": "Z", "target_object": "a", "attention_units": 0}])["signal"] == "WITHIN_BUDGET"
