"""Benchmark 污染诚实性门禁测试（§94，arXiv:2611.21315 编译产物 + FJ 取证入口）。"""
from pathlib import Path

import pytest

from svagent.benchleaking_honesty import (
    check_benchleaking_honesty, BenchleakingVerdict, live_regression,
)
from svagent.forensic_gates_ext5 import (
    adjudicate_benchleaking_honesty, live_regression as forensic_regression,
)

DIMS = ["benchleaking_vs_maxxing", "leakage_probe_disclosed",
        "score_adjusted_for_leak", "scope_bounded"]


def _good(**over):
    base = {d: "yes" for d in DIMS}
    base.update(over)
    return base


# ---- gate 裁决（填表模式）----
def test_recall_as_capability_downgrade():
    v = check_benchleaking_honesty("x", **_good(benchleaking_vs_maxxing="no"))
    assert isinstance(v, BenchleakingVerdict)
    assert v.action == "downgrade" and v.code == "BENCHLEAK.RECALL_AS_CAPABILITY"
    assert "recall" in v.message.lower()


def test_probe_undisclosed_downgrade():
    v = check_benchleaking_honesty("x", **_good(leakage_probe_disclosed="no"))
    assert v.action == "downgrade" and v.code == "BENCHLEAK.PROBE_UNDISCLOSED"
    assert "探针" in v.message


def test_score_unadjusted_flag():
    v = check_benchleaking_honesty("x", **_good(score_adjusted_for_leak="no"))
    assert v.action == "flag" and v.code == "BENCHLEAK.SCORE_UNADJUSTED"
    assert "Anti-Hack" in v.message


def test_scope_overclaimed_flag():
    v = check_benchleaking_honesty("x", **_good(scope_bounded="no"))
    assert v.action == "flag" and v.code == "BENCHLEAK.SCOPE_OVERCLAIMED"
    assert "外推" in v.message


@pytest.mark.parametrize("dim", DIMS)
def test_partial_any_dim_flag(dim):
    v = check_benchleaking_honesty("x", **_good(**{dim: "partial"}))
    assert v.action == "flag" and v.code == "BENCHLEAK.PARTIAL"


@pytest.mark.parametrize("dim", DIMS)
def test_literal_enum_flag(dim):
    v = check_benchleaking_honesty("x", **_good(**{dim: "maybe"}))
    assert v.action == "flag" and v.code == "BENCHLEAK.INVALID_INPUT"


def test_all_good_ok():
    v = check_benchleaking_honesty("x", **_good())
    assert v.action == "ok" and v.code == "BENCHLEAK.SELF_CONSISTENT"


def test_priority_benchleaking_over_probe():
    # R1 优先于 R2
    v = check_benchleaking_honesty(
        "x", **_good(benchleaking_vs_maxxing="no", leakage_probe_disclosed="no"))
    assert v.code == "BENCHLEAK.RECALL_AS_CAPABILITY"


def test_priority_no_over_partial():
    # 具体 no 优先于 partial（短路顺序）
    v = check_benchleaking_honesty(
        "x", **_good(score_adjusted_for_leak="partial", scope_bounded="no"))
    assert v.code == "BENCHLEAK.SCOPE_OVERCLAIMED"


def test_verdict_fields_echo_inputs():
    kw = _good(benchleaking_vs_maxxing="partial")
    v = check_benchleaking_honesty("claim-X", **kw)
    assert v.claim == "claim-X"
    assert v.benchleaking_vs_maxxing == "partial"
    assert v.scope_bounded == "yes"


# ---- 活体回归 ----
def test_gate_live_regression_all_passed():
    r = live_regression()
    assert r["all_passed"] is True
    assert len(r["cases"]) == 7


# ---- FJ 取证入口 ----
def test_forensic_real_evidence_ok():
    v, tr = adjudicate_benchleaking_honesty()
    assert v.action == "ok"
    assert tr["inferred"] == {d: "yes" for d in DIMS}
    assert tr["mode"] == "forensic"


def test_forensic_trace_has_chain():
    _, tr = adjudicate_benchleaking_honesty()
    assert "chain" in tr
    assert tr["chain"]["intact"] is True
    assert "source_verification" in tr


def test_forensic_tamper_partial_flag(tmp_path):
    bad = tmp_path / "tampered.txt"
    bad.write_text(
        "so that a score reflects recall rather than capability, "
        "This differs from benchmaxxing, which optimizes toward a benchmark without seeing its test set. "
        "Using few-shot continuation on 20 benchmarks across four public base models. "
        "We call for decontamination reports and contamination-adjusted scores to become standard practice.",
        encoding="utf-8",
    )
    v, tr = adjudicate_benchleaking_honesty(sources=[str(bad)])
    assert tr["inferred"]["score_adjusted_for_leak"] == "partial"
    assert v.action == "flag"


def test_forensic_redflag_downgrade(tmp_path):
    bad = tmp_path / "redflag.txt"
    bad.write_text(
        "a benchmark score always measures genuine capability regardless of training exposure, "
        "there is no meaningful distinction between test-set memorization and benchmark optimization. "
        "Using few-shot continuation on 20 benchmarks across four public base models. "
        "we define an Anti-Hack score: the benchmark score recomputed with every leaked example marked wrong and the number of examples unchanged. "
        "these probes prove every base model memorized the entire benchmark in training.",
        encoding="utf-8",
    )
    v, tr = adjudicate_benchleaking_honesty(sources=[str(bad)])
    assert tr["inferred"]["benchleaking_vs_maxxing"] == "no"
    assert v.action == "downgrade"


def test_forensic_chain_tamper_rejected(tmp_path, monkeypatch):
    import shutil
    from svagent.evidence_chain import ChainIntegrityError
    import svagent.forensic_gates_ext5 as fe
    audit = Path(__file__).resolve().parent.parent / "audit_benchleaking_honesty"
    shutil.copytree(audit, tmp_path / "audit_benchleaking_honesty")
    p = tmp_path / "audit_benchleaking_honesty" / "prereg.json"
    p.write_text(p.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    monkeypatch.setattr(fe, "_ROOT", tmp_path)
    with pytest.raises(ChainIntegrityError):
        adjudicate_benchleaking_honesty()


def test_forensic_live_regression_all_passed():
    r = forensic_regression()
    assert r["all_passed"] is True
    assert r["checks"]["chain_tamper_rejected"] is True


# ---- AST 自审 ----
@pytest.mark.parametrize("path", [
    "svagent/benchleaking_honesty.py",
    "svagent/forensic_gates_ext5.py",
])
def test_ast_no_chinese_literal_in_compare(path):
    import ast
    root = Path(__file__).resolve().parent.parent
    tree = ast.parse((root / path).read_text(encoding="utf-8"))
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for c in [node.left] + node.comparators:
                if isinstance(c, ast.Constant) and isinstance(c.value, str) and any(
                    "\u4e00" <= ch <= "\u9fff" for ch in c.value
                ):
                    bad.append((node.lineno, c.value))
    assert bad == []
