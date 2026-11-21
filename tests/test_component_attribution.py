"""组件归因门禁判据测试（RSI-Structure 综述 Where 维度编译）。"""
import pytest

from svagent.component_attribution import (
    COMPONENTS,
    VERIFICATION_BY_COMPONENT,
    AttributionClaim,
    classify_component_by_description,
    guard,
    verification_for,
)


def test_components_are_the_four_from_paper():
    assert COMPONENTS == ("Prompt", "Memory", "Skill", "Harness")


def test_missing_component_is_blocked():
    v = guard(AttributionClaim(failure="API参数报错"))
    assert v.action == "block"
    assert v.code == "ATTR.COMPONENT_MISSING"


def test_illegal_component_is_blocked():
    v = guard(AttributionClaim(failure="x", component="Weights"))
    assert v.action == "block"
    assert v.code == "ATTR.COMPONENT_MISSING"


def test_component_without_evidence_is_blocked():
    v = guard(AttributionClaim(failure="x", component="Memory"))
    assert v.code == "ATTR.NO_EVIDENCE"


def test_component_without_verification_is_blocked():
    v = guard(AttributionClaim(failure="x", component="Memory", why_this_component="旧字段过期"))
    assert v.code == "ATTR.VERIFY_MISSING"


def test_complete_attribution_allowed():
    c = AttributionClaim(
        failure="字段过期", component="Memory", why_this_component="检索到旧schema",
        verification=verification_for("Memory"),
    )
    v = guard(c)
    assert v.action == "allow"
    assert v.code == "ATTR.OK"


def test_retirement_without_rare_use_check_downgraded():
    d = AttributionClaim(
        failure="技能冗余", component="Skill", why_this_component="与另一技能重叠",
        verification="执行成功率测试", dropping=True,
    )
    v = guard(d)
    assert v.action == "downgrade"
    assert v.code == "ATTR.RARE_USE_UNCHECKED"


def test_retirement_with_rare_use_check_allowed():
    d = AttributionClaim(
        failure="技能冗余", component="Skill", why_this_component="与另一技能重叠",
        verification="执行成功率测试", dropping=True, checked_rare_uses=True,
    )
    assert guard(d).action == "allow"


def test_verification_map_covers_all_components():
    assert set(VERIFICATION_BY_COMPONENT) == set(COMPONENTS)
    for comp in COMPONENTS:
        assert verification_for(comp)


def test_heuristic_classification_hand_audited():
    # 期望值已手工核算（§36 纪律：先审工具再落笔）
    assert classify_component_by_description("从向量库检索一条历史案例") == ["Memory"]
    assert classify_component_by_description("把规则写进 system prompt")[0] == "Prompt"
    assert "Harness" in classify_component_by_description("在工具调用前加参数校验逻辑")


def test_heuristic_is_only_hint_not_gate():
    # 失败叙述能识别出候选，但无显式声明仍须拦截（防自证）
    v = guard(AttributionClaim(failure="从向量库检索一条历史案例但结果过期"))
    assert v.action == "block"
