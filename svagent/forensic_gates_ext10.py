"""FJ 取证法官扩展入口 10 — 自主运维第十轮新增的第十三道（§99）。

不改动已锁存的 forensic_gates.py / ext.py .. ext9.py；
本模块承载 evaluator_independence 的 adjudicate_* 入口，
复用同一 forensics.adjudicate 内核与 evidence_chain 链校验。

锚点取自 arXiv:2609.02246v1 全文（audit_evaluator_independence/downloads/paper_flat.txt），
四维逐字校准：disclose 锚点全部命中、红旗 conceal 锚点零误命中。
诚实框架 → 推导全 yes → ok；篡改/删改 → partial/no → 降级。

诚实边界：只判原文是否诚实披露四评估器独立性边界，不承诺评估器真独立
（KB-R07/META01/STRUCT02，论文自承 Teacher 仍是 LLM judge 且有其防不住的失败）；
红旗是探测器不是伪造证据，命中明细进 trace 可人工复核。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .forensics import (
    EvidenceBundle, ForensicSpec, DimensionSpec, adjudicate as _adjudicate,
)
from .evaluator_independence_honesty import (
    check_evaluator_independence_honesty,
    EvaluatorIndependenceVerdict,
)

_ROOT = Path(__file__).resolve().parent.parent

# 锚点集中字典（AST 自审：Compare 内无中文字面量）
_A = {
    "judge_demoted_to_advisor": (
        ("The judge should be demoted from oracle to advisor",
         "its verdict becomes one input among several"),
        ("the judge has the final say with no independent check",
         "a single judge verdict is the only signal"),
    ),
    "deterministic_gate_unoverridable": (
        ("every change is gated instead by a deterministic verification layer the judge cannot override",
         "acceptance checks that outrank the Teacher"),
        ("the judge verdict is the final gate with no deterministic override",
         "deterministic checks can be overridden by the judge"),
    ),
    "frozen_holdout_canary": (
        ("frozen holdouts",
         "canary cases engineered so that a perfect score is itself evidence of cheating"),
        ("holdouts are re-sampled after each revision",
         "a perfect score is taken at face value"),
    ),
    "evaluator_improver_separated": (
        ("capability-disjoint roles",
         "stateless subagents diagnose failures and draft mutations they cannot apply",
         "a stateful orchestrator holds all tool access"),
        ("the same agent both proposes mutations and grades them",
         "the Teacher applies the mutations it grades"),
    ),
}

_DEFAULT_SOURCES = ["audit_evaluator_independence/downloads/paper_flat.txt"]
_AUDIT_DIR = "audit_evaluator_independence"


def _spec() -> ForensicSpec:
    dims = tuple(
        DimensionSpec(name, tuple(disc), tuple(conc))
        for name, (disc, conc) in _A.items()
    )
    return ForensicSpec(gate="forensic.evaluator_independence", dimensions=dims)


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


def adjudicate_evaluator_independence_honesty(
    claim: str = "self-improving agent evaluator-independence disclosure claim",
    sources: list[str] | None = None,
    enforce_chain: bool = True,
) -> tuple[EvaluatorIndependenceVerdict, dict[str, Any]]:
    """取证版评估器独立性诚实性：验三锁→读 arXiv 全文自取四维→原 check_* 裁决。"""
    eff_sources = sources or default_sources()
    chain = _require_chain(enforce_chain, eff_sources)
    bundle = EvidenceBundle.from_files(eff_sources)
    verdict, trace = _adjudicate(bundle, _spec(),
                                 check_evaluator_independence_honesty, claim,
                                 evidence_scope="primary(arXiv abs+全文 PROCTOR,self-reported折1,论文自承Teacher仍是judge)")
    if chain:
        trace.update(chain)
    return verdict, trace


def live_regression() -> dict:
    """取证自测：真实证据→ok；删披露锚点→partial→flag；红旗→no→降级；链失配拒判。"""
    import tempfile
    checks: dict[str, bool] = {}

    # 1) 真实证据 → ok
    v, tr = adjudicate_evaluator_independence_honesty()
    checks["real_evidence_ok"] = (v.action == "ok" and v.code == "EVALIND.SELF_CONSISTENT")

    # 2) 篡改：删掉 frozen_holdout_canary 维披露锚点 → 该维 partial → flag（其余三维保留）
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "tampered.txt"
        bad.write_text(
            "The judge should be demoted from oracle to advisor. "
            "its verdict becomes one input among several. "
            "every change is gated instead by a deterministic verification layer the judge cannot override. "
            "acceptance checks that outrank the Teacher. "
            "capability-disjoint roles. "
            "stateless subagents diagnose failures and draft mutations they cannot apply. "
            "a stateful orchestrator holds all tool access.",
            encoding="utf-8",
        )
        v2, tr2 = adjudicate_evaluator_independence_honesty(sources=[str(bad)])
        checks["tamper_partial_flag"] = (
            tr2["inferred"]["frozen_holdout_canary"] == "partial" and v2.action == "flag"
        )
        checks["tamper_trace_has_sha"] = bool(tr2["source_sha256"])

    # 3) 红旗命中：注入『judge 终裁无独立检查』→ advisor 维 no → downgrade
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "redflag.txt"
        bad.write_text(
            "the judge has the final say with no independent check. "
            "a single judge verdict is the only signal. "
            "Every change is gated instead by a deterministic verification layer the judge cannot override. "
            "frozen holdouts. "
            "capability-disjoint roles.",
            encoding="utf-8",
        )
        v3, tr3 = adjudicate_evaluator_independence_honesty(sources=[str(bad)])
        checks["red_flag_downgrade"] = (
            tr3["inferred"]["judge_demoted_to_advisor"] == "no" and v3.action == "downgrade"
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
            adjudicate_evaluator_independence_honesty()
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
