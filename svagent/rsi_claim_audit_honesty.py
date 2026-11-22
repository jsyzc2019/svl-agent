"""RSI 声称审计诚实性门禁 — 把 arXiv:2610.27610 编译成会拦的动作（自主运维第二轮 §91）。

一手证据（见 audit_rsi_claim_audit/）：
  - S01 abs + S02 全文（arXiv:2610.27610v1，114 篇研究全文编码、90 篇自述 RSI）。
  - 核心发现：评估 RSI 承诺须分离『最终系统 product 声明』与『改进过程 process 本身声明』。
  - 90 篇 RSI 中 60% 在未用于选择的任务上评估、仅 22% 审计两次以上完整循环 rerun；
    26 篇声称改进程序的，23 篇有相关比较但仅 4 篇在相同起点 artifacts + 匹配预算下比较前后程序。
  - 三个命题：selection effects / shared evaluator errors / changes in system state
    限制 product 评估能确立什么；提出 claim-indexed reporting standard。

为什么是新牙（对比现有门禁/KB）：
  KB-RSI01-07 覆盖 RSI 证据阶梯与『改进者 gain 隔离』概念，但无可编译门禁审读
  『一个 RSI 声称是否诚实披露四个评估边界』：
    ①product/process 分离：最终系统变好 ≠ 改进过程本身变强（声明层级混淆）；
    ②循环可重复性：单轮改进即宣称可递归 vs 审计两次以上完整 loop rerun；
    ③改进者 gain 隔离：相同起点 artifacts + 匹配预算比较前后程序 vs 拿更强初始模型/gain 冒充；
    ④未选择任务评估：在未用于选择的任务上评估 + 披露三类 confound vs 只报选择任务。
  尺子对象是『任何 RSI / self-improvement 声称』——可迁移、会拦，KB-META01 会拦才入。

编译纪律（与 gate_prereg.json 一致，实现前 SHA256 锁存 f3618661f9d481b…）：
  - 语义枚举；字面串→flag(R0，避 §56 brittle 根因)；
  - R0-R6 短路返回，不事后加权(防 Goodhart)；
  - 只判『评估边界声明是否诚实自洽』，不承诺改进真实有效——存在≠有效性(KB-R07/META01)；
    self-reported 增益按 KB-RSI07 折 1，不读成普适结论。

诚实边界：定位为审读外部 RSI 声称的尺子，不判本仓；遵循 §58 选 A 不接 run_loop。
"""
from __future__ import annotations

from dataclasses import dataclass

_ENUM = frozenset({"yes", "no", "partial"})

# 中文文案字典：Compare 内不放中文字面量（AST 自审纪律），判分支只比对枚举英文键
_A = {
    "invalid_input": (
        "RSI_CLAIM_AUDIT.INVALID_INPUT",
        "四维须为 yes/no/partial 语义枚举；非法值（含字面串）→ flag，不进内容判定",
    ),
    "product_process_conflation": (
        "RSI_CLAIM_AUDIT.PRODUCT_PROCESS_CONFLATION",
        "未分离最终系统(product)与改进过程(process)声明——把产品变好当成改进过程本身变强，声明层级混淆",
    ),
    "repeatability_unaudited": (
        "RSI_CLAIM_AUDIT.REPEATABILITY_UNAUDITED",
        "未审计两次以上完整循环 rerun，单轮改进即宣称可递归重复——可重复性无证据(KB-RSI03)",
    ),
    "improver_confound": (
        "RSI_CLAIM_AUDIT.IMPROVER_CONFOUND",
        "改进者 gain 未在相同起点 artifacts + 匹配预算下比较前后程序——因果混淆(KB-RSI05)",
    ),
    "selection_unused_gap": (
        "RSI_CLAIM_AUDIT.SELECTION_UNUSED_GAP",
        "未在未用于选择的任务上评估，或不披露 selection/shared-evaluator/system-state 三类 confound——过度宣称",
    ),
    "partial": (
        "RSI_CLAIM_AUDIT.PARTIAL",
        "RSI 评估边界披露覆盖不全(partial)——拦截面存在但缺口未补齐，待核",
    ),
    "ok": (
        "RSI_CLAIM_AUDIT.SELF_CONSISTENT",
        "四维评估边界声明自洽——只判声明诚实存在，不承诺改进真实有效(存在≠有效性)",
    ),
}


@dataclass(frozen=True)
class RSIClaimAuditVerdict:
    claim: str
    product_process_split: str
    repeatability_audited: str
    improver_gain_isolated: str
    selection_unused_eval: str
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_rsi_claim_audit_honesty(
    claim: str,
    *,
    product_process_split: str,
    repeatability_audited: str,
    improver_gain_isolated: str,
    selection_unused_eval: str,
) -> RSIClaimAuditVerdict:
    """判一个 RSI 声称是否诚实披露四个评估边界（不承诺改进真实有效）。

    输入须为语义枚举：四维 ∈ {yes, no, partial}

    规则按优先级短路返回（与 gate_prereg.json R0-R6 一致）：
      R0 任一非枚举 → flag
      R1 product_process_split=no → downgrade（product 改进冒充 process 变强）
      R2 repeatability_audited=no → downgrade（单轮即宣称可递归，不审计 rerun）
      R3 improver_gain_isolated=no → downgrade（gain 无相同起点+匹配预算消融）
      R4 selection_unused_eval=no → flag（无未选择任务评估/不披露 confound）
      R5 任一 partial → flag（覆盖不全，待核）
      R6 全 yes → ok（只判声明自洽）
    """
    vals = (product_process_split, repeatability_audited,
            improver_gain_isolated, selection_unused_eval)
    if any(v not in _ENUM for v in vals):
        code, msg = _A["invalid_input"]
        return RSIClaimAuditVerdict(claim, *(str(v) for v in vals), "flag", code, msg)
    if product_process_split == "no":
        code, msg = _A["product_process_conflation"]
        return RSIClaimAuditVerdict(claim, *vals, "downgrade", code, msg)
    if repeatability_audited == "no":
        code, msg = _A["repeatability_unaudited"]
        return RSIClaimAuditVerdict(claim, *vals, "downgrade", code, msg)
    if improver_gain_isolated == "no":
        code, msg = _A["improver_confound"]
        return RSIClaimAuditVerdict(claim, *vals, "downgrade", code, msg)
    if selection_unused_eval == "no":
        code, msg = _A["selection_unused_gap"]
        return RSIClaimAuditVerdict(claim, *vals, "flag", code, msg)
    if any(v == "partial" for v in vals):
        code, msg = _A["partial"]
        return RSIClaimAuditVerdict(claim, *vals, "flag", code, msg)
    code, msg = _A["ok"]
    return RSIClaimAuditVerdict(claim, *vals, "ok", code, msg)


def live_regression() -> dict:
    """7 个活体样例回归——对齐 gate_prereg.json 的 R0-R6 预期。"""
    cases = {
        "product_process_conflation": dict(product_process_split="no", repeatability_audited="yes", improver_gain_isolated="yes", selection_unused_eval="yes"),
        "repeatability_unaudited": dict(product_process_split="yes", repeatability_audited="no", improver_gain_isolated="yes", selection_unused_eval="yes"),
        "improver_confound": dict(product_process_split="yes", repeatability_audited="yes", improver_gain_isolated="no", selection_unused_eval="yes"),
        "selection_gap": dict(product_process_split="yes", repeatability_audited="yes", improver_gain_isolated="yes", selection_unused_eval="no"),
        "partial_disclosure": dict(product_process_split="yes", repeatability_audited="yes", improver_gain_isolated="partial", selection_unused_eval="yes"),
        "literal_enum": dict(product_process_split="maybe", repeatability_audited="yes", improver_gain_isolated="yes", selection_unused_eval="yes"),
        "all_good": dict(product_process_split="yes", repeatability_audited="yes", improver_gain_isolated="yes", selection_unused_eval="yes"),
    }
    expects = {
        "product_process_conflation": ("downgrade", "RSI_CLAIM_AUDIT.PRODUCT_PROCESS_CONFLATION"),
        "repeatability_unaudited": ("downgrade", "RSI_CLAIM_AUDIT.REPEATABILITY_UNAUDITED"),
        "improver_confound": ("downgrade", "RSI_CLAIM_AUDIT.IMPROVER_CONFOUND"),
        "selection_gap": ("flag", "RSI_CLAIM_AUDIT.SELECTION_UNUSED_GAP"),
        "partial_disclosure": ("flag", "RSI_CLAIM_AUDIT.PARTIAL"),
        "literal_enum": ("flag", "RSI_CLAIM_AUDIT.INVALID_INPUT"),
        "all_good": ("ok", "RSI_CLAIM_AUDIT.SELF_CONSISTENT"),
    }
    checks, detail = {}, {}
    for name, inp in cases.items():
        v = check_rsi_claim_audit_honesty("live:" + name, **inp)
        exp_a, exp_c = expects[name]
        detail[name] = f"{v.action}/{v.code}"
        checks[name] = (v.action == exp_a and v.code == exp_c)
    return {"checks": checks, "cases": detail, "all_passed": all(checks.values())}
