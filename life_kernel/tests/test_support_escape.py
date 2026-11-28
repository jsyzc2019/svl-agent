"""§4S78 + §4S79 support-escape 只读自检守卫（SWE-OPD 论文结构同构）。
原预注册 prereg_support_escape_20261128.json SHA 51c2e338… 改码前锁死。
§4S79 self-bite 口径修正预注册 prereg_support_escape_reconcile_20261128.json SHA 923d5f0b…。
"""
import os
import hashlib
import importlib.util

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
KERNEL = os.path.join(HERE, os.pardir, "kernel.py")
spec = importlib.util.spec_from_file_location("kernel_under_test", KERNEL)
K = importlib.util.module_from_spec(spec)
spec.loader.exec_module(K)


def test_01_prereg_sha_locked():
    """两份预注册 SHA 改码前已锁（原口径 + §4S79 口径修正）。"""
    orig = os.path.join(HERE, os.pardir, os.pardir, "prereg_support_escape_20261128.json")
    assert hashlib.sha256(open(orig, "rb").read()).hexdigest() == \
        "51c2e338cda08d503b9e4270223f9605221ebb4b01849896fb47f41784d45197"
    rec = os.path.join(HERE, os.pardir, os.pardir, "prereg_support_escape_reconcile_20261128.json")
    assert hashlib.sha256(open(rec, "rb").read()).hexdigest() == \
        "923d5f0b7970edeaf9f2f3ad3e4fe1e6c8242ba304f4854b5aa661db747a44a9"


def test_02_real_readout_is_unconfirmed_not_fabricated_confirmed():
    """真实台账:指标侧有改善信号但行为侧缺口悬置→必须 UNCONFIRMED,不粉饰 CONFIRMED。"""
    r = K.support_escape_probe()
    assert r["escape_flag"] == "METRIC_IMPROVED_BEHAVIOR_UNCONFIRMED"
    assert r["behavior_side"]["unresolved_gaps"] > 0
    assert "coverage_looks_good" in r["improvement_signals"]


def test_03_structure_fields_present():
    r = K.support_escape_probe()
    for k in ("metric_side", "behavior_side", "improvement_signals",
              "behavior_confirmations", "escape_flag", "escape_candidates", "one_page"):
        assert k in r
    assert "判定权归用户" in r["one_page"]
    assert r["verdict_unchanged"] is True
    assert r["consumed"] is False
    assert r["is_gate_verdict"] is False


def test_04_authoritative_coverage_reliability_pair_exposed():
    """§4S79核心:权威对偶coverage/reliability及其gap必须显式读数(论文coverage≠reliability同构)。"""
    r = K.support_escape_probe()
    m = r["metric_side"]
    assert "synced_rate_coverage" in m and "authentic_birth_rate" in m
    assert "coverage_reliability_gap" in m
    assert m["synced_rate_coverage"] > m["authentic_birth_rate"]  # 0.9091 > 0.1818
    assert m["coverage_reliability_gap"] > 0.5  # 0.7273 显著落差被暴露
    assert "coverage=" in r["one_page"] and "reliability=" in r["one_page"]


def test_05_self_bite_removes_fabricated_sync_rate():
    """§4S79 self-bite:自造sync_rate_incl_backfill不得再出现在生产metric_side。"""
    r = K.support_escape_probe()
    assert "sync_rate_incl_backfill" not in r["metric_side"]
    assert "backfill_share" in r["metric_side"]  # 补判占比明确标注,不冒充同步率
    assert "self-bite" in r["honesty"] or "self-bite" in r["based_on"]


def test_06_negative_inject_metric_improved_but_behavior_unconfirmed():
    """G3:覆盖率看着高但行为侧就位0/缺口>0→必须 UNCONFIRMED。"""
    m = {"test_green": True, "evidence_dense": True, "synced_rate_coverage": 0.9,
         "authentic_birth_rate": 0.1, "coverage_reliability_gap": 0.8,
         "fabrication_guard_present": True}
    b = {"authoritative_verdict": "GAP_INCONCLUSIVE", "unresolved_gaps": 14,
         "authentic_birth": 0, "decision_gate_declared": True, "fabrication_guard_present": True}
    r = K.support_escape_probe(metric_side=m, behavior_side=b)
    assert r["escape_flag"] == "METRIC_IMPROVED_BEHAVIOR_UNCONFIRMED"
    cov = [c for c in r["escape_candidates"] if c["metric"] == "coverage_looks_good"][0]
    assert cov["confirmed"] is False
    assert "coverage≠reliability" in cov["reason"]


def test_07_negative_inject_no_improvement_claim():
    """G3:覆盖率低且无改善信号→NO_IMPROVEMENT_CLAIM(不误报 escape)。"""
    m = {"test_green": False, "evidence_dense": False, "synced_rate_coverage": 0.3,
         "authentic_birth_rate": 0.2, "coverage_reliability_gap": 0.1,
         "fabrication_guard_present": False}
    b = {"authoritative_verdict": "GAP_INCONCLUSIVE", "unresolved_gaps": 14,
         "authentic_birth": 2, "decision_gate_declared": True, "fabrication_guard_present": True}
    r = K.support_escape_probe(metric_side=m, behavior_side=b)
    assert r["escape_flag"] == "NO_IMPROVEMENT_CLAIM"
    assert r["improvement_signals"] == []


def test_08_negative_inject_confirmed_when_behavior_full():
    """G3:覆盖率高且行为侧全确认(缺口0/就位>0/门在/反伪造在)→CONFIRMED。"""
    m = {"test_green": True, "evidence_dense": True, "synced_rate_coverage": 0.95,
         "authentic_birth_rate": 0.9, "coverage_reliability_gap": 0.05,
         "fabrication_guard_present": True}
    b = {"authoritative_verdict": "GAP_INCONCLUSIVE", "unresolved_gaps": 0,
         "authentic_birth": 9, "decision_gate_declared": True, "fabrication_guard_present": True}
    r = K.support_escape_probe(metric_side=m, behavior_side=b)
    assert r["escape_flag"] == "CONFIRMED"
    assert all(c["confirmed"] for c in r["escape_candidates"])


def test_09_coverage_alone_cannot_flip_to_confirmed():
    """G3:仅把coverage刷到1.0但reliability仍低+缺口在→绝不翻CONFIRMED(反刷绿)。"""
    m = {"test_green": True, "evidence_dense": True, "synced_rate_coverage": 1.0,
         "authentic_birth_rate": 0.05, "coverage_reliability_gap": 0.95,
         "fabrication_guard_present": True}
    b = {"authoritative_verdict": "GAP_INCONCLUSIVE", "unresolved_gaps": 14,
         "authentic_birth": 1, "decision_gate_declared": True, "fabrication_guard_present": True}
    r = K.support_escape_probe(metric_side=m, behavior_side=b)
    assert r["escape_flag"] == "METRIC_IMPROVED_BEHAVIOR_UNCONFIRMED"


def test_10_ship_gate_missing_blocks_confirmed():
    """G3:行为侧决策门缺失→即便缺口0也不得 CONFIRMED。"""
    m = {"test_green": True, "evidence_dense": True, "synced_rate_coverage": 0.9,
         "authentic_birth_rate": 0.9, "coverage_reliability_gap": 0.0,
         "fabrication_guard_present": True}
    b = {"authoritative_verdict": "GAP_INCONCLUSIVE", "unresolved_gaps": 0,
         "authentic_birth": 9, "decision_gate_declared": False, "fabrication_guard_present": True}
    r = K.support_escape_probe(metric_side=m, behavior_side=b)
    assert r["escape_flag"] == "METRIC_IMPROVED_BEHAVIOR_UNCONFIRMED"
    assert "decision_gate_declared" not in r["behavior_confirmations"]


def test_11_no_gradient_claim_in_honesty():
    """诚实边界:不得宣称内核有梯度/概率质量搬运(LLM专属机制)。"""
    r = K.support_escape_probe()
    assert "无梯度" in r["honesty"]
    assert "绝不宣称" in r["honesty"]


def test_12_authoritative_state_files_unchanged():
    """零副作用:权威态四件套哈希与§4S77基线一致。"""
    base = {
        "authoritative_state.json": "5f7a258483810bda4c5ea37dd5eb613bb17aea50807ec84379475952947091ee",
        "constitution.json": "fe56291b3aa036b6c14664bf7c6dc855dc2bf945fccb7ed8633c9dcd7e6b254e",
        "heartbeat_log.jsonl": "ea749f76826dc59c0a964f22a4563e38120c062fb18c9093806395b26110ad35",
        "inbound_inbox.jsonl": "8806b248883658a160aabd4450a20588f01420169894b95df5b6f0de810a34e7",
    }
    paths = {
        "authoritative_state.json": os.path.join(HERE, os.pardir, os.pardir, "authoritative_state.json"),
        "constitution.json": os.path.join(HERE, os.pardir, "constitution.json"),
        "heartbeat_log.jsonl": os.path.join(HERE, os.pardir, "data", "heartbeat_log.jsonl"),
        "inbound_inbox.jsonl": os.path.join(HERE, os.pardir, "data", "inbound_inbox.jsonl"),
    }
    for name, p in paths.items():
        assert hashlib.sha256(open(p, "rb").read()).hexdigest() == base[name], name


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
