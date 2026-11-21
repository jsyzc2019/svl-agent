"""评估可靠性门禁 — 从 RSI-Structure 综述 §10.3/§10.5/§10.6 编译。

一手逐字依据（rsi_structure_full.txt）：
  §10.3 "Multiple model judges can share errors, so their number alone does not
         ensure independent judgments."
  §10.3 "Reports should record evaluator versions and the information available to them"
  §10.5 "Reproducing continued improvement requires records of the final system and
         of the update process."
  §10.6 "classifications ... have not been independently double-coded."

编译成两道会拦/会降级的动作：
  1. judge 独立性：多个 judge 若共享同一来源（同源模型/同源训练数据），其一致结论
     不算独立佐证 → downgrade。有效独立源数 < 2 即降级。
  2. 复现完整性/双编码：缺关键记录字段、或分类未经独立双编码 → flag 不可复现/信度不足。

设计纪律：只编译全文核对后新发现的缺口，不重复 component_attribution（组件归因）
与 improvement_memory（回归/命中率/上下文迁移）已有的判据。
"""
from __future__ import annotations

from dataclasses import dataclass, field


REPRODUCTION_FIELDS = (
    "models", "components", "tools", "tasks", "feedback_source",
    "edits_per_round", "candidate_selection", "data_at_each_stage",
    "evaluator_version", "costs", "failures", "rollback",
)


@dataclass
class JudgePanel:
    """一组评估者。n_judge 是数量，independent_sources 是真正独立的来源数。"""
    name: str
    n_judge: int
    independent_sources: int
    evaluator_version_recorded: bool = False
    evaluator_changed: bool = False
    rechecked_old_new: bool = False


@dataclass
class ReproRecord:
    """复现记录完整性声明。"""
    present_fields: set[str] = field(default_factory=set)
    double_coded: bool = False
    purposeful_selection_only: bool = False  # 仅目的性抽样、不估计流行率


@dataclass(frozen=True)
class ReliabilityVerdict:
    action: str      # ok | downgrade | flag
    code: str
    message: str


def judge_independence(panel: JudgePanel) -> ReliabilityVerdict:
    """judge 数量不等于独立判断数。"""
    if panel.evaluator_changed and not panel.rechecked_old_new:
        return ReliabilityVerdict(
            "downgrade", "REL.EVALUATOR_DRIFT",
            "评估标准/评估器变更后未用同一批任务重验新旧版本——分数变化可能来自标准本身（§10.3）",
        )
    if panel.n_judge >= 2 and panel.independent_sources < 2:
        return ReliabilityVerdict(
            "downgrade", "REL.SHARED_JUDGE_ERROR",
            f"{panel.n_judge} 个 judge 但仅 {panel.independent_sources} 个独立来源——"
            "多个模型 judge 共享错误，数量本身不保证独立判断，一致结论不作独立佐证（§10.3）",
        )
    if not panel.evaluator_version_recorded:
        return ReliabilityVerdict(
            "flag", "REL.NO_EVALUATOR_VERSION",
            "未记录 evaluator 版本与可用信息——结果不可独立解释（§10.3/§10.5）",
        )
    if panel.n_judge < 2:
        return ReliabilityVerdict(
            "flag", "REL.SINGLE_JUDGE",
            "单一 judge，无交叉验证；结论可靠性有限",
        )
    return ReliabilityVerdict("ok", "REL.OK", "judge 具备独立性且记录了评估器版本")


def reproduction_completeness(rec: ReproRecord) -> ReliabilityVerdict:
    """复现记录完整性 + 分类信度。"""
    missing = [f for f in REPRODUCTION_FIELDS if f not in rec.present_fields]
    if len(missing) >= 4:
        return ReliabilityVerdict(
            "flag", "REL.IRREPRODUCIBLE",
            f"复现记录缺 {len(missing)} 项关键字段（{', '.join(missing[:5])}…）——"
            "无法独立复现持续改进（§10.5）",
        )
    if not rec.double_coded and rec.purposeful_selection_only:
        return ReliabilityVerdict(
            "flag", "REL.UNDOUBLECODED",
            "分类为目的性抽样且未经独立双编码——只支持定性比较，不估计设计流行率，"
            "不据此下强普遍性结论（§10.6）",
        )
    if missing:
        return ReliabilityVerdict(
            "flag", "REL.PARTIAL_RECORD",
            f"复现记录缺 {len(missing)} 项：{', '.join(missing)}",
        )
    return ReliabilityVerdict("ok", "REL.REPRODUCIBLE", "复现记录完整" + ("且分类已双编码" if rec.double_coded else ""))


def completeness_ratio(rec: ReproRecord) -> float:
    return len(rec.present_fields & set(REPRODUCTION_FIELDS)) / len(REPRODUCTION_FIELDS)


@dataclass
class EvaluationPlan:
    """评估方案的可扩展性声明。"""
    domain: str                      # 目标域，如 superhuman_general / mathematical_proofs
    requires_human_judgment: bool    # 是否依赖人工判断
    has_automated_verification: bool # 是否有自动验证/可检验的客观标准


def evaluation_scalability(plan: EvaluationPlan) -> ReliabilityVerdict:
    """评估方案能否扩展到超人域（DeepMind essay §RSI：人类群体也难判AI输出时，评估须可扩展）。

    规则写死：目标为超人域 + 完全依赖人工且无自动验证 → flag（评估不可扩展，
    无法支撑该域的强结论）；其余放行。不重复 judge_independence 的独立性检查。
    """
    superhuman = "superhuman" in plan.domain.lower()
    human_only = plan.requires_human_judgment and not plan.has_automated_verification
    if superhuman and human_only:
        return ReliabilityVerdict(
            "flag", "REL.NOT_SCALABLE",
            "目标为超人域但评估完全依赖人工判断、无自动验证——人类群体也难判AI输出，"
            "该评估不可扩展，不能支撑超人域强结论（DeepMind essay: evaluation must scale into superhuman regime）",
        )
    return ReliabilityVerdict(
        "ok", "REL.SCALABLE_OK",
        "评估方案与目标域匹配"
        + ("（超人域具备自动验证）" if superhuman and plan.has_automated_verification else ""),
    )
