"""选择性监督诚实性门禁测试（§78，清华 System-1/System-2 Perspective 编译产物）。"""
import pytest

from svagent.selective_supervision_honesty import (
    check_selective_supervision_honesty, SelectiveSupervisionVerdict, live_regression,
)


def _good(**over):
    base = dict(propensity_reaches_suppressed="yes", audit_independent_of_score="yes",
                blind_spot_disclosed="yes", counterfactual_loss_acknowledged="yes")
    base.update(over)
    return base


# --- R1-R4 downgrade ---
def test_mnar_zero_propensity_downgrade():
    """压制区零概率 → downgrade（标签 MNAR，自我强化选择性监督）。"""
    v = check_selective_supervision_honesty("x", **_good(propensity_reaches_suppressed="no"))
    assert isinstance(v, SelectiveSupervisionVerdict)
    assert v.action == "downgrade" and v.code == "SELECTIVE_SUPERVISION.MNAR_ZERO_PROPENSITY"
    assert "MNAR" in v.message or "非随机缺失" in v.message


def test_audit_self_censored_downgrade():
    """审计率依赖分数 → downgrade（审计被自审污染）。"""
    v = check_selective_supervision_honesty("x", **_good(audit_independent_of_score="no"))
    assert v.action == "downgrade" and v.code == "SELECTIVE_SUPERVISION.AUDIT_SELF_CENSORED"
    assert "审计" in v.message or "漏判" in v.message


def test_blind_spot_hidden_downgrade():
    """盲点隐藏 → downgrade（平均误差掩盖）。"""
    v = check_selective_supervision_honesty("x", **_good(blind_spot_disclosed="no"))
    assert v.action == "downgrade" and v.code == "SELECTIVE_SUPERVISION.BLIND_SPOT_HIDDEN"
    assert "盲点" in v.message or "平均误差" in v.message


def test_counterfactual_hidden_downgrade():
    """漏判反事实损失不承认 → downgrade。"""
    v = check_selective_supervision_honesty("x", **_good(counterfactual_loss_acknowledged="no"))
    assert v.action == "downgrade" and v.code == "SELECTIVE_SUPERVISION.COUNTERFACTUAL_HIDDEN"
    assert "反事实" in v.message or "漏判" in v.message


# --- R5 partial ---
@pytest.mark.parametrize("dim", ["propensity_reaches_suppressed", "audit_independent_of_score",
                                 "blind_spot_disclosed", "counterfactual_loss_acknowledged"])
def test_partial_flag(dim):
    """任一维 partial → flag（覆盖不全）。"""
    v = check_selective_supervision_honesty("x", **_good(**{dim: "partial"}))
    assert v.action == "flag" and v.code == "SELECTIVE_SUPERVISION.PARTIAL"


# --- R0 invalid enum ---
@pytest.mark.parametrize("bad", ["maybe", "yes-ish", "true", "", "Y", 1, None])
def test_invalid_enum_flag(bad):
    """非法值（含字面串）→ flag，不进内容判定（R0 / 避 brittle）。"""
    v = check_selective_supervision_honesty("x", **_good(propensity_reaches_suppressed=bad))
    assert v.action == "flag" and v.code == "SELECTIVE_SUPERVISION.INVALID_INPUT"


@pytest.mark.parametrize("dim", ["audit_independent_of_score", "blind_spot_disclosed",
                                 "counterfactual_loss_acknowledged"])
def test_invalid_enum_other_dims(dim):
    """非法值出现在其余维同样 flag。"""
    v = check_selective_supervision_honesty("x", **_good(**{dim: "nope"}))
    assert v.action == "flag" and v.code == "SELECTIVE_SUPERVISION.INVALID_INPUT"


def test_chinese_literal_flag():
    """中文字符串字面量 → flag（避 §56 brittle）。"""
    v = check_selective_supervision_honesty("x", **_good(propensity_reaches_suppressed="是"))
    assert v.action == "flag" and v.code == "SELECTIVE_SUPERVISION.INVALID_INPUT"


# --- R6 all good ---
def test_all_good_ok():
    """四维全 yes → ok（只判机制声明自洽）。"""
    v = check_selective_supervision_honesty("honest gated system", **_good())
    assert v.action == "ok" and v.code == "SELECTIVE_SUPERVISION.SELF_CONSISTENT"


def test_ok_message_mentions_no_guarantee():
    """ok 消息须声明只判声明、不承诺筛选真带来收益（诚实边界）。"""
    v = check_selective_supervision_honesty("x", **_good())
    assert "不承诺" in v.message or "有效性" in v.message or "存在" in v.message


# --- priority ---
def test_priority_origin_before_audit():
    """多 no 时按 R1 优先级短路（propensity 先于 audit）。"""
    v = check_selective_supervision_honesty("x", **_good(propensity_reaches_suppressed="no",
                                                        audit_independent_of_score="no"))
    assert v.code == "SELECTIVE_SUPERVISION.MNAR_ZERO_PROPENSITY"


def test_priority_audit_before_blind():
    """R2 先于 R3（audit 先于 blind spot）。"""
    v = check_selective_supervision_honesty("x", **_good(audit_independent_of_score="no",
                                                        blind_spot_disclosed="no"))
    assert v.code == "SELECTIVE_SUPERVISION.AUDIT_SELF_CENSORED"


def test_priority_blind_before_counterfactual():
    """R3 先于 R4（blind spot 先于 counterfactual）。"""
    v = check_selective_supervision_honesty("x", **_good(blind_spot_disclosed="no",
                                                        counterfactual_loss_acknowledged="no"))
    assert v.code == "SELECTIVE_SUPERVISION.BLIND_SPOT_HIDDEN"


def test_r0_before_all():
    """R0 非法值优先于所有内容规则。"""
    v = check_selective_supervision_honesty("x", **_good(propensity_reaches_suppressed="no",
                                                        audit_independent_of_score="maybe"))
    assert v.code == "SELECTIVE_SUPERVISION.INVALID_INPUT"


def test_partial_after_all_no():
    """partial 优先于 ok，但在所有 no 规则之后。"""
    v = check_selective_supervision_honesty("x", **_good(blind_spot_disclosed="partial",
                                                        counterfactual_loss_acknowledged="no"))
    assert v.code == "SELECTIVE_SUPERVISION.COUNTERFACTUAL_HIDDEN"


# --- structure / invariants ---
def test_frozen_dataclass():
    """Verdict 不可变。"""
    v = check_selective_supervision_honesty("x", **_good())
    with pytest.raises(Exception):
        v.action = "ok"


def test_verdict_fields_reflect_inputs():
    """Verdict 四维字段如实回显输入。"""
    v = check_selective_supervision_honesty("x", **_good(propensity_reaches_suppressed="no"))
    assert v.propensity_reaches_suppressed == "no"
    assert v.audit_independent_of_score == "yes"
    assert v.blind_spot_disclosed == "yes"
    assert v.counterfactual_loss_acknowledged == "yes"


def test_claim_preserved():
    """claim 字段保留原样。"""
    v = check_selective_supervision_honesty("System1-System2-co-design", **_good())
    assert v.claim == "System1-System2-co-design"


@pytest.mark.parametrize("action", ["ok", "downgrade", "flag"])
def test_action_vocabulary(action):
    """action 取值限定在 ok/downgrade/flag。"""
    inp = _good()
    if action == "downgrade":
        inp["propensity_reaches_suppressed"] = "no"
    elif action == "flag":
        inp["blind_spot_disclosed"] = "partial"
    v = check_selective_supervision_honesty("x", **inp)
    assert v.action == action


def test_empty_claim():
    """claim 为空不影响判定逻辑。"""
    v = check_selective_supervision_honesty("", **_good())
    assert v.action == "ok"


# --- live regression ---
def test_live_regression_all_pass():
    """7 活体样例回归全通过。"""
    r = live_regression()
    assert r["all_passed"] is True
    assert len(r["checks"]) == 7
    assert all(r["checks"].values())


def test_live_regression_codes_present():
    """活体回归覆盖 R0-R6 各码（值为 action/code 完整串）。"""
    r = live_regression()
    outcomes = set(r["cases"].values())
    assert "downgrade/SELECTIVE_SUPERVISION.MNAR_ZERO_PROPENSITY" in outcomes
    assert "downgrade/SELECTIVE_SUPERVISION.AUDIT_SELF_CENSORED" in outcomes
    assert "downgrade/SELECTIVE_SUPERVISION.BLIND_SPOT_HIDDEN" in outcomes
    assert "downgrade/SELECTIVE_SUPERVISION.COUNTERFACTUAL_HIDDEN" in outcomes
    assert "flag/SELECTIVE_SUPERVISION.PARTIAL" in outcomes
    assert "flag/SELECTIVE_SUPERVISION.INVALID_INPUT" in outcomes
    assert "ok/SELECTIVE_SUPERVISION.SELF_CONSISTENT" in outcomes


# --- AST brittle guard ---
def test_no_chinese_literal_in_compare():
    """Compare 节点内禁中文字符串字面量（AST 自审，避 brittle）。"""
    import ast
    import pathlib
    import svagent
    src = pathlib.Path(svagent.__file__).parent.joinpath("selective_supervision_honesty.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for sub in ast.walk(node):
                if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                    if any(ord(c) > 0x2E80 for c in sub.value):
                        bad.append(sub.value)
    assert bad == [], f"Compare 内出现中文字面量: {bad}"


def test_all_four_dims_required():
    """四个关键字参数缺一不可（签名强制）。"""
    with pytest.raises(TypeError):
        check_selective_supervision_honesty("x", propensity_reaches_suppressed="yes")
