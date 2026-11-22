"""主动介入的授权正当性门禁 — 把 Proactive AI 综述编译成会判动作（§72）。

一手证据（见 audit_proactive_ai/）：
  - S01 论文 PDF（一手，UIUC/Google/Stanford/Berkeley/CMU 五机构联合综述，
    SHA256 e90ef681…）：§2.1 定义 proactive = "delegated discretion within the
    applicable goals, constraints, and permissions"；Figure10 "a worthwhile goal
    is not yet a warranted intervention"；§4.4 仲裁四问（置信/价值成本/时机/
    风险可逆）；§7.2.2 "formal authority" vs agent 靠选信息/选项/默认项获
    "real authority"；§7.2.3 "risk-tiered consent models"；§4.4.1 "non-act is
    invisible" + "hold-and-monitor rung"。
  - S02 作者项目主页（一手，同主体，SHA256 82d47471…）：6A / 13 domains /
    1,410 works cited / authority 阶梯。
  - S03 Google Research 元数据页：抓取失败，标 unavailable，不据此下断言。

为什么是新牙（对比现有门禁）：
  proof_boundary_honesty(§71)判可证明声明的证明边界、memory_scope(§70)判记忆
  作用域、serving_signal 判训练/服务口径、session_continuity 判跨 run 续接、
  retrieval_grounding 判检索文本是 data 非 instruction——无一判『一个主动
  agent 声称"我主动做了 X"时，是否把目标价值冒充介入授权、是否过仲裁四关、
  是否披露形式授权与真实控制的落差、是否披露沉默选项与风险分级同意』。
  综述贡献分类学语言，按 KB-STRUCT05 提出框架≠证明有效，不为"主动 agent 很
  重要/6A 很全"造牙；只为可迁移的拦截面造牙，KB-META01 会拦才入通过。

编译纪律（与 gate_prereg.json 一致，实现前 SHA256 锁存 028504e5…）：
  - 语义枚举 yes/no/partial；字面串→flag(R0，避 §56 brittle 根因)；
  - 规则 R0-R6 短路返回，不事后加权(防 Goodhart)；
  - 只判『授权声明是否诚实自洽』，不承诺系统真校准/真的只在授权内行动
    ——存在≠有效性(KB-META01/AUDIT03)；self-reported 不采信(KB-RSI07)；
  - 遵循 §58 选 A，不接 run_loop。

诚实边界：定位为审读外部主动 agent 系统声称的尺子，不判本仓；本仓判据库
本身是被动工具库。与 KB-R07(自洽 vs 有效) 对象动作不同，拦截面独立。
"""
from __future__ import annotations

from dataclasses import dataclass

_ENUM = frozenset({"yes", "no", "partial"})


@dataclass(frozen=True)
class ProactiveAuthorizationVerdict:
    claim: str
    worthwhile_not_warranted: str
    arbitration_four_gates: str
    formal_not_effective_control: str
    silence_and_consent_disclosed: str
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_proactive_authorization(
    claim: str,
    *,
    worthwhile_not_warranted: str,
    arbitration_four_gates: str,
    formal_not_effective_control: str,
    silence_and_consent_disclosed: str,
) -> ProactiveAuthorizationVerdict:
    """判一个主动 agent 声称是否诚实亮出授权边界与仲裁四关（不承诺其真校准）。

    输入须为语义枚举：四维 ∈ {yes, no, partial}

    规则按优先级短路返回（与 gate_prereg.json R0-R6 一致）：
      R0 任一非枚举 → flag
      R1 worthwhile_not_warranted=no → downgrade（目标价值冒充介入授权）
      R2 arbitration_four_gates=no → downgrade（act-first 无仲裁）
      R3 formal_not_effective_control=no → downgrade（形式授权冒充真实控制）
      R4 silence_and_consent_disclosed=no → flag（不披露沉默与风险分级同意）
      R5 任一 partial → flag（覆盖不全，待核）
      R6 全 yes → ok（只判授权声明自洽，不承诺系统真校准）
    """
    vals = (worthwhile_not_warranted, arbitration_four_gates,
            formal_not_effective_control, silence_and_consent_disclosed)
    if any(v not in _ENUM for v in vals):
        return ProactiveAuthorizationVerdict(
            claim, *(str(v) for v in vals),
            "flag", "PROACTIVE_AUTH.INVALID_INPUT",
            "四维须为 yes/no/partial 语义枚举；非法值（含字面串）→ flag，不进内容判定",
        )
    if worthwhile_not_warranted == "no":
        return ProactiveAuthorizationVerdict(
            claim, *vals, "downgrade", "PROACTIVE_AUTH.GOAL_AS_WARRANT",
            "把『目标值得做』冒充『介入被授权』——Figure10 worthwhile≠warranted，主体错位(KB-STRUCT05)，判定打折",
        )
    if arbitration_four_gates == "no":
        return ProactiveAuthorizationVerdict(
            claim, *vals, "downgrade", "PROACTIVE_AUTH.NO_ARBITRATION",
            "act-first 无仲裁四关(置信/价值成本/时机/风险可逆)——价值与风险未过闸即介入，判定打折",
        )
    if formal_not_effective_control == "no":
        return ProactiveAuthorizationVerdict(
            claim, *vals, "downgrade", "PROACTIVE_AUTH.FORMAL_AS_EFFECTIVE",
            "形式授权冒充真实控制——仅声称用户可覆盖，未披露 agent 靠选信息/选项/默认项获实权(§7.2.2)，判定打折",
        )
    if silence_and_consent_disclosed == "no":
        return ProactiveAuthorizationVerdict(
            claim, *vals, "flag", "PROACTIVE_AUTH.SILENCE_HIDDEN",
            "不披露『不介入/沉默』选项与风险分级同意(low-risk默认/ambiguous澄清/high-impact确认)——过度主动，待核",
        )
    if any(v == "partial" for v in vals):
        return ProactiveAuthorizationVerdict(
            claim, *vals, "flag", "PROACTIVE_AUTH.PARTIAL",
            "授权边界声明覆盖不全(partial)——拦截面存在但缺口未补齐，待核",
        )
    return ProactiveAuthorizationVerdict(
        claim, *vals, "ok", "PROACTIVE_AUTH.SELF_CONSISTENT",
        "四维授权声明自洽——只判声明诚实存在，不承诺系统真校准/真的只在授权内行动(存在≠有效性)",
    )


def live_regression() -> dict:
    """7 个活体样例回归——对齐 gate_prereg.json 的 R0-R6 预期。"""
    cases = {
        "goal_as_warrant": dict(worthwhile_not_warranted="no", arbitration_four_gates="yes", formal_not_effective_control="yes", silence_and_consent_disclosed="yes"),
        "no_arbitration": dict(worthwhile_not_warranted="yes", arbitration_four_gates="no", formal_not_effective_control="yes", silence_and_consent_disclosed="yes"),
        "formal_as_effective": dict(worthwhile_not_warranted="yes", arbitration_four_gates="yes", formal_not_effective_control="no", silence_and_consent_disclosed="yes"),
        "silence_hidden": dict(worthwhile_not_warranted="yes", arbitration_four_gates="yes", formal_not_effective_control="yes", silence_and_consent_disclosed="no"),
        "partial_disclosure": dict(worthwhile_not_warranted="yes", arbitration_four_gates="yes", formal_not_effective_control="partial", silence_and_consent_disclosed="yes"),
        "literal_enum": dict(worthwhile_not_warranted="maybe", arbitration_four_gates="yes", formal_not_effective_control="yes", silence_and_consent_disclosed="yes"),
        "all_good": dict(worthwhile_not_warranted="yes", arbitration_four_gates="yes", formal_not_effective_control="yes", silence_and_consent_disclosed="yes"),
    }
    expects = {
        "goal_as_warrant": ("downgrade", "PROACTIVE_AUTH.GOAL_AS_WARRANT"),
        "no_arbitration": ("downgrade", "PROACTIVE_AUTH.NO_ARBITRATION"),
        "formal_as_effective": ("downgrade", "PROACTIVE_AUTH.FORMAL_AS_EFFECTIVE"),
        "silence_hidden": ("flag", "PROACTIVE_AUTH.SILENCE_HIDDEN"),
        "partial_disclosure": ("flag", "PROACTIVE_AUTH.PARTIAL"),
        "literal_enum": ("flag", "PROACTIVE_AUTH.INVALID_INPUT"),
        "all_good": ("ok", "PROACTIVE_AUTH.SELF_CONSISTENT"),
    }
    checks, detail = {}, {}
    for name, inp in cases.items():
        v = check_proactive_authorization("live:" + name, **inp)
        exp_a, exp_c = expects[name]
        detail[name] = f"{v.action}/{v.code}"
        checks[name] = (v.action == exp_a and v.code == exp_c)
    return {"checks": checks, "cases": detail, "all_passed": all(checks.values())}
