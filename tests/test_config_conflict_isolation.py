"""配置冲突隔离门禁测试（§85，UltraBERT 配置冲突编译产物）。"""
import pytest

from svagent.config_conflict_isolation import (
    check_config_conflict_isolation, ConfigConflictVerdict, live_regression,
)
import svagent


def _good(**over):
    base = dict(conflict_identified="yes", mechanism_isolation="yes",
                de_confounded_comparison="yes", no_blanket_tradeoff="yes")
    base.update(over)
    return base


def test_conflict_hidden_downgrade():
    v = check_config_conflict_isolation("x", **_good(conflict_identified="no"))
    assert isinstance(v, ConfigConflictVerdict)
    assert v.action == "downgrade" and v.code == "CONFIG_CONFLICT.CONFLICT_HIDDEN"


def test_no_isolation_downgrade():
    v = check_config_conflict_isolation("x", **_good(mechanism_isolation="no"))
    assert v.action == "downgrade" and v.code == "CONFIG_CONFLICT.NO_ISOLATION"


def test_confoounded_downgrade():
    v = check_config_conflict_isolation("x", **_good(de_confounded_comparison="no"))
    assert v.action == "downgrade" and v.code == "CONFIG_CONFLICT.CONFOUNDED"
    assert "收敛" in v.message or "饱和" in v.message


def test_blanket_downgrade():
    v = check_config_conflict_isolation("x", **_good(no_blanket_tradeoff="no"))
    assert v.action == "downgrade" and v.code == "CONFIG_CONFLICT.BLANKET_TRADEOFF"


def test_r1_before_r2():
    v = check_config_conflict_isolation("x", **_good(conflict_identified="no", mechanism_isolation="no"))
    assert v.code == "CONFIG_CONFLICT.CONFLICT_HIDDEN"


def test_r2_before_r3():
    v = check_config_conflict_isolation("x", **_good(mechanism_isolation="no", de_confounded_comparison="no"))
    assert v.code == "CONFIG_CONFLICT.NO_ISOLATION"


def test_r3_before_r4():
    v = check_config_conflict_isolation("x", **_good(de_confounded_comparison="no", no_blanket_tradeoff="no"))
    assert v.code == "CONFIG_CONFLICT.CONFOUNDED"


@pytest.mark.parametrize("dim", ["conflict_identified", "mechanism_isolation",
                                 "de_confounded_comparison", "no_blanket_tradeoff"])
def test_partial_flag(dim):
    v = check_config_conflict_isolation("x", **_good(**{dim: "partial"}))
    assert v.action == "flag" and v.code == "CONFIG_CONFLICT.PARTIAL"


@pytest.mark.parametrize("bad", ["maybe", "yes-ish", "true", "", "Y", 1, None])
def test_invalid_enum_flag(bad):
    v = check_config_conflict_isolation("x", **_good(conflict_identified=bad))
    assert v.action == "flag" and v.code == "CONFIG_CONFLICT.INVALID_INPUT"


def test_all_good_ok():
    v = check_config_conflict_isolation("x", **_good())
    assert v.action == "ok" and v.code == "CONFIG_CONFLICT.SELF_CONSISTENT"
    assert "不承诺" in v.message or "存在≠有效性" in v.message


def test_claim_passthrough():
    v = check_config_conflict_isolation("my-encoder", **_good())
    assert v.claim == "my-encoder"


def test_lazy_export():
    assert callable(svagent.check_config_conflict_isolation)
    assert svagent.ConfigConflictVerdict is ConfigConflictVerdict


def test_not_in_run_loop():
    import inspect
    src = inspect.getsource(svagent.run_loop) if hasattr(svagent, "run_loop") else ""
    assert "config_conflict_isolation" not in src


def test_live_regression_all_passed():
    r = live_regression()
    assert r["all_passed"] is True
    assert all(r["checks"].values())


def test_live_regression_cases_count():
    r = live_regression()
    assert len(r["cases"]) == 7
    assert len(r["checks"]) == 7
