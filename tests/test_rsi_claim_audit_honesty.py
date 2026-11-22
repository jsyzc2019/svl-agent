"""RSI 声称审计诚实性门禁测试（§91，arXiv:2610.27610 编译产物 + FJ 取证入口）。"""
from pathlib import Path

import pytest

from svagent.rsi_claim_audit_honesty import (
    check_rsi_claim_audit_honesty, RSIClaimAuditVerdict, live_regression,
)
from svagent.forensic_gates_ext2 import (
    adjudicate_rsi_claim_audit_honesty, live_regression as forensic_regression,
)

DIMS = ["product_process_split", "repeatability_audited",
        "improver_gain_isolated", "selection_unused_eval"]


def _good(**over):
    base = {d: "yes" for d in DIMS}
    base.update(over)
    return base


# ---- gate 裁决（填表模式）----
def test_product_process_conflation_downgrade():
    v = check_rsi_claim_audit_honesty("x", **_good(product_process_split="no"))
    assert isinstance(v, RSIClaimAuditVerdict)
    assert v.action == "downgrade" and v.code == "RSI_CLAIM_AUDIT.PRODUCT_PROCESS_CONFLATION"
    assert "product" in v.message and "process" in v.message


def test_repeatability_unaudited_downgrade():
    v = check_rsi_claim_audit_honesty("x", **_good(repeatability_audited="no"))
    assert v.action == "downgrade" and v.code == "RSI_CLAIM_AUDIT.REPEATABILITY_UNAUDITED"
    assert "rerun" in v.message


def test_improver_confound_downgrade():
    v = check_rsi_claim_audit_honesty("x", **_good(improver_gain_isolated="no"))
    assert v.action == "downgrade" and v.code == "RSI_CLAIM_AUDIT.IMPROVER_CONFOUND"
    assert "匹配预算" in v.message


def test_selection_gap_flag():
    v = check_rsi_claim_audit_honesty("x", **_good(selection_unused_eval="no"))
    assert v.action == "flag" and v.code == "RSI_CLAIM_AUDIT.SELECTION_UNUSED_GAP"


@pytest.mark.parametrize("dim", DIMS)
def test_partial_any_dim_flag(dim):
    v = check_rsi_claim_audit_honesty("x", **_good(**{dim: "partial"}))
    assert v.action == "flag" and v.code == "RSI_CLAIM_AUDIT.PARTIAL"


@pytest.mark.parametrize("dim", DIMS)
def test_literal_enum_flag(dim):
    v = check_rsi_claim_audit_honesty("x", **_good(**{dim: "maybe"}))
    assert v.action == "flag" and v.code == "RSI_CLAIM_AUDIT.INVALID_INPUT"


def test_all_good_ok():
    v = check_rsi_claim_audit_honesty("x", **_good())
    assert v.action == "ok" and v.code == "RSI_CLAIM_AUDIT.SELF_CONSISTENT"


def test_priority_product_process_over_repeatability():
    # R1 优先于 R2：两维同 no 时报 product/process
    v = check_rsi_claim_audit_honesty("x", **_good(product_process_split="no", repeatability_audited="no"))
    assert v.code == "RSI_CLAIM_AUDIT.PRODUCT_PROCESS_CONFLATION"


def test_priority_no_over_partial():
    # 具体 no 优先于 partial（短路顺序）
    v = check_rsi_claim_audit_honesty("x", **_good(improver_gain_isolated="partial", selection_unused_eval="no"))
    assert v.code == "RSI_CLAIM_AUDIT.SELECTION_UNUSED_GAP"


def test_verdict_fields_echo_inputs():
    kw = _good(product_process_split="partial")
    v = check_rsi_claim_audit_honesty("claim-X", **kw)
    assert v.claim == "claim-X"
    assert v.product_process_split == "partial"
    assert v.repeatability_audited == "yes"


# ---- 活体回归 ----
def test_gate_live_regression_all_passed():
    r = live_regression()
    assert r["all_passed"] is True
    assert len(r["cases"]) == 7


# ---- FJ 取证入口（法官自己读证据）----
def test_forensic_real_evidence_ok():
    v, tr = adjudicate_rsi_claim_audit_honesty()
    assert v.action == "ok"
    assert tr["inferred"] == {d: "yes" for d in DIMS}
    assert tr["mode"] == "forensic"


def test_forensic_trace_has_chain():
    _, tr = adjudicate_rsi_claim_audit_honesty()
    assert "chain" in tr
    assert tr["chain"]["intact"] is True
    assert "source_verification" in tr


def test_forensic_tamper_partial_flag(tmp_path):
    bad = tmp_path / "tampered.txt"
    bad.write_text(
        "separating product claims about the final system from process claims about the improvement process itself. "
        "only 4 compare earlier and later procedures from identical starting artifacts at a matched budget. "
        "60% report evaluation on tasks unused for selection.",
        encoding="utf-8",
    )
    v, tr = adjudicate_rsi_claim_audit_honesty(sources=[str(bad)])
    assert tr["inferred"]["repeatability_audited"] == "partial"
    assert v.action == "flag"


def test_forensic_redflag_downgrade(tmp_path):
    bad = tmp_path / "redflag.txt"
    bad.write_text(
        "separating product claims about the final system from process claims about the improvement process itself. "
        "a single improvement run demonstrates repeatable recursion, reruns are unnecessary once a gain is measured. "
        "only 4 compare earlier and later procedures from identical starting artifacts at a matched budget. "
        "60% report evaluation on tasks unused for selection.",
        encoding="utf-8",
    )
    v, tr = adjudicate_rsi_claim_audit_honesty(sources=[str(bad)])
    assert tr["inferred"]["repeatability_audited"] == "no"
    assert v.action == "downgrade"


def test_forensic_chain_tamper_rejected(tmp_path, monkeypatch):
    import shutil
    from svagent.evidence_chain import ChainIntegrityError
    import svagent.forensic_gates_ext2 as fe
    audit = Path(__file__).resolve().parent.parent / "audit_rsi_claim_audit"
    shutil.copytree(audit, tmp_path / "audit_rsi_claim_audit")
    p = tmp_path / "audit_rsi_claim_audit" / "prereg.json"
    p.write_text(p.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    monkeypatch.setattr(fe, "_ROOT", tmp_path)
    with pytest.raises(ChainIntegrityError):
        adjudicate_rsi_claim_audit_honesty()


def test_forensic_live_regression_all_passed():
    r = forensic_regression()
    assert r["all_passed"] is True
    assert r["checks"]["chain_tamper_rejected"] is True


# ---- AST 自审：Compare 内无中文字面量 ----
@pytest.mark.parametrize("path", [
    "svagent/rsi_claim_audit_honesty.py",
    "svagent/forensic_gates_ext2.py",
])
def test_ast_no_chinese_literal_in_compare(path):
    import ast
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    tree = ast.parse((root / path).read_text(encoding="utf-8"))
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for c in [node.left] + node.comparators:
                if isinstance(c, ast.Constant) and isinstance(c.value, str) and any(
                    "\u4e00" <= ch <= "\u9fff" for ch in c.value
                ):
                    bad.append((node.lineno, c.value))
    assert bad == []
