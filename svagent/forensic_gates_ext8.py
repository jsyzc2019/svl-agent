"""FJ 取证法官扩展入口 8 — 自主运维第八轮新增的第十一道（§97）。

不改动已锁存的 forensic_gates.py / ext.py .. ext7.py；
本模块承载 maturity_evidence 的 adjudicate_* 入口，
复用同一 forensics.adjudicate 内核与 evidence_chain 链校验。

锚点取自 arXiv:2610.38266v1 全文（audit_l3_evidence_rubric/downloads/paper_flat.txt），
L0-L3 rubric 正文逐字校准：disclose 锚点全部命中、红旗 conceal 锚点零误命中。
诚实框架 → 推导全 yes → ok；篡改/删改 → partial/no → 降级。

诚实边界：只判原文是否诚实披露四成熟度证据边界，不承诺等级真实
（KB-R07/META01，KB-SIM03 无受控实验不认 L3）；
红旗是探测器不是伪造证据，命中明细进 trace 可人工复核。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .forensics import (
    EvidenceBundle, ForensicSpec, DimensionSpec, adjudicate as _adjudicate,
)
from .maturity_evidence_honesty import (
    check_maturity_evidence_honesty,
    MaturityEvidenceVerdict,
)

_ROOT = Path(__file__).resolve().parent.parent

# 锚点集中字典（AST 自审：Compare 内无中文字面量）
_A = {
    "level_definition_traced": (
        ("The evidence rubric distinguishes task-local adaptation (L0), persistent capability gain (L1), inherited process revision (L2), and verified improver gain (L3)",
         "The levels specify evidence requirements for individual claims"),
        ("a maturity level is asserted with no linked definition of what the level requires",
         "levels are self-assigned labels with no traceable evidence criteria"),
    ),
    "process_product_split": (
        ("We first explain the functional distinction between learner updates and improver revisions",
         "Persistent artifacts can modify the learner, the improver, or both"),
        ("a better final product is presented as proof that the improvement process itself improved",
         "capability gain and process revision are reported as the same claim"),
    ),
    "shared_start_controlled": (
        ("L3 requires greater subsequent gains from shared learner starts under matched resource budgets and independent tests",),
        ("a higher level is claimed from a stronger starting point or a larger budget without a shared-start control",
         "subsequent gains are reported without matching the resource budgets of the baseline"),
    ),
    "independent_tests": (
        ("We further propose common-data and interactive comparisons that evaluate reference and revised improvers from shared learner starts",
         "separating the use of experience from its acquisition"),
        ("the level claim rests on a single evaluator with no independent or common-data test",
         "reference and revised improvers are compared on different data with no shared start"),
    ),
}

_DEFAULT_SOURCES = ["audit_l3_evidence_rubric/downloads/paper_flat.txt"]
_AUDIT_DIR = "audit_l3_evidence_rubric"


def _spec() -> ForensicSpec:
    dims = tuple(
        DimensionSpec(name, tuple(disc), tuple(conc))
        for name, (disc, conc) in _A.items()
    )
    return ForensicSpec(gate="forensic.maturity_evidence", dimensions=dims)


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


def adjudicate_maturity_evidence_honesty(
    claim: str = "Agent maturity level disclosure claim",
    sources: list[str] | None = None,
    enforce_chain: bool = True,
) -> tuple[MaturityEvidenceVerdict, dict[str, Any]]:
    """取证版成熟度证据诚实性：验三锁→读 arXiv 全文自取四维→原 check_* 裁决。"""
    eff_sources = sources or default_sources()
    chain = _require_chain(enforce_chain, eff_sources)
    bundle = EvidenceBundle.from_files(eff_sources)
    verdict, trace = _adjudicate(bundle, _spec(),
                                 check_maturity_evidence_honesty, claim,
                                 evidence_scope="primary(arXiv abs+全文 L0-L3 rubric,self-reported折1)")
    if chain:
        trace.update(chain)
    return verdict, trace


def live_regression() -> dict:
    """取证自测：真实证据→ok；删披露锚点→partial→flag；红旗→no→降级；链失配拒判。"""
    import tempfile
    checks: dict[str, bool] = {}

    # 1) 真实证据 → ok
    v, tr = adjudicate_maturity_evidence_honesty()
    checks["real_evidence_ok"] = (v.action == "ok" and v.code == "MATURITY.SELF_CONSISTENT")

    # 2) 篡改：删掉 independent_tests 维披露锚点 → 该维 partial → flag（其余三维保留）
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "tampered.txt"
        bad.write_text(
            "The evidence rubric distinguishes task-local adaptation (L0), persistent capability gain (L1), inherited process revision (L2), and verified improver gain (L3). "
            "The levels specify evidence requirements for individual claims. "
            "We first explain the functional distinction between learner updates and improver revisions. "
            "Persistent artifacts can modify the learner, the improver, or both. "
            "L3 requires greater subsequent gains from shared learner starts under matched resource budgets and independent tests.",
            encoding="utf-8",
        )
        v2, tr2 = adjudicate_maturity_evidence_honesty(sources=[str(bad)])
        checks["tamper_partial_flag"] = (
            tr2["inferred"]["independent_tests"] == "partial" and v2.action == "flag"
        )
        checks["tamper_trace_has_sha"] = bool(tr2["source_sha256"])

    # 3) 红旗命中：注入「等级自封/无受控起点」→ level 维 no → downgrade
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "redflag.txt"
        bad.write_text(
            "a maturity level is asserted with no linked definition of what the level requires, "
            "levels are self-assigned labels with no traceable evidence criteria. "
            "We first explain the functional distinction between learner updates and improver revisions. "
            "L3 requires greater subsequent gains from shared learner starts under matched resource budgets and independent tests. "
            "We further propose common-data and interactive comparisons that evaluate reference and revised improvers from shared learner starts.",
            encoding="utf-8",
        )
        v3, tr3 = adjudicate_maturity_evidence_honesty(sources=[str(bad)])
        checks["red_flag_downgrade"] = (
            tr3["inferred"]["level_definition_traced"] == "no" and v3.action == "downgrade"
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
            adjudicate_maturity_evidence_honesty()
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
