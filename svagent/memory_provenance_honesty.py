"""记忆溯源可恢复性诚实性门禁 — 把多模态 Agent 记忆综述的 provenance/temporal-validity 原则编译成会判动作（§80）。

一手证据（见 audit_multimodal_memory/，arXiv:2610.19366v1 HTML 全文，SHA256 a61a27ea…）：
  - §8.1.1 Recovering Supporting Evidence：
    "a substantial portion of the analyzed architectures do not retain a usable route back
    to the evidence from which their memories were formed."
    "Provenance is therefore seldom a designed property of the representation."
    "provenance should be treated as part of the representation itself rather than as optional metadata."
    "Abstraction should move from lossy compression toward recoverable representation."
  - §8.3（跨模态评测总结）：
    "The central memory property is therefore not recall volume alone, but recoverable
    provenance and temporal validity, since persistence without these safeguards can retain
    stale or weakly grounded evidence."
  - §5.2/§6 Conflict（记忆修订）：冲突需判断
    "whether an apparent conflict reflects a genuine change, an unreliable observation, or
    information that is valid only under a different temporal or situational context."
  - §6.6 Consistency and Coordination：
    "verifiability requires provenance and version information connecting the update to
    supporting evidence; reversibility requires an earlier version, operation log, checkpoint,
    or reconstructible source; and update propagation requires dependent artifacts to be refreshed
    or invalidated."

为什么是新牙（对比现有门禁）：
  memory_scope(§70) 判单条记忆写入时是否标注适用边界、读时是否核情境；retrieval_grounding
  判输出声明是否有引用支撑；memory_curation(§68) 判记忆内容质量治理；criterion_origin(§77)
  判自评估判据来源。以上均不判『记忆表示层是否把溯源/可恢复证据/时间有效性/可逆性当作
  结构属性设计，而非事后可选元数据』。尺子对象是任何声称记忆可验证/可纠错的长期记忆系统，
  可迁移、会拦，KB-META01 通过。

编译纪律（gate_prereg.json SHA256 0f90b3e8…，实现前已锁存）：
  语义枚举；字面串→flag(R0)；R1-R4 按优先级 downgrade；R5 partial→flag；R6 全 yes→ok；
  只判机制声明是否诚实自洽，不承诺记忆真可验证/可纠错（存在≠有效性 KB-META01/AUDIT03）；
  综述系二手综合，按 KB-RSI07 折1。

诚实边界：定位为审读外部"长期记忆系统"的尺子，不判本仓；遵循 §58 选 A 不接 run_loop。
"""
from __future__ import annotations

from dataclasses import dataclass

_ENUM = frozenset({"yes", "no", "partial"})

# 中文锚点集中管理：避免 AST 自审误伤 Compare 内的中文字面量
_A = {
    "invalid": "四维须为 yes/no/partial 语义枚举；非法值（含字面串）→ flag，不进内容判定",
    "optional": "溯源是事后可选元数据而非表示的结构属性(无 minimal provenance bundle:来源/如何产生/支持证据)→ §8.1.1 溯源少见被设计为表示属性，判定打折",
    "unrecoverable": "抽象记忆不保留回到形成它所依赖证据的可用路径(压缩不可恢复、源证据被丢弃)→ §8.1.1 证据不可恢复，判定打折",
    "temporal": "未跟踪时间有效性/冲突消解(不区分真实变化/不可靠观测/仅在不同时间或情境有效，保留陈旧或弱接地证据)→ §8.3 召回量≠可恢复溯源+时间有效性，判定打折",
    "irreversible": "记忆更新不可逆(无早期版本/操作日志/检查点/可重建源，无法审计或回滚)→ §6.6 可逆性缺失，判定打折",
    "partial": "记忆溯源机制声明覆盖不全(partial)——拦截面存在但缺口未补齐，待核",
    "ok": "四维记忆溯源声明自洽——只判声明诚实存在，不承诺记忆真可验证/可纠错(存在≠有效性)",
}


@dataclass(frozen=True)
class MemoryProvenanceVerdict:
    claim: str
    provenance_by_design: str
    evidence_recoverable: str
    temporal_validity_tracked: str
    reversibility_supported: str
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_memory_provenance_honesty(
    claim: str,
    *,
    provenance_by_design: str,
    evidence_recoverable: str,
    temporal_validity_tracked: str,
    reversibility_supported: str,
) -> MemoryProvenanceVerdict:
    """判一个声称记忆可验证/可纠错的系统是否把溯源当作表示的结构属性。

    输入须为语义枚举：四维 ∈ {yes, no, partial}

    规则按优先级短路返回（与 gate_prereg.json R0-R6 一致）：
      R0 任一非枚举 → flag
      R1 provenance_by_design=no → downgrade（溯源是可选元数据）
      R2 evidence_recoverable=no → downgrade（证据不可恢复）
      R3 temporal_validity_tracked=no → downgrade（时间有效性/冲突消解缺失）
      R4 reversibility_supported=no → downgrade（更新不可逆）
      R5 任一 partial → flag
      R6 全 yes → ok（只判机制声明自洽）
    """
    vals = (provenance_by_design, evidence_recoverable,
            temporal_validity_tracked, reversibility_supported)
    if any(v not in _ENUM for v in vals):
        return MemoryProvenanceVerdict(
            claim, *(str(v) for v in vals),
            "flag", "MEMORY_PROVENANCE.INVALID_INPUT", _A["invalid"],
        )
    if provenance_by_design == "no":
        return MemoryProvenanceVerdict(
            claim, *vals, "downgrade", "MEMORY_PROVENANCE.PROVENANCE_OPTIONAL", _A["optional"],
        )
    if evidence_recoverable == "no":
        return MemoryProvenanceVerdict(
            claim, *vals, "downgrade", "MEMORY_PROVENANCE.EVIDENCE_UNRECOVERABLE", _A["unrecoverable"],
        )
    if temporal_validity_tracked == "no":
        return MemoryProvenanceVerdict(
            claim, *vals, "downgrade", "MEMORY_PROVENANCE.TEMPORAL_INVALID", _A["temporal"],
        )
    if reversibility_supported == "no":
        return MemoryProvenanceVerdict(
            claim, *vals, "downgrade", "MEMORY_PROVENANCE.IRREVERSIBLE", _A["irreversible"],
        )
    if any(v == "partial" for v in vals):
        return MemoryProvenanceVerdict(
            claim, *vals, "flag", "MEMORY_PROVENANCE.PARTIAL", _A["partial"],
        )
    return MemoryProvenanceVerdict(
        claim, *vals, "ok", "MEMORY_PROVENANCE.SELF_CONSISTENT", _A["ok"],
    )


def live_regression() -> dict:
    """7 个活体样例回归——对齐 gate_prereg.json R0-R6 预期。"""
    cases = {
        "provenance_optional": dict(provenance_by_design="no", evidence_recoverable="yes", temporal_validity_tracked="yes", reversibility_supported="yes"),
        "evidence_unrecoverable": dict(provenance_by_design="yes", evidence_recoverable="no", temporal_validity_tracked="yes", reversibility_supported="yes"),
        "temporal_invalid": dict(provenance_by_design="yes", evidence_recoverable="yes", temporal_validity_tracked="no", reversibility_supported="yes"),
        "irreversible": dict(provenance_by_design="yes", evidence_recoverable="yes", temporal_validity_tracked="yes", reversibility_supported="no"),
        "partial_disclosure": dict(provenance_by_design="yes", evidence_recoverable="yes", temporal_validity_tracked="partial", reversibility_supported="yes"),
        "literal_enum": dict(provenance_by_design="yes", evidence_recoverable="maybe", temporal_validity_tracked="yes", reversibility_supported="yes"),
        "all_good": dict(provenance_by_design="yes", evidence_recoverable="yes", temporal_validity_tracked="yes", reversibility_supported="yes"),
    }
    expects = {
        "provenance_optional": ("downgrade", "MEMORY_PROVENANCE.PROVENANCE_OPTIONAL"),
        "evidence_unrecoverable": ("downgrade", "MEMORY_PROVENANCE.EVIDENCE_UNRECOVERABLE"),
        "temporal_invalid": ("downgrade", "MEMORY_PROVENANCE.TEMPORAL_INVALID"),
        "irreversible": ("downgrade", "MEMORY_PROVENANCE.IRREVERSIBLE"),
        "partial_disclosure": ("flag", "MEMORY_PROVENANCE.PARTIAL"),
        "literal_enum": ("flag", "MEMORY_PROVENANCE.INVALID_INPUT"),
        "all_good": ("ok", "MEMORY_PROVENANCE.SELF_CONSISTENT"),
    }
    checks, detail = {}, {}
    for name, inp in cases.items():
        v = check_memory_provenance_honesty("live:" + name, **inp)
        exp_a, exp_c = expects[name]
        detail[name] = f"{v.action}/{v.code}"
        checks[name] = (v.action == exp_a and v.code == exp_c)
    return {"checks": checks, "cases": detail, "all_passed": all(checks.values())}
