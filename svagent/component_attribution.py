"""组件归因门禁 — 把 RSI-Structure 综述的 Where 维度编译成可执行判据。

来源（一手逐字，rsi_structure_paper.txt §3）：
  "Failure alone does not specify what to edit; the system must analyze what happened."
  "content directly included in context is Prompt, records retrieved under a condition
   is Memory, and procedures selected and executed by the agent as Skill. Changes to
   mechanisms such as context management, tool dispatch, or verification are Harness."
  "the check needs to cover intended uses, including less frequent but still important tasks."

对应框架缺口（T4 识别，T6 判定为可长牙）：
  V3 — 失败叙述未强制归因到具体组件、未按组件选验证方式 → 拦截
  V6 — 退役/drop 未检查低频但重要用途 → 降级为 verify

设计纪律：
  - 分类按"内容如何进入执行"而非存储介质（论文明确：文本/介质/时长不决定分类）。
  - 判据写死、可测试；不事后加权；防"我诊断过了"的自证。
  - 只编译真缺口，不重复 improvement_memory 已有的回归/命中率/上下文迁移判据。
"""
from __future__ import annotations

from dataclasses import dataclass, field

COMPONENTS = ("Prompt", "Memory", "Skill", "Harness")

# 每个组件的"内容如何进入执行"判据（关键词仅为启发式提示，最终需显式声明）
COMPONENT_SIGNALS: dict[str, tuple[str, ...]] = {
    "Prompt": ("system prompt", "指令", "instruction", "直接纳入上下文", "示例", "demonstration"),
    "Memory": ("检索", "retriev", "向量库", "历史案例", "记忆条目", "按条件读取"),
    "Skill": ("可调用", "工具函数", "流程", "procedure", "技能", "可执行程序", "选择并执行"),
    "Harness": ("校验", "调度", "验证逻辑", "上下文管理", "工具调用管理", "admission", "检查机制"),
}

# 组件 → 适配的验证方式（论文：不同组件 need different evaluations）
VERIFICATION_BY_COMPONENT: dict[str, str] = {
    "Prompt": "held-out 任务上测指令改善",
    "Memory": "检索有效性测试（取出的记录是否改善决策）",
    "Skill": "执行成功率测试（agent 能否跑通流程并改善结果）",
    "Harness": "回归/副作用测试（约束是否生效且不破坏合法行为）",
}


@dataclass
class AttributionClaim:
    """一次'失败→要改哪里'的诊断声明。"""
    failure: str                              # 失败/触发事件描述
    component: str = ""                       # 归因到的组件（须在 COMPONENTS 中）
    why_this_component: str = ""              # 为什么是这个组件（执行证据）
    verification: str = ""                    # 打算如何验证该改动
    dropping: bool = False                    # 是否是退役/drop 决策
    checked_rare_uses: bool = False           # 退役时是否检查了低频但重要用途


@dataclass(frozen=True)
class GateVerdict:
    action: str        # allow | block | downgrade
    code: str
    message: str


def classify_component_by_description(description: str) -> list[str]:
    """启发式：返回可能的组件候选（按命中信号数排序）。仅作提示，不替代显式声明。"""
    d = description.lower()
    scores: dict[str, int] = {}
    for comp, signals in COMPONENT_SIGNALS.items():
        s = sum(1 for sig in signals if sig.lower() in d)
        if s:
            scores[comp] = s
    return [c for c, _ in sorted(scores.items(), key=lambda x: -x[1])]


def guard(claim: AttributionClaim) -> GateVerdict:
    """归因充分性门禁。写死规则，按优先级拦截。"""
    # 先看启发式候选，用于给出提示（不作为放行依据）
    candidates = classify_component_by_description(claim.failure)

    # G1 组件缺失/非法 → 拦截（V3 核心：失败不指定改哪里，须显式归因）
    if claim.component not in COMPONENTS:
        hint = f"（提示候选：{', '.join(candidates)}）" if candidates else ""
        return GateVerdict(
            "block", "ATTR.COMPONENT_MISSING",
            f"失败叙述未归因到具体组件 Prompt/Memory/Skill/Harness{hint}——"
            "失败本身不告诉你要改哪里，必须基于执行证据显式归因（论文 §9.1）",
        )

    # G2 归因无证据 → 拦截（防"我诊断过了"的自证）
    if not claim.why_this_component.strip():
        return GateVerdict(
            "block", "ATTR.NO_EVIDENCE",
            f"归因为 {claim.component} 但无执行证据说明——同一次失败可能多组件致因，"
            "归因须由证据支持（论文 §3.1 / §9.2）",
        )

    # G3 验证方式缺失 → 拦截（不同组件需不同验证）
    if not claim.verification.strip():
        expected = VERIFICATION_BY_COMPONENT[claim.component]
        return GateVerdict(
            "block", "ATTR.VERIFY_MISSING",
            f"改动 {claim.component} 但未声明验证方式；该组件适配：{expected}（论文 §3.4/§4.1 Evaluate≠Verify）",
        )

    # G4 退役未检查低频用途 → 降级（V6：retirement 须覆盖低频重要任务）
    if claim.dropping and not claim.checked_rare_uses:
        return GateVerdict(
            "downgrade", "ATTR.RARE_USE_UNCHECKED",
            "退役/删除该组件内容前未检查'低频但重要用途'——"
            "退役改变后续可选范围，须覆盖少见但关键的任务（论文 §9.3），降为 verify 后重验",
        )

    return GateVerdict(
        "allow", "ATTR.OK",
        f"归因 {claim.component} 且有证据、有适配验证"
        + ("，退役已覆盖低频用途" if claim.dropping else ""),
    )


def verification_for(component: str) -> str:
    """查询某组件适配的验证方式。"""
    return VERIFICATION_BY_COMPONENT.get(component, "未知组件，无法给出适配验证")
