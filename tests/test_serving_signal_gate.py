"""训练-服务信号可得性门禁测试（§62，HiGR 编译产物）。"""
import pytest

from svagent.serving_signal_gate import (
    check_serving_signal, ServingSignalVerdict, live_regression,
)


def test_higr_undisclosed_gap_downgrade():
    """HiGR 真实例：y+ 依赖 true feedback 排序，服务时不可得、未声明、无桥接 → downgrade。"""
    v = check_serving_signal(
        "HiGR slate preference alignment",
        training_signal_available_at_serving="no",
        gap_disclosed=False, no_bridge=True, serving_input_equivalent=False,
    )
    assert isinstance(v, ServingSignalVerdict)
    assert v.action == "downgrade"
    assert v.code == "SERVING.UNDISCLOSED_GAP"
    assert "口径不对等" in v.message or "不可复现" in v.message


def test_disclosed_no_bridge_flag():
    v = check_serving_signal("x", training_signal_available_at_serving="no",
                             gap_disclosed=True, no_bridge=True, serving_input_equivalent=False)
    assert v.action == "flag" and v.code == "SERVING.DISCLOSED_NO_BRIDGE"


def test_disclosed_with_bridge_ok():
    v = check_serving_signal("x", training_signal_available_at_serving="no",
                             gap_disclosed=True, no_bridge=False, serving_input_equivalent=False)
    assert v.action == "ok" and v.code == "SERVING.BRIDGED"


def test_signal_available_ok():
    v = check_serving_signal("x", training_signal_available_at_serving="yes",
                             gap_disclosed=False, no_bridge=False, serving_input_equivalent=True)
    assert v.action == "ok" and v.code == "SERVING.INVARIANT"


def test_partial_undisclosed_flag():
    v = check_serving_signal("x", training_signal_available_at_serving="partial",
                             gap_disclosed=False, no_bridge=False, serving_input_equivalent=False)
    assert v.action == "flag" and v.code == "SERVING.PROXY_UNDISCLOSED"


@pytest.mark.parametrize("bad", ["高度同构", "同谱系", "NONE", "offline", ""])
def test_literal_string_flag(bad):
    """R0：任何字面串（含中文枚举词）→ flag，不进内容判定（§56 教训）。"""
    v = check_serving_signal("x", training_signal_available_at_serving=bad,
                             gap_disclosed=False, no_bridge=False, serving_input_equivalent=False)
    assert v.action == "flag" and v.code == "SERVING.INVALID_ENUM"


@pytest.mark.parametrize("field", ["gap_disclosed", "no_bridge", "serving_input_equivalent"])
def test_non_bool_flag(field):
    kw = dict(training_signal_available_at_serving="no", gap_disclosed=False,
              no_bridge=True, serving_input_equivalent=False)
    kw[field] = "yes"  # 非 bool
    v = check_serving_signal("x", **kw)
    assert v.action == "flag" and v.code == "SERVING.INVALID_FLAG"


def test_no_bridge_undisclosed_but_bridged_flag():
    """no + 未声明 + 有桥接 → flag（口径未披露），非 downgrade。"""
    v = check_serving_signal("x", training_signal_available_at_serving="no",
                             gap_disclosed=False, no_bridge=False, serving_input_equivalent=False)
    assert v.action == "flag" and v.code == "SERVING.BRIDGE_UNDISCLOSED"


def test_verdict_is_frozen():
    v = check_serving_signal("x", training_signal_available_at_serving="yes",
                             gap_disclosed=False, no_bridge=False, serving_input_equivalent=True)
    with pytest.raises(Exception):
        v.action = "downgrade"


def test_live_regression_all_pass():
    r = live_regression()
    assert r["all_passed"]
    assert len(r["checks"]) == 6 and all(r["checks"].values())


def test_lazy_import():
    import svagent
    assert svagent.check_serving_signal is check_serving_signal
    assert svagent.ServingSignalVerdict is ServingSignalVerdict
