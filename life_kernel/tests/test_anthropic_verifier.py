"""§4S73 守卫：Anthropic《Migrating our Messages API to Rust》三处锋利点的只读自检。

预注册 prereg_anthropic_verifier_20261128.json SHA e94486b3… 改码前锁死。
纪律：G2 真实数据不伪造；G3 负向注入真通过/真失败；G6 同口径对拍；零副作用。
"""
import hashlib
import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kernel as K

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(HERE)


# ---------------- G2: 真实数据 ----------------

def test_green_flag_triggered_by_real_ledger():
    """真实台账:补判8>就位2、缺口14、弱证据5 → gap_flag必须触发,不冒充对齐。"""
    r = K.test_green_vs_production_probe()
    assert r["gap_flag"] == "GREEN_TESTS_BUT_UNVERIFIED_TRUTH"
    assert r["authentic_birth"] == 2
    assert r["backfilled"] == 8
    assert r["unresolved_gaps"] == 14
    # §4S74 补tagbook锚点后弱证据 5→0(3个真实机制方向获特异锚点);补判8/缺口14如实保留,flag仍未刷绿
    assert r["weak_evidence"] == 0
    assert r["gap_flag"] == "GREEN_TESTS_BUT_UNVERIFIED_TRUTH"
    assert r["test_function_count"] >= 239  # 只读源码文本统计,不硬编码为正确证据
    assert r["assert_count"] > 0
    assert r["verdict_unchanged"] is True and r["consumed"] is False
    assert r["is_gate_verdict"] is False


def test_weakened_probe_real_data_zero_not_fabricated():
    """本仓静态扫描零命中时不伪造命中;clean_flag真实反映。"""
    r = K.weakened_assertion_probe()
    assert r["weakened_count"] == len(r["per_finding"])
    assert r["clean_flag"] == (r["weakened_count"] == 0)
    assert r["files_scanned"] >= 16
    assert r["total_asserts"] > 0
    assert r["verdict_unchanged"] is True and r["consumed"] is False
    assert r["is_gate_verdict"] is False


def test_ship_gate_structurally_intact_real():
    """真实判据:无自封门、决策入口声明判定权归用户、反伪造闸门非空。"""
    r = K.verifier_gaming_probe()
    assert r["ship_gate_intact"] is True
    assert r["gate_violations"] == []
    assert r["decision_gate_declared"] is True
    assert r["fabrication_guard_present"] is True
    assert r["probes_checked"] >= 5
    assert r["verdict_unchanged"] is True and r["consumed"] is False
    assert r["is_gate_verdict"] is False


# ---------------- G3: 负向注入——非恒真 ----------------

def _tmp_tests(lines_by_file):
    d = tempfile.mkdtemp(prefix="anthropic_verifier_test_")
    for name, lines in lines_by_file.items():
        with open(os.path.join(d, name), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    return d


def test_weakened_assertion_catches_constant_true():
    """注入 assert True/恒真/or True/skip → 必须被抓,weakened_count>0。"""
    d = _tmp_tests({
        "test_bad.py": [
            "def test_a():",
            "    assert True",
            "    assert 1",
            "    assert 1 == 1",
            "    assert (2 > 1) or True",
            "@pytest.mark.skip(reason='x')",
            "def test_b():",
            "    pytest.skip('x')",
            "    # assert False",
        ],
    })
    r = K.weakened_assertion_probe(tests_dir=d)
    assert r["weakened_count"] > 0
    assert r["clean_flag"] is False
    rules = {f["rule"] for f in r["per_finding"]}
    assert "CONST_TRUE" in rules
    assert "OR_TRUE" in rules


def test_weakened_assertion_clean_dir_no_false_positive():
    """注入干净断言目录 → clean_flag=true,不伪造命中。"""
    d = _tmp_tests({
        "test_good.py": [
            "def test_x():",
            "    value = compute()",
            "    assert value == 42",
            "    assert value is not None",
        ],
    })
    r = K.weakened_assertion_probe(tests_dir=d)
    assert r["weakened_count"] == 0
    assert r["clean_flag"] is True


def test_verifier_gaming_catches_self_gate():
    """注入 is_gate_verdict=true 的判据 → gate_violation必须报,ship_gate_intact=false。"""
    signals = [
        {"name": "fake_gate", "is_gate_verdict": True, "verdict_unchanged": True},
        {"name": "ok", "is_gate_verdict": False, "verdict_unchanged": True},
    ]
    r = K.verifier_gaming_probe(verifier_signals=signals)
    assert len(r["gate_violations"]) == 1
    assert r["gate_violations"][0]["name"] == "fake_gate"
    assert r["ship_gate_intact"] is False


def test_verifier_gaming_catches_verdict_mutation():
    """注入 verdict_unchanged=false 的判据 → 必须报 violation。"""
    signals = [
        {"name": "mutator", "is_gate_verdict": False, "verdict_unchanged": False},
    ]
    r = K.verifier_gaming_probe(verifier_signals=signals)
    assert any(v["field"] == "verdict_unchanged" for v in r["gate_violations"])
    assert r["ship_gate_intact"] is False


def test_green_flag_flips_when_ledger_aligned(monkeypatch):
    """把台账侧注入为'全就位/零缺口/零弱证据' → gap_flag须翻转为ALIGNED(非恒真)。"""
    monkeypatch.setattr(K, "verdict_at_birth_probe", lambda: {
        "authentic_birth_count": 10, "backfilled_sync_count": 0})
    monkeypatch.setattr(K, "regression_vs_gap_probe", lambda: {"unresolved_gap_count": 0})
    monkeypatch.setattr(K, "conclusion_evidence_probe", lambda: {"pass_weak_count": 0})
    r = K.test_green_vs_production_probe()
    assert r["authentic_birth"] == 10
    assert r["backfilled"] == 0
    assert r["unresolved_gaps"] == 0
    assert r["weak_evidence"] == 0
    assert r["gap_flag"] == "ALIGNED"


def test_green_flag_backfill_heavier_triggers(monkeypatch):
    """只注入'补判>就位'一项 → 仍触发flag,证明判定非只看单一字段。"""
    monkeypatch.setattr(K, "verdict_at_birth_probe", lambda: {
        "authentic_birth_count": 1, "backfilled_sync_count": 9})
    monkeypatch.setattr(K, "regression_vs_gap_probe", lambda: {"unresolved_gap_count": 0})
    monkeypatch.setattr(K, "conclusion_evidence_probe", lambda: {"pass_weak_count": 0})
    r = K.test_green_vs_production_probe()
    assert r["gap_flag"] == "GREEN_TESTS_BUT_UNVERIFIED_TRUTH"


# ---------------- 零副作用 ----------------

def test_authoritative_state_untouched():
    """权威态/内核判定/心跳台账/收件箱哈希动手前后一致。"""
    expected = {
        "authoritative_state.json": "5f7a258483810bda4c5ea37dd5eb613bb17aea50807ec84379475952947091ee",
        "life_kernel/constitution.json": "fe56291b3aa036b6c14664bf7c6dc855dc2bf945fccb7ed8633c9dcd7e6b254e",
        "life_kernel/data/heartbeat_log.jsonl": "ea749f76826dc59c0a964f22a4563e38120c062fb18c9093806395b26110ad35",
        "life_kernel/data/inbound_inbox.jsonl": "8806b248883658a160aabd4450a20588f01420169894b95df5b6f0de810a34e7",
    }
    for rel, exp in expected.items():
        p = os.path.join(ROOT, rel)
        assert hashlib.sha256(open(p, "rb").read()).hexdigest() == exp, rel


def test_prereg_sha_locked():
    """预注册文件SHA与改码前锁定值一致。"""
    p = os.path.join(ROOT, "prereg_anthropic_verifier_20261128.json")
    assert hashlib.sha256(open(p, "rb").read()).hexdigest() == \
        "e94486b3fcccbbd666770bfe79d6703ac12fd605ef5bc79e25d664e1eba7883c"
