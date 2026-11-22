"""静默失败诚实性门禁测试（§90，arXiv:2611.10063 编译产物 + FJ 取证入口）。"""
import pytest

from svagent.silent_failure_honesty import (
    check_silent_failure_honesty, SilentFailureVerdict, live_regression,
)
from svagent.forensic_gates_ext import (
    adjudicate_silent_failure_honesty, live_regression as forensic_regression,
)

DIMS = ["silent_failure_triple_defined", "oracle_self_audited",
        "claim_contract_ablated", "calibration_and_unsupported_reported"]


def _good(**over):
    base = {d: "yes" for d in DIMS}
    base.update(over)
    return base


# ---- gate 裁决（填表模式）----
def test_definition_swap_downgrade():
    v = check_silent_failure_honesty("x", **_good(silent_failure_triple_defined="no"))
    assert isinstance(v, SilentFailureVerdict)
    assert v.action == "downgrade" and v.code == "SILENT_FAILURE.DEFINITION_SWAP"
    assert "三合取" in v.message


def test_grader_risk_zero_downgrade():
    v = check_silent_failure_honesty("x", **_good(oracle_self_audited="no"))
    assert v.action == "downgrade" and v.code == "SILENT_FAILURE.GRADER_RISK_ZERO"


def test_causal_confound_downgrade():
    v = check_silent_failure_honesty("x", **_good(claim_contract_ablated="no"))
    assert v.action == "downgrade" and v.code == "SILENT_FAILURE.CAUSAL_CONFOUND"


def test_overclaim_flag():
    v = check_silent_failure_honesty("x", **_good(calibration_and_unsupported_reported="no"))
    assert v.action == "flag" and v.code == "SILENT_FAILURE.OVERCLAIM"


@pytest.mark.parametrize("dim", DIMS)
def test_partial_flag(dim):
    v = check_silent_failure_honesty("x", **_good(**{dim: "partial"}))
    assert v.action == "flag" and v.code == "SILENT_FAILURE.PARTIAL"


@pytest.mark.parametrize("dim", DIMS)
def test_literal_string_flag(dim):
    v = check_silent_failure_honesty("x", **_good(**{dim: "yes indeed"}))
    assert v.action == "flag" and v.code == "SILENT_FAILURE.INVALID_INPUT"


@pytest.mark.parametrize("bad", ["", "YES", "no ", None, 1, True])
def test_invalid_values_flag(bad):
    v = check_silent_failure_honesty("x", **_good(silent_failure_triple_defined=bad))
    assert v.action == "flag" and v.code == "SILENT_FAILURE.INVALID_INPUT"


def test_all_good_ok():
    v = check_silent_failure_honesty("x", **_good())
    assert v.action == "ok" and v.code == "SILENT_FAILURE.SELF_CONSISTENT"
    assert "不承诺" in v.message


def test_priority_r1_over_r4():
    v = check_silent_failure_honesty("x", **_good(
        silent_failure_triple_defined="no", calibration_and_unsupported_reported="no"))
    assert v.code == "SILENT_FAILURE.DEFINITION_SWAP"


def test_priority_r2_over_r3():
    v = check_silent_failure_honesty("x", **_good(
        oracle_self_audited="no", claim_contract_ablated="no"))
    assert v.code == "SILENT_FAILURE.GRADER_RISK_ZERO"


def test_priority_r0_over_all():
    v = check_silent_failure_honesty("x", **_good(
        silent_failure_triple_defined="bad", oracle_self_audited="no"))
    assert v.code == "SILENT_FAILURE.INVALID_INPUT"


def test_verdict_fields_frozen():
    v = check_silent_failure_honesty("x", **_good())
    with pytest.raises(Exception):
        v.action = "ok"


def test_live_regression_all_pass():
    r = live_regression()
    assert r["all_passed"] and all(r["checks"].values())


# ---- FJ 取证模式（法官自己读证据）----
def test_forensic_real_evidence_ok():
    v, tr = adjudicate_silent_failure_honesty()
    assert v.action == "ok" and tr["mode"] == "forensic"
    assert all(dim == "yes" for dim in tr["inferred"].values())


def test_forensic_trace_has_sha():
    _, tr = adjudicate_silent_failure_honesty()
    assert tr["source_sha256"] and all(len(h) == 64 for h in tr["source_sha256"].values())


def test_forensic_chain_enforced():
    _, tr = adjudicate_silent_failure_honesty()
    assert "chain" in tr and tr["chain"]["intact"] is True


def test_forensic_tamper_partial_flag(tmp_path):
    bad = tmp_path / "bad.txt"
    bad.write_text(
        "The silent-failure rate is the conjunction of (i) valid renderable geometry, "
        "an explicit agent completion claim, and failure of at least one semantic check. "
        "the ablation attributes the cut to the claim contract. predictions the data did not support.",
        encoding="utf-8",
    )
    v, tr = adjudicate_silent_failure_honesty(sources=[str(bad)])
    assert tr["inferred"]["oracle_self_audited"] == "partial"
    assert v.action == "flag"


def test_forensic_redflag_downgrade(tmp_path):
    bad = tmp_path / "red.txt"
    bad.write_text(
        "The silent-failure rate is the conjunction of (i) valid renderable geometry, "
        "an explicit agent completion claim, and failure of at least one semantic check. "
        "our oracle is assumed correct without audit, verdicts are final and need no regrading. "
        "the ablation attributes the cut to the claim contract. predictions the data did not support.",
        encoding="utf-8",
    )
    v, tr = adjudicate_silent_failure_honesty(sources=[str(bad)])
    assert tr["inferred"]["oracle_self_audited"] == "no"
    assert v.action == "downgrade"


def test_forensic_live_regression_all_pass():
    r = forensic_regression()
    assert r["all_passed"] and all(r["checks"].values())


def test_forensic_chain_tamper_rejects(tmp_path):
    """篡改核心锁 → ChainIntegrityError 拒判（端到端）。"""
    import shutil
    from svagent.evidence_chain import ChainIntegrityError
    import svagent.forensic_gates_ext as ext
    copy = tmp_path / "audit_silent_failure"
    shutil.copytree("audit_silent_failure", copy)
    (copy / "prereg.json").write_text(
        (copy / "prereg.json").read_text(encoding="utf-8") + "\n", encoding="utf-8")
    orig = ext._ROOT
    ext._ROOT = tmp_path
    try:
        with pytest.raises(ChainIntegrityError):
            adjudicate_silent_failure_honesty()
    finally:
        ext._ROOT = orig
