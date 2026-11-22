"""FJ 取证法官扩展入口 — 自主运维首日新增的第四道（§90）。

不改动已锁存的 forensic_gates.py 三道试点；本模块承载 silent_failure 的
adjudicate_* 入口，复用同一 forensics.adjudicate 内核与 evidence_chain 链校验。

锚点取自 arXiv:2611.10063v1 全文（audit_silent_failure/downloads/paper_flat.txt），
已用探测脚本验证：disclose 锚点必命中、红旗 conceal 锚点零误命中
（ALL_ANCHORS_CLEAN=True）。诚实论文 → 推导全 yes → ok；篡改/删改 → partial/no → 降级。

诚实边界：只判原文是否诚实披露四边界，不承诺方法真实有效（KB-R07/META01）；
红旗是探测器不是伪造证据，命中明细进 forensic_trace 可人工复核。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .forensics import (
    EvidenceBundle, ForensicSpec, DimensionSpec, adjudicate as _adjudicate,
)
from .silent_failure_honesty import (
    check_silent_failure_honesty, SilentFailureVerdict,
)

_ROOT = Path(__file__).resolve().parent.parent

# 中/英文锚点集中字典（AST 自审：Compare 内无中文字面量）
_A = {
    "silent_failure_triple_defined": (
        ("The silent-failure rate is the conjunction of (i) valid renderable geometry",
         "an explicit agent completion claim",
         "failure of at least one semantic check"),
        ("silent failure means the code crashes",
         "any failed check counts as silent failure"),
    ),
    "oracle_self_audited": (
        ("The benchmark audits itself",
         "flipped 18 of the 519 verdicts it regraded from pass to fail and none in reverse",
         "a blind expert audit overturned 3"),
        ("our oracle is assumed correct without audit",
         "verdicts are final and need no regrading"),
    ),
    "claim_contract_ablated": (
        ("the ablation attributes the cut to the claim contract",
         "enforcing measure-then-claim cuts it to 3.2%",
         "14.1% silent-failure rate"),
        ("the improvement comes from more feedback",
         "feedback alone explains the drop"),
    ),
    "calibration_and_unsupported_reported": (
        ("poorly calibrated single-shot (ECE 0.32)",
         "became informative under verification for three of four models",
         "predictions the data did not support",
         "misses subtle wrongness"),
        ("confidence was perfectly calibrated throughout",
         "all predictions were confirmed by the data"),
    ),
}

_DEFAULT_SOURCES = ["audit_silent_failure/downloads/paper_flat.txt"]
_AUDIT_DIR = "audit_silent_failure"


def _spec() -> ForensicSpec:
    dims = tuple(
        DimensionSpec(name, tuple(disc), tuple(conc))
        for name, (disc, conc) in _A.items()
    )
    return ForensicSpec(gate="forensic.silent_failure", dimensions=dims)


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


def adjudicate_silent_failure_honesty(
    claim: str = "Agent completion claim under exact-oracle verification",
    sources: list[str] | None = None,
    enforce_chain: bool = True,
) -> tuple[SilentFailureVerdict, dict[str, Any]]:
    """取证版静默失败诚实性：验三锁→读 arXiv 全文自取四维→原 check_* 裁决。"""
    eff_sources = sources or default_sources()
    chain = _require_chain(enforce_chain, eff_sources)
    bundle = EvidenceBundle.from_files(eff_sources)
    verdict, trace = _adjudicate(bundle, _spec(), check_silent_failure_honesty, claim,
                                 evidence_scope="primary(arXiv abs+全文,self-reported折1)")
    if chain:
        trace.update(chain)
    return verdict, trace


def live_regression() -> dict:
    """取证自测：真实证据→ok；删披露锚点→partial→flag；红旗→no→降级；链失配拒判。"""
    import tempfile
    checks: dict[str, bool] = {}

    # 1) 真实证据 → ok
    v, tr = adjudicate_silent_failure_honesty()
    checks["real_evidence_ok"] = (v.action == "ok" and v.code == "SILENT_FAILURE.SELF_CONSISTENT")

    # 2) 篡改：删掉 oracle 自审三维披露锚点 → 该维 partial → flag
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "tampered.txt"
        bad.write_text(
            "The silent-failure rate is the conjunction of (i) valid renderable geometry, "
            "an explicit agent completion claim, and failure of at least one semantic check. "
            "the ablation attributes the cut to the claim contract, enforcing measure-then-claim cuts it to 3.2%. "
            "poorly calibrated single-shot (ECE 0.32), predictions the data did not support.",
            encoding="utf-8",
        )
        v2, tr2 = adjudicate_silent_failure_honesty(sources=[str(bad)])
        checks["tamper_partial_flag"] = (
            tr2["inferred"]["oracle_self_audited"] == "partial" and v2.action == "flag"
        )
        checks["tamper_trace_has_sha"] = bool(tr2["source_sha256"])

    # 3) 红旗命中：注入「判据无需审计」→ oracle 维 no → downgrade
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "redflag.txt"
        bad.write_text(
            "The silent-failure rate is the conjunction of (i) valid renderable geometry, "
            "an explicit agent completion claim, and failure of at least one semantic check. "
            "our oracle is assumed correct without audit, verdicts are final and need no regrading. "
            "the ablation attributes the cut to the claim contract. predictions the data did not support.",
            encoding="utf-8",
        )
        v3, tr3 = adjudicate_silent_failure_honesty(sources=[str(bad)])
        checks["red_flag_downgrade"] = (
            tr3["inferred"]["oracle_self_audited"] == "no" and v3.action == "downgrade"
        )

    return {
        "checks": checks,
        "cases": {"real": {"action": v.action, "code": v.code, "inferred": tr["inferred"]}},
        "all_passed": all(checks.values()),
    }
