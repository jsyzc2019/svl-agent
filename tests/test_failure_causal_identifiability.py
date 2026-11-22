"""失败因果可识别性门禁测试（§83，MLLM 因果任务分解编译产物）。"""
import pytest

from svagent.failure_causal_identifiability import (
    check_failure_causal_identifiability, FailureCausalVerdict, live_regression,
)
import svagent


def _good(**over):
    base = dict(end_to_end_only="no", trace_or_cooccurrence="no",
                controlled_intervention="yes", upstream_vs_intrinsic_split="yes")
    base.update(over)
    return base


# --- R1-R4 downgrade ---
def test_end_to_end_only_downgrade():
    """只有聚合端到端准确率 → downgrade（§1 records how often not where）。"""
    v = check_failure_causal_identifiability("x", **_good(end_to_end_only="yes"))
    assert isinstance(v, FailureCausalVerdict)
    assert v.action == "downgrade" and v.code == "FAILURE_CAUSAL.END_TO_END_ONLY"


def test_trace_cooccurrence_downgrade():
    """仅凭 trace/子问题共现归因 → downgrade（§2）。"""
    v = check_failure_causal_identifiability("x", **_good(trace_or_cooccurrence="yes"))
    assert v.action == "downgrade" and v.code == "FAILURE_CAUSAL.TRACE_COOCCURRENCE"
    assert "trace" in v.message or "共现" in v.message


def test_no_intervention_downgrade():
    """无受控干预（未设前提为已知正确/错误）→ downgrade。"""
    v = check_failure_causal_identifiability("x", **_good(controlled_intervention="no"))
    assert v.action == "downgrade" and v.code == "FAILURE_CAUSAL.NO_INTERVENTION"


def test_no_split_downgrade():
    """未区分上游级联与内在缺陷 → downgrade（§1 opposite diagnoses）。"""
    v = check_failure_causal_identifiability("x", **_good(upstream_vs_intrinsic_split="no"))
    assert v.action == "downgrade" and v.code == "FAILURE_CAUSAL.NO_SPLIT"


# --- 优先级短路 ---
def test_r1_before_r2():
    v = check_failure_causal_identifiability("x", **_good(end_to_end_only="yes", trace_or_cooccurrence="yes"))
    assert v.code == "FAILURE_CAUSAL.END_TO_END_ONLY"


def test_r2_before_r3():
    v = check_failure_causal_identifiability("x", **_good(trace_or_cooccurrence="yes", controlled_intervention="no"))
    assert v.code == "FAILURE_CAUSAL.TRACE_COOCCURRENCE"


def test_r3_before_r4():
    v = check_failure_causal_identifiability("x", **_good(controlled_intervention="no", upstream_vs_intrinsic_split="no"))
    assert v.code == "FAILURE_CAUSAL.NO_INTERVENTION"


# --- R5 partial ---
@pytest.mark.parametrize("dim", ["end_to_end_only", "trace_or_cooccurrence",
                                 "controlled_intervention", "upstream_vs_intrinsic_split"])
def test_partial_flag(dim):
    v = check_failure_causal_identifiability("x", **_good(**{dim: "partial"}))
    assert v.action == "flag" and v.code == "FAILURE_CAUSAL.PARTIAL"


# --- R0 invalid enum ---
@pytest.mark.parametrize("bad", ["maybe", "yes-ish", "true", "", "Y", 1, None])
def test_invalid_enum_flag(bad):
    v = check_failure_causal_identifiability("x", **_good(end_to_end_only=bad))
    assert v.action == "flag" and v.code == "FAILURE_CAUSAL.INVALID_INPUT"


# --- R6 ok（否定语义取反后全自洽） ---
def test_all_good_ok():
    v = check_failure_causal_identifiability("x", **_good())
    assert v.action == "ok" and v.code == "FAILURE_CAUSAL.SELF_CONSISTENT"
    assert "不承诺" in v.message or "存在≠有效性" in v.message


def test_both_defects_present_still_downgrade():
    """两否定维都 no、两能力维都 yes 才 ok；缺 controlled_intervention 即使无缺陷也降。"""
    v = check_failure_causal_identifiability("x", **_good(controlled_intervention="no", upstream_vs_intrinsic_split="no"))
    assert v.action == "downgrade"  # R3 先命中


def test_claim_passthrough():
    v = check_failure_causal_identifiability("my-diagnoser", **_good())
    assert v.claim == "my-diagnoser"


# --- 惰性导入 / 不接 run_loop ---
def test_lazy_export():
    assert callable(svagent.check_failure_causal_identifiability)
    assert svagent.FailureCausalVerdict is FailureCausalVerdict


def test_not_in_run_loop():
    import inspect
    src = inspect.getsource(svagent.run_loop) if hasattr(svagent, "run_loop") else ""
    assert "failure_causal_identifiability" not in src


# --- live regression ---
def test_live_regression_all_passed():
    r = live_regression()
    assert r["all_passed"] is True
    assert all(r["checks"].values())


def test_live_regression_cases_count():
    r = live_regression()
    assert len(r["cases"]) == 7
    assert len(r["checks"]) == 7
