"""FJ 取证法官扩展入口 7 — 自主运维第七轮新增的第十道（§96）。

不改动已锁存的 forensic_gates.py / ext.py / ext2.py / ext3.py / ext4.py / ext5.py / ext6.py；
本模块承载 skill_lifecycle 的 adjudicate_* 入口，
复用同一 forensics.adjudicate 内核与 evidence_chain 链校验。

锚点取自 arXiv:2610.09832v2 全文（audit_skill_lifecycle_honesty/downloads/paper_flat.txt），
摘要段 + 附录 H 逐字校准：disclose 锚点全部命中、红旗 conceal 锚点零误命中。
诚实框架 → 推导全 yes → ok；篡改/删改 → partial/no → 降级。

诚实边界：只判原文是否诚实披露四演化治理边界，不承诺 lifecycle 真实有效
（KB-R07/META01，self-reported 7.8% 折 1）；
红旗是探测器不是伪造证据，命中明细进 trace 可人工复核。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .forensics import (
    EvidenceBundle, ForensicSpec, DimensionSpec, adjudicate as _adjudicate,
)
from .skill_lifecycle_honesty import (
    check_skill_lifecycle_honesty,
    SkillLifecycleVerdict,
)

_ROOT = Path(__file__).resolve().parent.parent

# 锚点集中字典（AST 自审：Compare 内无中文字面量）
_A = {
    "lifecycle_stages_disclosed": (
        ("fitness-driven skill lifecycle of trial , active , stable , and retired states",
         "pre-retire low-fitness skills"),
        ("every skill is retained indiscriminately forever with no fitness lifecycle",
         "obsolete and harmful entries are never retired and keep misleading the agent"),
    ),
    "credit_assignment_audited": (
        ("Eq. ( 7 ) attributes one binary reward to all K K co-retrieved skills. We test this approximation in two ways",
         "replaces Eq. ( 7 ) with each skill ’s leave-one-out marginal contribution over its co-retrieval sets"),
        ("the shared reward is assumed exact and no credit approximation test is reported",
         "co-retrieved skills all receive full credit with no leave-one-out or single-skill stress test"),
    ),
    "mutation_teacher_controlled": (
        ("grant SkillRL the same B B rewrites appended to its library with no lifecycle gate",
         "Table 12 : Teacher capability for LLM-guided mutation"),
        ("the teacher gain is credited to the lifecycle with no matched rewrite-budget control",
         "mutation uses an external teacher and no teacher-capability ablation is reported"),
    ),
    "retirement_failure_attributed": (
        ("retirement events with human-annotated failure categories",
         "the remaining 96.9% contain prescriptions inconsistent with successful rollouts"),
        ("retirement events are counted but no failure categories or reasons are given",
         "skills are retired without recording why they became obsolete"),
    ),
}

_DEFAULT_SOURCES = ["audit_skill_lifecycle_honesty/downloads/paper_flat.txt"]
_AUDIT_DIR = "audit_skill_lifecycle_honesty"


def _spec() -> ForensicSpec:
    dims = tuple(
        DimensionSpec(name, tuple(disc), tuple(conc))
        for name, (disc, conc) in _A.items()
    )
    return ForensicSpec(gate="forensic.skill_lifecycle", dimensions=dims)


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


def adjudicate_skill_lifecycle_honesty(
    claim: str = "Skill library evolution lifecycle disclosure claim",
    sources: list[str] | None = None,
    enforce_chain: bool = True,
) -> tuple[SkillLifecycleVerdict, dict[str, Any]]:
    """取证版技能演化诚实性：验三锁→读 arXiv 全文自取四维→原 check_* 裁决。"""
    eff_sources = sources or default_sources()
    chain = _require_chain(enforce_chain, eff_sources)
    bundle = EvidenceBundle.from_files(eff_sources)
    verdict, trace = _adjudicate(bundle, _spec(),
                                 check_skill_lifecycle_honesty, claim,
                                 evidence_scope="primary(arXiv abs+全文附录H,self-reported 7.8%折1)")
    if chain:
        trace.update(chain)
    return verdict, trace


def live_regression() -> dict:
    """取证自测：真实证据→ok；删披露锚点→partial→flag；红旗→no→降级；链失配拒判。"""
    import tempfile
    checks: dict[str, bool] = {}

    # 1) 真实证据 → ok
    v, tr = adjudicate_skill_lifecycle_honesty()
    checks["real_evidence_ok"] = (v.action == "ok" and v.code == "SKILL_LIFE.SELF_CONSISTENT")

    # 2) 篡改：删掉 retirement_failure_attributed 维披露锚点 → 该维 partial → flag（其余三维保留）
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "tampered.txt"
        bad.write_text(
            "fitness-driven skill lifecycle of trial , active , stable , and retired states, "
            "pre-retire low-fitness skills. "
            "Eq. ( 7 ) attributes one binary reward to all K K co-retrieved skills. We test this approximation in two ways. "
            "replaces Eq. ( 7 ) with each skill ’s leave-one-out marginal contribution over its co-retrieval sets. "
            "grant SkillRL the same B B rewrites appended to its library with no lifecycle gate. "
            "Table 12 : Teacher capability for LLM-guided mutation.",
            encoding="utf-8",
        )
        v2, tr2 = adjudicate_skill_lifecycle_honesty(sources=[str(bad)])
        checks["tamper_partial_flag"] = (
            tr2["inferred"]["retirement_failure_attributed"] == "partial" and v2.action == "flag"
        )
        checks["tamper_trace_has_sha"] = bool(tr2["source_sha256"])

    # 3) 红旗命中：注入「无差别保留/信用分配假设精确」→ stages 维 no → downgrade
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "redflag.txt"
        bad.write_text(
            "every skill is retained indiscriminately forever with no fitness lifecycle, "
            "obsolete and harmful entries are never retired and keep misleading the agent. "
            "Eq. ( 7 ) attributes one binary reward to all K K co-retrieved skills. We test this approximation in two ways. "
            "grant SkillRL the same B B rewrites appended to its library with no lifecycle gate. "
            "retirement events with human-annotated failure categories.",
            encoding="utf-8",
        )
        v3, tr3 = adjudicate_skill_lifecycle_honesty(sources=[str(bad)])
        checks["red_flag_downgrade"] = (
            tr3["inferred"]["lifecycle_stages_disclosed"] == "no" and v3.action == "downgrade"
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
            adjudicate_skill_lifecycle_honesty()
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
