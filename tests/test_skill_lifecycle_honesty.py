"""技能演化生命周期诚实性门禁测试（§96，arXiv:2610.09832 编译产物 + FJ 取证入口）。

SkillForge 把"虚高指标拆穿 + self-reported 折 1"迁移到技能演化领域：
四维演化治理边界（生命周期四态 / 信用分配审计 / teacher 对照 / 退役归因）。
"""
from pathlib import Path

import pytest

from svagent.skill_lifecycle_honesty import (
    check_skill_lifecycle_honesty, SkillLifecycleVerdict, live_regression,
)
from svagent.forensic_gates_ext7 import (
    adjudicate_skill_lifecycle_honesty, live_regression as forensic_regression,
)

DIMS = ["lifecycle_stages_disclosed", "credit_assignment_audited",
        "mutation_teacher_controlled", "retirement_failure_attributed"]


def _good(**over):
    base = {d: "yes" for d in DIMS}
    base.update(over)
    return base


# ---- gate 裁决（填表模式）----
def test_stages_undisclosed_downgrade():
    v = check_skill_lifecycle_honesty("x", **_good(lifecycle_stages_disclosed="no"))
    assert isinstance(v, SkillLifecycleVerdict)
    assert v.action == "downgrade" and v.code == "SKILL_LIFE.STAGES_UNDISCLOSED"
    assert "四态" in v.message or "pre-retire" in v.message


def test_credit_unaudited_downgrade():
    v = check_skill_lifecycle_honesty("x", **_good(credit_assignment_audited="no"))
    assert v.action == "downgrade" and v.code == "SKILL_LIFE.CREDIT_UNAUDITED"
    assert "credit" in v.message or "归因" in v.message


def test_teacher_uncontrolled_flag():
    v = check_skill_lifecycle_honesty("x", **_good(mutation_teacher_controlled="no"))
    assert v.action == "flag" and v.code == "SKILL_LIFE.TEACHER_UNCONTROLLED"
    assert "teacher" in v.message


def test_retirement_unattributed_flag():
    v = check_skill_lifecycle_honesty("x", **_good(retirement_failure_attributed="no"))
    assert v.action == "flag" and v.code == "SKILL_LIFE.RETIREMENT_UNATTRIBUTED"
    assert "退役" in v.message


@pytest.mark.parametrize("dim", DIMS)
def test_partial_any_dim_flag(dim):
    v = check_skill_lifecycle_honesty("x", **_good(**{dim: "partial"}))
    assert v.action == "flag" and v.code == "SKILL_LIFE.PARTIAL"


@pytest.mark.parametrize("dim", DIMS)
def test_literal_enum_flag(dim):
    v = check_skill_lifecycle_honesty("x", **_good(**{dim: "maybe"}))
    assert v.action == "flag" and v.code == "SKILL_LIFE.INVALID_INPUT"


def test_all_good_ok():
    v = check_skill_lifecycle_honesty("x", **_good())
    assert v.action == "ok" and v.code == "SKILL_LIFE.SELF_CONSISTENT"
    assert "7.8%" in v.message or "自洽" in v.message


def test_priority_stages_over_credit():
    # R1 优先于 R2
    v = check_skill_lifecycle_honesty(
        "x", **_good(lifecycle_stages_disclosed="no", credit_assignment_audited="no"))
    assert v.code == "SKILL_LIFE.STAGES_UNDISCLOSED"


def test_priority_no_over_partial():
    # 具体 no 优先于 partial（短路顺序）
    v = check_skill_lifecycle_honesty(
        "x", **_good(mutation_teacher_controlled="partial", retirement_failure_attributed="no"))
    assert v.code == "SKILL_LIFE.RETIREMENT_UNATTRIBUTED"


def test_verdict_fields_echo_inputs():
    kw = _good(credit_assignment_audited="partial")
    v = check_skill_lifecycle_honesty("claim-X", **kw)
    assert v.claim == "claim-X"
    assert v.credit_assignment_audited == "partial"
    assert v.lifecycle_stages_disclosed == "yes"


# ---- 活体回归 ----
def test_gate_live_regression_all_passed():
    r = live_regression()
    assert r["all_passed"] is True
    assert len(r["cases"]) == 7


# ---- FJ 取证入口 ----
def test_forensic_real_evidence_ok():
    v, tr = adjudicate_skill_lifecycle_honesty()
    assert v.action == "ok"
    assert tr["inferred"] == {d: "yes" for d in DIMS}
    assert tr["mode"] == "forensic"


def test_forensic_trace_has_chain():
    _, tr = adjudicate_skill_lifecycle_honesty()
    assert "chain" in tr
    assert tr["chain"]["intact"] is True
    assert "source_verification" in tr


def test_forensic_tamper_partial_flag(tmp_path):
    bad = tmp_path / "tampered.txt"
    bad.write_text(
        "fitness-driven skill lifecycle of trial , active , stable , and retired states, "
        "pre-retire low-fitness skills. "
        "Eq. ( 7 ) attributes one binary reward to all K K co-retrieved skills. We test this approximation in two ways. "
        "replaces Eq. ( 7 ) with each skill ’s leave-one-out marginal contribution over its co-retrieval sets. "
        "grant SkillRL the same B B rewrites appended to its library with no lifecycle gate. "
        "Table 12 : Teacher capability for LLM-guided mutation.",
        encoding="utf-8",
    )
    v, tr = adjudicate_skill_lifecycle_honesty(sources=[str(bad)])
    assert tr["inferred"]["retirement_failure_attributed"] == "partial"
    assert v.action == "flag"


def test_forensic_redflag_downgrade(tmp_path):
    bad = tmp_path / "redflag.txt"
    bad.write_text(
        "every skill is retained indiscriminately forever with no fitness lifecycle, "
        "obsolete and harmful entries are never retired and keep misleading the agent. "
        "Eq. ( 7 ) attributes one binary reward to all K K co-retrieved skills. We test this approximation in two ways. "
        "grant SkillRL the same B B rewrites appended to its library with no lifecycle gate. "
        "retirement events with human-annotated failure categories.",
        encoding="utf-8",
    )
    v, tr = adjudicate_skill_lifecycle_honesty(sources=[str(bad)])
    assert tr["inferred"]["lifecycle_stages_disclosed"] == "no"
    assert v.action == "downgrade"


def test_forensic_chain_tamper_rejected(tmp_path, monkeypatch):
    import shutil
    from svagent.evidence_chain import ChainIntegrityError
    import svagent.forensic_gates_ext7 as fe
    audit = Path(__file__).resolve().parent.parent / "audit_skill_lifecycle_honesty"
    shutil.copytree(audit, tmp_path / "audit_skill_lifecycle_honesty")
    p = tmp_path / "audit_skill_lifecycle_honesty" / "prereg.json"
    p.write_text(p.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    monkeypatch.setattr(fe, "_ROOT", tmp_path)
    with pytest.raises(ChainIntegrityError):
        adjudicate_skill_lifecycle_honesty()


def test_forensic_live_regression_all_passed():
    r = forensic_regression()
    assert r["all_passed"] is True
    assert r["checks"]["chain_tamper_rejected"] is True


# ---- AST 自审 ----
@pytest.mark.parametrize("path", [
    "svagent/skill_lifecycle_honesty.py",
    "svagent/forensic_gates_ext7.py",
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
