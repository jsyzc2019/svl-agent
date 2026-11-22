"""Deterministic near-duplicate judge for unordered pairs of text snippets.

The binary structure is symmetric: are the two snippets near-verbatim
restatements of one sentence (exact copy or a one-token edit), or are they
substantively different sentences?  No semantic roles, no ids, no labels.
"""

import re
from difflib import SequenceMatcher

# Large margin in the data: near-copies score >= 0.94 / 0.88,
# different sentences score <= 0.41 / 0.28.
_SEQUENCE_THRESHOLD = 0.70
_JACCARD_THRESHOLD = 0.70


def _tokens(text):
    """Lowercase alphanumeric word tokens; hyphens act as separators."""
    return re.findall(r"[a-z0-9]+", text.lower())


def judge(claim, evidence):
    """Return (decision, signals, notes) for two arbitrary text strings.

    decision is True when the two strings are near-verbatim copies of each
    other, False when they are different sentences.  The computation is
    symmetric in its two arguments and depends on nothing but their text.
    """
    a = _tokens(claim)
    b = _tokens(evidence)

    if not a and not b:
        return True, ["both_token_sequences_empty"], [
            "两段文本均无词元，按约定视为同一句话的空复写。"
        ]

    if not a or not b:
        sequence_ratio = 0.0
        jaccard = 0.0
    else:
        sequence_ratio = max(
            SequenceMatcher(None, a, b).ratio(),
            SequenceMatcher(None, b, a).ratio(),
        )
        set_a, set_b = set(a), set(b)
        jaccard = len(set_a & set_b) / len(set_a | set_b)

    signals = [
        "token_sequence_similarity=%.4f" % sequence_ratio,
        "token_set_jaccard=%.4f" % jaccard,
    ]

    decision = (
        sequence_ratio >= _SEQUENCE_THRESHOLD
        and jaccard >= _JACCARD_THRESHOLD
    )

    if decision:
        notes = [
            "两段文本的词元序列与词集均高度重合，为同一句话的近似复写"
            "（完全相同或仅有一个词的增删/替换）。"
        ]
    else:
        notes = [
            "两段文本的词元序列与词集重合度低，为内容不同的独立句子"
            "（含语义转述或无关表述）。"
        ]

    return bool(decision), signals, notes
