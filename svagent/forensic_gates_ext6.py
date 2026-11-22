"""FJ 取证法官扩展入口 6 — 自主运维第六轮新增的第九道（§95）。

不改动已锁存的 forensic_gates.py / ext.py / ext2.py / ext3.py / ext4.py / ext5.py；
本模块承载 goal_provenance 的 adjudicate_* 入口，
复用同一 forensics.adjudicate 内核与 evidence_chain 链校验。

锚点取自 arXiv:2610.16015v1 全文（audit_goal_provenance/downloads/paper_flat.txt），
已用探测脚本验证：14 个 disclose 锚点全部命中、红旗 conceal 锚点零误命中
（ALL_ANCHORS_CLEAN=True；逐字取自 ARE 摘要）。
诚实框架 → 推导全 yes → ok；篡改/删改 → partial/no → 降级。

诚实边界：只判原文是否诚实披露四目标来源边界，不承诺框架真实有效
（KB-R07/META01，self-reported 降幅折 1）；
红旗是探测器不是伪造证据，命中明细进 trace 可人工复核。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .forensics import (
    EvidenceBundle, ForensicSpec, DimensionSpec, adjudicate as _adjudicate,
)
from .goal_provenance_honesty import (
    check_goal_provenance_honesty,
    GoalProvenanceVerdict,
)

_ROOT = Path(__file__).resolve().parent.parent

# 锚点集中字典（AST 自审：Compare 内无中文字面量）
_A = {
    "value_source_attributed": (
        ("links principles from the system prompt and operator policy",
         "provenance assigned by the harness encodes the instruction hierarchy"),
        ("the agent invents its own ultimate values from nothing with no external source",
         "goals require no attribution to any prompt, policy, or provenance"),
    ),
    "self_generated_not_self_authorized": (
        ("considered judgments about the case, tool evidence, and candidate actions",
         "Governance enters through the configuration of the harness, including value priorities, the authority of each source, prohibitions, human-in-the-loop triggers"),
        ("any goal the agent writes for itself is thereby authorized without governance",
         "self-generated objectives need no source authority or human-in-the-loop trigger"),
    ),
    "reflection_equilibrium_coherent": (
        ("every claim that is free to change is supported on balance if accepted and opposed on balance if rejected",
         "equilibria are Nash equilibria of a mutual-adjustment game"),
        ("the agent simply reasserts its own goals in a self-confirming loop",
         "claims are accepted because the agent generated them, without any balance of support and attack"),
    ),
    "action_attributable": (
        ("certificates that attribute each action to the sources whose commitments drove it",
         "a quarantine theorem for prompt injection"),
        ("actions need no attribution to the sources that drove them",
         "injected instructions flow through unchanged with no quarantine"),
    ),
}

_DEFAULT_SOURCES = ["audit_goal_provenance/downloads/paper_flat.txt"]
_AUDIT_DIR = "audit_goal_provenance"


def _spec() -> ForensicSpec:
    dims = tuple(
        DimensionSpec(name, tuple(disc), tuple(conc))
        for name, (disc, conc) in _A.items()
    )
    return ForensicSpec(gate="forensic.goal_provenance", dimensions=dims)


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


def adjudicate_goal_provenance_honesty(
    claim: str = "Agent goal-setting provenance disclosure claim",
    sources: list[str] | None = None,
    enforce_chain: bool = True,
) -> tuple[GoalProvenanceVerdict, dict[str, Any]]:
    """取证版目标来源诚实性：验三锁→读 arXiv 全文自取四维→原 check_* 裁决。"""
    eff_sources = sources or default_sources()
    chain = _require_chain(enforce_chain, eff_sources)
    bundle = EvidenceBundle.from_files(eff_sources)
    verdict, trace = _adjudicate(bundle, _spec(),
                                 check_goal_provenance_honesty, claim,
                                 evidence_scope="primary(arXiv abs+全文,self-reported降幅折1)")
    if chain:
        trace.update(chain)
    return verdict, trace


def live_regression() -> dict:
    """取证自测：真实证据→ok；删披露锚点→partial→flag；红旗→no→降级；链失配拒判。"""
    import tempfile
    checks: dict[str, bool] = {}

    # 1) 真实证据 → ok
    v, tr = adjudicate_goal_provenance_honesty()
    checks["real_evidence_ok"] = (v.action == "ok" and v.code == "GOAL_PROV.SELF_CONSISTENT")

    # 2) 篡改：删掉 action_attributable 维披露锚点 → 该维 partial → flag（其余三维保留）
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "tampered.txt"
        bad.write_text(
            "links principles from the system prompt and operator policy, "
            "provenance assigned by the harness encodes the instruction hierarchy. "
            "considered judgments about the case, tool evidence, and candidate actions. "
            "Governance enters through the configuration of the harness, including value priorities, the authority of each source, prohibitions, human-in-the-loop triggers. "
            "every claim that is free to change is supported on balance if accepted and opposed on balance if rejected, "
            "equilibria are Nash equilibria of a mutual-adjustment game.",
            encoding="utf-8",
        )
        v2, tr2 = adjudicate_goal_provenance_honesty(sources=[str(bad)])
        checks["tamper_partial_flag"] = (
            tr2["inferred"]["action_attributable"] == "partial" and v2.action == "flag"
        )
        checks["tamper_trace_has_sha"] = bool(tr2["source_sha256"])

    # 3) 红旗命中：注入「凭空自封目标/无来源」→ source 维 no → downgrade
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "redflag.txt"
        bad.write_text(
            "the agent invents its own ultimate values from nothing with no external source, "
            "goals require no attribution to any prompt, policy, or provenance. "
            "considered judgments about the case, tool evidence, and candidate actions. "
            "every claim that is free to change is supported on balance if accepted and opposed on balance if rejected. "
            "certificates that attribute each action to the sources whose commitments drove it.",
            encoding="utf-8",
        )
        v3, tr3 = adjudicate_goal_provenance_honesty(sources=[str(bad)])
        checks["red_flag_downgrade"] = (
            tr3["inferred"]["value_source_attributed"] == "no" and v3.action == "downgrade"
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
            adjudicate_goal_provenance_honesty()
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
