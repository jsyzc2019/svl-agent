"""Deterministic binary judge induced from the 18 text pairs.

Discovered structure
--------------------
Every pair falls into one of three shapes (6 each):
  * text_b is byte-for-byte the same sentence as text_a;
  * text_b is text_a with exactly one word removed (a "shortened copy");
  * text_b is a *different* sentence that merely talks about a related topic
    (new words appear that are absent from text_a).

The stable binary split is therefore: "is text_b essentially the same sentence
as text_a?"  A shortened copy keeps every one of text_b's words inside text_a,
in the same order; a genuinely different sentence introduces words that text_a
does not contain.  No role (claim/evidence/premise/...) is assumed for either
side -- the rule is symmetric-free and purely lexical.
"""

import re


def _tokens(s):
    """Lowercase alphanumeric word tokens; punctuation is ignored."""
    return re.findall(r"[a-z0-9]+", s.lower())


def judge(text_a, text_b):
    """Return (decision, signals, notes).

    decision is True iff text_b is a shortened copy of text_a: every word of
    text_b occurs in text_a in the same order (text_b == text_a is the trivial
    case with zero deletions), and text_b retains a substantial fraction of
    text_a.  text_b that introduces new words is a different sentence -> False.
    """
    signals = []
    notes = []

    ta = _tokens(text_a)
    tb = _tokens(text_b)

    if not tb or not ta:
        decision = False
        signals.append("empty_token_sequence")
        notes.append("至少一段文本没有有效词元，无法构成删减副本关系。")
        return decision, signals, notes

    exact = text_a.strip() == text_b.strip()
    if exact:
        signals.append("exact_string_match")

    # Greedy order-preserving match: is tb a token-subsequence of ta?
    idx = 0
    deleted = []
    is_subseq = True
    for tok in tb:
        found = -1
        for j in range(idx, len(ta)):
            if ta[j] == tok:
                found = j
                break
        if found == -1:
            is_subseq = False
            break
        if found > idx:
            deleted.extend(ta[idx:found])
        idx = found + 1
    if is_subseq:
        deleted.extend(ta[idx:])

    coverage = len(tb) / len(ta)
    signals.append("coverage=%.3f" % coverage)

    if is_subseq and coverage >= 0.5:
        signals.append("b_is_ordered_token_subsequence_of_a")
        signals.append("deleted_token_count=%d" % len(deleted))
        if deleted:
            signals.append("deleted_words=" + ",".join(deleted[:8]))
        decision = True
        if exact:
            notes.append("两段文本完全相同，是同一句话，判 True。")
        else:
            notes.append(
                "text_b 的每个词都能在 text_a 中按原顺序找到，仅删去了 %d 个词"
                "（%s），属于同一句话的删减版，判 True。"
                % (len(deleted), ", ".join(deleted[:8]))
            )
        return decision, signals, notes

    # b is not an ordered subsequence -> it must contain genuinely new content.
    set_a = set(ta)
    new_words = list(dict.fromkeys(w for w in tb if w not in set_a))
    signals.append("b_not_ordered_subsequence_of_a")
    signals.append("new_token_count=%d" % len(new_words))
    if new_words:
        signals.append("new_tokens_in_b=" + ",".join(new_words[:8]))
    decision = False
    notes.append(
        "text_b 无法由 text_a 按原顺序删词得到，且引入了 text_a 中不存在的词"
        "（如 %s），是另一句话/改写而非同一句话的删减版，判 False。"
        % (", ".join(new_words[:5]) if new_words else "词序已改变")
    )
    return decision, signals, notes
