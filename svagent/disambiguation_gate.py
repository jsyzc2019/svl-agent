"""术语歧义前置门禁 — 把 KB-SIM01 从"事后教训"编译成"执行前拦截"。

设计动机（RSI 翻车事件）：
  首轮把 RSI 默认为"证券相对强弱指数"，只因最近语境全是金融。根因不是知识缺失
  （KB-SIM01 已入库），而是那条知识没有被挂到执行流上——它躺在知识库里等人想起来。
  本模块把"遇到多义术语→强制用户消歧"做成 fail-closed 的前置门禁：
    - 命中歧义且无用户确认 → BLOCK，产出人工交接卡，不猜、不按最近语境默认；
    - 有用户确认(且确认来源必须是用户口述) → PASS，携带解析结果放行。

框架对齐：
  - 触发≠真相：检测到多义只是"触发"，不自动得出含义；含义必须由用户确认。
  - 真值隔离(is_user_said)：确认来源必须是已确认的用户口述，agent 自猜不算。
  - Diagnostic/Locus：与 harness 的判据体系统一，可直接进 handoff。
  - addressable：本模块是 KB-SIM01(addressable=True, class=fix) 的可执行编译产物。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .core import Diagnostic, Locus, Message, is_user_said


# ---------------------------------------------------------------- 词典
@dataclass(frozen=True)
class Sense:
    """一个术语的一种可能含义 + 据此的检索/执行方向。"""
    domain: str        # 领域，如 "证券/技术分析"
    expansion: str     # 全称，如 "Relative Strength Index"
    direction: str     # 选定该含义后的检索/执行方向
    note: str = ""


@dataclass(frozen=True)
class AmbiguousTerm:
    """一个已知多义术语。source_lesson 指回它在知识库里的教训来源。"""
    token: str
    senses: tuple[Sense, ...]
    source_lesson: str = "KB-SIM01"

    def __post_init__(self) -> None:
        if len(self.senses) < 2:
            raise ValueError(f"{self.token} 只有一个含义，不构成歧义术语")


def default_registry() -> dict[str, AmbiguousTerm]:
    """内置词典，至少收录本次真实翻车的 RSI；可用 build_registry 扩展。"""
    return {
        "RSI": AmbiguousTerm(
            token="RSI",
            senses=(
                Sense("证券/技术分析", "Relative Strength Index",
                      "检索相对强弱指数的计算/有效性/回测文献与实现",
                      "金融量化语境的常见含义；本次首轮误用即此项"),
                Sense("AI/自我改进", "Recursive Self-Improvement",
                      "检索递归自我改进、自进化 Agent、harness/memory 自改进论文与项目",
                      "用户本次真实意图；SIM/CRSI 论文所属领域"),
            ),
        ),
    }


def build_registry(terms: Iterable[AmbiguousTerm], *, include_defaults: bool = True) -> dict[str, AmbiguousTerm]:
    reg = default_registry() if include_defaults else {}
    for t in terms:
        reg[t.token.upper()] = t
    return reg


# ---------------------------------------------------------------- 确认
@dataclass(frozen=True)
class Confirmation:
    """用户对某术语含义的确认。source 必须是已确认的用户口述。"""
    token: str
    sense_domain: str
    source_message: Message

    @classmethod
    def from_user(cls, token: str, sense_domain: str, msg: Message) -> "Confirmation | None":
        """只接受来自 user 角色、非话题提示、非空的确认；否则拒绝(None)。"""
        if not is_user_said(msg):
            return None
        return cls(token=token.upper(), sense_domain=sense_domain, source_message=msg)


# ---------------------------------------------------------------- 门禁结果
@dataclass
class GateResult:
    status: str                       # "PASS" | "BLOCK"
    query: str
    ambiguity: AmbiguousTerm | None = None
    resolved: dict[str, Sense] = field(default_factory=dict)
    diagnostic: Diagnostic | None = None
    handoff_card: dict | None = None
    situation_tags: list[str] = field(default_factory=list)

    @property
    def allowed(self) -> bool:
        return self.status == "PASS"


# ---------------------------------------------------------------- 检测与门禁
def detect_ambiguous_terms(query: str, registry: dict[str, AmbiguousTerm]) -> list[AmbiguousTerm]:
    """在查询文本中检测词典里的多义术语（词边界匹配，大小写不敏感）。"""
    import re
    found = []
    for token, term in registry.items():
        if re.search(rf"(?<![A-Za-z0-9]){re.escape(token)}(?![A-Za-z0-9])", query, flags=re.IGNORECASE):
            found.append(term)
    return found


def _matching_sense(term: AmbiguousTerm, domain: str) -> Sense | None:
    d = domain.strip().lower()
    for s in term.senses:
        if s.domain.strip().lower() == d or s.expansion.strip().lower() == d:
            return s
    return None


def disambiguation_card(term: AmbiguousTerm, query: str) -> dict:
    """把歧义切成可局部裁决的小靶子——与 handoff.py 的人工交接卡同构。"""
    return {
        "判据": "GATE.TERM_AMBIGUITY",
        "来源教训": term.source_lesson,
        "问题": f"查询中的 '{term.token}' 存在 {len(term.senses)} 种含义，执行前需确认",
        "触发查询": query,
        "候选含义": [
            {"序号": i + 1, "领域": s.domain, "全称": s.expansion,
             "选定后方向": s.direction, "备注": s.note}
            for i, s in enumerate(term.senses)
        ],
        "需用户确认": f"请回答：'{term.token}' 指的是上面第几种含义？（或给出领域/全称）",
    }


def guard(
    query: str,
    registry: dict[str, AmbiguousTerm] | None = None,
    confirmations: list[Confirmation] | None = None,
) -> GateResult:
    """前置门禁主入口：fail-closed。

    - 无歧义 → PASS
    - 有歧义但对应术语无有效用户确认 → BLOCK（附交接卡）
    - 有歧义且所有命中术语都已确认 → PASS（携带解析结果 + 情境标签）
    """
    reg = registry if registry is not None else default_registry()
    # 被拒绝的确认(from_user 返回 None)不应计入，更不能让门禁崩溃——防御性过滤。
    confs = [c for c in (confirmations or []) if c is not None]
    found = detect_ambiguous_terms(query, reg)
    if not found:
        return GateResult(status="PASS", query=query)

    # 按 token 收集已确认的含义
    confirmed_by_token: dict[str, str] = {}
    for c in confs:
        confirmed_by_token[c.token] = c.sense_domain

    unresolved = [t for t in found if t.token not in confirmed_by_token]
    if unresolved:
        term = unresolved[0]
        diag = Diagnostic(
            "GATE.TERM_AMBIGUITY", "block", Locus(ref=term.token),
            f"'{term.token}' 有 {len(term.senses)} 种含义且未经用户确认，禁止按默认语境推断",
        )
        return GateResult(
            status="BLOCK", query=query, ambiguity=term,
            diagnostic=diag, handoff_card=disambiguation_card(term, query),
        )

    # 全部命中术语已确认 → 解析为 Sense 并放行
    resolved: dict[str, Sense] = {}
    tags: list[str] = []
    for t in found:
        sense = _matching_sense(t, confirmed_by_token[t.token])
        if sense is None:
            # 确认了无法匹配的含义 → 同样 fail-closed
            diag = Diagnostic(
                "GATE.CONFIRM_UNMATCHED", "block", Locus(ref=t.token),
                f"对 '{t.token}' 的确认 '{confirmed_by_token[t.token]}' 无法匹配任何已知含义",
            )
            return GateResult(status="BLOCK", query=query, ambiguity=t,
                              diagnostic=diag, handoff_card=disambiguation_card(t, query))
        resolved[t.token] = sense
        tags.extend([t.token.lower(), sense.domain])
    return GateResult(status="PASS", query=query, resolved=resolved,
                      situation_tags=sorted(set(tags)))


# ---------------------------------------------------------------- 与知识库联动
LESSON_ID = "KB-SIM01"


def verify_wiring(kb: Any) -> dict[str, Any]:
    """校验这条门禁确实由知识库里 addressable 的 fix 教训编译而来。"""
    item = kb.items.get(LESSON_ID)
    ok = bool(
        item
        and item.addressable
        and item.improvement_class == "fix"
        and any(k in item.action for k in ("消歧", "确认", "候选"))
    )
    return {
        "wired": ok,
        "lesson_id": LESSON_ID,
        "lesson_exists": item is not None,
        "addressable": bool(item and item.addressable),
        "class": item.improvement_class if item else None,
        "gate_module": "svagent.disambiguation_gate.guard",
        "note": ("门禁已挂接知识库教训，可被召回并编译为执行前拦截"
                 if ok else "未找到可编译的教训，门禁成为无来源的硬编码——需修正"),
    }


def compiled_action() -> str:
    """供知识库 to_opportunities/注入消费的标准动作描述。"""
    return "任何检索或执行前，先运行 disambiguation_gate.guard 检测多义术语；命中则拦截并要求用户确认后再放行。"
