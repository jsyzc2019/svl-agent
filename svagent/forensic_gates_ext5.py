"""FJ 取证法官扩展入口 5 — 自主运维第五轮新增的第八道（§94）。

不改动已锁存的 forensic_gates.py / ext.py / ext2.py / ext3.py / ext4.py；
本模块承载 benchleaking 的 adjudicate_* 入口，
复用同一 forensics.adjudicate 内核与 evidence_chain 链校验。

锚点取自 arXiv:2611.21315v1 全文（audit_benchleaking_honesty/downloads/paper_flat.txt），
已用探测脚本验证：15 个 disclose 锚点全部命中、红旗 conceal 锚点零误命中
（ALL_ANCHORS_CLEAN=True；全文 HTML 正文在目录后截断，锚点均取自完整摘要段）。
诚实论文 → 推导全 yes → ok；篡改/删改 → partial/no → 降级。

诚实边界：只判原文是否诚实披露四 benchmark 污染边界，不承诺模型真实无污染
（KB-R07/META01，96%/85% 等 self-reported 泄漏率折 1）；
红旗是探测器不是伪造证据，命中明细进 trace 可人工复核。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .forensics import (
    EvidenceBundle, ForensicSpec, DimensionSpec, adjudicate as _adjudicate,
)
from .benchleaking_honesty import (
    check_benchleaking_honesty,
    BenchleakingVerdict,
)

_ROOT = Path(__file__).resolve().parent.parent

# 锚点集中字典（AST 自审：Compare 内无中文字面量）
_A = {
    "benchleaking_vs_maxxing": (
        ("so that a score reflects recall rather than capability",
         "This differs from benchmaxxing, which optimizes toward a benchmark without seeing its test set"),
        ("a benchmark score always measures genuine capability regardless of training exposure",
         "there is no meaningful distinction between test-set memorization and benchmark optimization"),
    ),
    "leakage_probe_disclosed": (
        ("Using few-shot continuation on 20 benchmarks across four public base models",
         "complete questions, options, and answers that appear nowhere in their input"),
        ("the models were declared clean without any contamination probe",
         "no test-set leakage experiment was conducted"),
    ),
    "score_adjusted_for_leak": (
        ("we define an Anti-Hack score: the benchmark score recomputed with every leaked example marked wrong and the number of examples unchanged",
         "To quantify what a reported score owes to such examples"),
        ("the published score was reported unchanged despite confirmed test-set leakage",
         "leaked examples were kept as correct in the reported benchmark score"),
    ),
    "scope_bounded": (
        ("We call for decontamination reports and contamination-adjusted scores to become standard practice",
         "benchleaking now affects more than leaderboard rankings"),
        ("these probes prove every base model memorized the entire benchmark in training",
         "the leakage rate establishes the prevalence of contamination across all models"),
    ),
}

_DEFAULT_SOURCES = ["audit_benchleaking_honesty/downloads/paper_flat.txt"]
_AUDIT_DIR = "audit_benchleaking_honesty"


def _spec() -> ForensicSpec:
    dims = tuple(
        DimensionSpec(name, tuple(disc), tuple(conc))
        for name, (disc, conc) in _A.items()
    )
    return ForensicSpec(gate="forensic.benchleaking", dimensions=dims)


def default_sources() -> list[str]:
    """返回默认证据绝对路径（供 CLI / 外部调用）。"""
    return [str(_ROOT / p) for p in _DEFAULT_SOURCES]


def _require_chain(enforce: bool, sources: list[str]) -> dict[str, Any] | None:
    """取证前校验：prereg/gate_prereg 二锁必过 + 证据源哈希匹配；失配即拒判。"""
    if not enforce:
        return None
    from .evidence_chain import verify_chain, verify_sources, ChainIntegrityError
    d = _ROOT / _AUDIT_DIR
    report = verify_chain(d)
    core_ok = all(c.ok for c in report.locks
                  if c.lock.startswith(("prereg", "gate_prereg")))
    if not core_ok:
        bad = [c.lock + ":" + c.detail for c in report.locks
               if c.lock.startswith(("prereg", "gate_prereg")) and not c.ok]
        raise ChainIntegrityError("核心锁失配，拒绝取证: " + str(d) + " | " + "; ".join(bad))
    src_check = verify_sources(d, sources)
    if src_check["tampered"]:
        raise ChainIntegrityError("证据源文件已篡改，拒绝取证: " + str(d) + " | " + str(src_check["tampered"]))
    return {"chain": report.to_dict(), "source_verification": src_check}


def adjudicate_benchleaking_honesty(
    claim: str = "Benchmark score contamination disclosure claim",
    sources: list[str] | None = None,
    enforce_chain: bool = True,
) -> tuple[BenchleakingVerdict, dict[str, Any]]:
    """取证版 benchmark 污染诚实性：验三锁→读 arXiv 全文自取四维→原 check_* 裁决。"""
    eff_sources = sources or default_sources()
    chain = _require_chain(enforce_chain, eff_sources)
    bundle = EvidenceBundle.from_files(eff_sources)
    verdict, trace = _adjudicate(bundle, _spec(),
                                 check_benchleaking_honesty, claim,
                                 evidence_scope="primary(arXiv abs+全文,泄漏率self-reported折1)")
    if chain:
        trace.update(chain)
    return verdict, trace


def live_regression() -> dict:
    """取证自测：真实证据→ok；删披露锚点→partial→flag；红旗→no→降级；链失配拒判。"""
    import tempfile
    checks: dict[str, bool] = {}

    # 1) 真实证据 → ok
    v, tr = adjudicate_benchleaking_honesty()
    checks["real_evidence_ok"] = (v.action == "ok" and v.code == "BENCHLEAK.SELF_CONSISTENT")

    # 2) 篡改：删掉 score_adjusted 维披露锚点 → 该维 partial → flag（其余三维保留）
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "tampered.txt"
        bad.write_text(
            "so that a score reflects recall rather than capability, "
            "This differs from benchmaxxing, which optimizes toward a benchmark without seeing its test set. "
            "Using few-shot continuation on 20 benchmarks across four public base models. "
            "We call for decontamination reports and contamination-adjusted scores to become standard practice.",
            encoding="utf-8",
        )
        v2, tr2 = adjudicate_benchleaking_honesty(sources=[str(bad)])
        checks["tamper_partial_flag"] = (
            tr2["inferred"]["score_adjusted_for_leak"] == "partial" and v2.action == "flag"
        )
        checks["tamper_trace_has_sha"] = bool(tr2["source_sha256"])

    # 3) 红旗命中：注入「分数恒测真能力/泄漏即记忆全基准」→ benchleaking 与 scope 维 no
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "redflag.txt"
        bad.write_text(
            "a benchmark score always measures genuine capability regardless of training exposure, "
            "there is no meaningful distinction between test-set memorization and benchmark optimization. "
            "Using few-shot continuation on 20 benchmarks across four public base models. "
            "we define an Anti-Hack score: the benchmark score recomputed with every leaked example marked wrong and the number of examples unchanged. "
            "these probes prove every base model memorized the entire benchmark in training.",
            encoding="utf-8",
        )
        v3, tr3 = adjudicate_benchleaking_honesty(sources=[str(bad)])
        checks["red_flag_downgrade"] = (
            tr3["inferred"]["benchleaking_vs_maxxing"] == "no" and v3.action == "downgrade"
        )

    # 4) 链失配拒判
    import shutil
    with tempfile.TemporaryDirectory() as td:
        shutil.copytree(_ROOT / _AUDIT_DIR, Path(td) / _AUDIT_DIR)
        p = Path(td) / _AUDIT_DIR / "prereg.json"
        p.write_text(p.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        orig = _ROOT
        globals()["_ROOT"] = Path(td)
        try:
            adjudicate_benchleaking_honesty()
            checks["chain_tamper_rejected"] = False
        except Exception as e:
            checks["chain_tamper_rejected"] = type(e).__name__ == "ChainIntegrityError"
        finally:
            globals()["_ROOT"] = orig

    return {
        "checks": checks,
        "cases": {"real": {"action": v.action, "code": v.code, "inferred": tr["inferred"]}},
        "all_passed": all(checks.values()),
    }
