"""记忆巩固治理诚实性门禁 — 把 arXiv:2609.33013 编译成会拦的动作（自主运维第三轮 §92）。

一手证据（见 audit_memory_epistemics/）：
  - S01 abs + S02 全文（arXiv:2609.33013v1，四阶段研究纲领）。
  - 中心发现是"测量什么"的转移：从记得多少 → 巩固决策好不好 → 决策能不能被信任。
  - Phase1 情景边界学习是 honest near-miss（oracle correlation 0.691 vs 0.70 bar），
    持久产出是三道抗泄漏协议；Phase2 token 预算下的晋升/压缩 +22.7% 但暴露
    degenerate-forgetting 与 lambda-prevalence coupling；Phase3 ConsolidationBench
    oracle-by-construction 三非循环轴，生产检索系统"retain information yet score zero
    on cross-level transfer"；Phase4 governed consolidation（poison-resistant /
    reversible / auditable + quality gate），治理轴与质量分统计可分离（r²=0.43 /
    partial r=0.27 / 同质量策略治理差三倍）；外部效度 resolved negative（质量分不预测
    真实迁移 ρ=-0.24, 95% CI 跨零, 三轴各自都失败）；对抗自审 zero surviving overclaims。

为什么是新牙（对比已有记忆门禁）：
  memory_curation(内容质量) / memory_scope(作用域) / memory_provenance_honesty(溯源)
  / policy_evolution_grounding(策略接地) 都不判"巩固决策的可信性(epistemics)"：
    ①巩固质量是否被单独测量（oracle 锚/非循环轴 vs 只报召回量）；
    ②治理保证是否与质量分统计可分离（贡献不依赖质量分外部效度）；
    ③负结果是否如实披露（质量分不预测真实迁移，而非只报正面）；
    ④near-miss 是否诚实（0.691 vs 0.70 bar）+ 对抗自审清 overclaims。
  尺子对象是"任何长时程 agent memory 巩固决策"——可迁移、会拦，KB-META01 会拦才入。

编译纪律（与 gate_prereg.json 一致，实现前 SHA256 锁存 163c4663…）：
  - 语义枚举；字面串→flag(R0)；R0-R6 短路返回，不事后加权(防 Goodhart)；
  - 只判"边界声明是否诚实自洽"，不承诺方法真实有效(KB-R07/META01)；
    self-reported 增益(+22.7%/7×压缩)按 KB-RSI07 折 1。

诚实边界：定位为审读外部记忆巩固研究的尺子，不判本仓；遵循 §58 选 A 不接 run_loop。
"""
from __future__ import annotations

from dataclasses import dataclass

_ENUM = frozenset({"yes", "no", "partial"})

# 中文文案字典：Compare 内不放中文字面量（AST 自审纪律）
_A = {
    "invalid_input": (
        "MEM_CONSOLIDATION.INVALID_INPUT",
        "四维须为 yes/no/partial 语义枚举；非法值（含字面串）→ flag，不进内容判定",
    ),
    "quality_not_separated": (
        "MEM_CONSOLIDATION.QUALITY_NOT_SEPARATED",
        "未单独测量巩固决策质量（无 oracle 锚/非循环轴，只报记得多少/召回率）——把留存量冒充巩固质量",
    ),
    "governance_absorbed": (
        "MEM_CONSOLIDATION.GOVERNANCE_ABSORBED",
        "治理（poison-resistant/reversible/auditable）被质量分完全吸收、无统计分离证据——贡献依赖质量分外部效度",
    ),
    "negative_hidden": (
        "MEM_CONSOLIDATION.NEGATIVE_HIDDEN",
        "负结果隐瞒（如质量分不预测真实迁移 ρ=-0.24 CI 跨零不披露）——只报正面，过度宣称",
    ),
    "near_miss_papered": (
        "MEM_CONSOLIDATION.NEAR_MISS_PAPERED",
        "near-miss 包装成达标（0.691 vs 0.70 bar 不 disclosed）或无对抗自审清 overclaims——反后知缺失",
    ),
    "partial": (
        "MEM_CONSOLIDATION.PARTIAL",
        "记忆巩固 epistemics 边界披露覆盖不全(partial)——拦截面存在但缺口未补齐，待核",
    ),
    "ok": (
        "MEM_CONSOLIDATION.SELF_CONSISTENT",
        "四维边界声明自洽——只判声明诚实存在，不承诺方法真实有效(存在≠有效性)",
    ),
}


@dataclass(frozen=True)
class MemoryConsolidationGovernanceVerdict:
    claim: str
    consolidation_quality_separated: str
    governance_quality_split: str
    negative_result_disclosed: str
    near_miss_and_overclaim_guarded: str
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_memory_consolidation_governance_honesty(
    claim: str,
    *,
    consolidation_quality_separated: str,
    governance_quality_split: str,
    negative_result_disclosed: str,
    near_miss_and_overclaim_guarded: str,
) -> MemoryConsolidationGovernanceVerdict:
    """判一个记忆巩固研究/系统是否诚实披露四个 epistemics 边界（不承诺有效）。

    输入须为语义枚举：四维 ∈ {yes, no, partial}

    规则按优先级短路返回（与 gate_prereg.json R0-R6 一致）：
      R0 任一非枚举 → flag
      R1 consolidation_quality_separated=no → downgrade（留存量冒充巩固质量）
      R2 governance_quality_split=no → downgrade（治理被质量分吸收/无保证）
      R3 negative_result_disclosed=no → flag（负结果隐瞒）
      R4 near_miss_and_overclaim_guarded=no → flag（near-miss 包装/无自审）
      R5 任一 partial → flag（覆盖不全，待核）
      R6 全 yes → ok（只判声明自洽）
    """
    vals = (consolidation_quality_separated, governance_quality_split,
            negative_result_disclosed, near_miss_and_overclaim_guarded)
    if any(v not in _ENUM for v in vals):
        code, msg = _A["invalid_input"]
        return MemoryConsolidationGovernanceVerdict(claim, *(str(v) for v in vals), "flag", code, msg)
    if consolidation_quality_separated == "no":
        code, msg = _A["quality_not_separated"]
        return MemoryConsolidationGovernanceVerdict(claim, *vals, "downgrade", code, msg)
    if governance_quality_split == "no":
        code, msg = _A["governance_absorbed"]
        return MemoryConsolidationGovernanceVerdict(claim, *vals, "downgrade", code, msg)
    if negative_result_disclosed == "no":
        code, msg = _A["negative_hidden"]
        return MemoryConsolidationGovernanceVerdict(claim, *vals, "flag", code, msg)
    if near_miss_and_overclaim_guarded == "no":
        code, msg = _A["near_miss_papered"]
        return MemoryConsolidationGovernanceVerdict(claim, *vals, "flag", code, msg)
    if any(v == "partial" for v in vals):
        code, msg = _A["partial"]
        return MemoryConsolidationGovernanceVerdict(claim, *vals, "flag", code, msg)
    code, msg = _A["ok"]
    return MemoryConsolidationGovernanceVerdict(claim, *vals, "ok", code, msg)


def live_regression() -> dict:
    """7 个活体样例回归——对齐 gate_prereg.json 的 R0-R6 预期。"""
    cases = {
        "quality_not_separated": dict(consolidation_quality_separated="no", governance_quality_split="yes", negative_result_disclosed="yes", near_miss_and_overclaim_guarded="yes"),
        "governance_absorbed": dict(consolidation_quality_separated="yes", governance_quality_split="no", negative_result_disclosed="yes", near_miss_and_overclaim_guarded="yes"),
        "negative_hidden": dict(consolidation_quality_separated="yes", governance_quality_split="yes", negative_result_disclosed="no", near_miss_and_overclaim_guarded="yes"),
        "near_miss_papered": dict(consolidation_quality_separated="yes", governance_quality_split="yes", negative_result_disclosed="yes", near_miss_and_overclaim_guarded="no"),
        "partial_disclosure": dict(consolidation_quality_separated="yes", governance_quality_split="yes", negative_result_disclosed="partial", near_miss_and_overclaim_guarded="yes"),
        "literal_enum": dict(consolidation_quality_separated="maybe", governance_quality_split="yes", negative_result_disclosed="yes", near_miss_and_overclaim_guarded="yes"),
        "all_good": dict(consolidation_quality_separated="yes", governance_quality_split="yes", negative_result_disclosed="yes", near_miss_and_overclaim_guarded="yes"),
    }
    expects = {
        "quality_not_separated": ("downgrade", "MEM_CONSOLIDATION.QUALITY_NOT_SEPARATED"),
        "governance_absorbed": ("downgrade", "MEM_CONSOLIDATION.GOVERNANCE_ABSORBED"),
        "negative_hidden": ("flag", "MEM_CONSOLIDATION.NEGATIVE_HIDDEN"),
        "near_miss_papered": ("flag", "MEM_CONSOLIDATION.NEAR_MISS_PAPERED"),
        "partial_disclosure": ("flag", "MEM_CONSOLIDATION.PARTIAL"),
        "literal_enum": ("flag", "MEM_CONSOLIDATION.INVALID_INPUT"),
        "all_good": ("ok", "MEM_CONSOLIDATION.SELF_CONSISTENT"),
    }
    checks, detail = {}, {}
    for name, inp in cases.items():
        v = check_memory_consolidation_governance_honesty("live:" + name, **inp)
        exp_a, exp_c = expects[name]
        detail[name] = f"{v.action}/{v.code}"
        checks[name] = (v.action == exp_a and v.code == exp_c)
    return {"checks": checks, "cases": detail, "all_passed": all(checks.values())}
