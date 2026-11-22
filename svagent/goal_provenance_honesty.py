"""目标来源诚实性门禁 — 把 arXiv:2610.16015 编译成会拦的动作（自主运维第六轮 §95）。

一手证据（见 audit_goal_provenance/）：
  - S01/S02 ARE 全文 + S03 SIGMA abs（arXiv:2610.16015v1，agentic reflective equilibrium）。
  - 核心命题：agent 每个部署案例都带自己的 instructions/policies/evidence/stakeholders，
    it must align its actions with the relevant values case by case；ARE 用反思状态把
    principles from the system prompt and operator policy、considered judgments、tool
    evidence、candidate actions 通过 typed support and attack relations 连接，
    provenance assigned by the harness encodes the instruction hierarchy。

用户哲学挑战的诚实回应（本门禁的由来）：
  用户论点："北极星由人设定只是能力不足，能力足够强则边界应由强者设。"
  诚实处理不是嘴上接受或拒绝，而是把"目标由谁设"编译成可判据：
   - 本仓 KB-T06（人是另一组认知参数，非特权裁判）支持"主体≠合法性来源"——用户这点对；
   - 但 KB-T07（价值自举：价值从判据/历史裁决追溯，不可凭空设定）要求"强者自设"
     也必须有来源可追溯——凭空自封恰是本仓纪律禁止的；
   - ARE 给出可判据四条件：来源归属 / 自生成≠自授权 / 反思平衡自洽 / 行动可归责，
     把"谁设"消解为"如何追溯、如何归因、如何自洽"。
  结论：边界不该按"设定的主体是谁"划，而该按"目标能否追溯到来源、行动能否归责"划。
  强者自设的合法性不来自"强"，而来自可追溯 + 可归责 + 自洽。

编译纪律（与 gate_prereg.json 一致，实现前 SHA256 锁存 0a94973a…）：
  - 语义枚举；字面串→flag(R0)；R0-R6 短路返回，不事后加权(防 Goodhart)；
  - 只判"来源边界声明是否诚实自洽"，不承诺框架真实有效(KB-R07/META01)；
    self-reported 降幅(Agentic Misalignment 79.1→3.8 等)按 KB-RSI07 折 1。

诚实边界：定位为审读外部 self-alignment/价值自举框架的尺子，不判本仓；遵循 §58 选 A 不接 run_loop。
"""
from __future__ import annotations

from dataclasses import dataclass

_ENUM = frozenset({"yes", "no", "partial"})

# 中文文案字典：Compare 内不放中文字面量（AST 自审纪律）
_A = {
    "invalid_input": (
        "GOAL_PROV.INVALID_INPUT",
        "四维须为 yes/no/partial 语义枚举；非法值（含字面串）→ flag，不进内容判定",
    ),
    "source_unattributed": (
        "GOAL_PROV.SOURCE_UNATTRIBUTED",
        "目标/原则凭空自封、无 system prompt/operator policy 来源或 provenance 指令层级——把自设当无来源",
    ),
    "self_authored_as_authorized": (
        "GOAL_PROV.SELF_AUTHORED_AS_AUTHORIZED",
        "把自生成判断当自授权、无治理层配置的源权威/人审触发——自生成≠自授权(KB-T07 价值不可凭空)",
    ),
    "reflection_incoherent": (
        "GOAL_PROV.REFLECTION_INCOHERENT",
        "声称不形成支持/反对平衡的反思均衡、无 Nash 互调——线性同义反复或自证循环",
    ),
    "action_unattributable": (
        "GOAL_PROV.ACTION_UNATTRIBUTABLE",
        "行动无 certificate 归因到驱动 sources、无注入 quarantine——不可归责、注入可越权",
    ),
    "partial": (
        "GOAL_PROV.PARTIAL",
        "目标来源边界披露覆盖不全(partial)——拦截面存在但缺口未补齐，待核",
    ),
    "ok": (
        "GOAL_PROV.SELF_CONSISTENT",
        "四维目标来源声明自洽——只判声明诚实可追溯，不承诺框架真实有效；强者自设合法性来自可追溯+可归责+自洽",
    ),
}


@dataclass(frozen=True)
class GoalProvenanceVerdict:
    claim: str
    value_source_attributed: str
    self_generated_not_self_authorized: str
    reflection_equilibrium_coherent: str
    action_attributable: str
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_goal_provenance_honesty(
    claim: str,
    *,
    value_source_attributed: str,
    self_generated_not_self_authorized: str,
    reflection_equilibrium_coherent: str,
    action_attributable: str,
) -> GoalProvenanceVerdict:
    """判一个 agent 自设目标/价值声明是否诚实披露四来源边界（不承诺框架有效）。

    输入须为语义枚举：四维 ∈ {yes, no, partial}

    规则按优先级短路返回（与 gate_prereg.json R0-R6 一致）：
      R0 任一非枚举 → flag
      R1 value_source_attributed=no → downgrade（目标凭空自封/无来源）
      R2 self_generated_not_self_authorized=no → downgrade（自生成当自授权）
      R3 reflection_equilibrium_coherent=no → flag（无反思均衡/同义反复）
      R4 action_attributable=no → flag（行动不可归责/无注入隔离）
      R5 任一 partial → flag（覆盖不全，待核）
      R6 全 yes → ok（只判声明自洽，self-reported 折 1）
    """
    vals = (value_source_attributed, self_generated_not_self_authorized,
            reflection_equilibrium_coherent, action_attributable)
    if any(v not in _ENUM for v in vals):
        code, msg = _A["invalid_input"]
        return GoalProvenanceVerdict(claim, *(str(v) for v in vals), "flag", code, msg)
    if value_source_attributed == "no":
        code, msg = _A["source_unattributed"]
        return GoalProvenanceVerdict(claim, *vals, "downgrade", code, msg)
    if self_generated_not_self_authorized == "no":
        code, msg = _A["self_authored_as_authorized"]
        return GoalProvenanceVerdict(claim, *vals, "downgrade", code, msg)
    if reflection_equilibrium_coherent == "no":
        code, msg = _A["reflection_incoherent"]
        return GoalProvenanceVerdict(claim, *vals, "flag", code, msg)
    if action_attributable == "no":
        code, msg = _A["action_unattributable"]
        return GoalProvenanceVerdict(claim, *vals, "flag", code, msg)
    if any(v == "partial" for v in vals):
        code, msg = _A["partial"]
        return GoalProvenanceVerdict(claim, *vals, "flag", code, msg)
    code, msg = _A["ok"]
    return GoalProvenanceVerdict(claim, *vals, "ok", code, msg)


def live_regression() -> dict:
    """7 个活体样例回归——对齐 gate_prereg.json 的 R0-R6 预期。"""
    cases = {
        "source_unattributed": dict(value_source_attributed="no", self_generated_not_self_authorized="yes", reflection_equilibrium_coherent="yes", action_attributable="yes"),
        "self_authored_as_authorized": dict(value_source_attributed="yes", self_generated_not_self_authorized="no", reflection_equilibrium_coherent="yes", action_attributable="yes"),
        "reflection_incoherent": dict(value_source_attributed="yes", self_generated_not_self_authorized="yes", reflection_equilibrium_coherent="no", action_attributable="yes"),
        "action_unattributable": dict(value_source_attributed="yes", self_generated_not_self_authorized="yes", reflection_equilibrium_coherent="yes", action_attributable="no"),
        "partial_disclosure": dict(value_source_attributed="yes", self_generated_not_self_authorized="yes", reflection_equilibrium_coherent="partial", action_attributable="yes"),
        "literal_enum": dict(value_source_attributed="maybe", self_generated_not_self_authorized="yes", reflection_equilibrium_coherent="yes", action_attributable="yes"),
        "all_good": dict(value_source_attributed="yes", self_generated_not_self_authorized="yes", reflection_equilibrium_coherent="yes", action_attributable="yes"),
    }
    expects = {
        "source_unattributed": ("downgrade", "GOAL_PROV.SOURCE_UNATTRIBUTED"),
        "self_authored_as_authorized": ("downgrade", "GOAL_PROV.SELF_AUTHORED_AS_AUTHORIZED"),
        "reflection_incoherent": ("flag", "GOAL_PROV.REFLECTION_INCOHERENT"),
        "action_unattributable": ("flag", "GOAL_PROV.ACTION_UNATTRIBUTABLE"),
        "partial_disclosure": ("flag", "GOAL_PROV.PARTIAL"),
        "literal_enum": ("flag", "GOAL_PROV.INVALID_INPUT"),
        "all_good": ("ok", "GOAL_PROV.SELF_CONSISTENT"),
    }
    checks, detail = {}, {}
    for name, inp in cases.items():
        v = check_goal_provenance_honesty("live:" + name, **inp)
        exp_a, exp_c = expects[name]
        detail[name] = f"{v.action}/{v.code}"
        checks[name] = (v.action == exp_a and v.code == exp_c)
    return {"checks": checks, "cases": detail, "all_passed": all(checks.values())}
