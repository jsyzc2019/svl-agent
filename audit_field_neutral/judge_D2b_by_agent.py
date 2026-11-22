"""Deterministic, symmetry-free judge for the text-pair relation.

The binary structure we discovered is symmetric: a pair is "True" when the two
texts are near-identical once negation words are stripped, yet a negation word
(not / never / no / ...) appears in exactly one of them.  Stripping the negation
then makes the two texts collapse onto each other, i.e. the *only* substantive
difference is the presence of negation -- the core assertion is polarity-flipped
(a contradiction).  Everything else (byte-identical texts, edits that drop a
non-negation modifier, or entirely different-but-consistent wording) is False.

No ids, no cached sample text, no external files, no randomness, no time, no
subjective scoring: the decision follows only from regex extraction and a
deterministic SequenceMatcher ratio on the two input strings.
"""

import re
import difflib

_NEG_RE = re.compile(r"\b(?:no|not|never|none|neither|nor)\b", re.IGNORECASE)
_NONWORD_RE = re.compile(r"[^\w\s]+")
_WS_RE = re.compile(r"\s+")

# Large margin in the data: true cases score >= 0.929; the closest non-true
# case with the same polarity still scores 0.957 but has NO polarity flip,
# and every polarity-flipping pair that is not a negation edit scores <= 0.34.
_SIM_THRESHOLD = 0.85


def _negatives(text):
    """Negation tokens present in a text, in order of appearance."""
    return [m.group(0).lower() for m in _NEG_RE.finditer(text)]


def _without_negation(text):
    """Lower-cased, punctuation-stripped text with negation words removed."""
    t = _NEG_RE.sub(" ", text)
    t = _NONWORD_RE.sub(" ", t)
    return _WS_RE.sub(" ", t).strip().lower()


def judge(text_a, text_b):
    """Return (decision, signals, notes) for the two neutral text slots.

    decision is True iff the pair is a polarity-flip contradiction: one text
    carries a negation word and the other does not, while after removing
    negation words the two texts are near-identical.
    """
    neg_a = _negatives(text_a)
    neg_b = _negatives(text_b)
    a_has_neg = bool(neg_a)
    b_has_neg = bool(neg_b)

    ratio = difflib.SequenceMatcher(
        None,
        _without_negation(text_a).split(),
        _without_negation(text_b).split(),
    ).ratio()

    polarity_flip = a_has_neg != b_has_neg
    near_duplicate = ratio >= _SIM_THRESHOLD
    decision = polarity_flip and near_duplicate

    signals = [
        ("negation_in_a", neg_a),
        ("negation_in_b", neg_b),
        ("word_ratio_without_negation", round(ratio, 4)),
        ("polarity_flip", polarity_flip),
        ("near_duplicate", near_duplicate),
    ]

    notes = []
    if polarity_flip:
        notes.append(
            "A negation word occurs in exactly one of the two texts, so the "
            "assertion's polarity differs."
        )
        if near_duplicate:
            notes.append(
                "After removing negation words the two texts are near-identical, "
                "so the negation is the sole substantive difference and the pair "
                "is a polarity-flip contradiction (True)."
            )
        else:
            notes.append(
                "The texts are not near-identical, so the negation difference is "
                "not a polarity flip of one and the same claim (False)."
            )
    else:
        notes.append(
            "Both texts carry negation words or neither does; there is no "
            "one-sided negation and hence no polarity flip (False)."
        )

    return decision, signals, notes
