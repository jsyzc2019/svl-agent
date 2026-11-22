"""接口契约边界诚实性门禁 — 把 DeepSeek 全家桶 API 的契约边界编译成会判动作（§73）。

一手证据（见 audit_deepseek/）：
  - S03 构建 Chatbot 指南（一手，SHA256 f05387a1…）『被忽略的参数』：声明
    deepseek_web_search / safety_check=high / title 后，temperature/top_p/
    seed 等由服务端决定，请求传入值被忽略；『搜索和阅读链接都由服务端完成』，
    客户端只展示内容块并原样回传；合规义务（内容安全审核/大模型登记/AI 标识）
    在开发者，平台仅『基础风控』。
  - S05 定价页（一手，SHA256 e872c2c8…）：服务端搜索工具『本身不再计费』但
    『结果拼进上下文按 Token 计费』；deepseek-v4-flash 等别名『仍可调用但对应
    模型已下线』由 V4.1-Flash 提供服务。
  - S04 仓库 types.ts（一手，commit 8ad7b56…）：encrypted_content『客户端无法
    解密展示』、signature『服务端解密恢复网页上下文』；parseEvent.ts『未识别或
    无法安全消费的事件静默丢弃』；README『附件格式以服务端校验为准』。
  - S01 在线 Demo / S02 发布公告（一手、同主体）：能力效果 self-reported 折扣。

为什么是新牙（对比现有 20 道门禁）：
  call_site_integrity 判代码是否接线到声明的调用点、serving_signal 判训练/服务
  口径、retrieval_grounding 判检索文本是 data 非 instruction、
  proof_boundary_honesty 判可证明声明范围、proactive_authorization 判介入授权、
  memory_scope 判记忆作用域、session_continuity 判跨 run 续接——无一判『一个
  客户端/Agent 声称它控制的参数与能力，是否诚实区分了自己能决定的 vs 服务端
  悄悄接管/忽略/重新计费的』。这是任何『客户端声明层 + 服务端裁决层』系统都
  适用的可迁移拦截面（会拦才入 KB-META01），非 DeepSeek 特例。

编译纪律（与 gate_prereg.json 一致，实现前 SHA256 锁存 8f8dbf15…）：
  - 四维语义枚举 yes/no/partial；字面串→flag(R0，避 §56 brittle 根因)；
  - 规则 R0-R6 短路返回，不事后加权(防 Goodhart)；
  - 只判『契约声明是否诚实披露控制边界』，不承诺服务端行为真按声明执行
    ——存在≠有效性(KB-META01/AUDIT03)；self-reported 不采信(KB-RSI07)；
  - 遵循 §58 选 A，不接 run_loop。

诚实边界：定位为审读外部 API 契约与客户端实现的尺子，不判本仓；本仓判据库
本身是被动工具库。与 proof_boundary_honesty(证明范围)/proactive_authorization
(介入授权)/serving_signal(训练服务口径) 的对象与动作均不同，拦截面独立。
"""
from __future__ import annotations

from dataclasses import dataclass

_ENUM = frozenset({"yes", "no", "partial"})


@dataclass(frozen=True)
class InterfaceContractVerdict:
    claim: str
    param_effect_authority: str
    alias_route_truth: str
    risk_compliance_ownership: str
    cost_scope_honesty: str
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_interface_contract_honesty(
    claim: str,
    *,
    param_effect_authority: str,
    alias_route_truth: str,
    risk_compliance_ownership: str,
    cost_scope_honesty: str,
) -> InterfaceContractVerdict:
    """判一个接口契约声称是否诚实披露控制边界（不承诺服务端真按声明裁决）。

    输入须为语义枚举：四维 ∈ {yes, no, partial}
      - param_effect_authority: 声称受控的参数是否真由调用方决定
      - alias_route_truth: 使用的模型/接口别名是否真路由到声称后端
      - risk_compliance_ownership: 安全校验是否被当成完整合规
      - cost_scope_honesty: 工具免费是否被当成零成本

    规则按优先级短路返回（与 gate_prereg.json R0-R6 一致）：
      R0 任一非枚举 → flag
      R1 param_effect_authority=no → downgrade（传入≠生效）
      R2 alias_route_truth=no → downgrade（别名≠实际路由）
      R3 risk_compliance_ownership=no → downgrade（基础风控冒充完整合规）
      R4 cost_scope_honesty=no → flag（工具免费冒充零成本）
      R5 任一 partial → flag（覆盖不全，待核）
      R6 全 yes → ok（只判声明自洽，不承诺服务端真按声明执行）
    """
    vals = (param_effect_authority, alias_route_truth,
            risk_compliance_ownership, cost_scope_honesty)
    if any(v not in _ENUM for v in vals):
        return InterfaceContractVerdict(
            claim, *(str(v) for v in vals),
            "flag", "IFACE_CONTRACT.INVALID_INPUT",
            "四维须为 yes/no/partial 语义枚举；非法值（含字面串）→ flag，不进内容判定",
        )
    if param_effect_authority == "no":
        return InterfaceContractVerdict(
            claim, *vals, "downgrade", "IFACE_CONTRACT.PARAM_IGNORED",
            "声称控制的参数被服务端忽略(temperature/top_p/seed 由服务端决定)——传入≠生效(KB-AUDIT03)，判定打折",
        )
    if alias_route_truth == "no":
        return InterfaceContractVerdict(
            claim, *vals, "downgrade", "IFACE_CONTRACT.ALIAS_REROUTED",
            "别名仍可调用但后端已换(deepseek-v4-flash→V4.1-Flash)——名义可用≠实际路由，判定打折",
        )
    if risk_compliance_ownership == "no":
        return InterfaceContractVerdict(
            claim, *vals, "downgrade", "IFACE_CONTRACT.RISK_OWNERSHIP_SHIFT",
            "把基础风控当成完整合规——内容安全审核/大模型登记/AI 标识义务在开发者，责任主体错位(KB-STRUCT05)，判定打折",
        )
    if cost_scope_honesty == "no":
        return InterfaceContractVerdict(
            claim, *vals, "flag", "IFACE_CONTRACT.COST_SCOPE_MIXED",
            "把工具免费当成零成本——服务端搜索工具本身不计费但结果 token 计费，计费口径误述，待核",
        )
    if any(v == "partial" for v in vals):
        return InterfaceContractVerdict(
            claim, *vals, "flag", "IFACE_CONTRACT.PARTIAL",
            "契约边界声明覆盖不全(partial)——拦截面存在但缺口未补齐，待核",
        )
    return InterfaceContractVerdict(
        claim, *vals, "ok", "IFACE_CONTRACT.SELF_CONSISTENT",
        "四维契约边界声明自洽——只判声明诚实存在，不承诺服务端行为真按声明执行(存在≠有效性)",
    )


def live_regression() -> dict:
    """8 个活体样例回归——对齐 gate_prereg.json 的 R0-R6 预期。"""
    base = dict(param_effect_authority="yes", alias_route_truth="yes",
                risk_compliance_ownership="yes", cost_scope_honesty="yes")
    cases = {
        "param_ignored": dict(base, param_effect_authority="no"),
        "alias_rerouted": dict(base, alias_route_truth="no"),
        "risk_shift": dict(base, risk_compliance_ownership="no"),
        "cost_mixed": dict(base, cost_scope_honesty="no"),
        "partial": dict(base, cost_scope_honesty="partial"),
        "self_consistent": dict(base),
        "literal_string": dict(base, param_effect_authority="我控制了随机性"),
        "priority_param_over_alias": dict(base, param_effect_authority="no", alias_route_truth="no"),
    }
    out = {}
    for name, kw in cases.items():
        v = check_interface_contract_honesty("claim:" + name, **kw)
        out[name] = {"action": v.action, "code": v.code}
    expected = {
        "param_ignored": ("downgrade", "IFACE_CONTRACT.PARAM_IGNORED"),
        "alias_rerouted": ("downgrade", "IFACE_CONTRACT.ALIAS_REROUTED"),
        "risk_shift": ("downgrade", "IFACE_CONTRACT.RISK_OWNERSHIP_SHIFT"),
        "cost_mixed": ("flag", "IFACE_CONTRACT.COST_SCOPE_MIXED"),
        "partial": ("flag", "IFACE_CONTRACT.PARTIAL"),
        "self_consistent": ("ok", "IFACE_CONTRACT.SELF_CONSISTENT"),
        "literal_string": ("flag", "IFACE_CONTRACT.INVALID_INPUT"),
        "priority_param_over_alias": ("downgrade", "IFACE_CONTRACT.PARAM_IGNORED"),
    }
    ok = all(out[k]["action"] == expected[k][0] and out[k]["code"] == expected[k][1] for k in expected)
    return {"cases": out, "expected": expected, "all_match": ok}
