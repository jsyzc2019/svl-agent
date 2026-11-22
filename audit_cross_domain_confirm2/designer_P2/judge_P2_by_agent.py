"""Deterministic near-duplicate judge for text pairs.

The decision is based on two observations that can be computed from the two
strings alone:

1. Lexical overlap (Jaccard similarity over normalized word tokens).  Same
   sentences under small edits / rewording retain a high overlap, whereas a
   genuinely different sentence retains a low one.
2. Negation polarity.  If exactly one of the two strings carries a negation
   cue, the polarity has been flipped, so the two strings cannot express the
   same proposition even when their wording is otherwise almost identical.
"""

import re

_NEGATION_CUES = frozenset({
    "not", "no", "never", "none", "nothing", "neither", "nor",
    "cannot", "without", "hardly", "barely", "rarely",
    "unable", "fail", "fails", "failed", "lacks", "lack",
})

_CONTRACTIONS = {
    "doesnt": "does not", "doesn't": "does not",
    "isnt": "is not", "isn't": "is not",
    "arent": "are not", "aren't": "are not",
    "wasnt": "was not", "wasn't": "was not",
    "werent": "were not", "weren't": "were not",
    "cant": "can not", "can't": "can not", "cannot": "can not",
    "wont": "will not", "won't": "will not",
    "didnt": "did not", "didn't": "did not",
    "dont": "do not", "don't": "do not",
    "couldnt": "could not", "couldn't": "could not",
    "wouldnt": "would not", "wouldn't": "would not",
    "shouldnt": "should not", "shouldn't": "should not",
    "hasnt": "has not", "hasn't": "has not",
    "havent": "have not", "haven't": "have not",
    "neither": "neither", "nor": "nor",
}

_SIMILARITY_THRESHOLD = 0.40


def _normalize(text):
    t = str(text).lower().replace("’", "'")
    for contraction, expanded in _CONTRACTIONS.items():
        t = re.sub(r"\b" + re.escape(contraction) + r"\b", expanded, t)
    return t


def _tokens(text):
    return re.findall(r"[a-z0-9]+", _normalize(text))


def judge(text_a, text_b):
    """Return (decision, signals, notes) for a pair of texts."""
    tokens_a = _tokens(text_a)
    tokens_b = _tokens(text_b)
    set_a, set_b = set(tokens_a), set(tokens_b)

    shared = set_a & set_b
    union = set_a | set_b
    jaccard = len(shared) / len(union) if union else 1.0

    neg_a = set_a & _NEGATION_CUES
    neg_b = set_b & _NEGATION_CUES
    polarity_flipped = bool(neg_a) != bool(neg_b)

    signals = [
        "jaccard=%.4f" % jaccard,
        "shared_tokens=%d" % len(shared),
        "tokens_a=%d" % len(set_a),
        "tokens_b=%d" % len(set_b),
        "negation_a=%s" % ",".join(sorted(neg_a)),
        "negation_b=%s" % ",".join(sorted(neg_b)),
        "polarity_flipped=%s" % ("yes" if polarity_flipped else "no"),
    ]

    notes = []
    if polarity_flipped:
        notes.append("Negation cue appears in only one text; the asserted "
                     "polarity differs, so the propositions are not the same.")
    if jaccard < _SIMILARITY_THRESHOLD:
        notes.append("Lexical overlap is too low for the two sentences to be "
                     "versions of the same statement.")
    if not polarity_flipped and jaccard >= _SIMILARITY_THRESHOLD:
        notes.append("High lexical overlap with matching polarity: the text "
                     "differs only by deletions, minor wording changes or "
                     "rewording.")

    decision = (not polarity_flipped) and (jaccard >= _SIMILARITY_THRESHOLD)
    return decision, signals, notes
