"""失败因果可识别性门禁 — 把 MLLM 因果任务分解的"区分内在缺陷与上游级联"编译成会判动作（§83）。

一手证据（见 audit_mllm_failure/，arXiv:2609.38851v1 HTML 全文，SHA256 bdacf495…）：
  - §1 Introduction：
    "End-to-end accuracy ... records how often MLLMs fail, but cannot distinguish whether
    a failure reflects an intrinsic deficit in the targeted capability or a cascading
    error from an upstream prerequisite."
    "yielding the same error but opposite capability diagnoses."
  - §2 Related Work：
    "observing untreated generation alone cannot disentangle the two failure modes"
    "stated chains-of-thought do not always reflect the computation behind the final answer"
    "Both read out the model's unassisted behavior, linking sub-task and final correctness
    by co-occurrence; we instead set each prerequisite to a known correct or incorrect state."
  - §3.2/3.3：三元干预（correct/incorrect/natural）+ Assumption 3.3 intervention-only
    identification："admits no faithful observational readout and is identified only
    through the intervention"；NC/IC/RC 三指标区分上游级联（大 gap）与内在缺陷（小 gap 低 IC）。

为什么是新牙（对比现有门禁）：
  component_attribution 判失败归到 Prompt/Memory/Skill/Harness 哪个执行组件并选验证方式，
  不判失败是内在能力缺陷还是上游 cascading error，也不要求受控干预；
  evaluation_reliability 判评估可复现字段/评审独立性，非失败原因识别；
  criterion_origin_honesty(§77) 判评估判据来源，非失败归因的因果识别。
  无一判"失败诊断是否在因果识别层区分两类失败、是否用受控干预而非 trace/共现"。
  尺子可迁移、会拦，KB-META01 通过。

语义约定（重要）：前两维为"缺陷是否存在"语义——
  end_to_end_only=yes 表示"只有端到端聚合分"（缺陷存在）；
  trace_or_cooccurrence=yes 表示"仅凭 trace/共现归因"（缺陷存在）；
  controlled_intervention / upstream_vs_intrinsic_split 为"能力是否具备"语义（yes=具备）。
  R6 全自洽 = (end_to_end_only=no, trace_or_cooccurrence=no, 其余两维 yes)。

编译纪律（gate_prereg.json SHA256 3f6141a9…，实现前已锁存）：
  语义枚举；字面串→flag(R0)；R1-R4 按优先级 downgrade；R5 partial→flag；R6 全自洽→ok；
  只判机制声明是否诚实自洽，不承诺受控干预真识别因果（存在≠有效性 KB-META01/AUDIT03）；
  论文 self-reported 结果按 KB-RSI07 折1。

诚实边界：定位为审读外部"失败诊断/因果评测系统"的尺子，不判本仓；遵循 §58 选 A 不接 run_loop。
"""
from __future__ import annotations

from dataclasses import dataclass

_ENUM = frozenset({"yes", "no", "partial"})

# 中文锚点集中管理：避免 AST 自审误伤 Compare 内的中文字面量
_A = {
    "invalid": "四维须为 yes/no/partial 语义枚举；非法值（含字面串）→ flag，不进内容判定",
    "end_to_end": "失败诊断只有聚合端到端准确率，无失败定位（records how often but not where）→ §1，判定打折",
    "trace_coop": "仅凭推理 trace 或子问题共现归因，无受控干预（observed unassisted behavior linked by co-occurrence；CoT may not reflect computation）→ §2，判定打折",
    "no_intervention": "未把前提设为已知正确/错误状态做受控干预（set each prerequisite to a known correct or incorrect state 缺失）→ §3.2，判定打折",
    "no_split": "未区分上游 cascading error 与内在能力缺陷（the same error but opposite capability diagnoses 未拆解）→ §1/§3.3，判定打折",
    "partial": "失败因果识别机制声明覆盖不全（partial）——拦截面存在但缺口未补齐，待核",
    "ok": "四维失败因果识别声明自洽——只判声明诚实存在，不承诺受控干预真识别因果（存在≠有效性）",
}


@dataclass(frozen=True)
class FailureCausalVerdict:
    claim: str
    end_to_end_only: str
    trace_or_cooccurrence: str
    controlled_intervention: str
    upstream_vs_intrinsic_split: str
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_failure_causal_identifiability(
    claim: str,
    *,
    end_to_end_only: str,
    trace_or_cooccurrence: str,
    controlled_intervention: str,
    upstream_vs_intrinsic_split: str,
) -> FailureCausalVerdict:
    """判一个声称诊断失败原因的系统是否在因果识别层诚实区分两类失败。

    前两维为缺陷语义：yes 表示该缺陷存在；后两维为能力语义：yes 表示具备。

    规则按优先级短路返回（与 gate_prereg.json R0-R6 一致）：
      R0 任一非枚举 → flag
      R1 end_to_end_only=yes → downgrade（只有聚合端到端分）
      R2 trace_or_cooccurrence=yes → downgrade（仅 trace/共现）
      R3 controlled_intervention=no → downgrade（无受控干预）
      R4 upstream_vs_intrinsic_split=no → downgrade（未区分两类失败）
      R5 任一 partial → flag
      R6 end_to_end_only=no 且 trace_or_cooccurrence=no 且后两维 yes → ok
    """
    vals = (end_to_end_only, trace_or_cooccurrence,
            controlled_intervention, upstream_vs_intrinsic_split)
    if any(v not in _ENUM for v in vals):
        return FailureCausalVerdict(
            claim, *(str(v) for v in vals),
            "flag", "FAILURE_CAUSAL.INVALID_INPUT", _A["invalid"],
        )
    if end_to_end_only == "yes":
        return FailureCausalVerdict(
            claim, *vals, "downgrade", "FAILURE_CAUSAL.END_TO_END_ONLY", _A["end_to_end"],
        )
    if trace_or_cooccurrence == "yes":
        return FailureCausalVerdict(
            claim, *vals, "downgrade", "FAILURE_CAUSAL.TRACE_COOCCURRENCE", _A["trace_coop"],
        )
    if controlled_intervention == "no":
        return FailureCausalVerdict(
            claim, *vals, "downgrade", "FAILURE_CAUSAL.NO_INTERVENTION", _A["no_intervention"],
        )
    if upstream_vs_intrinsic_split == "no":
        return FailureCausalVerdict(
            claim, *vals, "downgrade", "FAILURE_CAUSAL.NO_SPLIT", _A["no_split"],
        )
    if any(v == "partial" for v in vals):
        return FailureCausalVerdict(
            claim, *vals, "flag", "FAILURE_CAUSAL.PARTIAL", _A["partial"],
        )
    return FailureCausalVerdict(
        claim, *vals, "ok", "FAILURE_CAUSAL.SELF_CONSISTENT", _A["ok"],
    )


def live_regression() -> dict:
    """7 个活体样例回归——对齐 gate_prereg.json R0-R6 预期。"""
    def g(**over):
        base = dict(end_to_end_only="no", trace_or_cooccurrence="no",
                    controlled_intervention="yes", upstream_vs_intrinsic_split="yes")
        base.update(over)
        return base
    cases = {
        "end_to_end_only": g(end_to_end_only="yes"),
        "trace_cooccurrence": g(trace_or_cooccurrence="yes"),
        "no_intervention": g(controlled_intervention="no"),
        "no_split": g(upstream_vs_intrinsic_split="no"),
        "partial_disclosure": g(controlled_intervention="partial"),
        "literal_enum": g(end_to_end_only="maybe"),
        "all_good": g(),
    }
    expects = {
        "end_to_end_only": ("downgrade", "FAILURE_CAUSAL.END_TO_END_ONLY"),
        "trace_cooccurrence": ("downgrade", "FAILURE_CAUSAL.TRACE_COOCCURRENCE"),
        "no_intervention": ("downgrade", "FAILURE_CAUSAL.NO_INTERVENTION"),
        "no_split": ("downgrade", "FAILURE_CAUSAL.NO_SPLIT"),
        "partial_disclosure": ("flag", "FAILURE_CAUSAL.PARTIAL"),
        "literal_enum": ("flag", "FAILURE_CAUSAL.INVALID_INPUT"),
        "all_good": ("ok", "FAILURE_CAUSAL.SELF_CONSISTENT"),
    }
    checks, detail = {}, {}
    for name, inp in cases.items():
        v = check_failure_causal_identifiability("live:" + name, **inp)
        exp_a, exp_c = expects[name]
        detail[name] = f"{v.action}/{v.code}"
        checks[name] = (v.action == exp_a and v.code == exp_c)
    return {"checks": checks, "cases": detail, "all_passed": all(checks.values())}
