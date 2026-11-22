"""改进者增益受控验证诚实性门禁测试（§98，arXiv:2610.16491 编译产物 + FJ 取证入口）。

SpecRSI 把"shared learner starts + matched budgets + fixed evaluator"编译成
四维受控对照边界（匹配预算 / 相同起点 / 固定独立评估器 / 增益隔离）。
"""
from pathlib import Path

import pytest

from svagent.improver_gain_controlled_honesty import (
    check_improver_gain_controlled_honesty, ImproverGainControlledVerdict,
    live_regression,
)
from svagent.forensic_gates_ext9 import (
    adjudicate_improver_gain_controlled_honesty,
    live_regression as forensic_regression,
)

DIMS = ["matched_budget_controlled", "shared_start_artifacts",
        "evaluator_fixed_independent", "improver_gain_isolated"]


def _good(**over):
    base = {d: "yes" for d in DIMS}
    base.update(over)
    return base


# ---- gate 裁决（填表模式）----
def test_budget_uncontrolled_downgrade():
    v = check_improver_gain_controlled_honesty("x", **_good(matched_budget_controlled="no"))
    assert isinstance(v, ImproverGainControlledVerdict)
    assert v.action == "downgrade" and v.code == "IGC.MATCHED_BUDGET_UNCONTROLLED"
    assert "预算" in v.message


def test_shared_start_uncontrolled_downgrade():
    v = check_improver_gain_controlled_honesty("x", **_good(shared_start_artifacts="no"))
    assert v.action == "downgrade" and v.code == "IGC.SHARED_START_UNCONTROLLED"
    assert "初始" in v.message or "起点" in v.message


def test_evaluator_not_independent_flag():
    v = check_improver_gain_controlled_honesty("x", **_good(evaluator_fixed_independent="no"))
    assert v.action == "flag" and v.code == "IGC.EVALUATOR_NOT_INDEPENDENT"
    assert "evaluator" in v.message or "评估器" in v.message


def test_gain_conflated_flag():
    v = check_improver_gain_controlled_honesty("x", **_good(improver_gain_isolated="no"))
    assert v.action == "flag" and v.code == "IGC.IMPROVER_GAIN_CONFLATED"
    assert "增益" in v.message or "product" in v.message


@pytest.mark.parametrize("dim", DIMS)
def test_partial_any_dim_flag(dim):
    v = check_improver_gain_controlled_honesty("x", **_good(**{dim: "partial"}))
    assert v.action == "flag" and v.code == "IGC.PARTIAL"


@pytest.mark.parametrize("dim", DIMS)
def test_literal_enum_flag(dim):
    v = check_improver_gain_controlled_honesty("x", **_good(**{dim: "maybe"}))
    assert v.action == "flag" and v.code == "IGC.INVALID_INPUT"


def test_all_good_ok():
    v = check_improver_gain_controlled_honesty("x", **_good())
    assert v.action == "ok" and v.code == "IGC.SELF_CONSISTENT"
    assert "折 1" in v.message or "自洽" in v.message


def test_priority_budget_over_shared_start():
    # R1 优先于 R2
    v = check_improver_gain_controlled_honesty(
        "x", **_good(matched_budget_controlled="no", shared_start_artifacts="no"))
    assert v.code == "IGC.MATCHED_BUDGET_UNCONTROLLED"


def test_priority_no_over_partial():
    # 具体 no 优先于 partial（短路顺序）
    v = check_improver_gain_controlled_honesty(
        "x", **_good(evaluator_fixed_independent="partial", improver_gain_isolated="no"))
    assert v.code == "IGC.IMPROVER_GAIN_CONFLATED"


def test_verdict_fields_echo_inputs():
    kw = _good(evaluator_fixed_independent="partial")
    v = check_improver_gain_controlled_honesty("claim-X", **kw)
    assert v.claim == "claim-X"
    assert v.evaluator_fixed_independent == "partial"
    assert v.matched_budget_controlled == "yes"


# ---- 活体回归 ----
def test_gate_live_regression_all_passed():
    r = live_regression()
    assert r["all_passed"] is True
    assert len(r["cases"]) == 7


# ---- FJ 取证入口 ----
def test_forensic_real_evidence_ok():
    v, tr = adjudicate_improver_gain_controlled_honesty()
    assert v.action == "ok"
    assert tr["inferred"] == {d: "yes" for d in DIMS}
    assert tr["mode"] == "forensic"


def test_forensic_trace_has_chain():
    _, tr = adjudicate_improver_gain_controlled_honesty()
    assert "chain" in tr
    assert tr["chain"]["intact"] is True
    assert "source_verification" in tr


def test_forensic_tamper_partial_flag(tmp_path):
    bad = tmp_path / "tampered.txt"
    bad.write_text(
        "Under matched evaluation-call budgets, SpecRSI improves scientific terminal gain. "
        "compares frozen and GVO-updated improvers from identical starting agents. "
        "GVO assigns credit across independent complete searches from the same start. "
        "keeping the real evaluator fixed. "
        "constitute the real evaluator. "
        "held-out gain is evaluated separately.",
        encoding="utf-8",
    )
    v, tr = adjudicate_improver_gain_controlled_honesty(sources=[str(bad)])
    assert tr["inferred"]["improver_gain_isolated"] == "partial"
    assert v.action == "flag"


def test_forensic_redflag_downgrade(tmp_path):
    bad = tmp_path / "redflag.txt"
    bad.write_text(
        "improvement is claimed from a larger evaluation budget without a matched-budget control; "
        "gains are reported with more evaluation calls than the baseline. "
        "compares frozen and GVO-updated improvers from identical starting agents. "
        "keeping the real evaluator fixed. "
        "tracks cumulative gains over successive rounds.",
        encoding="utf-8",
    )
    v, tr = adjudicate_improver_gain_controlled_honesty(sources=[str(bad)])
    assert tr["inferred"]["matched_budget_controlled"] == "no"
    assert v.action == "downgrade"


def test_forensic_chain_tamper_rejected(tmp_path, monkeypatch):
    import shutil
    from svagent.evidence_chain import ChainIntegrityError
    import svagent.forensic_gates_ext9 as fe
    audit = Path(__file__).resolve().parent.parent / "audit_shared_start_controlled"
    shutil.copytree(audit, tmp_path / "audit_shared_start_controlled")
    p = tmp_path / "audit_shared_start_controlled" / "prereg.json"
    p.write_text(p.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    monkeypatch.setattr(fe, "_ROOT", tmp_path)
    with pytest.raises(ChainIntegrityError):
        adjudicate_improver_gain_controlled_honesty()


def test_forensic_live_regression_all_passed():
    r = forensic_regression()
    assert r["all_passed"] is True
    assert r["checks"]["chain_tamper_rejected"] is True


# ---- AST 自审 ----
@pytest.mark.parametrize("path", [
    "svagent/improver_gain_controlled_honesty.py",
    "svagent/forensic_gates_ext9.py",
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
