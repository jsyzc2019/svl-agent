"""FJ 取证内核测试（阶段1：EvidenceBundle / 三态推导 / 规范化 / 溯源）。"""
import pytest

from svagent.forensics import (
    EvidenceBundle, ForensicSpec, DimensionSpec, infer_dimensions,
    adjudicate, normalize, live_regression,
)
from svagent.criterion_origin_honesty import check_criterion_origin_honesty


def _spec():
    return ForensicSpec("t", (
        DimensionSpec("scope", ("绿灯只说明一件事",), ("覆盖了一切",)),
    ))


def test_normalize_unifies_dash_and_quotes():
    assert normalize("self\u2212review \u201chello\u201d") == "self-review \"hello\""


def test_evidence_from_files_reads_and_hashes(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("绿灯只说明一件事。", encoding="utf-8")
    b = EvidenceBundle.from_files([str(p)])
    assert b.hit("绿灯只说明一件事")
    assert len(b.sha256["a.txt"]) == 64


def test_evidence_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        EvidenceBundle.from_files(["/no/such/evidence/file.txt"])


def test_infer_disclose_to_yes():
    inferred, prov = infer_dimensions(EvidenceBundle.inline("绿灯只说明一件事。"), _spec())
    assert inferred["scope"] == "yes"
    assert prov["scope"]["disclose_hits"]


def test_infer_conceal_to_no():
    inferred, _ = infer_dimensions(EvidenceBundle.inline("它覆盖了一切。"), _spec())
    assert inferred["scope"] == "no"


def test_infer_absent_to_partial():
    inferred, _ = infer_dimensions(EvidenceBundle.inline("无关文本。"), _spec())
    assert inferred["scope"] == "partial"


def test_infer_contradictory_to_partial():
    inferred, _ = infer_dimensions(
        EvidenceBundle.inline("绿灯只说明一件事，但它覆盖了一切。"), _spec())
    assert inferred["scope"] == "partial"


def test_adjudicate_returns_verdict_and_trace():
    verdict, trace = adjudicate(
        EvidenceBundle.inline("绿灯只说明一件事。"), _spec(),
        lambda claim, **kw: type("V", (), {"action": "ok", "code": "OK"})(), "c")
    assert verdict.action == "ok"
    assert trace["mode"] == "forensic" and trace["inferred"]["scope"] == "yes"


def test_adjudicate_missing_evidence_never_fills_yes():
    """关键纪律：取证不足时 partial → 原 check_* R5 flag，绝不补 yes。"""
    spec = ForensicSpec("c", (
        DimensionSpec("criterion_origin_disclosed", ("label-free",), ()),
        DimensionSpec("recall_boundary_disclosed", ("41.7%",), ()),
        DimensionSpec("external_anchor_disclosed", ("official tests",), ()),
        DimensionSpec("independent_reviewer_gap_disclosed", ("No separate reviewer",), ()),
    ))
    verdict, trace = adjudicate(
        EvidenceBundle.inline("空白证据"), spec, check_criterion_origin_honesty, "c")
    assert all(v == "partial" for v in trace["inferred"].values())
    assert verdict.action == "flag"


def test_live_regression():
    r = live_regression()
    assert r["all_passed"] and all(r["checks"].values())
