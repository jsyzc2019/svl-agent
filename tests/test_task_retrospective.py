"""任务复盘门禁回归测试 — 元学习闭环泛化（双源+可证伪+目的约束）。"""
import pytest

from svagent.task_retrospective import (
    KnowledgeCandidate,
    live_regression,
    retrospect,
)


def _good(**kw):
    base = dict(claim="学到X", source="both", predicted="预期P", observed="实测O",
                benefits_user=True, is_restatement=False,
                failure_recorded=True, had_failure=False)
    base.update(kw)
    return KnowledgeCandidate(**base)


# ---- G3 复述冒充 ----
def test_restatement_blocked():
    r = retrospect(_good(is_restatement=True))
    assert r.action == "block" and r.code == "RETRO.RESTATEMENT"
    assert r.classified_as == "vanity"


def test_restatement_beats_no_user_value():
    # 复述 + 无价值，应先命中复述（优先级）
    r = retrospect(_good(is_restatement=True, benefits_user=False))
    assert r.code == "RETRO.RESTATEMENT"


# ---- G4 目的约束 ----
def test_no_user_value_flagged():
    r = retrospect(_good(benefits_user=False))
    assert r.action == "flag" and r.code == "RETRO.NO_USER_VALUE"
    assert r.classified_as == "observe"


# ---- G1 双源 ----
def test_single_source_downgraded():
    r = retrospect(_good(source="task_content"))
    assert r.action == "downgrade" and r.code == "RETRO.SINGLE_SOURCE"


def test_process_source_ok():
    r = retrospect(_good(source="process"))
    assert r.action == "ok" and r.classified_as == "fix"


def test_bad_source_flagged():
    r = retrospect(_good(source="unknown"))
    assert r.action == "flag" and r.code == "RETRO.BAD_SOURCE"


# ---- G2 可证伪 ----
def test_unfalsifiable_no_predicted_downgraded():
    r = retrospect(_good(predicted=""))
    assert r.action == "downgrade" and r.code == "RETRO.UNFALSIFIABLE"


def test_unfalsifiable_no_observed_downgraded():
    r = retrospect(_good(observed=""))
    assert r.code == "RETRO.UNFALSIFIABLE"


# ---- G5 失败未记 ----
def test_failure_unrecorded_downgraded():
    r = retrospect(_good(had_failure=True, failure_recorded=False))
    assert r.action == "downgrade" and r.code == "RETRO.FAILURE_UNRECORDED"


def test_failure_recorded_ok():
    r = retrospect(_good(had_failure=True, failure_recorded=True))
    assert r.action == "ok"


# ---- PASS + 优先级 ----
def test_good_candidate_ok():
    r = retrospect(_good())
    assert r.action == "ok" and r.code == "RETRO.OK" and r.classified_as == "fix"


def test_priority_unfalsifiable_before_failure():
    # 不可证伪 + 失败未记，应先命中不可证伪
    r = retrospect(_good(predicted="", had_failure=True, failure_recorded=False))
    assert r.code == "RETRO.UNFALSIFIABLE"


# ---- 活体回归 + 惰性导入 ----
def test_live_regression_all_passed():
    r = live_regression()
    assert r["all_passed"], r
    assert r["dual_source"]["action"] == "ok"
    assert r["process"]["action"] == "ok"
    assert r["restatement"]["action"] == "block"
    assert r["single_source"]["action"] == "downgrade"


def test_lazy_import_registered():
    import svagent
    assert "retrospect" in svagent.__all__
    assert "KnowledgeCandidate" in svagent.__all__
