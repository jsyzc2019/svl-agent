"""自知诚实性门禁 — 把「批判性思考问题清单」编译成会判动作（§75）。

一手证据（见 audit_addy_critical_thinking/）：
  - S01 公众号 AINLP《Addy Osmani：当 Agent 接手工作，如何保持批判性思考》
    中文全文（用户 2026-11-22 确认出处；经同源同步站 52nlp 下载，2026-11-04，
    SHA256 26483d35…，页面文末『关注微信公众号AINLP』证实同源），含原作者
    英文原稿检测截图与完整参考链接。原文为 X 长文《Critical thinking when
    agents do the work》(2026-11-03)。这是 §74 认知投降谱系的门首篇——
    §74 时该 X 链接 DNS 劫持不可达，此次补齐一手内容。
    核心自问：提问前先形成假设；帮你想还是替你想；什么情况成立时结论会错；
    听过反方论证吗；不再练习的技能是什么；盲点检查（你不知道自己不知道的）。
    "你只需要知道，自己缺少哪些理解"；"知道什么时候该深挖，本身就是能力"。
  - S02 TechMoon 独立综述（2026-11-05，第三方证据分级）：明标这是"个人实务
    观察，无采用率/前后对照量化"；华顿研究只证明认知投降会发生，未证明六个
    自问能防止；Anthropic 132 人单公司、生产力数字自我报告。综合：证据只支持
    作者提出并自述这些自问，不支持六问有效。

为什么是新牙（对比现有 25 门禁）：
  supervision_viability(§74) 判『一个声称有人类评审的流程，是否诚实披露评审者
  仍具备独立判断能力这一前提』——是能力存在性层次（评审环节存在≠评审者仍有
  独立观点）。本门禁判『一个主体/流程是否诚实觉察并披露自己的认知边界』：
    ①假设先行——提问前是否先形成可错预期（认知卸载的起点防线）；
    ②认知局限自陈——是否标注自己缺少的理解，而非假装完整心智模型；
    ③可证伪自问——是否主动问"什么情况成立时我的结论会错"；
    ④技能退化披露——是否诚实列出不再练习的关键能力。
  这是比"评审能力前提"更内一层的元认知自知（self-knowledge）层次：
  "知道自己不知道什么"。拦截面独立可迁移（任何"输出结论+声称已审慎"的主体
  都适用，KB-META01 会拦才入）。

编译纪律（与 gate_prereg.json 一致，实现前 SHA256 锁存 7ca4020e…）：
  - 四维语义枚举 yes/no/partial；字面串→flag(R0，避 §56 brittle 根因)；
  - 规则 R0-R6 短路返回，不事后加权(防 Goodhart)；
  - 只判『认知边界声明是否诚实自洽』，不承诺真能防认知投降——提出框架≠证明
    有效(KB-STRUCT05)、自洽≠有效(KB-R07)、self-reported 折扣(KB-RSI07)、
    同谱系折扣(KB-STRUCT02)；
  - 遵循 §58 选 A，不接 run_loop；中文锚点集中 _A，Compare 内无中文字面量。

诚实边界：定位为审读外部主体/流程的尺子，不判本仓；本仓判据库是被动工具库。
"""
from __future__ import annotations

from dataclasses import dataclass

_ENUM = frozenset({"yes", "no", "partial"})

# 中文锚点集中管理（AST 自审：Compare 内禁中文字面量，避 §56 brittle 根因）
_A = {
    "invalid": "四维须为 yes/no/partial 语义枚举；非法值（含字面串）→ flag，不进内容判定",
    "no_hypothesis": (
        "提问前未形成任何可错假设——直接问 agent 该怎么做，认知卸载的起点；"
        "读过流畅回答后再想象其他可能性更难，判定打折"
    ),
    "false_completeness": (
        "假装拥有完整心智模型、不标注自己缺少的理解——现代大型代码库完整模型"
        "不可能常在脑中，要害是知道自己缺哪些理解；假装完整判定打折"
    ),
    "unfalsifiable": (
        "未主动问『什么情况成立时我的结论会错』——模型自陈把握远不如实测有价值，"
        "不可证伪的自洽判定打折"
    ),
    "hidden_atrophy": (
        "未诚实披露不再练习的关键能力——不再练习的能力会消失且更快，"
        "隐瞒技能退化却声称仍可监督，判定打折"
    ),
    "partial": "自知诚实性覆盖不全(partial)——拦截面存在但缺口未补齐，待核",
    "self_consistent": (
        "四维认知边界声明自洽——只判声明诚实存在，不承诺真能防认知投降"
        "(提出框架≠有效、自洽≠有效)"
    ),
}


@dataclass(frozen=True)
class SelfKnowledgeHonestyVerdict:
    claim: str
    hypothesis_before_query: str
    cognitive_limits_disclosed: str
    falsification_self_asked: str
    skill_atrophy_disclosed: str
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_self_knowledge_honesty(
    claim: str,
    *,
    hypothesis_before_query: str,
    cognitive_limits_disclosed: str,
    falsification_self_asked: str,
    skill_atrophy_disclosed: str,
) -> SelfKnowledgeHonestyVerdict:
    """判一个主体是否诚实觉察并披露自己的认知边界（不承诺真能防认知投降）。

    输入须为语义枚举：四维 ∈ {yes, no, partial}
      - hypothesis_before_query: 提问/委托前是否先形成可错的预期答案
      - cognitive_limits_disclosed: 是否标注自己缺少的理解，而非假装完整
      - falsification_self_asked: 是否主动问"什么情况成立时结论会错"
      - skill_atrophy_disclosed: 是否诚实列出不再练习的关键能力

    规则按优先级短路返回（与 gate_prereg.json R0-R6 一致）：
      R0 任一非枚举 → flag
      R1 hypothesis_before_query=no → downgrade（无假设直接问）
      R2 cognitive_limits_disclosed=no → downgrade（假装完整）
      R3 falsification_self_asked=no → downgrade（不可证伪的自洽）
      R4 skill_atrophy_disclosed=no → downgrade（隐瞒技能退化）
      R5 任一 partial → flag（覆盖不全，待核）
      R6 全 yes → ok（只判声明自洽，不承诺真防投降）
    """
    vals = (hypothesis_before_query, cognitive_limits_disclosed,
            falsification_self_asked, skill_atrophy_disclosed)
    if any(v not in _ENUM for v in vals):
        return SelfKnowledgeHonestyVerdict(
            claim, *(str(v) for v in vals),
            "flag", "SELF_KNOWLEDGE.INVALID_INPUT", _A["invalid"],
        )
    if hypothesis_before_query == "no":
        return SelfKnowledgeHonestyVerdict(
            claim, *vals, "downgrade", "SELF_KNOWLEDGE.NO_HYPOTHESIS",
            _A["no_hypothesis"],
        )
    if cognitive_limits_disclosed == "no":
        return SelfKnowledgeHonestyVerdict(
            claim, *vals, "downgrade", "SELF_KNOWLEDGE.FALSE_COMPLETENESS",
            _A["false_completeness"],
        )
    if falsification_self_asked == "no":
        return SelfKnowledgeHonestyVerdict(
            claim, *vals, "downgrade", "SELF_KNOWLEDGE.UNFALSIFIABLE",
            _A["unfalsifiable"],
        )
    if skill_atrophy_disclosed == "no":
        return SelfKnowledgeHonestyVerdict(
            claim, *vals, "downgrade", "SELF_KNOWLEDGE.HIDDEN_ATROPHY",
            _A["hidden_atrophy"],
        )
    if any(v == "partial" for v in vals):
        return SelfKnowledgeHonestyVerdict(
            claim, *vals, "flag", "SELF_KNOWLEDGE.PARTIAL", _A["partial"],
        )
    return SelfKnowledgeHonestyVerdict(
        claim, *vals, "ok", "SELF_KNOWLEDGE.SELF_CONSISTENT", _A["self_consistent"],
    )


def live_regression() -> dict:
    """8 个活体样例回归——对齐 gate_prereg.json 的 R0-R6 预期。"""
    base = dict(hypothesis_before_query="yes", cognitive_limits_disclosed="yes",
                falsification_self_asked="yes", skill_atrophy_disclosed="yes")
    cases = {
        "no_hypothesis": dict(base, hypothesis_before_query="no"),
        "false_completeness": dict(base, cognitive_limits_disclosed="no"),
        "unfalsifiable": dict(base, falsification_self_asked="no"),
        "hidden_atrophy": dict(base, skill_atrophy_disclosed="no"),
        "partial": dict(base, falsification_self_asked="partial"),
        "self_consistent": dict(base),
        "literal_string": dict(base, hypothesis_before_query="我们会先想清楚再问"),
        "priority_hypothesis_over_completeness": dict(
            base, hypothesis_before_query="no", cognitive_limits_disclosed="no"),
    }
    out = {}
    for name, kw in cases.items():
        v = check_self_knowledge_honesty("claim:" + name, **kw)
        out[name] = {"action": v.action, "code": v.code}
    expected = {
        "no_hypothesis": ("downgrade", "SELF_KNOWLEDGE.NO_HYPOTHESIS"),
        "false_completeness": ("downgrade", "SELF_KNOWLEDGE.FALSE_COMPLETENESS"),
        "unfalsifiable": ("downgrade", "SELF_KNOWLEDGE.UNFALSIFIABLE"),
        "hidden_atrophy": ("downgrade", "SELF_KNOWLEDGE.HIDDEN_ATROPHY"),
        "partial": ("flag", "SELF_KNOWLEDGE.PARTIAL"),
        "self_consistent": ("ok", "SELF_KNOWLEDGE.SELF_CONSISTENT"),
        "literal_string": ("flag", "SELF_KNOWLEDGE.INVALID_INPUT"),
        "priority_hypothesis_over_completeness": ("downgrade", "SELF_KNOWLEDGE.NO_HYPOTHESIS"),
    }
    ok = all(out[k]["action"] == expected[k][0] and out[k]["code"] == expected[k][1]
             for k in expected)
    return {"cases": out, "expected": expected, "all_match": ok}
