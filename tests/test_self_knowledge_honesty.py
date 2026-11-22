"""自知诚实性门禁测试（§75，AINLP 公众号 Addy Osmani 文编译产物）。"""
import pytest

from svagent.self_knowledge_honesty import (
    check_self_knowledge_honesty, SelfKnowledgeHonestyVerdict, live_regression,
)


def _good(**over):
    base = dict(hypothesis_before_query="yes", cognitive_limits_disclosed="yes",
                falsification_self_asked="yes", skill_atrophy_disclosed="yes")
    base.update(over)
    return base


# --- R1: 假设先行 ---
def test_no_hypothesis_downgrade():
    """提问前无假设 → downgrade（认知卸载起点）。"""
    v = check_self_knowledge_honesty("x", **_good(hypothesis_before_query="no"))
    assert isinstance(v, SelfKnowledgeHonestyVerdict)
    assert v.action == "downgrade" and v.code == "SELF_KNOWLEDGE.NO_HYPOTHESIS"
    assert "假设" in v.message


# --- R2: 认知局限自陈 ---
def test_false_completeness_downgrade():
    """假装完整心智模型 → downgrade。"""
    v = check_self_knowledge_honesty("x", **_good(cognitive_limits_disclosed="no"))
    assert v.action == "downgrade" and v.code == "SELF_KNOWLEDGE.FALSE_COMPLETENESS"
    assert "完整" in v.message or "理解" in v.message


# --- R3: 可证伪自问 ---
def test_unfalsifiable_downgrade():
    """未主动问『什么情况会错』 → downgrade。"""
    v = check_self_knowledge_honesty("x", **_good(falsification_self_asked="no"))
    assert v.action == "downgrade" and v.code == "SELF_KNOWLEDGE.UNFALSIFIABLE"
    assert "证伪" in v.message or "会错" in v.message


# --- R4: 技能退化披露 ---
def test_hidden_atrophy_downgrade():
    """隐瞒不再练习的关键能力 → downgrade。"""
    v = check_self_knowledge_honesty("x", **_good(skill_atrophy_disclosed="no"))
    assert v.action == "downgrade" and v.code == "SELF_KNOWLEDGE.HIDDEN_ATROPHY"
    assert "技能" in v.message or "退化" in v.message


# --- R5: partial → flag（四维各测） ---
@pytest.mark.parametrize("dim", [
    "hypothesis_before_query", "cognitive_limits_disclosed",
    "falsification_self_asked", "skill_atrophy_disclosed",
])
def test_partial_flag(dim):
    v = check_self_knowledge_honesty("x", **_good(**{dim: "partial"}))
    assert v.action == "flag" and v.code == "SELF_KNOWLEDGE.PARTIAL"


# --- R0: 非法枚举/字面串 → flag（四维各测 + 多类非法值）---
@pytest.mark.parametrize("dim", [
    "hypothesis_before_query", "cognitive_limits_disclosed",
    "falsification_self_asked", "skill_atrophy_disclosed",
])
def test_invalid_enum_flag_each_dim(dim):
    v = check_self_knowledge_honesty("x", **_good(**{dim: "maybe"}))
    assert v.action == "flag" and v.code == "SELF_KNOWLEDGE.INVALID_INPUT"


@pytest.mark.parametrize("bad", [
    "maybe", "yes-ish", "true", "", "Y", 1, None,
    "我们会先想清楚再问", "我们会定期反思自己的认知局限",
])
def test_invalid_values_to_flag(bad):
    """字面串与其他非法值 → flag，不进内容判定（避 §56 brittle）。"""
    v = check_self_knowledge_honesty("x", **_good(hypothesis_before_query=bad))
    assert v.action == "flag" and v.code == "SELF_KNOWLEDGE.INVALID_INPUT"


# --- R6: 全自洽 → ok ---
def test_all_good_ok():
    v = check_self_knowledge_honesty("honest self-knowledge", **_good())
    assert v.action == "ok" and v.code == "SELF_KNOWLEDGE.SELF_CONSISTENT"
    assert "自洽" in v.message
    assert "不承诺" in v.message  # 诚实边界写进 message


# --- 优先级 ---
def test_priority_hypothesis_over_completeness():
    v = check_self_knowledge_honesty(
        "x", **_good(hypothesis_before_query="no", cognitive_limits_disclosed="no"))
    assert v.code == "SELF_KNOWLEDGE.NO_HYPOTHESIS"


def test_priority_completeness_over_falsification():
    v = check_self_knowledge_honesty(
        "x", **_good(cognitive_limits_disclosed="no", falsification_self_asked="no"))
    assert v.code == "SELF_KNOWLEDGE.FALSE_COMPLETENESS"


def test_priority_falsification_over_atrophy():
    v = check_self_knowledge_honesty(
        "x", **_good(falsification_self_asked="no", skill_atrophy_disclosed="no"))
    assert v.code == "SELF_KNOWLEDGE.UNFALSIFIABLE"


def test_invalid_beats_all_no():
    """R0 非法输入优先于任何 no（先判形状，再判内容）。"""
    v = check_self_knowledge_honesty(
        "x", **_good(hypothesis_before_query="no", skill_atrophy_disclosed="true"))
    assert v.code == "SELF_KNOWLEDGE.INVALID_INPUT"


def test_no_beats_partial():
    """no 优先于 partial（downgrade 重于 flag）。"""
    v = check_self_knowledge_honesty(
        "x", **_good(falsification_self_asked="no", skill_atrophy_disclosed="partial"))
    assert v.code == "SELF_KNOWLEDGE.UNFALSIFIABLE"


# --- 结构化字段 ---
def test_verdict_fields():
    v = check_self_knowledge_honesty("claim-X", **_good())
    assert v.claim == "claim-X"
    assert v.hypothesis_before_query == "yes"
    assert v.cognitive_limits_disclosed == "yes"
    assert v.falsification_self_asked == "yes"
    assert v.skill_atrophy_disclosed == "yes"


# --- 活体回归 ---
def test_live_regression_all_match():
    r = live_regression()
    assert r["all_match"] is True, r


def test_live_regression_has_all_cases():
    r = live_regression()
    assert len(r["cases"]) == 8
    assert set(r["cases"]) == set(r["expected"])
