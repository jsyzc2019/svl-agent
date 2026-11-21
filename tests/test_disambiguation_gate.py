"""术语歧义前置门禁判据固化测试——锁住"执行前拦截"机制。

这一组测试守护的核心是：KB-SIM01 不能再躺成事后教训，
多义术语在检索/执行前必须被 fail-closed 拦截并强制用户确认。
"""
import pytest

from svagent.core import Message
from svagent.disambiguation_gate import (
    AmbiguousTerm, Confirmation, Sense, build_registry, default_registry,
    detect_ambiguous_terms, guard, verify_wiring, compiled_action,
)
from svagent.knowledge_base import KnowledgeBase

QUERY = "检索 GitHub 上有关 RSI 的话题"


def _user_msg(text="RSI 指递归自我改进"):
    return Message(id="u1", role="user", source="user", content=text)


# --- 检测 ---
def test_detect_with_word_boundary():
    reg = default_registry()
    assert [t.token for t in detect_ambiguous_terms(QUERY, reg)] == ["RSI"]
    # "RSIndex" 不应误命中 RSI
    assert detect_ambiguous_terms("RSIndex 指标", reg) == []
    # 大小写不敏感
    assert [t.token for t in detect_ambiguous_terms("what is rsi?", reg)] == ["RSI"]


def test_no_ambiguity_passes():
    r = guard("今天天气怎么样")
    assert r.allowed and r.status == "PASS"
    assert r.handoff_card is None


def test_custom_registry_extensible():
    term = AmbiguousTerm("SIM", (
        Sense("AI论文", "Self-Improvement Memory", "检索 SIM 论文"),
        Sense("通信", "Subscriber Identity Module", "检索 SIM 卡"),
    ))
    reg = build_registry([term])
    assert "RSI" in reg and "SIM" in reg
    # 检测顺序取决于词典插入顺序，用集合比较（首版误按固定顺序断言，测试自身需被审计）
    assert {t.token for t in detect_ambiguous_terms("SIM and RSI", reg)} == {"SIM", "RSI"}


# --- fail-closed 拦截（本次翻车会被拦下）---
def test_ambiguous_without_confirmation_blocks():
    r = guard(QUERY)
    assert r.status == "BLOCK" and not r.allowed
    assert r.diagnostic.code == "GATE.TERM_AMBIGUITY"
    assert r.diagnostic.severity == "block"
    card = r.handoff_card
    assert card["判据"] == "GATE.TERM_AMBIGUITY"
    assert len(card["候选含义"]) == 2
    assert card["需用户确认"]


def test_agent_self_guess_rejected():
    """agent 不能自己确认自己——真值只来自用户口述(is_user_said)。"""
    fake = Message(id="a1", role="agent", source="agent", content="RSI指相对强弱指数")
    assert Confirmation.from_user("RSI", "证券/技术分析", fake) is None
    topic = Message(id="t1", role="user", source="topic", content="RSI指...")
    assert Confirmation.from_user("RSI", "证券/技术分析", topic) is None
    assert guard(QUERY, confirmations=[None]).status == "BLOCK"


# --- 用户确认后放行 ---
def test_user_confirmation_passes_with_direction():
    c = Confirmation.from_user("RSI", "AI/自我改进", _user_msg())
    r = guard(QUERY, confirmations=[c])
    assert r.allowed
    assert r.resolved["RSI"].expansion == "Recursive Self-Improvement"
    assert "ai/自我改进" in [t.lower() for t in r.situation_tags]


def test_unmatched_confirmation_blocks():
    c = Confirmation.from_user("RSI", "量子物理", _user_msg("RSI 指量子物理"))
    r = guard(QUERY, confirmations=[c])
    assert r.status == "BLOCK" and r.diagnostic.code == "GATE.CONFIRM_UNMATCHED"


def test_finance_sense_also_resolvable():
    c = Confirmation.from_user("RSI", "证券/技术分析", _user_msg("RSI 指相对强弱指数"))
    r = guard(QUERY, confirmations=[c])
    assert r.allowed and r.resolved["RSI"].expansion == "Relative Strength Index"


# --- 知识库联动 ---
def test_gate_wired_to_kb_lesson():
    kb = KnowledgeBase.load("knowledge_base_store.json")
    w = verify_wiring(kb)
    assert w["wired"] is True
    assert w["lesson_id"] == "KB-SIM01"
    assert "guard" in compiled_action()


def test_recall_injects_disambiguation_mechanism():
    kb = KnowledgeBase.load("knowledge_base_store.json")
    hits = kb.recall(["多义缩写", "术语歧义", "RSI", "跨领域检索", "需求澄清"])
    ids = {h.item_id for h in hits}
    assert "KB-SIM01" in ids
    injections = kb.injections_for(["多义缩写", "术语歧义", "RSI", "跨领域检索", "需求澄清"])
    assert any("消歧" in s or "确认" in s for s in injections)


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
