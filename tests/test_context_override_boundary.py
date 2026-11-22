"""结构覆盖边界诚实性门禁测试（§88，Latent Taxonomies context覆盖weights 编译产物）。"""
import pytest

from svagent.context_override_boundary import (
    check_context_override_boundary, ContextOverrideVerdict, live_regression,
)
import svagent


def _good(**over):
    base = dict(inweights_incontext_split="yes", override_disclosed="yes",
                conflict_tested="yes", steerability_bound_stated="yes")
    base.update(over)
    return base


def test_no_split_downgrade():
    v = check_context_override_boundary("x", **_good(inweights_incontext_split="no"))
    assert isinstance(v, ContextOverrideVerdict)
    assert v.action == "downgrade" and v.code == "CONTEXT_OVERRIDE.NO_SPLIT"


def test_override_hidden_downgrade():
    v = check_context_override_boundary("x", **_good(override_disclosed="no"))
    assert v.action == "downgrade" and v.code == "CONTEXT_OVERRIDE.OVERRIDE_HIDDEN"
    assert "上下文" in v.message or "权重" in v.message


def test_no_conflict_test_downgrade():
    v = check_context_override_boundary("x", **_good(conflict_tested="no"))
    assert v.action == "downgrade" and v.code == "CONTEXT_OVERRIDE.NO_CONFLICT_TEST"


def test_no_bound_downgrade():
    v = check_context_override_boundary("x", **_good(steerability_bound_stated="no"))
    assert v.action == "downgrade" and v.code == "CONTEXT_OVERRIDE.NO_BOUND"


def test_r1_before_r2():
    v = check_context_override_boundary("x", **_good(inweights_incontext_split="no", override_disclosed="no"))
    assert v.code == "CONTEXT_OVERRIDE.NO_SPLIT"


def test_r2_before_r3():
    v = check_context_override_boundary("x", **_good(override_disclosed="no", conflict_tested="no"))
    assert v.code == "CONTEXT_OVERRIDE.OVERRIDE_HIDDEN"


def test_r3_before_r4():
    v = check_context_override_boundary("x", **_good(conflict_tested="no", steerability_bound_stated="no"))
    assert v.code == "CONTEXT_OVERRIDE.NO_CONFLICT_TEST"


@pytest.mark.parametrize("dim", ["inweights_incontext_split", "override_disclosed",
                                 "conflict_tested", "steerability_bound_stated"])
def test_partial_flag(dim):
    v = check_context_override_boundary("x", **_good(**{dim: "partial"}))
    assert v.action == "flag" and v.code == "CONTEXT_OVERRIDE.PARTIAL"


@pytest.mark.parametrize("bad", ["maybe", "yes-ish", "true", "", "Y", 1, None])
def test_invalid_enum_flag(bad):
    v = check_context_override_boundary("x", **_good(inweights_incontext_split=bad))
    assert v.action == "flag" and v.code == "CONTEXT_OVERRIDE.INVALID_INPUT"


def test_all_good_ok():
    v = check_context_override_boundary("x", **_good())
    assert v.action == "ok" and v.code == "CONTEXT_OVERRIDE.SELF_CONSISTENT"
    assert "不承诺" in v.message or "存在≠有效性" in v.message


def test_claim_passthrough():
    v = check_context_override_boundary("my-lm", **_good())
    assert v.claim == "my-lm"


def test_lazy_export():
    assert callable(svagent.check_context_override_boundary)
    assert svagent.ContextOverrideVerdict is ContextOverrideVerdict


def test_not_in_run_loop():
    import inspect
    src = inspect.getsource(svagent.run_loop) if hasattr(svagent, "run_loop") else ""
    assert "context_override_boundary" not in src


def test_live_regression_all_passed():
    r = live_regression()
    assert r["all_passed"] is True
    assert all(r["checks"].values())


def test_live_regression_cases_count():
    r = live_regression()
    assert len(r["cases"]) == 7
    assert len(r["checks"]) == 7
