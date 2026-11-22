import re
from collections import Counter

# Negation cues: presence of one of these in exactly one of the two texts
# flips the asserted meaning, so such pairs are not near-duplicates.
_NEGATIONS = {
    "not", "never", "no", "none", "nor", "neither", "cannot", "without",
}

_WORD_RE = re.compile(r"\b\w+\b")


def _tokens(text):
    return _WORD_RE.findall(text.lower())


def judge(text_a, text_b):
    """Deterministic near-duplicate judge for a pair of texts.

    Returns (decision: bool, signals: list, notes: list).
    decision=True  -> the two texts are near-duplicates (one is essentially
                      the other with a few incidental words changed/dropped).
    decision=False -> they express different content, or differ only by a
                      negation that reverses the meaning.
    """
    ta, tb = _tokens(text_a), _tokens(text_b)
    ca, cb = Counter(ta), Counter(tb)

    inter = sum((ca & cb).values())
    shorter = min(len(ta), len(tb))
    containment = inter / shorter if shorter else 1.0
    union_size = sum((ca | cb).values())
    jaccard = inter / union_size if union_size else 1.0

    neg_a = bool(_NEGATIONS & set(ta))
    neg_b = bool(_NEGATIONS & set(tb))
    negation_flip = neg_a != neg_b

    threshold = 0.90
    decision = (containment >= threshold) and not negation_flip

    signals = [
        ("len_a=%d" % len(ta)),
        ("len_b=%d" % len(tb)),
        ("overlap=%d" % inter),
        ("containment=%.4f" % containment),
        ("jaccard=%.4f" % jaccard),
        ("neg_a=%d" % neg_a),
        ("neg_b=%d" % neg_b),
        ("negation_flip=%d" % negation_flip),
        ("threshold=%.2f" % threshold),
    ]
    notes = []
    if containment < threshold:
        notes.append("token overlap too low: texts describe different content")
    if negation_flip:
        notes.append("negation present in only one text: asserted meaning is reversed")
    if decision:
        notes.append("one text is essentially the other with only incidental word edits")

    return bool(decision), signals, notes
