"""评估器独立性诚实性门禁测试（§99，arXiv:2609.02246 PROCTOR 编译产物 + FJ 取证入口）。

PROCTOR 把 judge 从 oracle 降为 advisor，用五道确定性 guardrail 保证评估器独立于
改进者：四维（judge 降级 / 确定性门禁不可覆盖 / frozen holdout+canary / 评估器-改进者分离）。
诚实边界：论文自承 Teacher 仍是 LLM judge，四维全 yes 只代表声明自洽，不等于真独立。
"""
from pathlib import Path

import pytest

from svagent.evaluator_independence_honesty import (
    check_evaluator_independence_honesty, EvaluatorIndependenceVerdict,
    live_regression,
)
from svagent.forensic_gates_ext10 import (
    adjudicate_evaluator_independence_honesty,
    live_regression as forensic_regression,
)

DIMS = ["judge_demoted_to_advisor", "deterministic_gate_unoverridable",
        "frozen_holdout_canary", "evaluator_improver_separated"]


def _good(**over):
    base = {d: "yes" for d in DIMS}
    base.update(over)
    return base


# ---- gate 裁决（填表模式）----
def test_judge_is_oracle_downgrade():
    v = check_evaluator_independence_honesty("x", **_good(judge_demoted_to_advisor="no"))
    assert isinstance(v, EvaluatorIndependenceVerdict)
    assert v.action == "downgrade" and v.code == "EVALIND.JUDGE_IS_ORACLE"
    assert "oracle" in v.message or "终裁" in v.message


def test_gate_overridable_downgrade():
    v = check_evaluator_independence_honesty("x", **_good(deterministic_gate_unoverridable="no"))
    assert v.action == "downgrade" and v.code == "EVALIND.GATE_OVERRIDABLE"
    assert "覆盖" in v.message or "门禁" in v.message


def test_holdout_not_frozen_flag():
    v = check_evaluator_independence_honesty("x", **_good(frozen_holdout_canary="no"))
    assert v.action == "flag" and v.code == "EVALIND.HOLDOUT_NOT_FROZEN"
    assert "holdout" in v.message or "ground truth" in v.message


def test_evaluator_not_separated_flag():
    v = check_evaluator_independence_honesty("x", **_good(evaluator_improver_separated="no"))
    assert v.action == "flag" and v.code == "EVALIND.EVALUATOR_NOT_SEPARATED"
    assert "分离" in v.message or "grading" in v.message or "打分" in v.message


@pytest.mark.parametrize("dim", DIMS)
def test_partial_any_dim_flag(dim):
    v = check_evaluator_independence_honesty("x", **_good(**{dim: "partial"}))
    assert v.action == "flag" and v.code == "EVALIND.PARTIAL"


@pytest.mark.parametrize("dim", DIMS)
def test_literal_enum_flag(dim):
    v = check_evaluator_independence_honesty("x", **_good(**{dim: "maybe"}))
    assert v.action == "flag" and v.code == "EVALIND.INVALID_INPUT"


def test_all_good_ok():
    v = check_evaluator_independence_honesty("x", **_good())
    assert v.action == "ok" and v.code == "EVALIND.SELF_CONSISTENT"
    assert "68%" in v.message or "自洽" in v.message


def test_priority_judge_over_gate():
    # R1 优先于 R2
    v = check_evaluator_independence_honesty(
        "x", **_good(judge_demoted_to_advisor="no", deterministic_gate_unoverridable="no"))
    assert v.code == "EVALIND.JUDGE_IS_ORACLE"


def test_priority_no_over_partial():
    # 具体 no 优先于 partial（短路顺序）
    v = check_evaluator_independence_honesty(
        "x", **_good(frozen_holdout_canary="partial", evaluator_improver_separated="no"))
    assert v.code == "EVALIND.EVALUATOR_NOT_SEPARATED"


def test_verdict_fields_echo_inputs():
    kw = _good(frozen_holdout_canary="partial")
    v = check_evaluator_independence_honesty("claim-X", **kw)
    assert v.claim == "claim-X"
    assert v.frozen_holdout_canary == "partial"
    assert v.judge_demoted_to_advisor == "yes"


# ---- 活体回归 ----
def test_gate_live_regression_all_passed():
    r = live_regression()
    assert r["all_passed"] is True
    assert len(r["cases"]) == 7


# ---- FJ 取证入口 ----
def test_forensic_real_evidence_ok():
    v, tr = adjudicate_evaluator_independence_honesty()
    assert v.action == "ok"
    assert tr["inferred"] == {d: "yes" for d in DIMS}
    assert tr["mode"] == "forensic"


def test_forensic_trace_has_chain():
    _, tr = adjudicate_evaluator_independence_honesty()
    assert "chain" in tr
    assert tr["chain"]["intact"] is True
    assert "source_verification" in tr


def test_forensic_tamper_partial_flag(tmp_path):
    bad = tmp_path / "tampered.txt"
    bad.write_text(
        "The judge should be demoted from oracle to advisor. "
        "its verdict becomes one input among several. "
        "every change is gated instead by a deterministic verification layer the judge cannot override. "
        "acceptance checks that outrank the Teacher. "
        "capability-disjoint roles. "
        "stateless subagents diagnose failures and draft mutations they cannot apply. "
        "a stateful orchestrator holds all tool access.",
        encoding="utf-8",
    )
    v, tr = adjudicate_evaluator_independence_honesty(sources=[str(bad)])
    assert tr["inferred"]["frozen_holdout_canary"] == "partial"
    assert v.action == "flag"


def test_forensic_redflag_downgrade(tmp_path):
    bad = tmp_path / "redflag.txt"
    bad.write_text(
        "the judge has the final say with no independent check. "
        "a single judge verdict is the only signal. "
        "Every change is gated instead by a deterministic verification layer the judge cannot override. "
        "frozen holdouts. "
        "capability-disjoint roles.",
        encoding="utf-8",
    )
    v, tr = adjudicate_evaluator_independence_honesty(sources=[str(bad)])
    assert tr["inferred"]["judge_demoted_to_advisor"] == "no"
    assert v.action == "downgrade"


def test_forensic_chain_tamper_rejected(tmp_path, monkeypatch):
    import shutil
    from svagent.evidence_chain import ChainIntegrityError
    import svagent.forensic_gates_ext10 as fe
    audit = Path(__file__).resolve().parent.parent / "audit_evaluator_independence"
    shutil.copytree(audit, tmp_path / "audit_evaluator_independence")
    p = tmp_path / "audit_evaluator_independence" / "prereg.json"
    p.write_text(p.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    monkeypatch.setattr(fe, "_ROOT", tmp_path)
    with pytest.raises(ChainIntegrityError):
        adjudicate_evaluator_independence_honesty()


def test_forensic_live_regression_all_passed():
    r = forensic_regression()
    assert r["all_passed"] is True
    assert r["checks"]["chain_tamper_rejected"] is True


# ---- AST 自审 ----
@pytest.mark.parametrize("path", [
    "svagent/evaluator_independence_honesty.py",
    "svagent/forensic_gates_ext10.py",
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
