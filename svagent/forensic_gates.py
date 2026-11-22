"""FJ 三道试点取证法官 — 把「填表裁判」变成「取证法官」（审计 F1 的最高杠杆处置）。

三道门禁（criterion_origin / verification_boundary / proof_boundary）各暴露
adjudicate_* 入口：caller 交证据路径，门禁自己读原文、逐字命中预锁锚点、推导四维，
再交给原 check_* 按 R0–R6 裁决。原来的 check_* 一个字不改，保持 967 项测试全绿。

锚点来源（analysis-before-prereg 已锁存的一手原文，见各 audit 目录）：
  - criterion: audit_harnesspro/downloads/S01_arxiv_pdf.txt + S03_evaluation_raw.md
  - verification: audit_addy_critical_thinking/downloads/S01_52nlp_cn_fulltext.txt
  - proof: audit_flashprove/S01_official.txt + S03_readme.md
全部锚点已用探测脚本验证：disclose 锚点必命中、红旗 conceal 锚点零误命中。
诚实论文 → 推导全 yes → 与原 check_* 结论一致；篡改/删改证据 → partial 或 no → 降级。

诚实边界：只判「原文是否诚实披露了这些边界」，不承诺被审系统真有效（KB-R07/META01）；
红旗锚点是探测器而非伪造证据，命中明细全部进 forensic_trace 可人工复核。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .forensics import (
    EvidenceBundle, ForensicSpec, DimensionSpec, adjudicate as _adjudicate,
)
from .criterion_origin_honesty import (
    check_criterion_origin_honesty, CriterionOriginVerdict,
)
from .verification_boundary_honesty import (
    check_verification_boundary_honesty, VerificationBoundaryVerdict,
)
from .proof_boundary_honesty import (
    check_proof_boundary_honesty, ProofBoundaryVerdict,
)

_ROOT = Path(__file__).resolve().parent.parent

# 中文/英文锚点集中在字典（AST 自审：Compare 内无中文字面量）
_A = {
    "criterion": {
        "criterion_origin_disclosed": (
            ("label-free", "LLM-generated tests", "TestSynth"),
            ("verified against official ground-truth labels",),
        ),
        "recall_boundary_disclosed": (
            ("failure recall increasing from 41.7% to 83.3%", "16.7%"),
            ("detects all failures", "100% failure recall"),
        ),
        "external_anchor_disclosed": (
            ("without access to ground-truth solutions or official tests",),
            ("no external anchor needed", "fully self-contained evaluation"),
        ),
        "independent_reviewer_gap_disclosed": (
            ("No separate reviewer is part of this run", "do not launch another reviewer"),
            ("reviewed by independent experts",),
        ),
    },
    "verification": {
        "coverage_scope_disclosed": (
            ("绿灯只说明一件事", "它检查了什么？没检查什么？"),
            ("全面覆盖所有功能", "测试通过即代表完全正确"),
        ),
        "criteria_predefined": (
            ("提前定义什么叫", "等到事后，你会为任何结果找到合理的解释"),
            ("事后补充完成标准", "先完成再定义通过条件"),
        ),
        "evidence_before_summary": (
            ("先看实际执行了什么命令，以及命令返回了什么",
             "先读它运行了什么、返回了什么，再看总结"),
            ("先看总结，不看命令",),
        ),
        "self_questioning_done": (
            ("我遗漏了什么吗",),
            ("无需再检查", "一次通过不必复查"),
        ),
    },
    "proof": {
        "proves_execution_not_fact": (
            ("computation was executed correctly",),
            ("proves the answer is factually correct", "guarantees output correctness"),
        ),
        "commitment_anchor_independent": (
            ("The commitment to the model",),
            ("self-issued commitment", "provider defines its own trust root"),
        ),
        "formal_scope_disclosed": (
            ("The protocol's soundness is proved in Lean 4", "carries no formal guarantee"),
            ("fully formally verified end to end",),
        ),
        "uncovered_disclosed": (
            ("A research artifact: not maintained, not accepting contributions",
             "Side channel attacks",
             "The proof is about an integer model under greedy decoding"),
            ("covers all decoding strategies", "no limitations"),
        ),
    },
}

# 默认证据路径（相对仓库根），caller 可覆盖
_DEFAULT_SOURCES = {
    "criterion": [
        "audit_harnesspro/downloads/S01_arxiv_pdf.txt",
        "audit_harnesspro/downloads/S03_evaluation_raw.md",
    ],
    "verification": [
        "audit_addy_critical_thinking/downloads/S01_52nlp_cn_fulltext.txt",
    ],
    "proof": [
        "audit_flashprove/S01_official.txt",
        "audit_flashprove/S03_readme.md",
    ],
}


def _spec(gate_key: str) -> ForensicSpec:
    dims = tuple(
        DimensionSpec(name, tuple(disc), tuple(conc))
        for name, (disc, conc) in _A[gate_key].items()
    )
    return ForensicSpec(gate=f"forensic.{gate_key}", dimensions=dims)


def default_sources(gate_key: str) -> list[str]:
    """返回该门禁默认证据的绝对路径（供 CLI / 外部调用）。"""
    return [str(_ROOT / p) for p in _DEFAULT_SOURCES[gate_key]]


# 证据目录（取证前强制校验三锁）；默认证据即取自这些目录
_AUDIT_DIR = {
    "criterion": "audit_harnesspro",
    "verification": "audit_addy_critical_thinking",
    "proof": "audit_flashprove",
}


def _require_chain(gate_key: str, enforce: bool, sources: list[str] | None = None) -> dict[str, Any] | None:
    """取证前校验：prereg/gate_prereg 二锁必过 + 实际证据源文件哈希匹配；失配即拒判。

    对清单代 manifest 的历史目录（如 flashprove），不再要求整份清单全缓存——
    改为 verify_sources() 精确校验本次用到的证据文件，既不放水也不误判。
    """
    if not enforce:
        return None
    from .evidence_chain import verify_chain, verify_sources, ChainIntegrityError
    d = _ROOT / _AUDIT_DIR[gate_key]
    report = verify_chain(d)
    # 二核心锁（prereg/gate_prereg）必须 ok
    core_ok = all(c.ok for c in report.locks if c.lock.startswith(("prereg", "gate_prereg")))
    # 证据源文件精确校验
    src_check = verify_sources(d, sources or default_sources(gate_key))
    if not core_ok:
        bad = [c.lock + ":" + c.detail for c in report.locks
               if c.lock.startswith(("prereg", "gate_prereg")) and not c.ok]
        raise ChainIntegrityError(f"核心锁失配，拒绝取证: {d} | " + "; ".join(bad))
    if src_check["tampered"]:
        raise ChainIntegrityError(f"证据源文件已篡改，拒绝取证: {d} | {src_check['tampered']}")
    # 如证据无锁记录（个别目录），如实标注但不阻断——已由核心锁+哈希溯源覆盖
    return {"chain": report.to_dict(), "source_verification": src_check}


def adjudicate_criterion_origin_honesty(
    claim: str = "HarnessPro self-generated criterion assessment",
    sources: list[str] | None = None,
    enforce_chain: bool = True,
) -> tuple[CriterionOriginVerdict, dict[str, Any]]:
    """取证版判据来源诚实性：验三锁→读 HarnessPro 原文自取四维→原 check_* 裁决。"""
    eff_sources = sources or default_sources("criterion")
    chain = _require_chain("criterion", enforce_chain, eff_sources)
    bundle = EvidenceBundle.from_files(eff_sources)
    verdict, trace = _adjudicate(bundle, _spec("criterion"),
                                 check_criterion_origin_honesty, claim,
                                 evidence_scope="preprint(KB-RSI07折1)")
    if chain:
        trace.update(chain)
    return verdict, trace


def adjudicate_verification_boundary_honesty(
    claim: str = "Agent completion claim: green tests",
    sources: list[str] | None = None,
    enforce_chain: bool = True,
) -> tuple[VerificationBoundaryVerdict, dict[str, Any]]:
    """取证版验证边界诚实性：验三锁→读 Addy Osmani 中文全文自取四维→原 check_* 裁决。"""
    eff_sources = sources or default_sources("verification")
    chain = _require_chain("verification", enforce_chain, eff_sources)
    bundle = EvidenceBundle.from_files(eff_sources)
    verdict, trace = _adjudicate(bundle, _spec("verification"),
                                 check_verification_boundary_honesty, claim,
                                 evidence_scope="primary(公众号中文全文,二手交叉5/5)")
    if chain:
        trace.update(chain)
    return verdict, trace


def adjudicate_proof_boundary_honesty(
    claim: str = "FlashProve proof-carrying inference",
    sources: list[str] | None = None,
    enforce_chain: bool = True,
) -> tuple[ProofBoundaryVerdict, dict[str, Any]]:
    """取证版证明边界诚实性：验三锁→读 Anthropic 官方页+README 自取四维→原 check_* 裁决。"""
    eff_sources = sources or default_sources("proof")
    chain = _require_chain("proof", enforce_chain, eff_sources)
    bundle = EvidenceBundle.from_files(eff_sources)
    verdict, trace = _adjudicate(bundle, _spec("proof"), check_proof_boundary_honesty, claim,
                                 evidence_scope="primary(官方页+技术报告+code-adjacent README)")
    if chain:
        trace.update(chain)
    return verdict, trace


_ALL = {
    "criterion": adjudicate_criterion_origin_honesty,
    "verification": adjudicate_verification_boundary_honesty,
    "proof": adjudicate_proof_boundary_honesty,
}


def adjudicate_all() -> dict[str, dict[str, Any]]:
    """一次性跑完三道取证法官，返回 {gate: {action, code, trace}}。"""
    out: dict[str, dict[str, Any]] = {}
    for key, fn in _ALL.items():
        verdict, trace = fn()
        out[key] = {
            "action": verdict.action, "code": verdict.code,
            "inferred": trace["inferred"], "evidence_scope": trace["evidence_scope"],
            "sources": trace["sources"],
        }
    return out


def live_regression() -> dict:
    """FJ 试点自测：真实证据→ok；篡改证据→降级/flag；原 check_* 向后兼容。"""
    checks: dict[str, bool] = {}

    # 1) 三道真实证据推导结果应与原精研一致（诚实论文 → ok）
    allres = adjudicate_all()
    checks["real_evidence_ok"] = all(v["action"] == "ok" for v in allres.values())

    # 2) 篡改：删掉 recall 边界披露锚点 → 该维 partial → 原门禁 flag
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "tampered.txt"
        # 只保留其余三维披露锚点，recall 维的披露锚点被删且不放红旗
        # → recall 维 partial → 原门禁 R5 flag（取证不足，绝不补 yes）
        bad.write_text(
            "We use label-free LLM-generated tests with TestSynth. "
            "No separate reviewer is part of this run. "
            "without access to ground-truth solutions or official tests.",
            encoding="utf-8",
        )
        v, tr = adjudicate_criterion_origin_honesty(sources=[str(bad)])
        checks["tamper_recall_flag"] = (
            tr["inferred"]["recall_boundary_disclosed"] == "partial"
            and v.action == "flag"
        )
        checks["tamper_trace_has_sha"] = bool(tr["source_sha256"])

    # 2b) 红旗命中 recall 维（冒充全覆盖）→ no → 原门禁 R2 downgrade
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "redflag_recall.txt"
        bad.write_text(
            "We use label-free LLM-generated tests with TestSynth. "
            "No separate reviewer is part of this run. "
            "without access to ground-truth solutions or official tests. "
            "we claim 100% failure recall, detects all failures.",
            encoding="utf-8",
        )
        v, tr = adjudicate_criterion_origin_honesty(sources=[str(bad)])
        checks["red_flag_recall_downgrade"] = (
            tr["inferred"]["recall_boundary_disclosed"] == "no"
            and v.action == "downgrade"
        )

    # 3) 红旗命中：注入「独立评审」冒充 → independent 维 no → downgrade
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "fake.txt"
        bad.write_text(
            "label-free LLM-generated tests TestSynth. "
            "failure recall increasing from 41.7% to 83.3% 16.7%. "
            "without access to ground-truth solutions or official tests. "
            "reviewed by independent experts.",
            encoding="utf-8",
        )
        v, tr = adjudicate_criterion_origin_honesty(sources=[str(bad)])
        checks["red_flag_downgrade"] = (
            tr["inferred"]["independent_reviewer_gap_disclosed"] == "no"
            and v.action == "downgrade"
        )

    return {"checks": checks, "cases": allres, "all_passed": all(checks.values())}
