"""FJ 三道试点取证法官测试（阶段2：读原文取证 → 原 check_* 裁决 → 溯源）。"""
import pytest

from svagent.forensic_gates import (
    adjudicate_criterion_origin_honesty,
    adjudicate_verification_boundary_honesty,
    adjudicate_proof_boundary_honesty,
    adjudicate_all, default_sources, live_regression,
)
from svagent.criterion_origin_honesty import CriterionOriginVerdict
from svagent.verification_boundary_honesty import VerificationBoundaryVerdict
from svagent.proof_boundary_honesty import ProofBoundaryVerdict


# --- 真实证据：诚实论文 → ok，与原精研结论一致 ---
def test_criterion_real_evidence_ok():
    v, tr = adjudicate_criterion_origin_honesty()
    assert isinstance(v, CriterionOriginVerdict)
    assert v.action == "ok" and v.code == "CRITERION_ORIGIN.SELF_CONSISTENT"
    assert all(x == "yes" for x in tr["inferred"].values())
    assert tr["mode"] == "forensic" and len(tr["sources"]) == 2


def test_verification_real_evidence_ok():
    v, tr = adjudicate_verification_boundary_honesty()
    assert isinstance(v, VerificationBoundaryVerdict)
    assert v.action == "ok"
    assert all(x == "yes" for x in tr["inferred"].values())


def test_proof_real_evidence_ok():
    v, tr = adjudicate_proof_boundary_honesty()
    assert isinstance(v, ProofBoundaryVerdict)
    assert v.action == "ok"
    assert all(x == "yes" for x in tr["inferred"].values())


def test_adjudicate_all_ok():
    r = adjudicate_all()
    assert set(r) == {"criterion", "verification", "proof"}
    assert all(v["action"] == "ok" for v in r.values())


def test_default_sources_exist():
    for key in ("criterion", "verification", "proof"):
        for p in default_sources(key):
            assert __import__("pathlib").Path(p).is_file(), p


# --- 篡改：删披露锚点 → partial → flag；红旗命中 → no → downgrade ---
def test_tamper_deleted_disclosure_flags(tmp_path):
    bad = tmp_path / "t.txt"
    bad.write_text("label-free LLM-generated tests TestSynth. "
                   "No separate reviewer is part of this run. "
                   "without access to ground-truth solutions or official tests.",
                   encoding="utf-8")
    v, tr = adjudicate_criterion_origin_honesty(sources=[str(bad)])
    assert tr["inferred"]["recall_boundary_disclosed"] == "partial"
    assert v.action == "flag"


def test_tamper_red_flag_downgrades(tmp_path):
    bad = tmp_path / "t.txt"
    bad.write_text("label-free LLM-generated tests TestSynth. "
                   "failure recall increasing from 41.7% to 83.3%. "
                   "without access to ground-truth solutions or official tests. "
                   "reviewed by independent experts.",
                   encoding="utf-8")
    v, tr = adjudicate_criterion_origin_honesty(sources=[str(bad)])
    assert tr["inferred"]["independent_reviewer_gap_disclosed"] == "no"
    assert v.action == "downgrade"


def test_tamper_changes_verdict_vs_real(tmp_path):
    """同一门禁：真实证据 ok，篡改证据非 ok —— 取证模式的决定性验收。"""
    real, _ = adjudicate_criterion_origin_honesty()
    bad = tmp_path / "t.txt"
    bad.write_text("空白证据", encoding="utf-8")
    tampered, _ = adjudicate_criterion_origin_honesty(sources=[str(bad)])
    assert real.action == "ok" and tampered.action != "ok"


def test_trace_has_evidence_sha():
    _, tr = adjudicate_proof_boundary_honesty()
    for name, digest in tr["source_sha256"].items():
        assert len(digest) == 64


def test_live_regression():
    r = live_regression()
    assert r["all_passed"] and all(r["checks"].values())
