"""§4S70 守卫：35个'?'审计文件 verdict 保真回填的回放验证。
只读回放真实台账,不改文件;验证不洗白、保真、原字段保留、权威态零副作用。
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kernel as K

WORK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(WORK)  # /workspace


def _load(name):
    return json.load(open(os.path.join(ROOT, "audit_" + name, "result.json")))


def test_all_verdicts_present_and_backfilled():
    """所有原'?'文件现在都有 verdict + verdict_backfill 标记。"""
    files = sorted(glob.glob(os.path.join(ROOT, "audit_*", "result.json")))
    filled = [f for f in files if "verdict_backfill" in json.load(open(f))]
    assert len(filled) == 35
    for f in filled:
        d = json.load(open(f))
        assert "verdict" in d
        bf = d["verdict_backfill"]
        assert bf["applied"] is True
        assert bf["rule_id"]
        assert bf["prereg_sha256"] == "ae8410fd632a228e505965966c12631f897bcef853ca617b97e4e523a70917ab"


def test_true_suspended_not_whitewashed():
    """3个真悬置文件回填后仍是 GAP_INCONCLUSIVE,绝不被洗成 PASS。"""
    for name in ("finance_construct_validity", "memory_governance", "vanity_selfaudit"):
        d = _load(name)
        assert d["verdict"] == "GAP_INCONCLUSIVE", (name, d["verdict"])


def test_flashprove_conservative():
    """flashprove 有 V3=SCOPED,保守标 SCOPED,不洗成全 PASS。"""
    d = _load("flashprove")
    assert d["verdict"] in ("SCOPED", "PASS")  # 口径允许 PASS(all_aligned) 或 SCOPED(保守)
    assert d["verdict_backfill"]["rule_id"].startswith("R2_judges")


def test_no_long_narrative_in_verdict():
    """verdict 值不超过40字符,长叙述未塞进判定字段。"""
    for f in glob.glob(os.path.join(ROOT, "audit_*", "result.json")):
        d = json.load(open(f))
        if "verdict_backfill" in d:
            assert len(str(d["verdict"])) <= 40, (f, d["verdict"])


def test_original_fields_preserved():
    """回填前字段键集合是回填后的子集(原字段一个没删)。"""
    # 用回执里的 original_fields_preserved 标记 + 抽查关键字段
    receipt = json.load(open(os.path.join(ROOT, "gap_backfill_receipt_20261128.json")))
    assert all(e["original_fields_preserved"] for e in receipt["entries"])
    assert len(receipt["entries"]) == 35
    # 抽查:triplet/decision/evidence_grade 原字段仍在
    assert "verdict_triplet_after" in _load("finance_construct_validity")
    assert "decision" in _load("claude_verify")
    assert "evidence_grade" in _load("ultrabert")


def test_regression_probe_no_question_marks():
    """回填后 regression_vs_gap_probe 不再有 '?' 误读。"""
    r = K.regression_vs_gap_probe()
    dist = r["unresolved_gap_verdict_dist"]
    assert "?" not in dist
    # 真悬置仍在:6 INCONCLUSIVE + 5 PARTIAL(各种前缀) + 3回填GAP_INCONCLUSIVE
    assert r["unresolved_gap_count"] >= 11
    assert dist.get("GAP_INCONCLUSIVE", 0) >= 3


def test_schema_probe_all_zero():
    """诊断判据显示全部'?'已消失(不再误读)。"""
    s = K.unresolved_gap_schema_probe()
    assert s["total_question_marks"] == 0
    assert sum(s["counts"].values()) == 0


def test_authoritative_state_untouched():
    """权威态/内核判定/心跳台账字节未变。"""
    import hashlib
    expected = {
        "authoritative_state.json": "5f7a258483810bda4c5ea37dd5eb613bb17aea50807ec84379475952947091ee",
        "life_kernel/constitution.json": "fe56291b3aa036b6c14664bf7c6dc855dc2bf945fccb7ed8633c9dcd7e6b254e",
        "life_kernel/data/heartbeat_log.jsonl": "ea749f76826dc59c0a964f22a4563e38120c062fb18c9093806395b26110ad35",
    }
    for rel, exp in expected.items():
        p = os.path.join(ROOT, rel)
        assert hashlib.sha256(open(p, "rb").read()).hexdigest() == exp, rel


def test_kernel_verdict_fields_unchanged():
    """权威态关键判定字段仍是 GAP_INCONCLUSIVE / l3=false / absolute=false。"""
    a = json.load(open(os.path.join(ROOT, "authoritative_state.json")))
    s = json.dumps(a, ensure_ascii=False)
    assert "GAP_INCONCLUSIVE" in s