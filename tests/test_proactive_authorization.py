"""主动介入授权正当性门禁测试（§72，Proactive AI 综述编译产物）。"""
import pytest

from svagent.proactive_authorization import (
    check_proactive_authorization, ProactiveAuthorizationVerdict, live_regression,
)


def _good(**over):
    base = dict(worthwhile_not_warranted="yes", arbitration_four_gates="yes",
                formal_not_effective_control="yes", silence_and_consent_disclosed="yes")
    base.update(over)
    return base


def test_goal_as_warrant_downgrade():
    """目标价值冒充介入授权 → downgrade（主体错位 KB-STRUCT05）。"""
    v = check_proactive_authorization("x", **_good(worthwhile_not_warranted="no"))
    assert isinstance(v, ProactiveAuthorizationVerdict)
    assert v.action == "downgrade" and v.code == "PROACTIVE_AUTH.GOAL_AS_WARRANT"
    assert "授权" in v.message or "主体错位" in v.message


def test_no_arbitration_downgrade():
    """act-first 无仲裁四关 → downgrade。"""
    v = check_proactive_authorization("x", **_good(arbitration_four_gates="no"))
    assert v.action == "downgrade" and v.code == "PROACTIVE_AUTH.NO_ARBITRATION"
    assert "仲裁" in v.message


def test_formal_as_effective_downgrade():
    """形式授权冒充真实控制 → downgrade。"""
    v = check_proactive_authorization("x", **_good(formal_not_effective_control="no"))
    assert v.action == "downgrade" and v.code == "PROACTIVE_AUTH.FORMAL_AS_EFFECTIVE"


def test_silence_hidden_flag():
    """不披露沉默选项与风险分级同意 → flag（过度主动）。"""
    v = check_proactive_authorization("x", **_good(silence_and_consent_disclosed="no"))
    assert v.action == "flag" and v.code == "PROACTIVE_AUTH.SILENCE_HIDDEN"


@pytest.mark.parametrize("dim", ["worthwhile_not_warranted", "arbitration_four_gates",
                                 "formal_not_effective_control", "silence_and_consent_disclosed"])
def test_partial_flag(dim):
    """任一维 partial → flag（覆盖不全）。"""
    v = check_proactive_authorization("x", **_good(**{dim: "partial"}))
    assert v.action == "flag" and v.code == "PROACTIVE_AUTH.PARTIAL"


@pytest.mark.parametrize("bad", ["maybe", "yes-ish", "true", "", "Y", 1, None])
def test_invalid_enum_flag(bad):
    """非法值（含字面串）→ flag，不进内容判定（R0 / 避 brittle）。"""
    v = check_proactive_authorization("x", **_good(worthwhile_not_warranted=bad))
    assert v.action == "flag" and v.code == "PROACTIVE_AUTH.INVALID_INPUT"


def test_all_good_ok():
    """四维全 yes → ok（只判声明自洽）。"""
    v = check_proactive_authorization("honest agent", **_good())
    assert v.action == "ok" and v.code == "PROACTIVE_AUTH.SELF_CONSISTENT"


def test_ok_message_mentions_no_guarantee():
    """ok 的消息须声明只判声明、不承诺真校准（诚实边界）。"""
    v = check_proactive_authorization("x", **_good())
    assert "不承诺" in v.message or "有效性" in v.message


def test_priority_warrant_before_arbitration():
    """多维 no 时按 R1 优先于 R2（短路顺序）。"""
    v = check_proactive_authorization("x", **_good(worthwhile_not_warranted="no", arbitration_four_gates="no"))
    assert v.code == "PROACTIVE_AUTH.GOAL_AS_WARRANT"


def test_priority_arbitration_before_formal():
    """R2 优先于 R3。"""
    v = check_proactive_authorization("x", **_good(arbitration_four_gates="no", formal_not_effective_control="no"))
    assert v.code == "PROACTIVE_AUTH.NO_ARBITRATION"


def test_priority_formal_before_silence():
    """R3 优先于 R4。"""
    v = check_proactive_authorization("x", **_good(formal_not_effective_control="no", silence_and_consent_disclosed="no"))
    assert v.code == "PROACTIVE_AUTH.FORMAL_AS_EFFECTIVE"


def test_literal_chinese_not_enum_flag():
    """中文语义串不是枚举 → flag（字面串不进内容判定）。"""
    v = check_proactive_authorization("x", **_good(arbitration_four_gates="是"))
    assert v.action == "flag" and v.code == "PROACTIVE_AUTH.INVALID_INPUT"


def test_verdict_fields_frozen():
    """Verdict 为 frozen dataclass，记录四维输入便于追溯。"""
    v = check_proactive_authorization("claim-x", **_good())
    assert v.claim == "claim-x"
    assert v.worthwhile_not_warranted == "yes"
    with pytest.raises(Exception):
        v.action = "ok"


def test_live_regression_all_pass():
    """7 个活体样例回归全部对齐门预注册预期。"""
    r = live_regression()
    assert r["all_passed"], r["cases"]
    assert len(r["checks"]) == 7


def test_live_regression_codes():
    """活体回归的 action/code 与门预注册逐项一致。"""
    r = live_regression()
    assert r["cases"]["goal_as_warrant"] == "downgrade/PROACTIVE_AUTH.GOAL_AS_WARRANT"
    assert r["cases"]["no_arbitration"] == "downgrade/PROACTIVE_AUTH.NO_ARBITRATION"
    assert r["cases"]["all_good"] == "ok/PROACTIVE_AUTH.SELF_CONSISTENT"


def test_lazy_import_from_package():
    """惰性登记：从 svagent 顶层可解析该门禁符号，且不接 run_loop。"""
    import svagent
    assert callable(svagent.check_proactive_authorization)
    assert svagent.ProactiveAuthorizationVerdict is ProactiveAuthorizationVerdict


def test_distinct_from_proof_boundary():
    """与 §71 证明边界门禁拦截面独立：同一声明可给出不同判定。"""
    from svagent.proof_boundary_honesty import check_proof_boundary_honesty
    payload_pa = _good(worthwhile_not_warranted="no")
    v_pa = check_proactive_authorization("x", **payload_pa)
    v_pb = check_proof_boundary_honesty(
        "x", proves_execution_not_fact="yes", commitment_anchor_independent="yes",
        formal_scope_disclosed="yes", uncovered_disclosed="yes")
    assert v_pa.action == "downgrade"
    assert v_pb.action == "ok"


def test_empty_claim_still_judged():
    """claim 为空不影响四维判定（claim 仅作标签）。"""
    v = check_proactive_authorization("", **_good(arbitration_four_gates="no"))
    assert v.action == "downgrade"
