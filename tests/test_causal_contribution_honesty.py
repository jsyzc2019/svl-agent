"""因果贡献诚实性门禁测试（§84，MLLM N-Score/S-Score 编译产物）。"""
import pytest

from svagent.causal_contribution_honesty import (
    check_causal_contribution_honesty, CausalContributionVerdict, live_regression,
)
import svagent


def _good(**over):
    base = dict(necessity_sufficiency_split="yes", lower_bound_labeled="yes",
                monotonicity_disclosed="yes", bottleneck_sparsity_reported="yes")
    base.update(over)
    return base


# --- R1-R4 downgrade ---
def test_no_ns_split_downgrade():
    """未区分必要性与充分性 → downgrade（§3.4）。"""
    v = check_causal_contribution_honesty("x", **_good(necessity_sufficiency_split="no"))
    assert isinstance(v, CausalContributionVerdict)
    assert v.action == "downgrade" and v.code == "CAUSAL_CONTRIB.NO_NS_SPLIT"


def test_bound_as_exact_downgrade():
    """把下界当精确 PN/PS → downgrade（Theorem 3.9）。"""
    v = check_causal_contribution_honesty("x", **_good(lower_bound_labeled="no"))
    assert v.action == "downgrade" and v.code == "CAUSAL_CONTRIB.BOUND_AS_EXACT"
    assert "下界" in v.message or "精确" in v.message


def test_monotonicity_hidden_downgrade():
    """未披露单调性假设 → downgrade（Property 3.6）。"""
    v = check_causal_contribution_honesty("x", **_good(monotonicity_disclosed="no"))
    assert v.action == "downgrade" and v.code == "CAUSAL_CONTRIB.MONOTONICITY_HIDDEN"


def test_no_sparsity_downgrade():
    """未报告瓶颈稀疏性 → downgrade（single prerequisite captures 84% gain）。"""
    v = check_causal_contribution_honesty("x", **_good(bottleneck_sparsity_reported="no"))
    assert v.action == "downgrade" and v.code == "CAUSAL_CONTRIB.NO_SPARSITY"


# --- 优先级短路 ---
def test_r1_before_r2():
    v = check_causal_contribution_honesty("x", **_good(necessity_sufficiency_split="no", lower_bound_labeled="no"))
    assert v.code == "CAUSAL_CONTRIB.NO_NS_SPLIT"


def test_r2_before_r3():
    v = check_causal_contribution_honesty("x", **_good(lower_bound_labeled="no", monotonicity_disclosed="no"))
    assert v.code == "CAUSAL_CONTRIB.BOUND_AS_EXACT"


def test_r3_before_r4():
    v = check_causal_contribution_honesty("x", **_good(monotonicity_disclosed="no", bottleneck_sparsity_reported="no"))
    assert v.code == "CAUSAL_CONTRIB.MONOTONICITY_HIDDEN"


# --- R5 partial ---
@pytest.mark.parametrize("dim", ["necessity_sufficiency_split", "lower_bound_labeled",
                                 "monotonicity_disclosed", "bottleneck_sparsity_reported"])
def test_partial_flag(dim):
    v = check_causal_contribution_honesty("x", **_good(**{dim: "partial"}))
    assert v.action == "flag" and v.code == "CAUSAL_CONTRIB.PARTIAL"


# --- R0 invalid enum ---
@pytest.mark.parametrize("bad", ["maybe", "yes-ish", "true", "", "Y", 1, None])
def test_invalid_enum_flag(bad):
    v = check_causal_contribution_honesty("x", **_good(necessity_sufficiency_split=bad))
    assert v.action == "flag" and v.code == "CAUSAL_CONTRIB.INVALID_INPUT"


# --- R6 ok ---
def test_all_good_ok():
    v = check_causal_contribution_honesty("x", **_good())
    assert v.action == "ok" and v.code == "CAUSAL_CONTRIB.SELF_CONSISTENT"
    assert "不承诺" in v.message or "存在≠有效性" in v.message


def test_claim_passthrough():
    v = check_causal_contribution_honesty("my-attributor", **_good())
    assert v.claim == "my-attributor"


# --- 惰性导入 / 不接 run_loop ---
def test_lazy_export():
    assert callable(svagent.check_causal_contribution_honesty)
    assert svagent.CausalContributionVerdict is CausalContributionVerdict


def test_not_in_run_loop():
    import inspect
    src = inspect.getsource(svagent.run_loop) if hasattr(svagent, "run_loop") else ""
    assert "causal_contribution_honesty" not in src


# --- live regression ---
def test_live_regression_all_passed():
    r = live_regression()
    assert r["all_passed"] is True
    assert all(r["checks"].values())


def test_live_regression_cases_count():
    r = live_regression()
    assert len(r["cases"]) == 7
    assert len(r["checks"]) == 7
