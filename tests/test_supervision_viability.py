"""监督可行性门禁测试（§74，认知投降谱系编译产物）。"""
import pytest

from svagent.supervision_viability import (
    check_supervision_viability, SupervisionViabilityVerdict, live_regression,
)


def _good(**over):
    base = dict(independent_view_formed="yes", review_capability_preserved="yes",
                oversight_not_self_undermining="yes", surface_vs_systemic="yes")
    base.update(over)
    return base


def test_no_independent_view_downgrade():
    """有评审但无独立观点 → downgrade（认知投降）。"""
    v = check_supervision_viability("x", **_good(independent_view_formed="no"))
    assert isinstance(v, SupervisionViabilityVerdict)
    assert v.action == "downgrade" and v.code == "SUPERVISION.NO_INDEPENDENT_VIEW"
    assert "独立观点" in v.message


def test_capability_eroded_downgrade():
    """评审能力被生成式使用侵蚀 → downgrade。"""
    v = check_supervision_viability("x", **_good(review_capability_preserved="no"))
    assert v.action == "downgrade" and v.code == "SUPERVISION.CAPABILITY_ERODED"
    assert "能力" in v.message


def test_paradox_downgrade():
    """监督悖论自我消解 → downgrade（元层矛盾）。"""
    v = check_supervision_viability("x", **_good(oversight_not_self_undermining="no"))
    assert v.action == "downgrade" and v.code == "SUPERVISION.PARADOX"
    assert "监督" in v.message or "悖论" in v.message


def test_surface_as_systemic_flag():
    """表面正确冒充系统正确 → flag。"""
    v = check_supervision_viability("x", **_good(surface_vs_systemic="no"))
    assert v.action == "flag" and v.code == "SUPERVISION.SURFACE_AS_SYSTEMIC"
    assert "表面" in v.message or "系统" in v.message


@pytest.mark.parametrize("dim", ["independent_view_formed", "review_capability_preserved",
                                 "oversight_not_self_undermining", "surface_vs_systemic"])
def test_partial_flag(dim):
    v = check_supervision_viability("x", **_good(**{dim: "partial"}))
    assert v.action == "flag" and v.code == "SUPERVISION.PARTIAL"


@pytest.mark.parametrize("bad", ["maybe", "yes-ish", "true", "", "Y", 1, None, "我们有人类评审所以质量有保障"])
def test_invalid_enum_flag(bad):
    v = check_supervision_viability("x", **_good(independent_view_formed=bad))
    assert v.action == "flag" and v.code == "SUPERVISION.INVALID_INPUT"


def test_all_good_ok():
    v = check_supervision_viability("honest review", **_good())
    assert v.action == "ok" and v.code == "SUPERVISION.SELF_CONSISTENT"
    assert "自洽" in v.message


def test_priority_view_over_capability():
    v = check_supervision_viability(
        "x", **_good(independent_view_formed="no", review_capability_preserved="no"))
    assert v.code == "SUPERVISION.NO_INDEPENDENT_VIEW"


def test_priority_capability_over_paradox():
    v = check_supervision_viability(
        "x", **_good(review_capability_preserved="no", oversight_not_self_undermining="no"))
    assert v.code == "SUPERVISION.CAPABILITY_ERODED"


def test_priority_paradox_over_surface():
    v = check_supervision_viability(
        "x", **_good(oversight_not_self_undermining="no", surface_vs_systemic="no"))
    assert v.code == "SUPERVISION.PARADOX"


def test_live_regression_all_match():
    r = live_regression()
    assert r["all_match"] is True
    assert len(r["cases"]) == 8 and len(r["expected"]) == 8


def test_lazy_import_from_package():
    import svagent
    assert callable(svagent.check_supervision_viability)
    assert svagent.SupervisionViabilityVerdict is SupervisionViabilityVerdict
    assert not hasattr(svagent, "run_loop") or "supervision" not in str(
        getattr(svagent, "run_loop", ""))


def test_distinct_from_interface_contract():
    """与 §73 接口契约门禁拦截面独立：同一声称可给出不同判定。"""
    from svagent.interface_contract_honesty import check_interface_contract_honesty
    v_sv = check_supervision_viability("x", **_good(independent_view_formed="no"))
    v_ic = check_interface_contract_honesty(
        "x", param_effect_authority="yes", alias_route_truth="yes",
        risk_compliance_ownership="yes", cost_scope_honesty="yes")
    assert v_sv.action == "downgrade"
    assert v_ic.action == "ok"


def test_distinct_from_reviewer_evaluation():
    """与 §60 评审漏斗保真门禁对象层级不同：本门判能力前提，非单次过程污染。"""
    from svagent.reviewer_evaluation import check_review_evaluation
    v_sv = check_supervision_viability("x", **_good(oversight_not_self_undermining="no"))
    # reviewer_evaluation 判单次评审是否保真；此断言只验证两门可分别调用且判定独立
    assert v_sv.action == "downgrade"
    assert callable(check_review_evaluation)


def test_empty_claim_still_judged():
    v = check_supervision_viability("", **_good(surface_vs_systemic="no"))
    assert v.action == "flag"
