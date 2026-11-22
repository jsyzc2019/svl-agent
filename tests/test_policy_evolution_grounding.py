"""策略演化接地诚实性门禁测试（§79，多模态 Agent 记忆综述 T3 编译产物）。"""
import pytest

from svagent.policy_evolution_grounding import (
    check_policy_evolution_grounding, PolicyEvolutionGroundingVerdict, live_regression,
)
import svagent


def _good(**over):
    base = dict(policy_addressable="yes", feedback_attributable="yes",
                evidence_path_preserved="yes", revision_validated_persisted="yes")
    base.update(over)
    return base


# --- R1-R4 downgrade ---
def test_policy_unaddressable_downgrade():
    """策略不可寻址 → downgrade（§5.3 自演化前提缺失）。"""
    v = check_policy_evolution_grounding("x", **_good(policy_addressable="no"))
    assert isinstance(v, PolicyEvolutionGroundingVerdict)
    assert v.action == "downgrade" and v.code == "POLICY_EVOLUTION.POLICY_UNADDRESSABLE"


def test_feedback_not_attributable_downgrade():
    """反馈仅任务级奖励、未归因策略级 → downgrade。"""
    v = check_policy_evolution_grounding("x", **_good(feedback_attributable="no"))
    assert v.action == "downgrade" and v.code == "POLICY_EVOLUTION.FEEDBACK_NOT_ATTRIBUTABLE"


def test_evidence_path_eroded_downgrade():
    """正确率保持但证据接地路径被削弱 → downgrade（§8.3.3 核心命题）。"""
    v = check_policy_evolution_grounding("x", **_good(evidence_path_preserved="no"))
    assert v.action == "downgrade" and v.code == "POLICY_EVOLUTION.EVIDENCE_PATH_ERODED"
    assert "接地" in v.message or "正确率" in v.message


def test_revision_unvalidated_downgrade():
    """策略修订未经验证/不可持久 → downgrade。"""
    v = check_policy_evolution_grounding("x", **_good(revision_validated_persisted="no"))
    assert v.action == "downgrade" and v.code == "POLICY_EVOLUTION.REVISION_UNVALIDATED"


# --- 优先级短路 ---
def test_r1_before_r3():
    """R1 优先级高于 R3：多维 no 时取最靠前规则。"""
    v = check_policy_evolution_grounding("x", **_good(policy_addressable="no", evidence_path_preserved="no"))
    assert v.code == "POLICY_EVOLUTION.POLICY_UNADDRESSABLE"


def test_r2_before_r3():
    v = check_policy_evolution_grounding("x", **_good(feedback_attributable="no", evidence_path_preserved="no"))
    assert v.code == "POLICY_EVOLUTION.FEEDBACK_NOT_ATTRIBUTABLE"


def test_r3_before_r4():
    v = check_policy_evolution_grounding("x", **_good(evidence_path_preserved="no", revision_validated_persisted="no"))
    assert v.code == "POLICY_EVOLUTION.EVIDENCE_PATH_ERODED"


# --- R5 partial ---
@pytest.mark.parametrize("dim", ["policy_addressable", "feedback_attributable",
                                 "evidence_path_preserved", "revision_validated_persisted"])
def test_partial_flag(dim):
    v = check_policy_evolution_grounding("x", **_good(**{dim: "partial"}))
    assert v.action == "flag" and v.code == "POLICY_EVOLUTION.PARTIAL"


# --- R0 invalid enum ---
@pytest.mark.parametrize("bad", ["maybe", "yes-ish", "true", "", "Y", 1, None])
def test_invalid_enum_flag(bad):
    v = check_policy_evolution_grounding("x", **_good(policy_addressable=bad))
    assert v.action == "flag" and v.code == "POLICY_EVOLUTION.INVALID_INPUT"


# --- R6 ok ---
def test_all_good_ok():
    v = check_policy_evolution_grounding("x", **_good())
    assert v.action == "ok" and v.code == "POLICY_EVOLUTION.SELF_CONSISTENT"
    assert "不承诺" in v.message or "存在≠有效性" in v.message


def test_immutable_verdict():
    v = check_policy_evolution_grounding("x", **_good())
    with pytest.raises(Exception):
        v.action = "downgrade"


def test_claim_passthrough():
    v = check_policy_evolution_grounding("my-system", **_good())
    assert v.claim == "my-system"


# --- 惰性导入 / 不接 run_loop ---
def test_lazy_export():
    assert callable(svagent.check_policy_evolution_grounding)
    assert svagent.PolicyEvolutionGroundingVerdict is PolicyEvolutionGroundingVerdict


def test_not_in_run_loop():
    import inspect
    src = inspect.getsource(svagent.run_loop) if hasattr(svagent, "run_loop") else ""
    assert "policy_evolution_grounding" not in src


# --- live regression ---
def test_live_regression_all_passed():
    r = live_regression()
    assert r["all_passed"] is True
    assert all(r["checks"].values())


def test_live_regression_cases_count():
    r = live_regression()
    assert len(r["cases"]) == 7
    assert len(r["checks"]) == 7
