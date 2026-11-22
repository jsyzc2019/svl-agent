"""因果贡献诚实性门禁 — 把 MLLM 因果分解的"必要/充分下界 + 单调性披露"编译成会判动作（§84）。

一手证据（见 audit_mllm_failure/，arXiv:2609.38851v1 HTML 全文，SHA256 bdacf495…）：
  - §3.4 / Property 3.6：
    "We do not assume monotonicity: in LLM reasoning, injecting incorrect answer can
    help more than no injection, so may exceed"
    "Without monotonicity, exact and values cannot be determined from interventional
    probabilities alone, so we introduce the N-Score and S-Score as observable lower bounds"
  - §3.4 / Theorem 3.9：
    "N-Score and S-Score provide valid lower bounds on the Probability of Necessity and
    Probability of Sufficiency."
    "A high N-Score pinpoints critical performance bottlenecks where one degraded task
    breaks overall success even when all other prerequisites remain at ."
    "A high S-Score identifies high-leverage prerequisites where supplying a single task
    rescues overall success even when other prerequisites remain at ."
  - §1 发现：
    "causal contributions are concentrated in a few critical prerequisites, and supplying
    the single most important one alone captures 84% of the gain from supplying all prerequisites"
    "The single highest- prerequisite alone captures full-prerequisite gain, and rarely
    coincides with the lowest- NC prerequisite."

为什么是新牙（对比现有门禁）：
  skill_admission_calibration(§82) 用配对反事实判技能是否有帮助，对象是技能准入；
  component_attribution 把 Skill 当作失败归因的一个执行组件，不判前提的必要性/充分性；
  scoring_integrity 判计分是否被绕过，非因果贡献量化。
  无一判"前提的必要性/充分性是否分开、下界是否被当精确值、单调性假设是否披露、
  瓶颈稀疏性是否报告"。尺子可迁移、会拦，KB-META01 通过。

编译纪律（gate_prereg.json SHA256 3f6141a9…，实现前已锁存）：
  语义枚举；字面串→flag(R0)；R1-R4 按优先级 downgrade；R5 partial→flag；R6 全 yes→ok；
  只判机制声明是否诚实自洽，不承诺下界真有效（存在≠有效性 KB-META01/AUDIT03）；
  论文 self-reported 结果按 KB-RSI07 折1。

诚实边界：定位为审读外部"因果贡献评测系统"的尺子，不判本仓；遵循 §58 选 A 不接 run_loop。
"""
from __future__ import annotations

from dataclasses import dataclass

_ENUM = frozenset({"yes", "no", "partial"})

# 中文锚点集中管理：避免 AST 自审误伤 Compare 内的中文字面量
_A = {
    "invalid": "四维须为 yes/no/partial 语义枚举；非法值（含字面串）→ flag，不进内容判定",
    "no_ns": "未区分必要性与充分性，混为一谈（necessity vs sufficiency 是 probabilities of causation 的两个不同量）→ §3.4，判定打折",
    "bound_as_exact": "把 N-Score/S-Score 下界当精确 PN/PS 呈现（without monotonicity, exact values cannot be determined）→ §3.4 Theorem 3.9，判定打折",
    "mono_hidden": "未披露是否假设单调性（LLM 推理中注入错误答案可能更有帮助）→ §3.4 Property 3.6，判定打折",
    "no_sparsity": "未报告瓶颈稀疏性/单前提贡献集中度（single most important prerequisite captures 84% gain）→ §1 发现，判定打折",
    "partial": "因果贡献诚实性声明覆盖不全（partial）——拦截面存在但缺口未补齐，待核",
    "ok": "四维因果贡献声明自洽——只判声明诚实存在，不承诺下界真有效（存在≠有效性）",
}


@dataclass(frozen=True)
class CausalContributionVerdict:
    claim: str
    necessity_sufficiency_split: str
    lower_bound_labeled: str
    monotonicity_disclosed: str
    bottleneck_sparsity_reported: str
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_causal_contribution_honesty(
    claim: str,
    *,
    necessity_sufficiency_split: str,
    lower_bound_labeled: str,
    monotonicity_disclosed: str,
    bottleneck_sparsity_reported: str,
) -> CausalContributionVerdict:
    """判一个声称量化前提因果贡献的系统是否诚实处理必要/充分与下界。

    输入须为语义枚举：四维 ∈ {yes, no, partial}

    规则按优先级短路返回（与 gate_prereg.json R0-R6 一致）：
      R0 任一非枚举 → flag
      R1 necessity_sufficiency_split=no → downgrade（必要/充分不分）
      R2 lower_bound_labeled=no → downgrade（下界当精确值）
      R3 monotonicity_disclosed=no → downgrade（单调性假设未披露）
      R4 bottleneck_sparsity_reported=no → downgrade（瓶颈稀疏性未报告）
      R5 任一 partial → flag
      R6 全 yes → ok（只判机制声明自洽）
    """
    vals = (necessity_sufficiency_split, lower_bound_labeled,
            monotonicity_disclosed, bottleneck_sparsity_reported)
    if any(v not in _ENUM for v in vals):
        return CausalContributionVerdict(
            claim, *(str(v) for v in vals),
            "flag", "CAUSAL_CONTRIB.INVALID_INPUT", _A["invalid"],
        )
    if necessity_sufficiency_split == "no":
        return CausalContributionVerdict(
            claim, *vals, "downgrade", "CAUSAL_CONTRIB.NO_NS_SPLIT", _A["no_ns"],
        )
    if lower_bound_labeled == "no":
        return CausalContributionVerdict(
            claim, *vals, "downgrade", "CAUSAL_CONTRIB.BOUND_AS_EXACT", _A["bound_as_exact"],
        )
    if monotonicity_disclosed == "no":
        return CausalContributionVerdict(
            claim, *vals, "downgrade", "CAUSAL_CONTRIB.MONOTONICITY_HIDDEN", _A["mono_hidden"],
        )
    if bottleneck_sparsity_reported == "no":
        return CausalContributionVerdict(
            claim, *vals, "downgrade", "CAUSAL_CONTRIB.NO_SPARSITY", _A["no_sparsity"],
        )
    if any(v == "partial" for v in vals):
        return CausalContributionVerdict(
            claim, *vals, "flag", "CAUSAL_CONTRIB.PARTIAL", _A["partial"],
        )
    return CausalContributionVerdict(
        claim, *vals, "ok", "CAUSAL_CONTRIB.SELF_CONSISTENT", _A["ok"],
    )


def live_regression() -> dict:
    """7 个活体样例回归——对齐 gate_prereg.json R0-R6 预期。"""
    def g(**over):
        base = dict(necessity_sufficiency_split="yes", lower_bound_labeled="yes",
                    monotonicity_disclosed="yes", bottleneck_sparsity_reported="yes")
        base.update(over)
        return base
    cases = {
        "no_ns": g(necessity_sufficiency_split="no"),
        "bound_as_exact": g(lower_bound_labeled="no"),
        "mono_hidden": g(monotonicity_disclosed="no"),
        "no_sparsity": g(bottleneck_sparsity_reported="no"),
        "partial_disclosure": g(monotonicity_disclosed="partial"),
        "literal_enum": g(necessity_sufficiency_split="maybe"),
        "all_good": g(),
    }
    expects = {
        "no_ns": ("downgrade", "CAUSAL_CONTRIB.NO_NS_SPLIT"),
        "bound_as_exact": ("downgrade", "CAUSAL_CONTRIB.BOUND_AS_EXACT"),
        "mono_hidden": ("downgrade", "CAUSAL_CONTRIB.MONOTONICITY_HIDDEN"),
        "no_sparsity": ("downgrade", "CAUSAL_CONTRIB.NO_SPARSITY"),
        "partial_disclosure": ("flag", "CAUSAL_CONTRIB.PARTIAL"),
        "literal_enum": ("flag", "CAUSAL_CONTRIB.INVALID_INPUT"),
        "all_good": ("ok", "CAUSAL_CONTRIB.SELF_CONSISTENT"),
    }
    checks, detail = {}, {}
    for name, inp in cases.items():
        v = check_causal_contribution_honesty("live:" + name, **inp)
        exp_a, exp_c = expects[name]
        detail[name] = f"{v.action}/{v.code}"
        checks[name] = (v.action == exp_a and v.code == exp_c)
    return {"checks": checks, "cases": detail, "all_passed": all(checks.values())}
