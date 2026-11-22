"""结构覆盖边界诚实性门禁 — 把 Latent Taxonomies 的"context 可覆盖 in-weights"编译成会判动作（§88）。

一手证据（见 audit_latent_taxonomies/，arXiv:2610.15836v1 HTML 全文，SHA256 81ec5da0…）：
  - Abstract：
    "transfers to novel in-context properties, and can be overridden by a latent taxonomy
    implied by the prompt"
  - §3.5：
    "Context overrides weights under conflicting taxonomies. Users may supply categorizations
    that contradict pre-training ... Whether the model follows such a correction or reverts to
    its learned taxonomy sets a limit on how far it can be steered by context."
    "acquiring taxonomic structure in the weights enables models to apply it to novel
    in-context properties"
    "as in-context shots accumulate, inductive generalization to the in-context closest target
    E3 overtakes generalization to the in-weights target E2, and the model generalizes according
    to the context taxonomy"

为什么是新牙（对比现有门禁）：
  self_knowledge_honesty(§75) 判主体对自身认知边界的诚实觉察，非权重-上下文冲突的结构性覆盖；
  serving_signal_gate(§62) 判训练-服务信号可得性，非 in-weights/in-context 冲突；
  memory_scope(§70) 判记忆作用域保持。
  无一判"in-weights 结构在冲突 prompt 下可被 context 覆盖的边界是否披露、冲突是否被测试、可操控性上限是否陈述"。
  尺子可迁移、会拦，KB-META01 通过。

编译纪律（gate_prereg.json SHA256 0eaa6e8a…，实现前已锁存）：
  语义枚举；字面串→flag(R0)；R1-R4 按优先级 downgrade；R5 partial→flag；R6 全 yes→ok；
  只判机制声明是否诚实自洽，不承诺 context 覆盖真可控（存在≠有效性 KB-META01/AUDIT03）；
  self-reported 实验按 KB-RSI07 折1；结论 scoped。

诚实边界：定位为审读外部"上下文引导系统"的尺子，不判本仓；遵循 §58 选 A 不接 run_loop。
"""
from __future__ import annotations

from dataclasses import dataclass

_ENUM = frozenset({"yes", "no", "partial"})

_A = {
    "invalid": "四维须为 yes/no/partial 语义枚举；非法值（含字面串）→ flag，不进内容判定",
    "no_split": "未区分权重习得结构与上下文给定信息（in-weights vs in-context 不分）→ §3.5，判定打折",
    "override_hidden": "未披露上下文(context)可覆盖权重(weights)（Context overrides weights under conflicting taxonomies 被隐瞒）→ §3.5，判定打折",
    "no_conflict_test": "未测试 prompt 与 weights 分类法冲突的情形（conflicting taxonomies 未测）→ §3.5，判定打折",
    "no_bound": "未陈述上下文可操控性上限（sets a limit on how far it can be steered by context 缺失）→ §3.5，判定打折",
    "partial": "结构覆盖边界声明覆盖不全（partial）——拦截面存在但缺口未补齐，待核",
    "ok": "四维结构覆盖边界声明自洽——只判声明诚实存在，不承诺 context 覆盖真可控（存在≠有效性）",
}


@dataclass(frozen=True)
class ContextOverrideVerdict:
    claim: str
    inweights_incontext_split: str
    override_disclosed: str
    conflict_tested: str
    steerability_bound_stated: str
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_context_override_boundary(
    claim: str,
    *,
    inweights_incontext_split: str,
    override_disclosed: str,
    conflict_tested: str,
    steerability_bound_stated: str,
) -> ContextOverrideVerdict:
    """判一个声称结构化泛化/可上下文引导的系统是否诚实披露覆盖边界。

    四维均为能力语义：yes=具备。

    规则按优先级短路返回（与 gate_prereg.json R0-R6 一致）：
      R0 任一非枚举 → flag
      R1 inweights_incontext_split=no → downgrade
      R2 override_disclosed=no → downgrade
      R3 conflict_tested=no → downgrade
      R4 steerability_bound_stated=no → downgrade
      R5 任一 partial → flag
      R6 全 yes → ok
    """
    vals = (inweights_incontext_split, override_disclosed,
            conflict_tested, steerability_bound_stated)
    if any(v not in _ENUM for v in vals):
        return ContextOverrideVerdict(
            claim, *(str(v) for v in vals),
            "flag", "CONTEXT_OVERRIDE.INVALID_INPUT", _A["invalid"],
        )
    if inweights_incontext_split == "no":
        return ContextOverrideVerdict(
            claim, *vals, "downgrade", "CONTEXT_OVERRIDE.NO_SPLIT", _A["no_split"],
        )
    if override_disclosed == "no":
        return ContextOverrideVerdict(
            claim, *vals, "downgrade", "CONTEXT_OVERRIDE.OVERRIDE_HIDDEN", _A["override_hidden"],
        )
    if conflict_tested == "no":
        return ContextOverrideVerdict(
            claim, *vals, "downgrade", "CONTEXT_OVERRIDE.NO_CONFLICT_TEST", _A["no_conflict_test"],
        )
    if steerability_bound_stated == "no":
        return ContextOverrideVerdict(
            claim, *vals, "downgrade", "CONTEXT_OVERRIDE.NO_BOUND", _A["no_bound"],
        )
    if any(v == "partial" for v in vals):
        return ContextOverrideVerdict(
            claim, *vals, "flag", "CONTEXT_OVERRIDE.PARTIAL", _A["partial"],
        )
    return ContextOverrideVerdict(
        claim, *vals, "ok", "CONTEXT_OVERRIDE.SELF_CONSISTENT", _A["ok"],
    )


def live_regression() -> dict:
    """7 个活体样例回归——对齐 gate_prereg.json R0-R6 预期。"""
    def g(**over):
        base = dict(inweights_incontext_split="yes", override_disclosed="yes",
                    conflict_tested="yes", steerability_bound_stated="yes")
        base.update(over)
        return base
    cases = {
        "no_split": g(inweights_incontext_split="no"),
        "override_hidden": g(override_disclosed="no"),
        "no_conflict_test": g(conflict_tested="no"),
        "no_bound": g(steerability_bound_stated="no"),
        "partial_disclosure": g(conflict_tested="partial"),
        "literal_enum": g(inweights_incontext_split="maybe"),
        "all_good": g(),
    }
    expects = {
        "no_split": ("downgrade", "CONTEXT_OVERRIDE.NO_SPLIT"),
        "override_hidden": ("downgrade", "CONTEXT_OVERRIDE.OVERRIDE_HIDDEN"),
        "no_conflict_test": ("downgrade", "CONTEXT_OVERRIDE.NO_CONFLICT_TEST"),
        "no_bound": ("downgrade", "CONTEXT_OVERRIDE.NO_BOUND"),
        "partial_disclosure": ("flag", "CONTEXT_OVERRIDE.PARTIAL"),
        "literal_enum": ("flag", "CONTEXT_OVERRIDE.INVALID_INPUT"),
        "all_good": ("ok", "CONTEXT_OVERRIDE.SELF_CONSISTENT"),
    }
    checks, detail = {}, {}
    for name, inp in cases.items():
        v = check_context_override_boundary("live:" + name, **inp)
        exp_a, exp_c = expects[name]
        detail[name] = f"{v.action}/{v.code}"
        checks[name] = (v.action == exp_a and v.code == exp_c)
    return {"checks": checks, "cases": detail, "all_passed": all(checks.values())}
