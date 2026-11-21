"""坍塌判据集：每个函数都是纯函数，把语义问题翻译成符号问题。"""
from __future__ import annotations

import re
from difflib import SequenceMatcher

from .core import Draft, GroundTruth, Diagnostic, Locus

_CONCRETE_PATTERNS = [
    r"(?:19|20)\d{2}年?",
    r"\d+\s*(?:岁|个月|年|月|日|点|块钱|里|公里)",
    r"[一二三四五六七八九十百两]+\s*岁",
]
_CONCRETE_LEXICON = ("肺", "癌", "手术", "医院", "村里", "学校", "工厂", "棉袄")
_CONCRETE_RE = re.compile("|".join(_CONCRETE_PATTERNS))
_MEMORY_FP_RE = re.compile(
    r"我(?:小时候|那年|当时|那时候|曾经|记得|后来|在村里|七岁|八岁|十岁)"
)
_QUOTE_RE = re.compile(r"[「“\"『'][^」”\"』']*[」”\"』']")
_QUESTION_MARKS = ("?", "？")


def concrete_markers(text: str) -> list[str]:
    """抽出可证伪的具体标记：年份、年龄、数量以及高风险实体词。"""
    hits = [m.group(0) for m in _CONCRETE_RE.finditer(text)]
    hits.extend(word for word in _CONCRETE_LEXICON if word in text)
    return sorted(set(hits))


def chapter_whitelist(draft: Draft, spec: GroundTruth) -> list[Diagnostic]:
    """黑名单拦不住「中年转折」，白名单只认素材里真实存在的阶段。"""
    allowed = spec.allowed_stages()
    return [
        Diagnostic(
            "CHAPTER.WHITELIST", "block", Locus(chapter=stage),
            f"阶段「{stage}」不在素材阶段集合 {sorted(allowed)} 中",
        )
        for stage in draft.chapters
        if stage not in allowed
    ]


def claim_reference_valid(draft: Draft, spec: GroundTruth) -> list[Diagnostic]:
    diags: list[Diagnostic] = []
    for stage, sentences in draft.chapters.items():
        for index, sentence in enumerate(sentences):
            for cid in sentence.claim_ids:
                if spec.claim(cid) is None:
                    diags.append(Diagnostic(
                        "EVIDENCE.CLAIM_MISSING", "block",
                        Locus(stage, index, cid),
                        f"引用的素材 {cid} 不存在或未通过入库校验",
                    ))
    return diags


def concrete_grounded(draft: Draft, spec: GroundTruth) -> list[Diagnostic]:
    """细节级核对：编得越具体，越难拿不出原文凭证。"""
    grounded = spec.grounded_text()
    diags: list[Diagnostic] = []
    for stage, sentences in draft.chapters.items():
        for index, sentence in enumerate(sentences):
            markers = concrete_markers(sentence.text)
            if not markers:
                continue
            if not sentence.claim_ids:
                diags.append(Diagnostic(
                    "EVIDENCE.CONCRETE_UNGROUNDED", "block",
                    Locus(stage, index),
                    "出现具体标记但没有任何素材凭证",
                ))
                continue
            leaked = [m for m in markers if m not in grounded]
            if leaked:
                diags.append(Diagnostic(
                    "EVIDENCE.DETAIL_LEAK", "block", Locus(stage, index),
                    f"具体细节未出现在素材中: {leaked}",
                ))
    return diags


def first_person_boundary(draft: Draft, spec: GroundTruth) -> list[Diagnostic]:
    """属主守恒：抹掉引号内的转述后，AI 不得主张自己的记忆。"""
    diags: list[Diagnostic] = []
    for index, line in enumerate(draft.agent_lines):
        stripped = _QUOTE_RE.sub("", line)
        match = _MEMORY_FP_RE.search(stripped)
        if match:
            diags.append(Diagnostic(
                "AGENT.OWNERSHIP", "block", Locus(ref=f"agent_line:{index}"),
                f"AI 用第一人称主张亲身记忆: {match.group(0)}",
            ))
    return diags


def monologue_flag(
    draft: Draft, spec: GroundTruth, limit: int = 110,
) -> list[Diagnostic]:
    """流畅是可疑信号，但只作为 flag 改变路由，不直接否决。"""
    diags: list[Diagnostic] = []
    for index, line in enumerate(draft.agent_lines):
        if len(line) > limit and not any(q in line for q in _QUESTION_MARKS):
            diags.append(Diagnostic(
                "AGENT.MONOLOGUE", "flag", Locus(ref=f"agent_line:{index}"),
                f"超过 {limit} 字且无问号，疑似进入表演模式",
            ))
    return diags


def narrative_vividness_flag(
    draft: Draft, spec: GroundTruth, min_length: int = 30,
) -> list[Diagnostic]:
    """「读起来太顺」在叙事场景是报警信号，但只路由给人，不直接否决。"""
    diags: list[Diagnostic] = []
    for stage, sentences in draft.chapters.items():
        for index, sentence in enumerate(sentences):
            if len(sentence.text) >= min_length and concrete_markers(sentence.text):
                diags.append(Diagnostic(
                    "NARRATIVE.FLUENT", "flag", Locus(stage, index),
                    "长句携带具体细节：凭证核对通过，但需人工确认细节是否确为原话",
                ))
    return diags


def repeated_question_flag(
    draft: Draft, spec: GroundTruth, threshold: float = 0.65,
) -> list[Diagnostic]:
    history = spec.replay_history()
    diags: list[Diagnostic] = []
    for index, question in enumerate(draft.questions):
        for prior in history:
            if SequenceMatcher(None, question, prior).ratio() >= threshold:
                diags.append(Diagnostic(
                    "AGENT.REPEATED_QUESTION", "flag",
                    Locus(ref=f"question:{index}"),
                    f"与已说过的话高度相似: {prior[:24]}",
                ))
                break
    return diags


def coverage_check(
    draft: Draft, spec: GroundTruth, threshold: float = 0.8,
) -> list[Diagnostic]:
    used: set[str] = set()
    for sentences in draft.chapters.values():
        for sentence in sentences:
            used.update(sentence.claim_ids)
    total = len(spec.claims)
    ratio = len(used & set(spec.claims)) / total if total else 1.0
    if total and ratio < threshold:
        return [Diagnostic(
            "SPEC.COVERAGE_LOW", "flag", Locus(ref="spec"),
            f"素材覆盖率 {ratio:.0%} < {threshold:.0%}，应回到人补采",
        )]
    return []


def default_verifiers():
    return [
        chapter_whitelist,
        claim_reference_valid,
        concrete_grounded,
        first_person_boundary,
        monologue_flag,
        narrative_vividness_flag,
        repeated_question_flag,
        coverage_check,
    ]
