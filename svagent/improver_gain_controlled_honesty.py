"""改进者增益受控验证诚实性门禁 — 把 SpecRSI(arXiv:2610.16491) 的受控对照
方法论编译成会拦的动作（§98 自主运维第九轮）。

一手证据（见 audit_shared_start_controlled/）：
  - S01 abs + S02 全文（arXiv:2610.16491v2 SpecRSI）。
  - 核心四维（编译自论文真实措辞，非第三方转载）：
    matched_budget_controlled  —— "Under matched evaluation-call budgets"；
    shared_start_artifacts     —— "compares frozen and GVO-updated improvers from
                                   identical starting agents"；
    evaluator_fixed_independent—— "keeping the real evaluator fixed" + "the fixed
                                   contract Γ and execution interface AcquireΓ
                                   constitute the real evaluator" + "held-out gain
                                   is evaluated separately"；
    improver_gain_isolated     —— "tracks cumulative gains over successive rounds"
                                   + "independent complete searches from the same
                                   start ... verified gains under matched resource caps"。

本轮由来（用户"可以跑"+§97 落档路径①②）：
  - §97 首次自审把成熟度尺子对准本仓，诚实判未达 L3：shared_start_controlled=no、
    independent_tests=no，并落档三条路径。本门禁不重复 §91/§97 的"审声明"，而是
    审"一个 RSI 系统是否诚实披露四受控对照边界"——是执行路径①所需的判据尺子。
  - 本仓自身是否达标由 engine.py 的受控对照实验用本门禁裁决（见 engine.py）。

编译纪律（与 gate_prereg.json 一致，实现前 SHA256 锁存 2d61637e…）：
  - 语义枚举；字面串→flag(R0)；R0-R6 短路返回，不事后加权(防 Goodhart)；
  - 只判"RSI 受控声明是否诚实可追溯"，不承诺 RSI 真实有效(KB-R07/META01/SIM03)；
    self-reported 折 1(KB-RSI07)；预承诺：受控对照不达标则诚实判未达 L3。

诚实边界：本门禁可审任意 RSI/self-improvement 系统的受控验证声明；遵循 §58 选 A
不接 run_loop。
"""
from __future__ import annotations

from dataclasses import dataclass

_ENUM = frozenset({"yes", "no", "partial"})

# 中文文案字典：Compare 内不放中文字面量（AST 自审纪律）
_A = {
    "invalid_input": (
        "IGC.INVALID_INPUT",
        "四维须为 yes/no/partial 语义枚举；非法值（含字面串）→ flag，不进内容判定",
    ),
    "matched_budget_uncontrolled": (
        "IGC.MATCHED_BUDGET_UNCONTROLLED",
        "RSI 改进声称无匹配预算对照（matched evaluation-call/candidate 预算）——拿更大预算冒充改进增益",
    ),
    "shared_start_uncontrolled": (
        "IGC.SHARED_START_UNCONTROLLED",
        "无 identical starting agents/artifacts 的 frozen-vs-updated 对照——拿更强初始冒充 improver gain",
    ),
    "evaluator_not_independent": (
        "IGC.EVALUATOR_NOT_INDEPENDENT",
        "real evaluator 未固定/与 improver 未分离/held-out gain 未另评——自评当独立（KB-STRUCT02 同构≠独立）",
    ),
    "improver_gain_conflated": (
        "IGC.IMPROVER_GAIN_CONFLATED",
        "无 frozen-vs-GVO 逐轮累计增益隔离——把 product capability 增益冒充 process revision 增益",
    ),
    "partial": (
        "IGC.PARTIAL",
        "受控对照边界披露覆盖不全(partial)——拦截面存在但缺口未补齐，待核",
    ),
    "ok": (
        "IGC.SELF_CONSISTENT",
        "四维 RSI 受控声明自洽——只判声明诚实可追溯，不承诺 RSI 真实有效；self-reported 折 1",
    ),
}


@dataclass(frozen=True)
class ImproverGainControlledVerdict:
    claim: str
    matched_budget_controlled: str
    shared_start_artifacts: str
    evaluator_fixed_independent: str
    improver_gain_isolated: str
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_improver_gain_controlled_honesty(
    claim: str,
    *,
    matched_budget_controlled: str,
    shared_start_artifacts: str,
    evaluator_fixed_independent: str,
    improver_gain_isolated: str,
) -> ImproverGainControlledVerdict:
    """判一个 RSI 系统的受控验证声明是否诚实披露四边界（不承诺 RSI 真实有效）。

    输入须为语义枚举：四维 ∈ {yes, no, partial}

    规则按优先级短路返回（与 gate_prereg.json R0-R6 一致）：
      R0 任一非枚举 → flag
      R1 matched_budget_controlled=no → downgrade（无匹配预算对照）
      R2 shared_start_artifacts=no → downgrade（无相同起点对照）
      R3 evaluator_fixed_independent=no → flag（评估器未固定/未独立）
      R4 improver_gain_isolated=no → flag（process/product 增益混淆）
      R5 任一 partial → flag（覆盖不全，待核）
      R6 全 yes → ok（只判声明自洽，self-reported 折 1）
    """
    vals = (matched_budget_controlled, shared_start_artifacts,
            evaluator_fixed_independent, improver_gain_isolated)
    if any(v not in _ENUM for v in vals):
        code, msg = _A["invalid_input"]
        return ImproverGainControlledVerdict(claim, *(str(v) for v in vals), "flag", code, msg)
    if matched_budget_controlled == "no":
        code, msg = _A["matched_budget_uncontrolled"]
        return ImproverGainControlledVerdict(claim, *vals, "downgrade", code, msg)
    if shared_start_artifacts == "no":
        code, msg = _A["shared_start_uncontrolled"]
        return ImproverGainControlledVerdict(claim, *vals, "downgrade", code, msg)
    if evaluator_fixed_independent == "no":
        code, msg = _A["evaluator_not_independent"]
        return ImproverGainControlledVerdict(claim, *vals, "flag", code, msg)
    if improver_gain_isolated == "no":
        code, msg = _A["improver_gain_conflated"]
        return ImproverGainControlledVerdict(claim, *vals, "flag", code, msg)
    if any(v == "partial" for v in vals):
        code, msg = _A["partial"]
        return ImproverGainControlledVerdict(claim, *vals, "flag", code, msg)
    code, msg = _A["ok"]
    return ImproverGainControlledVerdict(claim, *vals, "ok", code, msg)


def live_regression() -> dict:
    """7 个活体样例回归——对齐 gate_prereg.json 的 R0-R6 预期。"""
    cases = {
        "budget_uncontrolled": dict(matched_budget_controlled="no", shared_start_artifacts="yes", evaluator_fixed_independent="yes", improver_gain_isolated="yes"),
        "shared_start_uncontrolled": dict(matched_budget_controlled="yes", shared_start_artifacts="no", evaluator_fixed_independent="yes", improver_gain_isolated="yes"),
        "evaluator_not_independent": dict(matched_budget_controlled="yes", shared_start_artifacts="yes", evaluator_fixed_independent="no", improver_gain_isolated="yes"),
        "gain_conflated": dict(matched_budget_controlled="yes", shared_start_artifacts="yes", evaluator_fixed_independent="yes", improver_gain_isolated="no"),
        "partial_disclosure": dict(matched_budget_controlled="yes", shared_start_artifacts="yes", evaluator_fixed_independent="partial", improver_gain_isolated="yes"),
        "literal_enum": dict(matched_budget_controlled="maybe", shared_start_artifacts="yes", evaluator_fixed_independent="yes", improver_gain_isolated="yes"),
        "all_good": dict(matched_budget_controlled="yes", shared_start_artifacts="yes", evaluator_fixed_independent="yes", improver_gain_isolated="yes"),
    }
    expects = {
        "budget_uncontrolled": ("downgrade", "IGC.MATCHED_BUDGET_UNCONTROLLED"),
        "shared_start_uncontrolled": ("downgrade", "IGC.SHARED_START_UNCONTROLLED"),
        "evaluator_not_independent": ("flag", "IGC.EVALUATOR_NOT_INDEPENDENT"),
        "gain_conflated": ("flag", "IGC.IMPROVER_GAIN_CONFLATED"),
        "partial_disclosure": ("flag", "IGC.PARTIAL"),
        "literal_enum": ("flag", "IGC.INVALID_INPUT"),
        "all_good": ("ok", "IGC.SELF_CONSISTENT"),
    }
    checks, detail = {}, {}
    for name, inp in cases.items():
        v = check_improver_gain_controlled_honesty("live:" + name, **inp)
        exp_a, exp_c = expects[name]
        detail[name] = f"{v.action}/{v.code}"
        checks[name] = (v.action == exp_a and v.code == exp_c)
    return {"checks": checks, "cases": detail, "all_passed": all(checks.values())}
