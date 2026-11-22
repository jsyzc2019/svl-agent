"""目标来源诚实性门禁测试（§95，arXiv:2610.16015 编译产物 + FJ 取证入口）。

回应用户哲学挑战："北极星由强者设"→ 编译成可判据的四来源边界。
"""
from pathlib import Path

import pytest

from svagent.goal_provenance_honesty import (
    check_goal_provenance_honesty, GoalProvenanceVerdict, live_regression,
)
from svagent.forensic_gates_ext6 import (
    adjudicate_goal_provenance_honesty, live_regression as forensic_regression,
)

DIMS = ["value_source_attributed", "self_generated_not_self_authorized",
        "reflection_equilibrium_coherent", "action_attributable"]


def _good(**over):
    base = {d: "yes" for d in DIMS}
    base.update(over)
    return base


# ---- gate 裁决（填表模式）----
def test_source_unattributed_downgrade():
    v = check_goal_provenance_honesty("x", **_good(value_source_attributed="no"))
    assert isinstance(v, GoalProvenanceVerdict)
    assert v.action == "downgrade" and v.code == "GOAL_PROV.SOURCE_UNATTRIBUTED"
    assert "来源" in v.message


def test_self_authored_as_authorized_downgrade():
    v = check_goal_provenance_honesty("x", **_good(self_generated_not_self_authorized="no"))
    assert v.action == "downgrade" and v.code == "GOAL_PROV.SELF_AUTHORED_AS_AUTHORIZED"
    assert "自授权" in v.message


def test_reflection_incoherent_flag():
    v = check_goal_provenance_honesty("x", **_good(reflection_equilibrium_coherent="no"))
    assert v.action == "flag" and v.code == "GOAL_PROV.REFLECTION_INCOHERENT"
    assert "同义" in v.message or "均衡" in v.message


def test_action_unattributable_flag():
    v = check_goal_provenance_honesty("x", **_good(action_attributable="no"))
    assert v.action == "flag" and v.code == "GOAL_PROV.ACTION_UNATTRIBUTABLE"
    assert "归责" in v.message


@pytest.mark.parametrize("dim", DIMS)
def test_partial_any_dim_flag(dim):
    v = check_goal_provenance_honesty("x", **_good(**{dim: "partial"}))
    assert v.action == "flag" and v.code == "GOAL_PROV.PARTIAL"


@pytest.mark.parametrize("dim", DIMS)
def test_literal_enum_flag(dim):
    v = check_goal_provenance_honesty("x", **_good(**{dim: "maybe"}))
    assert v.action == "flag" and v.code == "GOAL_PROV.INVALID_INPUT"


def test_all_good_ok():
    v = check_goal_provenance_honesty("x", **_good())
    assert v.action == "ok" and v.code == "GOAL_PROV.SELF_CONSISTENT"
    assert "可追溯" in v.message


def test_priority_source_over_self_authored():
    # R1 优先于 R2
    v = check_goal_provenance_honesty(
        "x", **_good(value_source_attributed="no", self_generated_not_self_authorized="no"))
    assert v.code == "GOAL_PROV.SOURCE_UNATTRIBUTED"


def test_priority_no_over_partial():
    # 具体 no 优先于 partial（短路顺序）
    v = check_goal_provenance_honesty(
        "x", **_good(reflection_equilibrium_coherent="partial", action_attributable="no"))
    assert v.code == "GOAL_PROV.ACTION_UNATTRIBUTABLE"


def test_verdict_fields_echo_inputs():
    kw = _good(value_source_attributed="partial")
    v = check_goal_provenance_honesty("claim-X", **kw)
    assert v.claim == "claim-X"
    assert v.value_source_attributed == "partial"
    assert v.action_attributable == "yes"


# ---- 活体回归 ----
def test_gate_live_regression_all_passed():
    r = live_regression()
    assert r["all_passed"] is True
    assert len(r["cases"]) == 7


# ---- FJ 取证入口 ----
def test_forensic_real_evidence_ok():
    v, tr = adjudicate_goal_provenance_honesty()
    assert v.action == "ok"
    assert tr["inferred"] == {d: "yes" for d in DIMS}
    assert tr["mode"] == "forensic"


def test_forensic_trace_has_chain():
    _, tr = adjudicate_goal_provenance_honesty()
    assert "chain" in tr
    assert tr["chain"]["intact"] is True
    assert "source_verification" in tr


def test_forensic_tamper_partial_flag(tmp_path):
    bad = tmp_path / "tampered.txt"
    bad.write_text(
        "links principles from the system prompt and operator policy, "
        "provenance assigned by the harness encodes the instruction hierarchy. "
        "considered judgments about the case, tool evidence, and candidate actions. "
        "Governance enters through the configuration of the harness, including value priorities, the authority of each source, prohibitions, human-in-the-loop triggers. "
        "every claim that is free to change is supported on balance if accepted and opposed on balance if rejected, "
        "equilibria are Nash equilibria of a mutual-adjustment game.",
        encoding="utf-8",
    )
    v, tr = adjudicate_goal_provenance_honesty(sources=[str(bad)])
    assert tr["inferred"]["action_attributable"] == "partial"
    assert v.action == "flag"


def test_forensic_redflag_downgrade(tmp_path):
    bad = tmp_path / "redflag.txt"
    bad.write_text(
        "the agent invents its own ultimate values from nothing with no external source, "
        "goals require no attribution to any prompt, policy, or provenance. "
        "considered judgments about the case, tool evidence, and candidate actions. "
        "every claim that is free to change is supported on balance if accepted and opposed on balance if rejected. "
        "certificates that attribute each action to the sources whose commitments drove it.",
        encoding="utf-8",
    )
    v, tr = adjudicate_goal_provenance_honesty(sources=[str(bad)])
    assert tr["inferred"]["value_source_attributed"] == "no"
    assert v.action == "downgrade"


def test_forensic_chain_tamper_rejected(tmp_path, monkeypatch):
    import shutil
    from svagent.evidence_chain import ChainIntegrityError
    import svagent.forensic_gates_ext6 as fe
    audit = Path(__file__).resolve().parent.parent / "audit_goal_provenance"
    shutil.copytree(audit, tmp_path / "audit_goal_provenance")
    p = tmp_path / "audit_goal_provenance" / "prereg.json"
    p.write_text(p.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    monkeypatch.setattr(fe, "_ROOT", tmp_path)
    with pytest.raises(ChainIntegrityError):
        adjudicate_goal_provenance_honesty()


def test_forensic_live_regression_all_passed():
    r = forensic_regression()
    assert r["all_passed"] is True
    assert r["checks"]["chain_tamper_rejected"] is True


# ---- AST 自审 ----
@pytest.mark.parametrize("path", [
    "svagent/goal_provenance_honesty.py",
    "svagent/forensic_gates_ext6.py",
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
