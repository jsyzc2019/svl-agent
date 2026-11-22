"""技能准入校准门禁测试（§82，EvoSteer Validated Skill Admission 编译产物）。"""
import pytest

from svagent.skill_admission_calibration import (
    check_skill_admission_calibration, SkillAdmissionVerdict, live_regression,
)
import svagent


def _good(**over):
    base = dict(tried_before_promotion="yes", paired_counterfactual="yes",
                sequential_budget="yes", retire_mechanism="yes")
    base.update(over)
    return base


# --- R1-R4 downgrade ---
def test_untried_promotion_downgrade():
    """未经试用即凭 judge/成功计数晋升 → downgrade（§1(iii)）。"""
    v = check_skill_admission_calibration("x", **_good(tried_before_promotion="no"))
    assert isinstance(v, SkillAdmissionVerdict)
    assert v.action == "downgrade" and v.code == "SKILL_ADMISSION.UNTRIED_PROMOTION"
    assert "试用" in v.message or "judge" in v.message


def test_no_paired_downgrade():
    """无配对反事实，点估计无法区分证据不足与确认效果 → downgrade。"""
    v = check_skill_admission_calibration("x", **_good(paired_counterfactual="no"))
    assert v.action == "downgrade" and v.code == "SKILL_ADMISSION.NO_PAIRED_EVIDENCE"


def test_uncalibrated_downgrade():
    """无共享预算序贯检验（成功计数当可靠信念）→ downgrade。"""
    v = check_skill_admission_calibration("x", **_good(sequential_budget="no"))
    assert v.action == "downgrade" and v.code == "SKILL_ADMISSION.UNCALIBRATED_TEST"
    assert "序贯" in v.message or "预算" in v.message


def test_no_retire_downgrade():
    """无退役/延迟机制（准入后永不复核）→ downgrade（§1(iii) never retired）。"""
    v = check_skill_admission_calibration("x", **_good(retire_mechanism="no"))
    assert v.action == "downgrade" and v.code == "SKILL_ADMISSION.NO_RETIRE"


# --- 优先级短路 ---
def test_r1_before_r2():
    v = check_skill_admission_calibration("x", **_good(tried_before_promotion="no", paired_counterfactual="no"))
    assert v.code == "SKILL_ADMISSION.UNTRIED_PROMOTION"


def test_r2_before_r3():
    v = check_skill_admission_calibration("x", **_good(paired_counterfactual="no", sequential_budget="no"))
    assert v.code == "SKILL_ADMISSION.NO_PAIRED_EVIDENCE"


def test_r3_before_r4():
    v = check_skill_admission_calibration("x", **_good(sequential_budget="no", retire_mechanism="no"))
    assert v.code == "SKILL_ADMISSION.UNCALIBRATED_TEST"


# --- R5 partial ---
@pytest.mark.parametrize("dim", ["tried_before_promotion", "paired_counterfactual",
                                 "sequential_budget", "retire_mechanism"])
def test_partial_flag(dim):
    v = check_skill_admission_calibration("x", **_good(**{dim: "partial"}))
    assert v.action == "flag" and v.code == "SKILL_ADMISSION.PARTIAL"


# --- R0 invalid enum ---
@pytest.mark.parametrize("bad", ["maybe", "yes-ish", "true", "", "Y", 1, None])
def test_invalid_enum_flag(bad):
    v = check_skill_admission_calibration("x", **_good(tried_before_promotion=bad))
    assert v.action == "flag" and v.code == "SKILL_ADMISSION.INVALID_INPUT"


# --- R6 ok ---
def test_all_good_ok():
    v = check_skill_admission_calibration("x", **_good())
    assert v.action == "ok" and v.code == "SKILL_ADMISSION.SELF_CONSISTENT"
    assert "不承诺" in v.message or "存在≠有效性" in v.message


def test_claim_passthrough():
    v = check_skill_admission_calibration("my-skilllib", **_good())
    assert v.claim == "my-skilllib"


# --- 惰性导入 / 不接 run_loop ---
def test_lazy_export():
    assert callable(svagent.check_skill_admission_calibration)
    assert svagent.SkillAdmissionVerdict is SkillAdmissionVerdict


def test_not_in_run_loop():
    import inspect
    src = inspect.getsource(svagent.run_loop) if hasattr(svagent, "run_loop") else ""
    assert "skill_admission_calibration" not in src


# --- live regression ---
def test_live_regression_all_passed():
    r = live_regression()
    assert r["all_passed"] is True
    assert all(r["checks"].values())


def test_live_regression_cases_count():
    r = live_regression()
    assert len(r["cases"]) == 7
    assert len(r["checks"]) == 7
