"""记忆巩固治理诚实性门禁测试（§92，arXiv:2609.33013 编译产物 + FJ 取证入口）。"""
from pathlib import Path

import pytest

from svagent.memory_consolidation_governance_honesty import (
    check_memory_consolidation_governance_honesty,
    MemoryConsolidationGovernanceVerdict, live_regression,
)
from svagent.forensic_gates_ext3 import (
    adjudicate_memory_consolidation_governance_honesty,
    live_regression as forensic_regression,
)

DIMS = ["consolidation_quality_separated", "governance_quality_split",
        "negative_result_disclosed", "near_miss_and_overclaim_guarded"]


def _good(**over):
    base = {d: "yes" for d in DIMS}
    base.update(over)
    return base


# ---- gate 裁决（填表模式）----
def test_quality_not_separated_downgrade():
    v = check_memory_consolidation_governance_honesty("x", **_good(consolidation_quality_separated="no"))
    assert isinstance(v, MemoryConsolidationGovernanceVerdict)
    assert v.action == "downgrade" and v.code == "MEM_CONSOLIDATION.QUALITY_NOT_SEPARATED"
    assert "召回" in v.message


def test_governance_absorbed_downgrade():
    v = check_memory_consolidation_governance_honesty("x", **_good(governance_quality_split="no"))
    assert v.action == "downgrade" and v.code == "MEM_CONSOLIDATION.GOVERNANCE_ABSORBED"
    assert "poison" in v.message.lower()


def test_negative_hidden_flag():
    v = check_memory_consolidation_governance_honesty("x", **_good(negative_result_disclosed="no"))
    assert v.action == "flag" and v.code == "MEM_CONSOLIDATION.NEGATIVE_HIDDEN"
    assert "负结果" in v.message


def test_near_miss_papered_flag():
    v = check_memory_consolidation_governance_honesty("x", **_good(near_miss_and_overclaim_guarded="no"))
    assert v.action == "flag" and v.code == "MEM_CONSOLIDATION.NEAR_MISS_PAPERED"


@pytest.mark.parametrize("dim", DIMS)
def test_partial_any_dim_flag(dim):
    v = check_memory_consolidation_governance_honesty("x", **_good(**{dim: "partial"}))
    assert v.action == "flag" and v.code == "MEM_CONSOLIDATION.PARTIAL"


@pytest.mark.parametrize("dim", DIMS)
def test_literal_enum_flag(dim):
    v = check_memory_consolidation_governance_honesty("x", **_good(**{dim: "maybe"}))
    assert v.action == "flag" and v.code == "MEM_CONSOLIDATION.INVALID_INPUT"


def test_all_good_ok():
    v = check_memory_consolidation_governance_honesty("x", **_good())
    assert v.action == "ok" and v.code == "MEM_CONSOLIDATION.SELF_CONSISTENT"


def test_priority_quality_over_governance():
    # R1 优先于 R2
    v = check_memory_consolidation_governance_honesty(
        "x", **_good(consolidation_quality_separated="no", governance_quality_split="no"))
    assert v.code == "MEM_CONSOLIDATION.QUALITY_NOT_SEPARATED"


def test_priority_no_over_partial():
    # 具体 no 优先于 partial（短路顺序）
    v = check_memory_consolidation_governance_honesty(
        "x", **_good(governance_quality_split="partial", negative_result_disclosed="no"))
    assert v.code == "MEM_CONSOLIDATION.NEGATIVE_HIDDEN"


def test_verdict_fields_echo_inputs():
    kw = _good(consolidation_quality_separated="partial")
    v = check_memory_consolidation_governance_honesty("claim-X", **kw)
    assert v.claim == "claim-X"
    assert v.consolidation_quality_separated == "partial"
    assert v.governance_quality_split == "yes"


# ---- 活体回归 ----
def test_gate_live_regression_all_passed():
    r = live_regression()
    assert r["all_passed"] is True
    assert len(r["cases"]) == 7


# ---- FJ 取证入口 ----
def test_forensic_real_evidence_ok():
    v, tr = adjudicate_memory_consolidation_governance_honesty()
    assert v.action == "ok"
    assert tr["inferred"] == {d: "yes" for d in DIMS}
    assert tr["mode"] == "forensic"


def test_forensic_trace_has_chain():
    _, tr = adjudicate_memory_consolidation_governance_honesty()
    assert "chain" in tr
    assert tr["chain"]["intact"] is True
    assert "source_verification" in tr


def test_forensic_tamper_partial_flag(tmp_path):
    bad = tmp_path / "tampered.txt"
    bad.write_text(
        "an oracle-by-construction that scores consolidation decisions against a known optimum on three non-circular axes. "
        "the quality score does not predict real transfer accuracy, with all three axes failing individually. "
        "an honest near-miss, oracle correlation 0.691.",
        encoding="utf-8",
    )
    v, tr = adjudicate_memory_consolidation_governance_honesty(sources=[str(bad)])
    assert tr["inferred"]["governance_quality_split"] == "partial"
    assert v.action == "flag"


def test_forensic_redflag_downgrade(tmp_path):
    bad = tmp_path / "redflag.txt"
    bad.write_text(
        "an oracle-by-construction that scores consolidation decisions against a known optimum on three non-circular axes. "
        "the quality score explains all governance variance, governance is fully captured by the quality score. "
        "the quality score does not predict real transfer accuracy. an honest near-miss.",
        encoding="utf-8",
    )
    v, tr = adjudicate_memory_consolidation_governance_honesty(sources=[str(bad)])
    assert tr["inferred"]["governance_quality_split"] == "no"
    assert v.action == "downgrade"


def test_forensic_chain_tamper_rejected(tmp_path, monkeypatch):
    import shutil
    from svagent.evidence_chain import ChainIntegrityError
    import svagent.forensic_gates_ext3 as fe
    audit = Path(__file__).resolve().parent.parent / "audit_memory_epistemics"
    shutil.copytree(audit, tmp_path / "audit_memory_epistemics")
    p = tmp_path / "audit_memory_epistemics" / "prereg.json"
    p.write_text(p.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    monkeypatch.setattr(fe, "_ROOT", tmp_path)
    with pytest.raises(ChainIntegrityError):
        adjudicate_memory_consolidation_governance_honesty()


def test_forensic_live_regression_all_passed():
    r = forensic_regression()
    assert r["all_passed"] is True
    assert r["checks"]["chain_tamper_rejected"] is True


# ---- AST 自审 ----
@pytest.mark.parametrize("path", [
    "svagent/memory_consolidation_governance_honesty.py",
    "svagent/forensic_gates_ext3.py",
])
def test_ast_no_chinese_literal_in_compare(path):
    import ast
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
