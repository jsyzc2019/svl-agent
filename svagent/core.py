"""SVL 原型：数据模型与受保护的判据源。

核心不变量：真值只能来自被确认的用户口述；任何生成内容都不能回灌成真值。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

NON_USER_SOURCES = {"topic", "agent", "system"}


def strip_punctuation(text: str) -> str:
    """去掉标点和空白，保留中英文字符与数字，用于纯符号级别的子串核对。"""
    return re.sub(r"[\W_]+", "", text or "", flags=re.UNICODE)


@dataclass(frozen=True)
class Message:
    id: str
    role: str
    source: str
    content: str


def is_user_said(msg: Message) -> bool:
    """判据输入的隔离门：角色是 user、来源不是话题提示、内容非空。"""
    return (
        bool(msg.content.strip())
        and msg.role.lower() == "user"
        and msg.source.lower() not in NON_USER_SOURCES
    )


@dataclass(frozen=True)
class Claim:
    """一条带凭证的最小事实单元；anchor 必须逐字抄自来源消息。"""

    id: str
    text: str
    anchor: str
    source_message_id: str
    stage: str
    entities: tuple[str, ...] = ()


@dataclass
class Sentence:
    text: str
    claim_ids: tuple[str, ...] = ()


@dataclass
class Draft:
    chapters: dict[str, list[Sentence]] = field(default_factory=dict)
    agent_lines: list[str] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Locus:
    """像编译器的 line:column 一样，把诊断定位到最小可修单元。"""

    chapter: str = ""
    sentence_index: int = -1
    ref: str = ""

    def __str__(self) -> str:
        if self.sentence_index >= 0:
            return f"{self.chapter}#{self.sentence_index}"
        return self.ref or self.chapter or "-"


@dataclass(frozen=True)
class Diagnostic:
    code: str
    severity: str  # "block" 直接挡；"flag" 只改变人工路由
    locus: Locus
    message: str


class GroundTruth:
    """只写一次的判据源：接收原话消息，接收经 anchor 核对的素材。"""

    def __init__(self) -> None:
        self.messages: dict[str, Message] = {}
        self.claims: dict[str, Claim] = {}
        self.rejected: list[Diagnostic] = []

    def add_message(self, msg: Message) -> None:
        self.messages[msg.id] = msg

    def ingest_claim(self, claim: Claim) -> Diagnostic | None:
        """素材入库前做坍塌核对；失败即隔离，绝不进入后续闭环。"""
        src = self.messages.get(claim.source_message_id)
        if src is None or not is_user_said(src):
            diag = Diagnostic(
                "GT.SOURCE_UNTRUSTED", "block", Locus(ref=claim.id),
                "来源不是已确认的用户口述",
            )
        elif not strip_punctuation(claim.anchor):
            diag = Diagnostic(
                "GT.ANCHOR_EMPTY", "block", Locus(ref=claim.id),
                "anchor 为空，无法核对",
            )
        elif strip_punctuation(claim.anchor) not in strip_punctuation(src.content):
            diag = Diagnostic(
                "GT.ANCHOR_MISMATCH", "block", Locus(ref=claim.id),
                "anchor 不是来源消息的子串",
            )
        else:
            self.claims[claim.id] = claim
            return None
        self.rejected.append(diag)
        return diag

    def replay_history(self) -> list[str]:
        """回灌给模型的历史只包含真正被用户说过的话。"""
        return [m.content for m in self.messages.values() if is_user_said(m)]

    def allowed_stages(self) -> set[str]:
        return {c.stage for c in self.claims.values()}

    def grounded_text(self) -> str:
        """所有已核验素材的文本池，用于细节级核对。"""
        return "\n".join(c.text + " " + c.anchor for c in self.claims.values())

    def claim(self, claim_id: str) -> Claim | None:
        return self.claims.get(claim_id)
