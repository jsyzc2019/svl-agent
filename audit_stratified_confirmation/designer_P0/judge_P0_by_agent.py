"""Deterministic binary judge for text pairs.

The rule discovered from the data:
    decision is True when text_b is a near-duplicate of text_a, i.e. after
    whitespace tokenisation the two token sequences are identical, or one
    can be obtained from the other by deleting exactly one token.
    Otherwise decision is False.

Pure string/regex implementation. No randomness, no time, no ids, no
external files, and no hard-coded sample text.
"""

import re

# Word-like tokens; punctuation at the edges (including a trailing full stop)
# is dropped so that e.g. "not." and "not" compare equal.
_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[.'’-][A-Za-z0-9]+)*")


def _tokens(text):
    return _WORD_RE.findall(text)


def _is_one_token_deletion(longer, shorter):
    """True iff `shorter` equals `longer` with exactly one token removed."""
    if len(longer) != len(shorter) + 1:
        return False
    i = j = 0
    skipped = 0
    while i < len(longer) and j < len(shorter):
        if longer[i] == shorter[j]:
            i += 1
            j += 1
        else:
            skipped += 1
            i += 1
            if skipped > 1:
                return False
    skipped += len(longer) - i
    return skipped == 1 and j == len(shorter)


def judge(text_a, text_b):
    a = _tokens(text_a)
    b = _tokens(text_b)

    signals = []
    notes = []

    if a == b:
        signals.append("identical_token_sequence")
        notes.append("text_a and text_b have identical whitespace tokens")
        return True, signals, notes

    if len(a) == len(b) + 1 and _is_one_token_deletion(a, b):
        signals.append("text_b_is_text_a_minus_one_token")
        notes.append(
            "text_b equals text_a after removing exactly one token "
            "(token counts %d -> %d)" % (len(a), len(b))
        )
        return True, signals, notes

    if len(b) == len(a) + 1 and _is_one_token_deletion(b, a):
        signals.append("text_a_is_text_b_minus_one_token")
        notes.append(
            "text_a equals text_b after removing exactly one token "
            "(token counts %d -> %d)" % (len(b), len(a))
        )
        return True, signals, notes

    signals.append("not_near_duplicate")
    notes.append(
        "token sequences differ by more than a single deletion "
        "(token counts %d vs %d)" % (len(a), len(b))
    )
    return False, signals, notes
