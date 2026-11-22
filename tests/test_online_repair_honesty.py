"""在线修复诚实性门禁测试（§81，EvoSteer 在线自演化图编排编译产物）。"""
import pytest

from svagent.online_repair_honesty import (
    check_online_repair_honesty, OnlineRepairVerdict, live_regression,
)
import svagent


def _good(**over):
    base = dict(in_run_edit="yes", rerun_drop="yes",
                execution_feature_driven="yes", ref_grounded_value="yes")
    base.update(over)
    return base


# --- R1-R4 downgrade ---
def test_post_hoc_only_downgrade():
    """只在轨迹之间/批次后修订 → downgrade（§1 post-hoc evolution）。"""
    v = check_online_repair_honesty("x", **_good(in_run_edit="no"))
    assert isinstance(v, OnlineRepairVerdict)
    assert v.action == "downgrade" and v.code == "ONLINE_REPAIR.POST_HOC_ONLY"
    assert "批次" in v.message or "事后" in v.message


def test_no_rerun_drop_downgrade():
    """不能 rerun/drop，只能追加 → downgrade。"""
    v = check_online_repair_honesty("x", **_good(rerun_drop="no"))
    assert v.action == "downgrade" and v.code == "ONLINE_REPAIR.NO_RERUN_DROP"


def test_not_execution_driven_downgrade():
    """编辑非执行特征驱动（仅凭输出表面合理性）→ downgrade。"""
    v = check_online_repair_honesty("x", **_good(execution_feature_driven="no"))
    assert v.action == "downgrade" and v.code == "ONLINE_REPAIR.NOT_EXECUTION_DRIVEN"
    assert "执行特征" in v.message or "合理性" in v.message


def test_ungrounded_value_downgrade():
    """价值估计无参考锚定（混淆任务难度/噪声/结构）→ downgrade（§1 credit diffusion）。"""
    v = check_online_repair_honesty("x", **_good(ref_grounded_value="no"))
    assert v.action == "downgrade" and v.code == "ONLINE_REPAIR.UNGROUNDED_VALUE"


# --- 优先级短路 ---
def test_r1_before_r2():
    v = check_online_repair_honesty("x", **_good(in_run_edit="no", rerun_drop="no"))
    assert v.code == "ONLINE_REPAIR.POST_HOC_ONLY"


def test_r2_before_r3():
    v = check_online_repair_honesty("x", **_good(rerun_drop="no", execution_feature_driven="no"))
    assert v.code == "ONLINE_REPAIR.NO_RERUN_DROP"


def test_r3_before_r4():
    v = check_online_repair_honesty("x", **_good(execution_feature_driven="no", ref_grounded_value="no"))
    assert v.code == "ONLINE_REPAIR.NOT_EXECUTION_DRIVEN"


# --- R5 partial ---
@pytest.mark.parametrize("dim", ["in_run_edit", "rerun_drop",
                                 "execution_feature_driven", "ref_grounded_value"])
def test_partial_flag(dim):
    v = check_online_repair_honesty("x", **_good(**{dim: "partial"}))
    assert v.action == "flag" and v.code == "ONLINE_REPAIR.PARTIAL"


# --- R0 invalid enum ---
@pytest.mark.parametrize("bad", ["maybe", "yes-ish", "true", "", "Y", 1, None])
def test_invalid_enum_flag(bad):
    v = check_online_repair_honesty("x", **_good(in_run_edit=bad))
    assert v.action == "flag" and v.code == "ONLINE_REPAIR.INVALID_INPUT"


# --- R6 ok ---
def test_all_good_ok():
    v = check_online_repair_honesty("x", **_good())
    assert v.action == "ok" and v.code == "ONLINE_REPAIR.SELF_CONSISTENT"
    assert "不承诺" in v.message or "存在≠有效性" in v.message


def test_claim_passthrough():
    v = check_online_repair_honesty("my-orchestrator", **_good())
    assert v.claim == "my-orchestrator"


# --- 惰性导入 / 不接 run_loop ---
def test_lazy_export():
    assert callable(svagent.check_online_repair_honesty)
    assert svagent.OnlineRepairVerdict is OnlineRepairVerdict


def test_not_in_run_loop():
    import inspect
    src = inspect.getsource(svagent.run_loop) if hasattr(svagent, "run_loop") else ""
    assert "online_repair_honesty" not in src


# --- live regression ---
def test_live_regression_all_passed():
    r = live_regression()
    assert r["all_passed"] is True
    assert all(r["checks"].values())


def test_live_regression_cases_count():
    r = live_regression()
    assert len(r["cases"]) == 7
    assert len(r["checks"]) == 7
