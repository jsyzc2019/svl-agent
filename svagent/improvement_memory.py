"""SIM 四要素改进记忆 — 把论文机制编译成可执行、可证伪的判据。

来源：arXiv:2611.18856 SIM 的四要素
  - Rationale（修改动机与具体代码）
  - Predicted outcomes（事前预期修复哪些任务）
  - Observed outcomes（实测修复/失败/引入的新 bug）
  - Evaluation context（在什么模型/数据集/轮次下评估）

为什么值得借鉴（框架立场）：
  本项目现有 KnowledgeItem 只有 mechanism/support/evidence，全是【事后记述】——
  没有"改之前预期什么"，所以无法证伪，与第32节康波文"不可证伪"同病。
  Predicted↔Observed 配对把"经验"变成"可被现实打脸的假设"。本模块据此生长出：
    1. prediction_hit_rate / missed / unexpected —— 预测命中与落空可量化；
    2. regression 检测 —— "有没有引入新 bug"强制显式记录；
    3. causality 门禁 —— observed 不得早于 predicted（防后知编造）；
    4. transfer_decision —— 跨模型/数据集迁移时给出 retain/revise/verify，
       直接对应论文中 Opus→Gemini 迁移反而变差(68.41<73.89)的现象；
    5. falsifiable 判定 —— 没有事前预测的记录判为不可证伪，不给强结论。

纪律：transfer 规则写死、不事后加权；不可证伪/有回归的记录一律降级，不因"成功叙事"放行。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


# ---------------------------------------------------------------- 评估上下文
@dataclass(frozen=True)
class EvaluationContext:
    """评估上下文——记录"在什么条件下验证"，防跨上下文过度外推。"""
    model: str = ""
    benchmark: str = ""
    dataset: str = ""
    round: int = 0

    def label(self) -> str:
        return f"{self.model or '?'}@{self.benchmark or self.dataset or '?'}#r{self.round}"

    def transferable_to(self, target: "EvaluationContext") -> bool:
        """模型不同则不可直接迁移（论文实测：换模型会让改进失效甚至倒退）。"""
        return (self.model == target.model and self.benchmark == target.benchmark)


# ---------------------------------------------------------------- 单条改进记录
@dataclass
class ImprovementRecord:
    """一条改进的四要素完整记录。"""
    record_id: str
    root_cause: str                      # 问题根因（分组键，SIM 按此分组）
    rationale: str                       # Rationale：为什么改
    code_ref: str                        # Rationale：改了哪一行/哪个文件
    predicted: list[str] = field(default_factory=list)      # Predicted outcomes（事前）
    observed_fixed: list[str] = field(default_factory=list) # Observed：修复的
    observed_broken: list[str] = field(default_factory=list) # Observed：新 bug/回归
    context: EvaluationContext = field(default_factory=EvaluationContext)
    accepted: bool = True                # 是否被采纳（失败尝试也要记录 accepted=False）
    predicted_at: str = ""               # 事前预测时间戳（防后知）
    observed_at: str = ""                # 实测时间戳

    @property
    def falsifiable(self) -> bool:
        """有事前预测才可被证伪。"""
        return len(self.predicted) > 0

    def predictions_missed(self) -> list[str]:
        """预期修复但实测没修——预测落空（最该被记住的失败）。"""
        return sorted(set(self.predicted) - set(self.observed_fixed))

    def unexpected_fixes(self) -> list[str]:
        """实测修好了但事前没预见——意外收获/未建模机制。"""
        return sorted(set(self.observed_fixed) - set(self.predicted))

    def has_regression(self) -> bool:
        return len(self.observed_broken) > 0

    def prediction_hit_rate(self) -> float | None:
        """命中率 = |预测∩实测修复| / |预测|；无预测返回 None（不可证伪，不给分）。"""
        if not self.predicted:
            return None
        return len(set(self.predicted) & set(self.observed_fixed)) / len(set(self.predicted))

    def causality_ok(self) -> bool:
        """防后知门禁：有时间戳时，observed 不得早于 predicted。"""
        if self.predicted_at and self.observed_at:
            return self.observed_at >= self.predicted_at
        return True  # 缺时间戳不判定违规，但 falsifiable/transfer 会因此降级


# ---------------------------------------------------------------- 迁移决策
@dataclass(frozen=True)
class TransferDecision:
    root_cause: str
    action: str          # retain | revise | verify | drop
    reason: str
    hit_rate: float | None
    regression: bool


# ---------------------------------------------------------------- 记忆库
class ImprovementMemory:
    def __init__(self) -> None:
        self.records: list[ImprovementRecord] = []

    def record(self, r: ImprovementRecord) -> str:
        self.records.append(r)
        return r.record_id

    def record_many(self, rs: Iterable[ImprovementRecord]) -> list[str]:
        return [self.record(r) for r in rs]

    def group_by_root_cause(self) -> dict[str, list[ImprovementRecord]]:
        g: dict[str, list[ImprovementRecord]] = {}
        for r in self.records:
            g.setdefault(r.root_cause, []).append(r)
        return g

    def falsifiability_rate(self) -> float:
        """可证伪记录占比——没有事前预测的经验都是不可证伪的叙事。"""
        if not self.records:
            return 0.0
        return sum(1 for r in self.records if r.falsifiable) / len(self.records)

    def transfer_decision(self, target: EvaluationContext) -> list[TransferDecision]:
        """跨上下文迁移建议。规则写死，优先级：回归 > 低命中 > 不可证伪 > 上下文不符 > 保留。"""
        out: list[TransferDecision] = []
        for cause, recs in self.group_by_root_cause().items():
            rates = [r.prediction_hit_rate() for r in recs]
            valid = [x for x in rates if x is not None]
            hit = sum(valid) / len(valid) if valid else None
            any_reg = any(r.has_regression() for r in recs)
            any_unfalsifiable = any(not r.falsifiable for r in recs)
            any_bad_causality = any(not r.causality_ok() for r in recs)
            any_incompatible = any(not r.context.transferable_to(target) for r in recs)

            if any_reg:
                action, reason = "revise", "历史有回归/新bug，迁移前必须修订"
            elif any_bad_causality:
                action, reason = "verify", "存在后知时序违规，证据不可信"
            elif any_unfalsifiable:
                action, reason = "verify", "含无事前预测的记录，不可证伪，不能直接迁移"
            elif hit is not None and hit < 0.5:
                action, reason = "revise", f"预测命中率仅{hit:.0%}，改进不稳"
            elif any_incompatible:
                action, reason = "verify", "上下文(模型/benchmark)不同，须重新验证再迁移"
            elif hit is not None and hit >= 0.8:
                action, reason = "retain", f"命中率{hit:.0%}且无回归，上下文兼容，可保留"
            else:
                action, reason = "verify", "证据不足以直接迁移"
            out.append(TransferDecision(cause, action, reason, hit, any_reg))
        return out

    def to_knowledge_item_kwargs(self) -> list[dict[str, Any]]:
        """桥接：把四要素记录转成知识库可 ingest 的字段草案。

        关键：把 predicted/observed 配对写进 support，让经验带上可证伪预期，
        而不是只留一句事后论述。
        """
        out = []
        for r in self.records:
            pred = "、".join(r.predicted) or "(无事前预测)"
            fixed = "、".join(r.observed_fixed) or "(无)"
            missed = "、".join(r.predictions_missed()) or "(无)"
            broken = "、".join(r.observed_broken) or "(无)"
            out.append({
                "mechanism": f"[{r.root_cause}] {r.rationale}",
                "trigger": [r.root_cause, "改进经验", "harness优化", r.context.model],
                "action": (
                    f"遇到'{r.root_cause}'：{r.code_ref}。事前预测修复[{pred}]；"
                    f"实测修复[{fixed}]、落空[{missed}]、引入bug[{broken}]。"
                    f"评估上下文：{r.context.label()}。"
                ),
                "support": [
                    f"SIM:predicted={pred}",
                    f"SIM:observed_fixed={fixed}",
                    f"SIM:missed={missed}",
                    f"SIM:regression={broken}",
                    f"SIM:ctx={r.context.label()}",
                ],
                "predicted_at": r.predicted_at,
                "observed_at": r.observed_at,
                "falsifiable": r.falsifiable,
            })
        return out
