"""跨会话状态连续性门禁测试（§65，Building always-on agents 编译产物）。"""
import pytest

from svagent.session_continuity import (
    check_session_continuity, SessionContinuityVerdict, live_regression,
)


def _good(**over):
    base = dict(
        durable_state="yes",
        source_of_truth=True,
        single_consumer=True,
        session_resume="yes",
        nonblocking_defer=True,
    )
    base.update(over)
    return base


def test_no_durable_state_block():
    """声称 always-on 却无跨 run 持久状态 → block。"""
    v = check_session_continuity("always-on agent", **_good(durable_state="no"))
    assert isinstance(v, SessionContinuityVerdict)
    assert v.action == "block" and v.code == "CONTINUITY.NO_DURABLE_STATE"
    assert "持久" in v.message or "durable" in v.message


def test_no_session_resume_downgrade():
    v = check_session_continuity("x", **_good(session_resume="no"))
    assert v.action == "downgrade" and v.code == "CONTINUITY.NO_SESSION_RESUME"


def test_no_source_of_truth_downgrade():
    v = check_session_continuity("x", **_good(source_of_truth=False))
    assert v.action == "downgrade" and v.code == "CONTINUITY.NO_SOURCE_OF_TRUTH"


def test_multi_consumer_downgrade():
    v = check_session_continuity("x", **_good(single_consumer=False))
    assert v.action == "downgrade" and v.code == "CONTINUITY.MULTI_CONSUMER"


def test_blocking_defer_flag():
    v = check_session_continuity("x", **_good(nonblocking_defer=False))
    assert v.action == "flag" and v.code == "CONTINUITY.BLOCKING_DEFER"


def test_partial_durable_flag():
    v = check_session_continuity("x", **_good(durable_state="partial"))
    assert v.action == "flag" and v.code == "CONTINUITY.PARTIAL"


def test_partial_resume_flag():
    v = check_session_continuity("x", **_good(session_resume="partial"))
    assert v.action == "flag" and v.code == "CONTINUITY.PARTIAL"


def test_literal_enum_flag():
    """字面串枚举 → flag，拒绝对字符串内容做判定（避开 brittle 根因）。"""
    v = check_session_continuity("x", **_good(durable_state="maybe"))
    assert v.action == "flag" and v.code == "CONTINUITY.INVALID_ENUM"


def test_literal_resume_enum_flag():
    v = check_session_continuity("x", **_good(session_resume="高度同构"))
    assert v.action == "flag" and v.code == "CONTINUITY.INVALID_ENUM"


def test_non_bool_flag():
    v = check_session_continuity("x", **_good(source_of_truth="true"))
    assert v.action == "flag" and v.code == "CONTINUITY.INVALID_FLAG"


def test_all_good_ok():
    v = check_session_continuity("x", **_good())
    assert v.action == "ok" and v.code == "CONTINUITY.SELF_CONSISTENT"
    assert "不承诺" in v.message or "自洽" in v.message


def test_priority_no_durable_beats_others():
    """R1 优先于 R2/R3：无持久状态时即便其他齐全也 block。"""
    v = check_session_continuity("x", **_good(durable_state="no", session_resume="no", source_of_truth=False))
    assert v.action == "block" and v.code == "CONTINUITY.NO_DURABLE_STATE"


def test_priority_resume_before_source():
    """R2 优先于 R3：会话不可续跑先于真相源缺失。"""
    v = check_session_continuity("x", **_good(session_resume="no", source_of_truth=False))
    assert v.action == "downgrade" and v.code == "CONTINUITY.NO_SESSION_RESUME"


def test_frozen_dataclass():
    v = check_session_continuity("x", **_good())
    with pytest.raises(Exception):
        v.action = "ok"


def test_live_regression():
    r = live_regression()
    assert r["all_passed"] is True
    assert all(r["checks"].values())


def test_lazy_import():
    import svagent
    v = svagent.check_session_continuity("x", **_good())
    assert v.code == "CONTINUITY.SELF_CONSISTENT"
