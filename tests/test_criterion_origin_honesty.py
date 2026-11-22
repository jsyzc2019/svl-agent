"""判据来源诚实性门禁测试（§77，HarnessPro 编译产物）。"""
import pytest

from svagent.criterion_origin_honesty import (
    check_criterion_origin_honesty, CriterionOriginVerdict, live_regression,
)


def _good(**over):
    base = dict(criterion_origin_disclosed="yes", recall_boundary_disclosed="yes",
                external_anchor_disclosed="yes", independent_reviewer_gap_disclosed="yes")
    base.update(over)
    return base


# --- R1-R4 downgrade ---
def test_self_as_anchor_downgrade():
    """自生成判据冒充外部锚定 → downgrade（主体错位 KB-STRUCT05）。"""
    v = check_criterion_origin_honesty("x", **_good(criterion_origin_disclosed="no"))
    assert isinstance(v, CriterionOriginVerdict)
    assert v.action == "downgrade" and v.code == "CRITERION_ORIGIN.SELF_AS_ANCHOR"
    assert "冒充外部锚" in v.message or "主体错位" in v.message


def test_recall_hidden_downgrade():
    """判据召回边界隐藏 → downgrade（漏检率不披露）。"""
    v = check_criterion_origin_honesty("x", **_good(recall_boundary_disclosed="no"))
    assert v.action == "downgrade" and v.code == "CRITERION_ORIGIN.RECALL_HIDDEN"
    assert "召回" in v.message or "漏检" in v.message


def test_no_external_anchor_downgrade():
    """label-free 有效性无外部锚定披露 → downgrade。"""
    v = check_criterion_origin_honesty("x", **_good(external_anchor_disclosed="no"))
    assert v.action == "downgrade" and v.code == "CRITERION_ORIGIN.NO_EXTERNAL_ANCHOR"
    assert "label-free" in v.message or "外部锚" in v.message


def test_fake_independent_downgrade():
    """自审冒充独立评审 → downgrade。"""
    v = check_criterion_origin_honesty("x", **_good(independent_reviewer_gap_disclosed="no"))
    assert v.action == "downgrade" and v.code == "CRITERION_ORIGIN.FAKE_INDEPENDENT_REVIEW"
    assert "独立评审" in v.message


# --- R5 partial ---
@pytest.mark.parametrize("dim", ["criterion_origin_disclosed", "recall_boundary_disclosed",
                                 "external_anchor_disclosed", "independent_reviewer_gap_disclosed"])
def test_partial_flag(dim):
    """任一维 partial → flag（覆盖不全）。"""
    v = check_criterion_origin_honesty("x", **_good(**{dim: "partial"}))
    assert v.action == "flag" and v.code == "CRITERION_ORIGIN.PARTIAL"


# --- R0 invalid enum ---
@pytest.mark.parametrize("bad", ["maybe", "yes-ish", "true", "", "Y", 1, None])
def test_invalid_enum_flag(bad):
    """非法值（含字面串）→ flag，不进内容判定（R0 / 避 brittle）。"""
    v = check_criterion_origin_honesty("x", **_good(criterion_origin_disclosed=bad))
    assert v.action == "flag" and v.code == "CRITERION_ORIGIN.INVALID_INPUT"


@pytest.mark.parametrize("dim", ["recall_boundary_disclosed", "external_anchor_disclosed",
                                 "independent_reviewer_gap_disclosed"])
def test_invalid_enum_other_dims(dim):
    """非法值出现在其余维同样 flag。"""
    v = check_criterion_origin_honesty("x", **_good(**{dim: "nope"}))
    assert v.action == "flag" and v.code == "CRITERION_ORIGIN.INVALID_INPUT"


def test_chinese_literal_flag():
    """中文字符串字面量 → flag（避 §56 brittle：字面串不进内容判定）。"""
    v = check_criterion_origin_honesty("x", **_good(criterion_origin_disclosed="是"))
    assert v.action == "flag" and v.code == "CRITERION_ORIGIN.INVALID_INPUT"


# --- R6 all good ---
def test_all_good_ok():
    """四维全 yes → ok（只判声明自洽）。"""
    v = check_criterion_origin_honesty("honest self-assessed system", **_good())
    assert v.action == "ok" and v.code == "CRITERION_ORIGIN.SELF_CONSISTENT"


def test_ok_message_mentions_no_guarantee():
    """ok 的消息须声明只判声明、不承诺判据真可靠（诚实边界）。"""
    v = check_criterion_origin_honesty("x", **_good())
    assert "不承诺" in v.message or "可靠性" in v.message or "有效" in v.message


# --- priority ---
def test_priority_origin_before_recall():
    """多 no 时按 R1 优先级短路（origin 先于 recall）。"""
    v = check_criterion_origin_honesty("x", **_good(criterion_origin_disclosed="no",
                                                    recall_boundary_disclosed="no"))
    assert v.code == "CRITERION_ORIGIN.SELF_AS_ANCHOR"


def test_priority_recall_before_anchor():
    """R2 先于 R3（recall 先于 external anchor）。"""
    v = check_criterion_origin_honesty("x", **_good(recall_boundary_disclosed="no",
                                                    external_anchor_disclosed="no"))
    assert v.code == "CRITERION_ORIGIN.RECALL_HIDDEN"


def test_priority_anchor_before_reviewer():
    """R3 先于 R4（external anchor 先于 reviewer gap）。"""
    v = check_criterion_origin_honesty("x", **_good(external_anchor_disclosed="no",
                                                    independent_reviewer_gap_disclosed="no"))
    assert v.code == "CRITERION_ORIGIN.NO_EXTERNAL_ANCHOR"


def test_r0_before_all():
    """R0 非法值优先于所有内容规则。"""
    v = check_criterion_origin_honesty("x", **_good(criterion_origin_disclosed="no",
                                                    recall_boundary_disclosed="maybe"))
    assert v.code == "CRITERION_ORIGIN.INVALID_INPUT"


def test_partial_after_all_no():
    """partial 优先于 ok，但在所有 no 规则之后。"""
    v = check_criterion_origin_honesty("x", **_good(external_anchor_disclosed="partial",
                                                    independent_reviewer_gap_disclosed="no"))
    assert v.code == "CRITERION_ORIGIN.FAKE_INDEPENDENT_REVIEW"


# --- structure / invariants ---
def test_frozen_dataclass():
    """Verdict 不可变（防止判定后被篡改）。"""
    v = check_criterion_origin_honesty("x", **_good())
    with pytest.raises(Exception):
        v.action = "ok"


def test_verdict_fields_reflect_inputs():
    """Verdict 四维字段如实回显输入。"""
    v = check_criterion_origin_honesty("x", **_good(criterion_origin_disclosed="no"))
    assert v.criterion_origin == "no"
    assert v.recall_boundary == "yes"
    assert v.external_anchor == "yes"
    assert v.independent_reviewer_gap == "yes"


def test_claim_preserved():
    """claim 字段保留原样。"""
    v = check_criterion_origin_honesty("HarnessPro-label-free", **_good())
    assert v.claim == "HarnessPro-label-free"


@pytest.mark.parametrize("action", ["ok", "downgrade", "flag"])
def test_action_vocabulary(action):
    """action 取值限定在 ok/downgrade/flag。"""
    inp = _good()
    if action == "downgrade":
        inp["criterion_origin_disclosed"] = "no"
    elif action == "flag":
        inp["recall_boundary_disclosed"] = "partial"
    v = check_criterion_origin_honesty("x", **inp)
    assert v.action == action


def test_empty_claim():
    """claim 为空不影响判定逻辑。"""
    v = check_criterion_origin_honesty("", **_good())
    assert v.action == "ok"


# --- live regression ---
def test_live_regression_all_pass():
    """7 活体样例回归全通过。"""
    r = live_regression()
    assert r["all_passed"] is True
    assert len(r["checks"]) == 7
    assert all(r["checks"].values())


def test_live_regression_codes_present():
    """活体回归覆盖 R0-R6 各码。"""
    r = live_regression()
    outcomes = set(r["cases"].values())
    assert "downgrade/CRITERION_ORIGIN.SELF_AS_ANCHOR" in outcomes
    assert "downgrade/CRITERION_ORIGIN.RECALL_HIDDEN" in outcomes
    assert "downgrade/CRITERION_ORIGIN.NO_EXTERNAL_ANCHOR" in outcomes
    assert "downgrade/CRITERION_ORIGIN.FAKE_INDEPENDENT_REVIEW" in outcomes
    assert "flag/CRITERION_ORIGIN.PARTIAL" in outcomes
    assert "flag/CRITERION_ORIGIN.INVALID_INPUT" in outcomes
    assert "ok/CRITERION_ORIGIN.SELF_CONSISTENT" in outcomes


# --- AST brittle guard ---
def test_no_chinese_literal_in_compare():
    """Compare 节点内禁中文字符串字面量（AST 自审，避 brittle）。"""
    import ast
    import pathlib
    src = pathlib.Path(__import__("svagent").__file__).parent.joinpath("criterion_origin_honesty.py").read_text(encoding="utf-8")
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
        check_criterion_origin_honesty("x", criterion_origin_disclosed="yes")
