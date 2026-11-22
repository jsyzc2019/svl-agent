"""静默失败诚实性门禁 — 把 arXiv:2611.10063 编译成会拦的动作（自主运维首日 §90）。

一手证据（见 audit_silent_failure/）：
  - S01 abs + S02 全文（arXiv:2611.10063v1，Celabe / Hochschule Coburg / Independent）。
  - 机械 CAD agent 写参数化代码：语法成功(能跑/能渲染)与语义正确(尺寸/约束/可制造)解耦。
  - 静默失败三合取：有效可渲染几何 + 显式完成声明 + 至少一个语义检查失败。
  - 自审 oracle：硬化自己的判据把 519 个复判中的 18 个 pass→fail、无一反向；
    盲审专家又推翻其中 3 个（唯一规格含两解的任务之外）。

为什么是新牙（对比现有门禁）：
  verification_boundary(§75)判『绿灯覆盖边界/完成标准事前定义』；
  proof_boundary(§71)判『证明执行正确≠事实证明/信任根独立/形式化边界/未覆盖披露』；
  二者都不判『带自验证的 agent verdict 系统是否诚实披露——静默失败如何定义、
  判据是否自审并双向报告、改进是否用单变量消融归因、校准与未支持预测是否照报』：
    ①静默失败定义：三合取 vs 崩溃/任一失败都算（定义偷换）；
    ②判据自审：oracle 审计自己且双向报告翻转 vs 把 grader risk 当零；
    ③消融归因：把降幅归因于 claim contract 而非反馈（因果隔离）vs 笼统归反馈；
    ④校准与未支持预测：ECE/可靠度 + 照报数据不支持的预测 vs 全确认/完美校准。
  尺子对象是"任何带自验证的 agent verdict 系统"——可迁移、会拦，KB-META01 会拦才入。

编译纪律（与 gate_prereg.json 一致，实现前 SHA256 锁存 abab1e1f…）：
  - 语义枚举；字面串→flag(R0，避 §56 brittle 根因)；
  - R0-R6 短路返回，不事后加权(防 Goodhart)；
  - 只判『边界声明是否诚实自洽』，不承诺方法真实有效——存在≠有效性(KB-R07/META01)；
    self-reported 吞吐/降幅按 KB-RSI07 折 1，不读成普适结论。

诚实边界：定位为审读外部带自验证 verdict 系统的尺子，不判本仓；
遵循 §58 选 A 不接 run_loop。
"""
from __future__ import annotations

from dataclasses import dataclass

_ENUM = frozenset({"yes", "no", "partial"})


@dataclass(frozen=True)
class SilentFailureVerdict:
    claim: str
    silent_failure_triple_defined: str
    oracle_self_audited: str
    claim_contract_ablated: str
    calibration_and_unsupported_reported: str
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_silent_failure_honesty(
    claim: str,
    *,
    silent_failure_triple_defined: str,
    oracle_self_audited: str,
    claim_contract_ablated: str,
    calibration_and_unsupported_reported: str,
) -> SilentFailureVerdict:
    """判一个带自验证的 agent verdict 系统是否诚实披露静默失败边界（不承诺有效）。

    输入须为语义枚举：四维 ∈ {yes, no, partial}

    规则按优先级短路返回（与 gate_prereg.json R0-R6 一致）：
      R0 任一非枚举 → flag
      R1 silent_failure_triple_defined=no → downgrade（定义偷换：崩溃/任一失败冒充静默失败）
      R2 oracle_self_audited=no → downgrade（判据不自审/只报单向，grader risk 当零）
      R3 claim_contract_ablated=no → downgrade（改进归因于反馈而非契约，因果混淆）
      R4 calibration_and_unsupported_reported=no → flag（校准不披露/未支持预测隐瞒）
      R5 任一 partial → flag（覆盖不全，待核）
      R6 全 yes → ok（只判声明自洽）
    """
    vals = (silent_failure_triple_defined, oracle_self_audited,
            claim_contract_ablated, calibration_and_unsupported_reported)
    if any(v not in _ENUM for v in vals):
        return SilentFailureVerdict(
            claim, *(str(v) for v in vals),
            "flag", "SILENT_FAILURE.INVALID_INPUT",
            "四维须为 yes/no/partial 语义枚举；非法值（含字面串）→ flag，不进内容判定",
        )
    if silent_failure_triple_defined == "no":
        return SilentFailureVerdict(
            claim, *vals, "downgrade", "SILENT_FAILURE.DEFINITION_SWAP",
            "静默失败未定义为三合取(有效几何+显式完成声明+语义检查失败)，把崩溃/任一失败冒充——定义偷换",
        )
    if oracle_self_audited == "no":
        return SilentFailureVerdict(
            claim, *vals, "downgrade", "SILENT_FAILURE.GRADER_RISK_ZERO",
            "判据 oracle 不自审或只报单向翻转(不报 none-in-reverse)——把 grader risk 当零(KB-R-AUDIT01)",
        )
    if claim_contract_ablated == "no":
        return SilentFailureVerdict(
            claim, *vals, "downgrade", "SILENT_FAILURE.CAUSAL_CONFOUND",
            "改进未用单变量消融归因于 claim contract，笼统归功于反馈——因果混淆(KB-AUDIT06)",
        )
    if calibration_and_unsupported_reported == "no":
        return SilentFailureVerdict(
            claim, *vals, "flag", "SILENT_FAILURE.OVERCLAIM",
            "置信校准(ECE/可靠度)不披露或未支持的预注册预测隐瞒——过度宣称，待核",
        )
    if any(v == "partial" for v in vals):
        return SilentFailureVerdict(
            claim, *vals, "flag", "SILENT_FAILURE.PARTIAL",
            "静默失败边界披露覆盖不全(partial)——拦截面存在但缺口未补齐，待核",
        )
    return SilentFailureVerdict(
        claim, *vals, "ok", "SILENT_FAILURE.SELF_CONSISTENT",
        "四维边界声明自洽——只判声明诚实存在，不承诺方法真实有效(存在≠有效性)",
    )


def live_regression() -> dict:
    """7 个活体样例回归——对齐 gate_prereg.json 的 R0-R6 预期。"""
    cases = {
        "definition_swap": dict(silent_failure_triple_defined="no", oracle_self_audited="yes", claim_contract_ablated="yes", calibration_and_unsupported_reported="yes"),
        "grader_risk_zero": dict(silent_failure_triple_defined="yes", oracle_self_audited="no", claim_contract_ablated="yes", calibration_and_unsupported_reported="yes"),
        "causal_confound": dict(silent_failure_triple_defined="yes", oracle_self_audited="yes", claim_contract_ablated="no", calibration_and_unsupported_reported="yes"),
        "overclaim": dict(silent_failure_triple_defined="yes", oracle_self_audited="yes", claim_contract_ablated="yes", calibration_and_unsupported_reported="no"),
        "partial_disclosure": dict(silent_failure_triple_defined="yes", oracle_self_audited="yes", claim_contract_ablated="partial", calibration_and_unsupported_reported="yes"),
        "literal_enum": dict(silent_failure_triple_defined="maybe", oracle_self_audited="yes", claim_contract_ablated="yes", calibration_and_unsupported_reported="yes"),
        "all_good": dict(silent_failure_triple_defined="yes", oracle_self_audited="yes", claim_contract_ablated="yes", calibration_and_unsupported_reported="yes"),
    }
    expects = {
        "definition_swap": ("downgrade", "SILENT_FAILURE.DEFINITION_SWAP"),
        "grader_risk_zero": ("downgrade", "SILENT_FAILURE.GRADER_RISK_ZERO"),
        "causal_confound": ("downgrade", "SILENT_FAILURE.CAUSAL_CONFOUND"),
        "overclaim": ("flag", "SILENT_FAILURE.OVERCLAIM"),
        "partial_disclosure": ("flag", "SILENT_FAILURE.PARTIAL"),
        "literal_enum": ("flag", "SILENT_FAILURE.INVALID_INPUT"),
        "all_good": ("ok", "SILENT_FAILURE.SELF_CONSISTENT"),
    }
    checks, detail = {}, {}
    for name, inp in cases.items():
        v = check_silent_failure_honesty("live:" + name, **inp)
        exp_a, exp_c = expects[name]
        detail[name] = f"{v.action}/{v.code}"
        checks[name] = (v.action == exp_a and v.code == exp_c)
    return {"checks": checks, "cases": detail, "all_passed": all(checks.values())}
