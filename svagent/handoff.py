"""人工交接：把不可约判断切成可局部裁决的小靶子。"""
from __future__ import annotations

from .core import Draft, GroundTruth, Diagnostic


def handoff_cards(
    draft: Draft, diagnostics: list[Diagnostic], spec: GroundTruth,
) -> list[dict]:
    cards: list[dict] = []
    for diag in diagnostics:
        if diag.severity != "flag":
            continue
        loc = diag.locus
        if loc.sentence_index >= 0 and loc.chapter in draft.chapters:
            sentences = draft.chapters[loc.chapter]
            if 0 <= loc.sentence_index < len(sentences):
                sentence = sentences[loc.sentence_index]
                supports = []
                for cid in sentence.claim_ids:
                    claim = spec.claim(cid)
                    if claim is None:
                        continue
                    source = spec.messages.get(claim.source_message_id)
                    supports.append({
                        "素材": claim.text,
                        "锚点": claim.anchor,
                        "原话": source.content if source else "",
                    })
                cards.append({
                    "判据": diag.code,
                    "问题": diag.message,
                    "正文片段": sentence.text,
                    "核对原话": supports,
                })
                continue
        cards.append({
            "判据": diag.code,
            "问题": diag.message,
            "正文片段": "(对话/提纲层，无正文句子)",
            "核对原话": [],
        })
    return cards
