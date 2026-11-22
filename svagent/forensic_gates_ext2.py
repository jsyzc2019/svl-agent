"""FJ 取证法官扩展入口 2 — 自主运维第二轮新增的第五道（§91）。

不改动已锁存的 forensic_gates.py / forensic_gates_ext.py；本模块承载
rsi_claim_audit 的 adjudicate_* 入口，复用同一 forensics.adjudicate 内核与链校验。

锚点取自 arXiv:2610.27610v1 全文（audit_rsi_claim_audit/downloads/paper_flat.txt），
已用探测脚本验证：disclose 锚点必命中、红旗 conceal 锚点零误命中
（ALL_ANCHORS_CLEAN=True）。诚实论文 → 推导全 yes → ok；篡改/删改 → partial/no → 降级。

诚实边界：只判原文是否诚实披露四边界，不承诺 RSI 改进真实有效（KB-R07/META01，
self-reported 增益折 1）；红旗是探测器不是伪造证据，命中明细进 trace 可人工复核。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .forensics import (
    EvidenceBundle, ForensicSpec, DimensionSpec, adjudicate as _adjudicate,
)
from .rsi_claim_audit_honesty import (
    check_rsi_claim_audit_honesty, RSIClaimAuditVerdict,
)

_ROOT = Path(__file__).resolve().parent.parent

# 锚点集中字典（AST 自审：Compare 内无中文字面量）
_A = {
    "product_process_split": (
        ("separating product claims about the final system from process claims about the improvement process itself",
         "claim-indexed reporting standard that connects each claim to the evaluation design needed to test it"),
        ("a better final score proves the improvement process improved",
         "product gains establish process gains"),
    ),
    "repeatability_audited": (
        ("Only 22% audit two or more reruns of the full loop",
         "14% audit two or more reruns",
         "evidence for repeatability and improved procedures remains less developed than product evaluation"),
        ("a single improvement run demonstrates repeatable recursion",
         "reruns are unnecessary once a gain is measured"),
    ),
    "improver_gain_isolated": (
        ("only 4 compare earlier and later procedures from identical starting artifacts at a matched budget",
         "23 report a related comparison"),
        ("improved procedures are validated by the strongest final model",
         "starting artifacts need not be held fixed across comparisons"),
    ),
    "selection_unused_eval": (
        ("60% report evaluation on tasks unused for selection",
         "45% evaluate on tasks unused for selection",
         "selection effects, shared evaluator errors, and changes in system state limit what product evaluations can establish"),
        ("evaluating on selection tasks is sufficient",
         "shared evaluator errors do not affect product claims"),
    ),
}

_DEFAULT_SOURCES = ["audit_rsi_claim_audit/downloads/paper_flat.txt"]
_AUDIT_DIR = "audit_rsi_claim_audit"


def _spec() -> ForensicSpec:
    dims = tuple(
        DimensionSpec(name, tuple(disc), tuple(conc))
        for name, (disc, conc) in _A.items()
    )
    return ForensicSpec(gate="forensic.rsi_claim_audit", dimensions=dims)


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


def adjudicate_rsi_claim_audit_honesty(
    claim: str = "Recursive self-improvement claim under evaluation auditing",
    sources: list[str] | None = None,
    enforce_chain: bool = True,
) -> tuple[RSIClaimAuditVerdict, dict[str, Any]]:
    """取证版 RSI 声称审计诚实性：验三锁→读 arXiv 全文自取四维→原 check_* 裁决。"""
    eff_sources = sources or default_sources()
    chain = _require_chain(enforce_chain, eff_sources)
    bundle = EvidenceBundle.from_files(eff_sources)
    verdict, trace = _adjudicate(bundle, _spec(), check_rsi_claim_audit_honesty, claim,
                                 evidence_scope="primary(arXiv abs+全文,self-reported折1)")
    if chain:
        trace.update(chain)
    return verdict, trace


def live_regression() -> dict:
    """取证自测：真实证据→ok；删披露锚点→partial→flag；红旗→no→降级；链失配拒判。"""
    import tempfile
    checks: dict[str, bool] = {}

    # 1) 真实证据 → ok
    v, tr = adjudicate_rsi_claim_audit_honesty()
    checks["real_evidence_ok"] = (v.action == "ok" and v.code == "RSI_CLAIM_AUDIT.SELF_CONSISTENT")

    # 2) 篡改：删掉 repeatability 三维披露锚点 → 该维 partial → flag
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "tampered.txt"
        bad.write_text(
            "separating product claims about the final system from process claims about the improvement process itself. "
            "only 4 compare earlier and later procedures from identical starting artifacts at a matched budget. "
            "60% report evaluation on tasks unused for selection.",
            encoding="utf-8",
        )
        v2, tr2 = adjudicate_rsi_claim_audit_honesty(sources=[str(bad)])
        checks["tamper_partial_flag"] = (
            tr2["inferred"]["repeatability_audited"] == "partial" and v2.action == "flag"
        )
        checks["tamper_trace_has_sha"] = bool(tr2["source_sha256"])

    # 3) 红旗命中：注入「单轮即可证明可重复」→ repeatability 维 no → downgrade
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "redflag.txt"
        bad.write_text(
            "separating product claims about the final system from process claims about the improvement process itself. "
            "a single improvement run demonstrates repeatable recursion, reruns are unnecessary once a gain is measured. "
            "only 4 compare earlier and later procedures from identical starting artifacts at a matched budget. "
            "60% report evaluation on tasks unused for selection.",
            encoding="utf-8",
        )
        v3, tr3 = adjudicate_rsi_claim_audit_honesty(sources=[str(bad)])
        checks["red_flag_downgrade"] = (
            tr3["inferred"]["repeatability_audited"] == "no" and v3.action == "downgrade"
        )

    # 4) 链失配拒判：临时副本里篡改 prereg.json，核心锁失配 → ChainIntegrityError
    import shutil
    with tempfile.TemporaryDirectory() as td:
        shutil.copytree(_ROOT / _AUDIT_DIR, Path(td) / _AUDIT_DIR)
        p = Path(td) / _AUDIT_DIR / "prereg.json"
        p.write_text(p.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        orig = _ROOT
        globals()["_ROOT"] = Path(td)
        try:
            adjudicate_rsi_claim_audit_honesty()
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
