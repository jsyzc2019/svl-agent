"""Deterministic, purely lexical binary judge for text pairs.

Decision rule discovered from the samples:
    True  - text_b is a near-verbatim copy of text_a: the word sequences are
            identical, or one of them can be obtained from the other by
            deleting at most one word token (a minimal one-word rewrite).
    False - text_b is a substantially different text (large word-sequence
            difference / new content), even when it is topically related or
            a semantic paraphrase of text_a.

No randomness, time, ids, external files or hard-coded sample content is used.
"""

import re

_WORD_RE = re.compile(r"[A-Za-z0-9']+")


def _tokens(text):
    """Lowercase word tokens; punctuation acts only as a separator."""
    return _WORD_RE.findall(text.lower())


def _lcs_len(a, b):
    """Length of the longest common subsequence of two token lists (DP)."""
    if not a or not b:
        return 0
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b):
            if x == y:
                cur.append(prev[j] + 1)
            else:
                cur.append(max(cur[j], prev[j + 1]))
        prev = cur
    return prev[len(b)]


def judge(text_a, text_b):
    """Return (decision: bool, signals: list, notes: list)."""
    signals = []
    notes = []

    ta, tb = str(text_a), str(text_b)
    a, b = _tokens(ta), _tokens(tb)

    if not a or not b:
        decision = ta.strip() == tb.strip()
        signals.append("empty_token_sequence")
        notes.append("至少一段文本没有有效词符；仅在规整后完全相等时判为同类。")
        return decision, signals, notes

    lcs = _lcs_len(a, b)
    del_a = len(a) - lcs
    del_b = len(b) - lcs
    edits = del_a + del_b
    longest = max(len(a), len(b))
    overlap = lcs / longest

    if ta.strip() == tb.strip():
        decision = True
        signals.append("exact_string_equal")
        notes.append("两段文本规整后完全逐字相同。")
    elif edits <= 1 and longest >= 6 and overlap >= 0.8:
        decision = True
        signals.append("near_verbatim_copy")
        signals.append("single_token_deletion" if edits == 1 else "identical_tokens")
        notes.append(
            "两段文本词序列仅相差不超过一个词符，text_b 是 text_a 的极小改写/近重复副本。"
        )
    else:
        decision = False
        signals.append("substantially_different_text")
        signals.append(
            "lcs={},len_a={},len_b={},deleted={}".format(lcs, len(a), len(b), edits)
        )
        notes.append(
            "两段文本词序列差异较大，text_b 含不同内容，不是 text_a 的近逐字副本；"
            "即使语义相关或为释义，也不归为同类。"
        )

    return decision, signals, notes
