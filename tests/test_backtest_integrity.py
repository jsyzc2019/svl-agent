"""回测信息污染隔离门禁测试：会拦/会判/会降级 + 活体回归 + 优先级。"""
import pytest

from svagent.backtest_integrity import BacktestVerdict, check_backtest_integrity, live_regression

BASE = dict(
    fresh_investigator="yes", original_signal="yes", stripped_giveaway="yes",
    no_saved_memories="yes", no_incident_writeup="yes", no_previous_runs="yes",
    inspect_transcript="yes", separate_timing_deployment="yes",
)


def test_clean_ok():
    v = check_backtest_integrity(**BASE)
    assert v.action == "ok" and v.code == "BACKTEST.CLEAN"


def test_critical_fresh_missing_blocked():
    v = check_backtest_integrity(**{**BASE, "fresh_investigator": "no"})
    assert v.action == "block" and v.code == "BACKTEST.GIVEWAY"
    assert "fresh_investigator" in v.missing_critical


def test_critical_stripped_missing_blocked():
    v = check_backtest_integrity(**{**BASE, "stripped_giveaway": "no"})
    assert v.action == "block"


def test_critical_incident_writeup_missing_blocked():
    v = check_backtest_integrity(**{**BASE, "no_incident_writeup": "no"})
    assert v.action == "block" and "no_incident_writeup" in v.missing_critical


def test_weak_no_saved_memories_downgraded():
    v = check_backtest_integrity(**{**BASE, "no_saved_memories": "no"})
    assert v.action == "downgrade" and v.code == "BACKTEST.PARTIAL_ISOLATION"


def test_weak_separate_scoring_downgraded():
    v = check_backtest_integrity(**{**BASE, "separate_timing_deployment": "no"})
    assert v.action == "downgrade"


def test_spoiler_found_blocked():
    v = check_backtest_integrity(**{**BASE, "spoiler_found": True})
    assert v.action == "block" and v.code == "BACKTEST.SPOILER_FOUND"


def test_undeclared_flagged():
    v = check_backtest_integrity(**{**BASE, "stripped_giveaway": "unknown"})
    assert v.action == "flag" and v.code == "BACKTEST.UNDECLARED"


def test_illegal_state_treated_as_undeclared():
    v = check_backtest_integrity(**{**BASE, "no_previous_runs": "wat"})
    assert v.action == "flag" and "no_previous_runs" in v.undeclared


def test_critical_priority_over_weak():
    v = check_backtest_integrity(**{**BASE, "no_incident_writeup": "no", "no_saved_memories": "no"})
    assert v.code == "BACKTEST.GIVEWAY"  # 关键缺失优先于弱缺失


def test_spoiler_priority_over_critical():
    v = check_backtest_integrity(**{**BASE, "no_incident_writeup": "no", "spoiler_found": True})
    assert v.code == "BACKTEST.SPOILER_FOUND"


def test_pure_and_frozen():
    assert check_backtest_integrity(**BASE) == check_backtest_integrity(**BASE)
    v = check_backtest_integrity(**BASE)
    assert isinstance(v, BacktestVerdict)
    with pytest.raises(Exception):
        v.action = "ok"


def test_live_regression_all_passed():
    r = live_regression()
    assert r["all_passed"] is True
    assert all(r["checks"].values())


def test_live_regression_five_scenarios():
    r = live_regression()
    assert r["clean"]["action"] == "ok"
    assert r["leak"]["action"] == "block"
    assert r["weak"]["action"] == "downgrade"
    assert r["spoiler"]["action"] == "block"
    assert r["undeclared"]["action"] == "flag"
