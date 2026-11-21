"""DeepMind essay 框架论证判据测试。"""
import hashlib
from pathlib import Path

from svagent import agi_essay_analysis as m


def test_e1_subject_disclaimer():
    r = m.run()
    assert r["E1"]["disclaimer_explicit"] is True
    assert "非Google官方" in r["E1"]["decision"]


def test_e2_arithmetic_recomputed():
    r = m.run()
    chk = r["E2"]["arithmetic_recomputed"]
    assert chk["effective_compute_per_year"] == [11.25, 22.5]
    assert chk["cost_after_10y"] == 953.67
    assert chk["at_least_10x"] and chk["cost_approx_1000"]


def test_e2_separates_arithmetic_from_extrapolation():
    r = m.run()
    assert "≠外推成立" in r["E2"]["critical_separation"]


def test_e3_falsifiability_grading():
    r = m.run()
    assert r["E3"]["n_falsifiable"] == 4
    assert r["E3"]["n_narrative"] == 2


def test_e4_contamination():
    r = m.run()
    assert r["E4"]["contamination_declared"] is True
    assert "同谱系" in r["E4"]["decision"]


def test_e5_honesty():
    r = m.run()
    assert "高诚实度" in r["E5"]["decision"]


def test_e6_absorption_no_overbuild():
    r = m.run()
    assert r["E6"]["actionable"] == ["evaluation_scalability"]
    assert r["E6"]["kb_meta01_compliance"] is True


def test_all_fired_and_lock_intact():
    r = m.run()
    assert r["all_judgments_fired"] is True
    root = Path(__file__).resolve().parent.parent
    exp = (root / "agi_essay_prereg.sha256").read_text().split()[0]
    act = hashlib.sha256((root / "agi_essay_preregistration.json").read_bytes()).hexdigest()
    assert exp == act
    assert r["pre_registration_sha256"] == exp
