"""计算饱和诚实性门禁测试（§86，UltraBERT loss≠下游编译产物）。"""
import pytest

from svagent.compute_saturation_honesty import (
    check_compute_saturation_honesty, ComputeSaturationVerdict, live_regression,
)
import svagent


def _good(**over):
    base = dict(saturation_reported="yes", loss_vs_downstream_split="yes",
                marginal_gain_measured="yes", no_loss_as_capability="yes")
    base.update(over)
    return base


def test_no_saturation_downgrade():
    v = check_compute_saturation_honesty("x", **_good(saturation_reported="no"))
    assert isinstance(v, ComputeSaturationVerdict)
    assert v.action == "downgrade" and v.code == "COMPUTE_SAT.NO_SATURATION"


def test_no_split_downgrade():
    v = check_compute_saturation_honesty("x", **_good(loss_vs_downstream_split="no"))
    assert v.action == "downgrade" and v.code == "COMPUTE_SAT.NO_SPLIT"
    assert "loss" in v.message or "下游" in v.message


def test_no_marginal_downgrade():
    v = check_compute_saturation_honesty("x", **_good(marginal_gain_measured="no"))
    assert v.action == "downgrade" and v.code == "COMPUTE_SAT.NO_MARGINAL"


def test_loss_as_capability_downgrade():
    v = check_compute_saturation_honesty("x", **_good(no_loss_as_capability="no"))
    assert v.action == "downgrade" and v.code == "COMPUTE_SAT.LOSS_AS_CAPABILITY"


def test_r1_before_r2():
    v = check_compute_saturation_honesty("x", **_good(saturation_reported="no", loss_vs_downstream_split="no"))
    assert v.code == "COMPUTE_SAT.NO_SATURATION"


def test_r2_before_r3():
    v = check_compute_saturation_honesty("x", **_good(loss_vs_downstream_split="no", marginal_gain_measured="no"))
    assert v.code == "COMPUTE_SAT.NO_SPLIT"


def test_r3_before_r4():
    v = check_compute_saturation_honesty("x", **_good(marginal_gain_measured="no", no_loss_as_capability="no"))
    assert v.code == "COMPUTE_SAT.NO_MARGINAL"


@pytest.mark.parametrize("dim", ["saturation_reported", "loss_vs_downstream_split",
                                 "marginal_gain_measured", "no_loss_as_capability"])
def test_partial_flag(dim):
    v = check_compute_saturation_honesty("x", **_good(**{dim: "partial"}))
    assert v.action == "flag" and v.code == "COMPUTE_SAT.PARTIAL"


@pytest.mark.parametrize("bad", ["maybe", "yes-ish", "true", "", "Y", 1, None])
def test_invalid_enum_flag(bad):
    v = check_compute_saturation_honesty("x", **_good(saturation_reported=bad))
    assert v.action == "flag" and v.code == "COMPUTE_SAT.INVALID_INPUT"


def test_all_good_ok():
    v = check_compute_saturation_honesty("x", **_good())
    assert v.action == "ok" and v.code == "COMPUTE_SAT.SELF_CONSISTENT"
    assert "不承诺" in v.message or "存在≠有效性" in v.message


def test_claim_passthrough():
    v = check_compute_saturation_honesty("my-scale", **_good())
    assert v.claim == "my-scale"


def test_lazy_export():
    assert callable(svagent.check_compute_saturation_honesty)
    assert svagent.ComputeSaturationVerdict is ComputeSaturationVerdict


def test_not_in_run_loop():
    import inspect
    src = inspect.getsource(svagent.run_loop) if hasattr(svagent, "run_loop") else ""
    assert "compute_saturation_honesty" not in src


def test_live_regression_all_passed():
    r = live_regression()
    assert r["all_passed"] is True
    assert all(r["checks"].values())


def test_live_regression_cases_count():
    r = live_regression()
    assert len(r["cases"]) == 7
    assert len(r["checks"]) == 7
