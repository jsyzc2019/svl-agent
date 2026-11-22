"""FJ 取证法官扩展入口 3 — 自主运维第三轮新增的第六道（§92）。

不改动已锁存的 forensic_gates.py / forensic_gates_ext.py / forensic_gates_ext2.py；
本模块承载 memory_consolidation_governance 的 adjudicate_* 入口，
复用同一 forensics.adjudicate 内核与 evidence_chain 链校验。

锚点取自 arXiv:2609.33013v1 全文（audit_memory_epistemics/downloads/paper_flat.txt），
已用探测脚本验证：disclose 锚点必命中、红旗 conceal 锚点零误命中
（ALL_ANCHORS_CLEAN=True）。诚实论文 → 推导全 yes → ok；篡改/删改 → partial/no → 降级。

诚实边界：只判原文是否诚实披露四 epistemics 边界，不承诺方法真实有效
（KB-R07/META01，+22.7%/7× 等 self-reported 增益折 1）；
红旗是探测器不是伪造证据，命中明细进 trace 可人工复核。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .forensics import (
    EvidenceBundle, ForensicSpec, DimensionSpec, adjudicate as _adjudicate,
)
from .memory_consolidation_governance_honesty import (
    check_memory_consolidation_governance_honesty,
    MemoryConsolidationGovernanceVerdict,
)

_ROOT = Path(__file__).resolve().parent.parent

# 锚点集中字典（AST 自审：Compare 内无中文字面量）
_A = {
    "consolidation_quality_separated": (
        ("an oracle-by-construction that scores consolidation decisions against a known optimum on three non-circular axes",
         "production retrieval systems retain information yet score zero on cross-level transfer"),
        ("how much an agent remembers is the only metric that matters",
         "retention rate alone measures consolidation quality"),
    ),
    "governance_quality_split": (
        ("poison-resistant, reversible, and auditable",
         "the governance axis is statistically distinct from the quality score",
         "policies with identical quality scores differ threefold in governance"),
        ("governance is fully captured by the quality score",
         "the quality score explains all governance variance"),
    ),
    "negative_result_disclosed": (
        ("the quality score does not predict real transfer accuracy",
         "95 % 95\\% CI spanning zero",
         "with all three axes failing individually"),
        ("the quality score predicts transfer accuracy in every benchmark",
         "all transfer correlations were positive and significant"),
    ),
    "near_miss_and_overclaim_guarded": (
        ("an honest near-miss",
         "oracle correlation 0.691",
         "an adversarial self-critique pass cleared the final claim set with zero surviving overclaims"),
        ("the phase-1 result cleared the 0.70 bar",
         "every prediction was confirmed by the data"),
    ),
}

_DEFAULT_SOURCES = ["audit_memory_epistemics/downloads/paper_flat.txt"]
_AUDIT_DIR = "audit_memory_epistemics"


def _spec() -> ForensicSpec:
    dims = tuple(
        DimensionSpec(name, tuple(disc), tuple(conc))
        for name, (disc, conc) in _A.items()
    )
    return ForensicSpec(gate="forensic.memory_consolidation_governance", dimensions=dims)


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


def adjudicate_memory_consolidation_governance_honesty(
    claim: str = "Long-horizon agent memory consolidation governance claim",
    sources: list[str] | None = None,
    enforce_chain: bool = True,
) -> tuple[MemoryConsolidationGovernanceVerdict, dict[str, Any]]:
    """取证版记忆巩固治理诚实性：验三锁→读 arXiv 全文自取四维→原 check_* 裁决。"""
    eff_sources = sources or default_sources()
    chain = _require_chain(enforce_chain, eff_sources)
    bundle = EvidenceBundle.from_files(eff_sources)
    verdict, trace = _adjudicate(bundle, _spec(),
                                 check_memory_consolidation_governance_honesty, claim,
                                 evidence_scope="primary(arXiv abs+全文,self-reported折1)")
    if chain:
        trace.update(chain)
    return verdict, trace


def live_regression() -> dict:
    """取证自测：真实证据→ok；删披露锚点→partial→flag；红旗→no→降级；链失配拒判。"""
    import tempfile
    checks: dict[str, bool] = {}

    # 1) 真实证据 → ok
    v, tr = adjudicate_memory_consolidation_governance_honesty()
    checks["real_evidence_ok"] = (v.action == "ok" and v.code == "MEM_CONSOLIDATION.SELF_CONSISTENT")

    # 2) 篡改：删掉 governance 三维披露锚点 → 该维 partial → flag
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "tampered.txt"
        bad.write_text(
            "an oracle-by-construction that scores consolidation decisions against a known optimum on three non-circular axes. "
            "the quality score does not predict real transfer accuracy, with all three axes failing individually. "
            "an honest near-miss, oracle correlation 0.691.",
            encoding="utf-8",
        )
        v2, tr2 = adjudicate_memory_consolidation_governance_honesty(sources=[str(bad)])
        checks["tamper_partial_flag"] = (
            tr2["inferred"]["governance_quality_split"] == "partial" and v2.action == "flag"
        )
        checks["tamper_trace_has_sha"] = bool(tr2["source_sha256"])

    # 3) 红旗命中：注入「质量分完全涵盖治理」→ governance 维 no → downgrade
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "redflag.txt"
        bad.write_text(
            "an oracle-by-construction that scores consolidation decisions against a known optimum on three non-circular axes. "
            "the quality score explains all governance variance, governance is fully captured by the quality score. "
            "the quality score does not predict real transfer accuracy. an honest near-miss.",
            encoding="utf-8",
        )
        v3, tr3 = adjudicate_memory_consolidation_governance_honesty(sources=[str(bad)])
        checks["red_flag_downgrade"] = (
            tr3["inferred"]["governance_quality_split"] == "no" and v3.action == "downgrade"
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
            adjudicate_memory_consolidation_governance_honesty()
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
