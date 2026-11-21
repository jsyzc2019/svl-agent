"""RSI-Structure 框架论证判据测试。"""
import json
from pathlib import Path

import pytest

from svagent import rsis_framework_analysis as m


def test_paper_is_survey_t1():
    ev = m.load_evidence()
    t = m.t1_subject_misplacement(ev)
    assert t["survey_not_empirical"] is True
    assert t["paper_self_limited"] is True
    assert "主体错位" in t["decision"]
    assert t["pass"] is True


def test_contamination_t2():
    ev = m.load_evidence()
    t = m.t2_isomorphism_contamination(ev)
    assert t["contaminated"] is True
    assert "同谱系" in t["decision"]
    assert t["pass"] is True


def test_criterion_fit_t3_no_stat_recompute():
    ev = m.load_evidence()
    t = m.t3_criterion_fit(ev)
    assert t["statistical_recompute_applicable"] is False
    assert t["counts_are_classification_not_samples"] is True
    assert t["pass"] is True


def test_counterparts_t4_gaps():
    t = m.t4_counterparts()
    assert t["n_already"] == 4
    assert t["n_gaps"] == 2
    assert "V3_failure_not_what_to_edit" in t["gap_ids"]
    assert "V6_retirement_cover_rare" in t["gap_ids"]
    assert t["pass"] is True


def test_honesty_t5():
    ev = m.load_evidence()
    t = m.t5_honesty(ev)
    assert t["decision"] == "高诚实度（preserve）"
    assert t["pass"] is True


def test_absorption_t6_teeth():
    t4 = m.t4_counterparts()
    t = m.t6_absorption(t4)
    assert len(t["actionable_ids"]) == 2
    assert t["kb_meta01_compliance"] is True
    assert "编译" in t["decision"]
    assert t["pass"] is True


def test_three_layer_conclusion_has_all_layers():
    r = m.run()
    c = r["conclusion"]
    assert all(k in c for k in ("layer1_fact", "layer2_boundary", "layer3_method"))
    assert "同谱系" in c["layer2_boundary"]
    assert "KB-META01" in c["layer3_method"]


def test_all_judgments_fired_and_lock_intact():
    r = m.run()
    assert r["all_judgments_fired"] is True
    # 预注册锁存未被改动
    import hashlib
    root = Path(__file__).resolve().parent.parent
    exp = (root / "rsi_structure_prereg.sha256").read_text().split()[0]
    act = hashlib.sha256((root / "rsi_structure_preregistration.json").read_bytes()).hexdigest()
    assert exp == act
    assert r["pre_registration_sha256"] == exp
