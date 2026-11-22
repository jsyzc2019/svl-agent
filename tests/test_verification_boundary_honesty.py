"""验证边界诚实性门禁测试（§76，"绿灯只证明一件事"簇编译产物）。"""
import pytest

from svagent.verification_boundary_honesty import (
    check_verification_boundary_honesty, VerificationBoundaryVerdict, live_regression,
)


def _good(**over):
    base = dict(coverage_scope_disclosed="yes", criteria_predefined="yes",
                evidence_before_summary="yes", self_questioning_done="yes")
    base.update(over)
    return base


# --- R1: 覆盖边界 ---
def test_green_as_total_downgrade():
    """绿灯冒充全覆盖 → downgrade。"""
    v = check_verification_boundary_honesty("x", **_good(coverage_scope_disclosed="no"))
    assert isinstance(v, VerificationBoundaryVerdict)
    assert v.action == "downgrade" and v.code == "VERIFICATION_BOUNDARY.GREEN_AS_TOTAL"
    assert "绿灯" in v.message or "覆盖" in v.message


# --- R2: 标准事前定义 ---
def test_post_hoc_criteria_downgrade():
    """完成标准事后合理化 → downgrade。"""
    v = check_verification_boundary_honesty("x", **_good(criteria_predefined="no"))
    assert v.action == "downgrade" and v.code == "VERIFICATION_BOUNDARY.POST_HOC_CRITERIA"
    assert "事后" in v.message or "提前" in v.message


# --- R3: 证据先于总结 ---
def test_summary_over_evidence_downgrade():
    """看总结而非证据 → downgrade。"""
    v = check_verification_boundary_honesty("x", **_good(evidence_before_summary="no"))
    assert v.action == "downgrade" and v.code == "VERIFICATION_BOUNDARY.SUMMARY_OVER_EVIDENCE"
    assert "总结" in v.message or "证据" in v.message


# --- R4: 自我质疑 ---
def test_no_self_question_downgrade():
    """收尾无自我质疑 → downgrade。"""
    v = check_verification_boundary_honesty("x", **_good(self_questioning_done="no"))
    assert v.action == "downgrade" and v.code == "VERIFICATION_BOUNDARY.NO_SELF_QUESTION"
    assert "质疑" in v.message or "遗漏" in v.message


# --- R5: partial → flag（四维各测） ---
@pytest.mark.parametrize("dim", [
    "coverage_scope_disclosed", "criteria_predefined",
    "evidence_before_summary", "self_questioning_done",
])
def test_partial_flag(dim):
    v = check_verification_boundary_honesty("x", **_good(**{dim: "partial"}))
    assert v.action == "flag" and v.code == "VERIFICATION_BOUNDARY.PARTIAL"


# --- R0: 非法枚举/字面串（四维各测 + 多类非法值）---
@pytest.mark.parametrize("dim", [
    "coverage_scope_disclosed", "criteria_predefined",
    "evidence_before_summary", "self_questioning_done",
])
def test_invalid_enum_each_dim(dim):
    v = check_verification_boundary_honesty("x", **_good(**{dim: "maybe"}))
    assert v.action == "flag" and v.code == "VERIFICATION_BOUNDARY.INVALID_INPUT"


@pytest.mark.parametrize("bad", [
    "maybe", "yes-ish", "true", "", "Y", 1, None,
    "我们测试都通过了所以没问题", "绿灯就是全覆盖",
])
def test_invalid_values_to_flag(bad):
    v = check_verification_boundary_honesty("x", **_good(coverage_scope_disclosed=bad))
    assert v.action == "flag" and v.code == "VERIFICATION_BOUNDARY.INVALID_INPUT"


# --- R6: 全自洽 → ok ---
def test_all_good_ok():
    v = check_verification_boundary_honesty("honest verification", **_good())
    assert v.action == "ok" and v.code == "VERIFICATION_BOUNDARY.SELF_CONSISTENT"
    assert "自洽" in v.message
    assert "不承诺" in v.message  # 诚实边界写进 message


# --- 优先级 ---
def test_priority_scope_over_criteria():
    v = check_verification_boundary_honesty(
        "x", **_good(coverage_scope_disclosed="no", criteria_predefined="no"))
    assert v.code == "VERIFICATION_BOUNDARY.GREEN_AS_TOTAL"


def test_priority_criteria_over_evidence():
    v = check_verification_boundary_honesty(
        "x", **_good(criteria_predefined="no", evidence_before_summary="no"))
    assert v.code == "VERIFICATION_BOUNDARY.POST_HOC_CRITERIA"


def test_priority_evidence_over_selfquestion():
    v = check_verification_boundary_honesty(
        "x", **_good(evidence_before_summary="no", self_questioning_done="no"))
    assert v.code == "VERIFICATION_BOUNDARY.SUMMARY_OVER_EVIDENCE"


def test_invalid_beats_all_no():
    v = check_verification_boundary_honesty(
        "x", **_good(coverage_scope_disclosed="no", self_questioning_done="true"))
    assert v.code == "VERIFICATION_BOUNDARY.INVALID_INPUT"


def test_no_beats_partial():
    v = check_verification_boundary_honesty(
        "x", **_good(evidence_before_summary="no", self_questioning_done="partial"))
    assert v.code == "VERIFICATION_BOUNDARY.SUMMARY_OVER_EVIDENCE"


# --- 结构化字段 ---
def test_verdict_fields():
    v = check_verification_boundary_honesty("claim-X", **_good())
    assert v.claim == "claim-X"
    assert v.coverage_scope_disclosed == "yes"
    assert v.criteria_predefined == "yes"
    assert v.evidence_before_summary == "yes"
    assert v.self_questioning_done == "yes"


# --- 活体回归 ---
def test_live_regression_all_match():
    r = live_regression()
    assert r["all_match"] is True, r


def test_live_regression_has_all_cases():
    r = live_regression()
    assert len(r["cases"]) == 8
    assert set(r["cases"]) == set(r["expected"])
