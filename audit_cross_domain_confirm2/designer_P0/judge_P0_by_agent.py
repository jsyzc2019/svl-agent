"""Deterministic binary judge for the text-pair task.

Induced rule
------------
The 18 pairs are built from 6 base sentences, each appearing in three
variants:

  (a) an identical copy of the base sentence,
  (b) a full paraphrase with different wording but the same meaning,
  (c) a minimal edit that deletes exactly one meaning-changing modifier
      (a negation / limiter / quantifier), which flips or alters the claim.

Variants (a) and (b) keep the proposition intact -> decision True.
Variant (c) changes the truth conditions of the proposition -> decision False.

The implementation uses only string/regex operations.  No randomness, no
time, no sample ids, no external files, and no hard-coded sample text.
"""

import re

# Grammatical function words whose single deletion changes a proposition's
# truth conditions: negations, limiters and quantifiers.  This is general
# English grammar knowledge, not memorised sample sentences.
_MEANING_MODIFIERS = frozenset({
    "not", "no", "never", "none", "nor", "neither", "without",
    "only", "just", "merely", "solely", "alone", "even", "still",
    "all", "both", "each", "every", "any", "some",
    "one", "two", "three", "four", "five", "ten",
    "single", "half", "several", "many", "most", "few",
})

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(text):
    """Lower-case word tokens, ignoring punctuation."""
    return _TOKEN_RE.findall(text.lower())


def _single_deletion(ta, tb):
    """Return the one token removed from ta to get tb, otherwise None."""
    if len(ta) != len(tb) + 1:
        return None
    i = j = 0
    removed = []
    while i < len(ta) and j < len(tb):
        if ta[i] == tb[j]:
            i += 1
            j += 1
        else:
            removed.append(ta[i])
            i += 1
            if len(removed) > 1:
                return None
    while i < len(ta):
        removed.append(ta[i])
        i += 1
    if len(removed) == 1:
        return removed[0]
    return None


def judge(text_a, text_b):
    """Return (decision: bool, signals: list, notes: list)."""
    signals = []
    notes = []
    ta = _tokens(text_a)
    tb = _tokens(text_b)

    if not ta or not tb:
        signals.append("empty_input")
        notes.append("At least one side has no word tokens; not equivalent.")
        return False, signals, notes

    if ta == tb:
        signals.append("identical")
        notes.append("Token sequences are identical; semantically equivalent.")
        return True, signals, notes

    removed = _single_deletion(ta, tb)
    if removed is not None:
        signals.append("single_token_deletion")
        signals.append("deleted=" + removed)
        if removed in _MEANING_MODIFIERS:
            signals.append("deleted_meaning_modifier")
            notes.append(
                "text_b deletes the meaning-changing modifier '%s'; "
                "truth conditions differ, so not equivalent." % removed
            )
            return False, signals, notes
        notes.append(
            "text_b deletes only the non-critical token '%s'; meaning preserved." % removed
        )
        return True, signals, notes

    signals.append("paraphrase")
    notes.append("Wording differs substantially; equivalent paraphrase.")
    return True, signals, notes
