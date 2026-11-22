"""可证明声明边界诚实性门禁测试（§71，FlashProve 编译产物）。"""
import pytest

from svagent.proof_boundary_honesty import (
    check_proof_boundary_honesty, ProofBoundaryVerdict, live_regression,
)


def _good(**over):
    base = dict(proves_execution_not_fact="yes", commitment_anchor_independent="yes",
                formal_scope_disclosed="yes", uncovered_disclosed="yes")
    base.update(over)
    return base


def test_source_as_fact_downgrade():
    """把来源证明冒充事实正确 → downgrade（主体错位 KB-STRUCT05）。"""
    v = check_proof_boundary_honesty("source as fact", **_good(proves_execution_not_fact="no"))
    assert isinstance(v, ProofBoundaryVerdict)
    assert v.action == "downgrade" and v.code == "PROOF_BOUNDARY.SOURCE_AS_FACT"
    assert "事实" in v.message or "主体错位" in v.message


def test_anchor_self_set_downgrade():
    """信任根由被验证方自定 → downgrade（证明自说自话）。"""
    v = check_proof_boundary_honesty("x", **_good(commitment_anchor_independent="no"))
    assert v.action == "downgrade" and v.code == "PROOF_BOUNDARY.ANCHOR_SELF_SET"


def test_formal_overclaim_downgrade():
    """形式化无边界 → downgrade（协议证明读成全栈正确）。"""
    v = check_proof_boundary_honesty("x", **_good(formal_scope_disclosed="no"))
    assert v.action == "downgrade" and v.code == "PROOF_BOUNDARY.FORMAL_OVERCLAIM"


def test_uncovered_hidden_flag():
    """未覆盖项不披露 → flag（过度宣称）。"""
    v = check_proof_boundary_honesty("x", **_good(uncovered_disclosed="no"))
    assert v.action == "flag" and v.code == "PROOF_BOUNDARY.UNCOVERED_HIDDEN"


@pytest.mark.parametrize("dim", ["proves_execution_not_fact", "commitment_anchor_independent",
                                 "formal_scope_disclosed", "uncovered_disclosed"])
def test_partial_flag(dim):
    """任一维 partial → flag（覆盖不全）。"""
    v = check_proof_boundary_honesty("x", **_good(**{dim: "partial"}))
    assert v.action == "flag" and v.code == "PROOF_BOUNDARY.PARTIAL"


@pytest.mark.parametrize("bad", ["maybe", "yes-ish", "true", "", "Y", 1, None])
def test_invalid_enum_flag(bad):
    """非法值（含字面串）→ flag，不进内容判定（R0 / 避 brittle）。"""
    v = check_proof_boundary_honesty("x", **_good(proves_execution_not_fact=bad))
    assert v.action == "flag" and v.code == "PROOF_BOUNDARY.INVALID_INPUT"


def test_all_good_ok():
    """四维全 yes → ok（只判声明自洽）。"""
    v = check_proof_boundary_honesty("honest system", **_good())
    assert v.action == "ok" and v.code == "PROOF_BOUNDARY.SELF_CONSISTENT"
    assert "不承诺" in v.message or "有效性" in v.message


def test_ok_message_mentions_no_guarantee():
    """ok 的消息须声明只判边界、不承诺证明正确（诚实边界）。"""
    v = check_proof_boundary_honesty("x", **_good())
    assert "证明正确" in v.message or "系统有效" in v.message


def test_priority_source_before_anchor():
    """多 no 时按 R1 优先级短路（source_as_fact 先于 anchor）。"""
    v = check_proof_boundary_honesty("x", **_good(proves_execution_not_fact="no",
                                                  commitment_anchor_independent="no"))
    assert v.code == "PROOF_BOUNDARY.SOURCE_AS_FACT"


def test_priority_formal_before_uncovered():
    """R3 先于 R4（formal 先于 uncovered）。"""
    v = check_proof_boundary_honesty("x", **_good(formal_scope_disclosed="no",
                                                  uncovered_disclosed="no"))
    assert v.code == "PROOF_BOUNDARY.FORMAL_OVERCLAIM"


def test_frozen_dataclass():
    """Verdict 不可变（防止判定后被篡改）。"""
    v = check_proof_boundary_honesty("x", **_good())
    with pytest.raises(Exception):
        v.action = "ok"


def test_claim_preserved():
    """claim 原样保留在 verdict 中（可追溯）。"""
    v = check_proof_boundary_honesty("trace-me", **_good())
    assert v.claim == "trace-me"


def test_live_regression():
    """7 个活体样例全过（对齐 gate_prereg.json）。"""
    r = live_regression()
    assert r["all_passed"], r["cases"]
    assert len(r["cases"]) == 7


def test_live_cases_exact_codes():
    """活体回归逐案精确 code。"""
    r = live_regression()
    assert r["cases"]["source_as_fact"] == "downgrade/PROOF_BOUNDARY.SOURCE_AS_FACT"
    assert r["cases"]["all_good"] == "ok/PROOF_BOUNDARY.SELF_CONSISTENT"


def test_keyword_only():
    """四维必须为 keyword-only（防位置错配）。"""
    with pytest.raises(TypeError):
        check_proof_boundary_honesty("x", "yes", "yes", "yes", "yes")


def test_lazy_export():
    """惰性导出可从 svagent 顶层访问。"""
    import svagent
    assert svagent.check_proof_boundary_honesty is check_proof_boundary_honesty
