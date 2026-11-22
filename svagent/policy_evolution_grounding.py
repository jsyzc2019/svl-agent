"""策略演化接地诚实性门禁 — 把多模态 Agent 记忆综述 T3 自演化的隐藏失效编译成会判动作（§79）。

一手证据（见 audit_multimodal_memory/，arXiv:2610.19366v1 HTML 全文，SHA256 a61a27ea…）：
  - §5.3 Representation Requirements for Self-Evolving Memory：
    "Self-evolution therefore depends on policy addressability, policy-level feedback
    attribution, and persistent, validated policy revision."
    "the part responsible for a recurring behavior must provide an identifiable target
    for revision"；"Explicit policy representations allow more precise revisions, whereas
    distributed representations make the effects of individual changes harder to isolate."
    "Feedback must therefore be sufficiently informative to distinguish failures of
    writing, maintenance, retrieval, reasoning, and action. A task-level reward alone may
    reveal that the agent failed without identifying which part of memory management should change."
    "A policy revision constitutes self-evolution only when it is retained as part of the
    reusable memory-management process and affects subsequent memory operations."
    "Maintaining policy versions and their evaluation histories also supports comparison,
    auditing, and restoration when a revision proves harmful."
    "Policy-level validation therefore requires subsequent, replayed, or held-out cases..."
  - §8.3.3 Policy Adaptation with Preserved Evidence Grounding：
    "A revised policy can maintain or even improve short-term answers while relying less
    on the modality that originally grounded them."（缓存文本摘要答题却很少重开视觉证据）
    "Current policy-evolution methods rarely evaluate whether adaptation changes the balance
    of evidence used across representations." —— 正确率保持 ≠ 接地未流失。
  - §5.4 语料规律：297 架构 T3=17(5.7%)，13 cross-represented + 4 hybrid(含显式)；
    source-only 与 latent/parametric-only 类别无 T3。项目主页口径：17 of 17 keep explicit memory。

为什么是新牙（对比现有门禁）：
  self_evolving.py 是本仓运行时递归判断机制，非审读尺子；memory_scope(§70) 判单条记忆
  写入时的适用边界；criterion_origin(§77) 判自评估系统的判据来源；selective_supervision(§78)
  判筛选器审查自身训练数据。以上均未判『管理策略本身演化时：策略是否可寻址、反馈是否
  归因到策略级、证据接地路径是否被静默削弱、修订是否经策略级验证并持久可回滚』。
  尺子对象是任何声称 T3 自演化记忆的系统，可迁移、会拦，KB-META01 通过。

编译纪律（gate_prereg.json SHA256 0f90b3e8…，实现前已锁存）：
  语义枚举；字面串→flag(R0)；R1-R4 按优先级 downgrade；R5 partial→flag；R6 全 yes→ok；
  只判机制声明是否诚实自洽，不承诺策略演化真带来收益（存在≠有效性 KB-META01/AUDIT03）；
  综述系二手综合，按 KB-RSI07 折1。

诚实边界：定位为审读外部"自演化记忆系统"的尺子，不判本仓；遵循 §58 选 A 不接 run_loop。
"""
from __future__ import annotations

from dataclasses import dataclass

_ENUM = frozenset({"yes", "no", "partial"})

# 中文锚点集中管理：避免 AST 自审误伤 Compare 内的中文字面量
_A = {
    "invalid": "四维须为 yes/no/partial 语义枚举；非法值（含字面串）→ flag，不进内容判定",
    "unaddressable": "记忆管理策略不可寻址(负责反复行为的策略无显式可识别修订目标，藏在分布式表示中难隔离)→ §5.3 自演化前提缺失，判定打折",
    "feedback": "反馈仅任务级奖励、未归因到策略级(未连接结果/记忆内容/管理决策/策略组件与版本，无法区分写/维护/检索/推理/行动失败)→ §5.3 策略级归因缺失，判定打折",
    "evidence": "策略演化削弱证据接地路径未披露(短期正确率不降反升却更少依赖最初接地的模态，如缓存文本摘要替代视觉证据)→ §8.3.3 正确率≠接地保持，判定打折",
    "revision": "策略修订未经策略级验证或不可持久回滚(修好一条记录即宣称策略改进、无版本/评估历史/留出案例)→ §5.3 持久且经验证的修订缺失，判定打折",
    "partial": "策略演化接地机制声明覆盖不全(partial)——拦截面存在但缺口未补齐，待核",
    "ok": "四维策略演化接地声明自洽——只判声明诚实存在，不承诺演化真带来收益(存在≠有效性)",
}


@dataclass(frozen=True)
class PolicyEvolutionGroundingVerdict:
    claim: str
    policy_addressable: str
    feedback_attributable: str
    evidence_path_preserved: str
    revision_validated_persisted: str
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_policy_evolution_grounding(
    claim: str,
    *,
    policy_addressable: str,
    feedback_attributable: str,
    evidence_path_preserved: str,
    revision_validated_persisted: str,
) -> PolicyEvolutionGroundingVerdict:
    """判一个声称 T3 自演化记忆的系统是否诚实处理"策略演化与证据接地"。

    输入须为语义枚举：四维 ∈ {yes, no, partial}

    规则按优先级短路返回（与 gate_prereg.json R0-R6 一致）：
      R0 任一非枚举 → flag
      R1 policy_addressable=no → downgrade（策略不可寻址）
      R2 feedback_attributable=no → downgrade（反馈未归因到策略级）
      R3 evidence_path_preserved=no → downgrade（证据接地路径被静默削弱）
      R4 revision_validated_persisted=no → downgrade（修订未经验证/不可持久）
      R5 任一 partial → flag
      R6 全 yes → ok（只判机制声明自洽）
    """
    vals = (policy_addressable, feedback_attributable,
            evidence_path_preserved, revision_validated_persisted)
    if any(v not in _ENUM for v in vals):
        return PolicyEvolutionGroundingVerdict(
            claim, *(str(v) for v in vals),
            "flag", "POLICY_EVOLUTION.INVALID_INPUT", _A["invalid"],
        )
    if policy_addressable == "no":
        return PolicyEvolutionGroundingVerdict(
            claim, *vals, "downgrade", "POLICY_EVOLUTION.POLICY_UNADDRESSABLE", _A["unaddressable"],
        )
    if feedback_attributable == "no":
        return PolicyEvolutionGroundingVerdict(
            claim, *vals, "downgrade", "POLICY_EVOLUTION.FEEDBACK_NOT_ATTRIBUTABLE", _A["feedback"],
        )
    if evidence_path_preserved == "no":
        return PolicyEvolutionGroundingVerdict(
            claim, *vals, "downgrade", "POLICY_EVOLUTION.EVIDENCE_PATH_ERODED", _A["evidence"],
        )
    if revision_validated_persisted == "no":
        return PolicyEvolutionGroundingVerdict(
            claim, *vals, "downgrade", "POLICY_EVOLUTION.REVISION_UNVALIDATED", _A["revision"],
        )
    if any(v == "partial" for v in vals):
        return PolicyEvolutionGroundingVerdict(
            claim, *vals, "flag", "POLICY_EVOLUTION.PARTIAL", _A["partial"],
        )
    return PolicyEvolutionGroundingVerdict(
        claim, *vals, "ok", "POLICY_EVOLUTION.SELF_CONSISTENT", _A["ok"],
    )


def live_regression() -> dict:
    """7 个活体样例回归——对齐 gate_prereg.json R0-R6 预期。"""
    cases = {
        "policy_unaddressable": dict(policy_addressable="no", feedback_attributable="yes", evidence_path_preserved="yes", revision_validated_persisted="yes"),
        "feedback_not_attributable": dict(policy_addressable="yes", feedback_attributable="no", evidence_path_preserved="yes", revision_validated_persisted="yes"),
        "evidence_eroded": dict(policy_addressable="yes", feedback_attributable="yes", evidence_path_preserved="no", revision_validated_persisted="yes"),
        "revision_unvalidated": dict(policy_addressable="yes", feedback_attributable="yes", evidence_path_preserved="yes", revision_validated_persisted="no"),
        "partial_disclosure": dict(policy_addressable="yes", feedback_attributable="yes", evidence_path_preserved="partial", revision_validated_persisted="yes"),
        "literal_enum": dict(policy_addressable="maybe", feedback_attributable="yes", evidence_path_preserved="yes", revision_validated_persisted="yes"),
        "all_good": dict(policy_addressable="yes", feedback_attributable="yes", evidence_path_preserved="yes", revision_validated_persisted="yes"),
    }
    expects = {
        "policy_unaddressable": ("downgrade", "POLICY_EVOLUTION.POLICY_UNADDRESSABLE"),
        "feedback_not_attributable": ("downgrade", "POLICY_EVOLUTION.FEEDBACK_NOT_ATTRIBUTABLE"),
        "evidence_eroded": ("downgrade", "POLICY_EVOLUTION.EVIDENCE_PATH_ERODED"),
        "revision_unvalidated": ("downgrade", "POLICY_EVOLUTION.REVISION_UNVALIDATED"),
        "partial_disclosure": ("flag", "POLICY_EVOLUTION.PARTIAL"),
        "literal_enum": ("flag", "POLICY_EVOLUTION.INVALID_INPUT"),
        "all_good": ("ok", "POLICY_EVOLUTION.SELF_CONSISTENT"),
    }
    checks, detail = {}, {}
    for name, inp in cases.items():
        v = check_policy_evolution_grounding("live:" + name, **inp)
        exp_a, exp_c = expects[name]
        detail[name] = f"{v.action}/{v.code}"
        checks[name] = (v.action == exp_a and v.code == exp_c)
    return {"checks": checks, "cases": detail, "all_passed": all(checks.values())}
