"""SIM/CRSI 框架论证判据固化测试。"""
import hashlib
import json
from pathlib import Path

from svagent.sim_framework_analysis import run_all, ROOT, _welch_t_paired, _leave_one_out


def test_prereg_sha256_lock():
    exp = (ROOT / "sim_prereg.sha256").read_text().split()[0]
    act = hashlib.sha256((ROOT / "sim_preregistration.json").read_bytes()).hexdigest()
    assert act == exp


def test_paper_downloaded_and_text_extracted():
    assert (ROOT / "rsi_sim_paper.pdf").stat().st_size > 100_000
    txt = (ROOT / "rsi_sim_paper.txt").read_text(encoding="utf-8", errors="ignore")
    assert "2611.18856" in txt and "Self-Improvement Memory" in txt


def test_statistics_reproduce_paper():
    r = run_all()
    assert r["S3"]["reproduces_reported"] is True
    assert abs(r["S3"]["recomputed"]["t"] - 4.06) < 0.3
    assert abs(r["S3"]["recomputed"]["mean"] - 2.36) < 0.05


def test_leave_one_out_robust():
    r = run_all()
    loo = r["S3"]["leave_one_out"]
    assert loo["drop_max"]["still_positive"]
    assert loo["drop_2nd_max"]["still_positive"]
    assert loo["all_positive_direction_count"] == 9


def test_subject_mismatch_and_ladder():
    """主体错位 + L3未证明：核心的触发≠真相判据。"""
    r = run_all()
    assert r["S1"]["subject_mismatch"] is True
    assert r["S2"]["L3_improver_gain_proven"] is False
    assert r["S2"]["optimization_procedure_fixed"] is True
    assert r["S4"]["memory_causal_contribution_isolated"] is False


def test_source_isolation_and_correction():
    r = run_all()
    assert "未交叉背书" in r["_meta"]["source_isolation"]
    assert "误判RSI" in r["_meta"]["correction"]


def test_welch_helpers_math():
    st = _welch_t_paired([1.0, 2.0, 3.0, 4.0])
    assert abs(st["mean"] - 2.5) < 1e-9
    # 样本方差=5/3, sd≈1.291, se≈0.6455, t≈3.873（非10；首版注释误把se当0.25）
    assert abs(st["t"] - 3.873) < 1e-2
    loo = _leave_one_out([1.0, 2.0, 100.0])
    assert loo["drop_max"]["mean"] == 1.5
