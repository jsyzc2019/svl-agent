"""成熟度证据诚实性门禁测试（§97，arXiv:2610.38266 L0-L3 rubric 编译产物 + FJ 取证入口）。

核心：回应"期待L3"——把 L3 门槛编译成尺子并首次对准本仓自审，
诚实结论=未达L3停在L2边缘偏上（shared_start_controlled=no → flag）。
"""
from pathlib import Path

import pytest

from svagent.maturity_evidence_honesty import (
    check_maturity_evidence_honesty, MaturityEvidenceVerdict, live_regression,
)
from svagent.forensic_gates_ext8 import (
    adjudicate_maturity_evidence_honesty, live_regression as forensic_regression,
)

DIMS = ["level_definition_traced", "process_product_split",
        "shared_start_controlled", "independent_tests"]


def _good(**over):
    base = {d: "yes" for d in DIMS}
    base.update(over)
    return base


# ---- gate 裁决（填表模式）----
def test_level_untraced_downgrade():
    v = check_maturity_evidence_honesty("x", **_good(level_definition_traced="no"))
    assert isinstance(v, MaturityEvidenceVerdict)
    assert v.action == "downgrade" and v.code == "MATURITY.LEVEL_UNTRACED"
    assert "等级" in v.message or "自封" in v.message


def test_process_product_conflation_downgrade():
    v = check_maturity_evidence_honesty("x", **_good(process_product_split="no"))
    assert v.action == "downgrade" and v.code == "MATURITY.PROCESS_PRODUCT_CONFLATION"
    assert "product" in v.message or "过程" in v.message


def test_shared_start_uncontrolled_flag():
    v = check_maturity_evidence_honesty("x", **_good(shared_start_controlled="no"))
    assert v.action == "flag" and v.code == "MATURITY.SHARED_START_UNCONTROLLED"
    assert "shared" in v.message or "预算" in v.message


def test_tests_not_independent_flag():
    v = check_maturity_evidence_honesty("x", **_good(independent_tests="no"))
    assert v.action == "flag" and v.code == "MATURITY.TESTS_NOT_INDEPENDENT"
    assert "独立" in v.message or "评估器" in v.message


@pytest.mark.parametrize("dim", DIMS)
def test_partial_any_dim_flag(dim):
    v = check_maturity_evidence_honesty("x", **_good(**{dim: "partial"}))
    assert v.action == "flag" and v.code == "MATURITY.PARTIAL"


@pytest.mark.parametrize("dim", DIMS)
def test_literal_enum_flag(dim):
    v = check_maturity_evidence_honesty("x", **_good(**{dim: "maybe"}))
    assert v.action == "flag" and v.code == "MATURITY.INVALID_INPUT"


def test_all_good_ok():
    v = check_maturity_evidence_honesty("x", **_good())
    assert v.action == "ok" and v.code == "MATURITY.SELF_CONSISTENT"
    assert "自洽" in v.message or "折 1" in v.message


def test_priority_level_over_process():
    # R1 优先于 R2
    v = check_maturity_evidence_honesty(
        "x", **_good(level_definition_traced="no", process_product_split="no"))
    assert v.code == "MATURITY.LEVEL_UNTRACED"


def test_priority_no_over_partial():
    # 具体 no 优先于 partial（短路顺序）
    v = check_maturity_evidence_honesty(
        "x", **_good(independent_tests="partial", shared_start_controlled="no"))
    assert v.code == "MATURITY.SHARED_START_UNCONTROLLED"


def test_verdict_fields_echo_inputs():
    kw = _good(shared_start_controlled="partial")
    v = check_maturity_evidence_honesty("claim-X", **kw)
    assert v.claim == "claim-X"
    assert v.shared_start_controlled == "partial"
    assert v.level_definition_traced == "yes"


# ---- 活体回归 ----
def test_gate_live_regression_all_passed():
    r = live_regression()
    assert r["all_passed"] is True
    assert len(r["cases"]) == 7


# ---- FJ 取证入口 ----
def test_forensic_real_evidence_ok():
    v, tr = adjudicate_maturity_evidence_honesty()
    assert v.action == "ok"
    assert tr["inferred"] == {d: "yes" for d in DIMS}
    assert tr["mode"] == "forensic"


def test_forensic_trace_has_chain():
    _, tr = adjudicate_maturity_evidence_honesty()
    assert "chain" in tr
    assert tr["chain"]["intact"] is True
    assert "source_verification" in tr


def test_forensic_tamper_partial_flag(tmp_path):
    bad = tmp_path / "tampered.txt"
    bad.write_text(
        "The evidence rubric distinguishes task-local adaptation (L0), persistent capability gain (L1), inherited process revision (L2), and verified improver gain (L3). "
        "The levels specify evidence requirements for individual claims. "
        "We first explain the functional distinction between learner updates and improver revisions. "
        "Persistent artifacts can modify the learner, the improver, or both. "
        "L3 requires greater subsequent gains from shared learner starts under matched resource budgets and independent tests.",
        encoding="utf-8",
    )
    v, tr = adjudicate_maturity_evidence_honesty(sources=[str(bad)])
    assert tr["inferred"]["independent_tests"] == "partial"
    assert v.action == "flag"


def test_forensic_redflag_downgrade(tmp_path):
    bad = tmp_path / "redflag.txt"
    bad.write_text(
        "a maturity level is asserted with no linked definition of what the level requires, "
        "levels are self-assigned labels with no traceable evidence criteria. "
        "We first explain the functional distinction between learner updates and improver revisions. "
        "L3 requires greater subsequent gains from shared learner starts under matched resource budgets and independent tests. "
        "We further propose common-data and interactive comparisons that evaluate reference and revised improvers from shared learner starts.",
        encoding="utf-8",
    )
    v, tr = adjudicate_maturity_evidence_honesty(sources=[str(bad)])
    assert tr["inferred"]["level_definition_traced"] == "no"
    assert v.action == "downgrade"


def test_forensic_chain_tamper_rejected(tmp_path, monkeypatch):
    import shutil
    from svagent.evidence_chain import ChainIntegrityError
    import svagent.forensic_gates_ext8 as fe
    audit = Path(__file__).resolve().parent.parent / "audit_l3_evidence_rubric"
    shutil.copytree(audit, tmp_path / "audit_l3_evidence_rubric")
    p = tmp_path / "audit_l3_evidence_rubric" / "prereg.json"
    p.write_text(p.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    monkeypatch.setattr(fe, "_ROOT", tmp_path)
    with pytest.raises(ChainIntegrityError):
        adjudicate_maturity_evidence_honesty()


def test_forensic_live_regression_all_passed():
    r = forensic_regression()
    assert r["all_passed"] is True
    assert r["checks"]["chain_tamper_rejected"] is True


# ---- 首次自审：诚实结论锁定 ----
def test_self_audit_conclusion_not_l3():
    """本仓首次自审必须诚实判未达 L3（预注册预承诺，不因用户期待抬级）。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "engine97", Path(__file__).resolve().parent.parent
        / "audit_l3_evidence_rubric" / "engine.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sa = mod.self_audit()
    assert sa["dimensions"]["shared_start_controlled"] == "no"
    assert sa["dimensions"]["independent_tests"] == "no"
    assert sa["verdict"]["action"] == "flag"
    assert "未达 L3" in sa["conclusion"]
    assert len(sa["path_to_l3"]) >= 3


# ---- AST 自审 ----
@pytest.mark.parametrize("path", [
    "svagent/maturity_evidence_honesty.py",
    "svagent/forensic_gates_ext8.py",
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
