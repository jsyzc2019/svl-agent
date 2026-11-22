"""Deterministic binary judge for claim/evidence pairs.

Discovered rule (induced purely from the 18 sample texts):
    The evidence is either a near-verbatim restatement of the claim -- the same
    sentence repeated, or a minimally edited version (a dropped word, a changed
    negation, etc.) -- or it is a materially different sentence (a paraphrase or
    an unrelated statement).  Near-verbatim restatements have very high lexical
    and character overlap; different sentences have very low overlap.  The two
    populations are cleanly separated, so a fixed threshold is enough.

    judge() returns (decision, signals, notes):
        decision True  -> evidence is a near-verbatim restatement of the claim
        decision False -> evidence is a substantially different sentence
    No id, no sample text, no external files, no randomness, no LLM judgement.
"""

import re
from difflib import SequenceMatcher

# Thresholds sit inside the wide gap observed in the data:
#   restatements : token-Jaccard >= 0.89, char-ratio >= 0.96
#   different    : token-Jaccard <= 0.27, char-ratio <= 0.55
JACCARD_THRESHOLD = 0.5
CHAR_RATIO_THRESHOLD = 0.7

_WORD_RE = re.compile(r"[a-z0-9]+")
_NEGATIONS = {"no", "not", "never", "none", "cannot", "neither", "nor", "without"}


def _tokens(text):
    """Lower-cased alphanumeric word tokens."""
    return _WORD_RE.findall(text.lower())


def judge(claim, evidence):
    """Judge whether ``evidence`` is a near-verbatim restatement of ``claim``.

    Args:
        claim: first text (string).
        evidence: second text (string).

    Returns:
        (decision: bool, signals: list[str], notes: list[str])
    """
    c = claim.strip()
    e = evidence.strip()
    c_low, e_low = c.lower(), e.lower()

    ct, et = _tokens(c), _tokens(e)
    cset, eset = set(ct), set(et)
    union = cset | eset
    jaccard = len(cset & eset) / len(union) if union else 1.0
    char_ratio = SequenceMatcher(None, c_low, e_low).ratio()

    exact = c_low == e_low
    contained = bool(c_low) and bool(e_low) and (c_low in e_low or e_low in c_low)
    shared = sorted(cset & eset)
    c_neg = sorted(cset & _NEGATIONS)
    e_neg = sorted(eset & _NEGATIONS)
    negation_mismatch = sorted(set(c_neg) ^ set(e_neg))

    decision = (jaccard >= JACCARD_THRESHOLD and char_ratio >= CHAR_RATIO_THRESHOLD)

    signals = [
        "exact_match=%s" % exact,
        "one_text_contained_in_other=%s" % contained,
        "token_jaccard=%.4f" % jaccard,
        "char_sequence_ratio=%.4f" % char_ratio,
        "shared_content_word_count=%d" % len(shared),
        "claim_negation_tokens=%s" % ",".join(c_neg) if c_neg else "claim_negation_tokens=none",
        "evidence_negation_tokens=%s" % ",".join(e_neg) if e_neg else "evidence_negation_tokens=none",
        "negation_mismatch=%s" % ",".join(negation_mismatch) if negation_mismatch else "negation_mismatch=none",
    ]

    if decision:
        notes = [
            "两段文本共享绝大多数词项且字符序列高度一致，evidence 是 claim 的近逐字复述（可含删词或否定词翻转等微小编辑）。",
            "词级 Jaccard=%.4f、字符序列比=%.4f 均高于阈值，落入复述类。" % (jaccard, char_ratio),
        ]
        if negation_mismatch:
            notes.append("注意：否定词存在差异（%s），属于最小编辑而非实质改写，仍判为复述类。" % ",".join(negation_mismatch))
    else:
        notes = [
            "两段文本词项与字符序列重合度很低，evidence 是与 claim 实质不同的句子（转述或无关表述）。",
            "词级 Jaccard=%.4f、字符序列比=%.4f 均低于阈值，落入不同句类。" % (jaccard, char_ratio),
        ]

    return decision, signals, notes
