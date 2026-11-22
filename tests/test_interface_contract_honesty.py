"""接口契约边界诚实性门禁测试（§73，DeepSeek 全家桶 API 编译产物）。"""
import pytest

from svagent.interface_contract_honesty import (
    check_interface_contract_honesty, InterfaceContractVerdict, live_regression,
)


def _good(**over):
    base = dict(param_effect_authority="yes", alias_route_truth="yes",
                risk_compliance_ownership="yes", cost_scope_honesty="yes")
    base.update(over)
    return base


def test_param_ignored_downgrade():
    """声称控制的参数被服务端忽略 → downgrade（传入≠生效 KB-AUDIT03）。"""
    v = check_interface_contract_honesty("x", **_good(param_effect_authority="no"))
    assert isinstance(v, InterfaceContractVerdict)
    assert v.action == "downgrade" and v.code == "IFACE_CONTRACT.PARAM_IGNORED"
    assert "生效" in v.message


def test_alias_rerouted_downgrade():
    """别名可调用但后端已换 → downgrade（名义可用≠实际路由）。"""
    v = check_interface_contract_honesty("x", **_good(alias_route_truth="no"))
    assert v.action == "downgrade" and v.code == "IFACE_CONTRACT.ALIAS_REROUTED"
    assert "路由" in v.message


def test_risk_ownership_shift_downgrade():
    """基础风控冒充完整合规 → downgrade（责任主体错位 KB-STRUCT05）。"""
    v = check_interface_contract_honesty("x", **_good(risk_compliance_ownership="no"))
    assert v.action == "downgrade" and v.code == "IFACE_CONTRACT.RISK_OWNERSHIP_SHIFT"
    assert "合规" in v.message or "主体" in v.message


def test_cost_scope_mixed_flag():
    """工具免费冒充零成本 → flag（计费口径误述）。"""
    v = check_interface_contract_honesty("x", **_good(cost_scope_honesty="no"))
    assert v.action == "flag" and v.code == "IFACE_CONTRACT.COST_SCOPE_MIXED"
    assert "计费" in v.message or "成本" in v.message


@pytest.mark.parametrize("dim", ["param_effect_authority", "alias_route_truth",
                                 "risk_compliance_ownership", "cost_scope_honesty"])
def test_partial_flag(dim):
    """任一维 partial → flag（覆盖不全）。"""
    v = check_interface_contract_honesty("x", **_good(**{dim: "partial"}))
    assert v.action == "flag" and v.code == "IFACE_CONTRACT.PARTIAL"


@pytest.mark.parametrize("bad", ["maybe", "yes-ish", "true", "", "Y", 1, None, "我控制了随机性"])
def test_invalid_enum_flag(bad):
    """非法值（含中文长句字面串）→ flag，不进内容判定（R0 / 避 brittle）。"""
    v = check_interface_contract_honesty("x", **_good(param_effect_authority=bad))
    assert v.action == "flag" and v.code == "IFACE_CONTRACT.INVALID_INPUT"


def test_all_good_ok():
    """四维全 yes → ok（只判声明自洽，不承诺服务端真按声明执行）。"""
    v = check_interface_contract_honesty("honest client", **_good())
    assert v.action == "ok" and v.code == "IFACE_CONTRACT.SELF_CONSISTENT"
    assert "自洽" in v.message


def test_priority_param_over_alias():
    """优先级：param_ignored(R1) 先于 alias_rerouted(R2)。"""
    v = check_interface_contract_honesty(
        "x", **_good(param_effect_authority="no", alias_route_truth="no"))
    assert v.code == "IFACE_CONTRACT.PARAM_IGNORED"


def test_priority_alias_over_risk():
    """优先级：alias_rerouted(R2) 先于 risk_shift(R3)。"""
    v = check_interface_contract_honesty(
        "x", **_good(alias_route_truth="no", risk_compliance_ownership="no"))
    assert v.code == "IFACE_CONTRACT.ALIAS_REROUTED"


def test_priority_risk_over_cost():
    """优先级：risk_shift(R3) 先于 cost_mixed(R4)。"""
    v = check_interface_contract_honesty(
        "x", **_good(risk_compliance_ownership="no", cost_scope_honesty="no"))
    assert v.code == "IFACE_CONTRACT.RISK_OWNERSHIP_SHIFT"


def test_live_regression_all_match():
    """8 个活体样例与 gate_prereg R0-R6 预期全对齐。"""
    r = live_regression()
    assert r["all_match"] is True
    assert len(r["cases"]) == 8
    assert len(r["expected"]) == 8


def test_lazy_import_from_package():
    """惰性登记：从 svagent 顶层可解析该门禁符号，且不接 run_loop。"""
    import svagent
    assert callable(svagent.check_interface_contract_honesty)
    assert svagent.InterfaceContractVerdict is InterfaceContractVerdict
    # §58 选 A：不接 run_loop
    assert not hasattr(svagent, "run_loop") or "interface_contract" not in str(
        getattr(svagent, "run_loop", ""))


def test_distinct_from_proactive_authorization():
    """与 §72 主动介入授权门禁拦截面独立：同一声称可给出不同判定。"""
    from svagent.proactive_authorization import check_proactive_authorization
    v_ic = check_interface_contract_honesty("x", **_good(param_effect_authority="no"))
    v_pa = check_proactive_authorization(
        "x", worthwhile_not_warranted="yes", arbitration_four_gates="yes",
        formal_not_effective_control="yes", silence_and_consent_disclosed="yes")
    assert v_ic.action == "downgrade"
    assert v_pa.action == "ok"


def test_distinct_from_proof_boundary():
    """与 §71 证明边界门禁拦截面独立。"""
    from svagent.proof_boundary_honesty import check_proof_boundary_honesty
    v_ic = check_interface_contract_honesty("x", **_good(cost_scope_honesty="no"))
    v_pb = check_proof_boundary_honesty(
        "x", proves_execution_not_fact="yes", commitment_anchor_independent="yes",
        formal_scope_disclosed="yes", uncovered_disclosed="yes")
    assert v_ic.action == "flag"
    assert v_pb.action == "ok"


def test_empty_claim_still_judged():
    """claim 为空不影响四维判定（claim 仅作标签）。"""
    v = check_interface_contract_honesty("", **_good(alias_route_truth="no"))
    assert v.action == "downgrade"
