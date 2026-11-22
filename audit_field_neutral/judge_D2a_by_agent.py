"""Deterministic binary judge for the field-neutral text pairs.

Discovered structure
--------------------
Looking only at the two strings, every pair falls into one of two modes:

  HIGH (near-verbatim): text_b is byte-identical to text_a, or text_a with a
      single small local deletion/edit (a dropped negation, focus word,
      number, or discourse marker). The two texts share almost all of their
      words.

  LOW (free paraphrase): text_b restates the same underlying topic in clearly
      different wording; only a small fraction of the words overlap.

These two modes are widely separated in token-set Jaccard overlap: the LOW
pairs top out around 0.24 while the HIGH pairs start around 0.80, leaving an
empty gap. judge() returns True for the HIGH (near-verbatim) mode.

The function is a pure string/regex algorithm: it reads no files, uses no id,
hardcodes no sample text, and involves no randomness, time, or LLM judgement.
"""

import re
from difflib import SequenceMatcher

_WORD_RE = re.compile(r"[a-z0-9]+")

# Placed inside the empirically empty overlap gap (observed low max ~0.24,
# observed high min ~0.80), so the rule is stable and reproducible.
OVERLAP_THRESHOLD = 0.5
# Char-level ratio is only a corroborating signal (its own gap: ~0.40 vs ~0.90).
SEQ_CORROBORATION = 0.6


def _words(text):
    """Lower-cased alphanumeric word tokens."""
    return _WORD_RE.findall(text.lower())


def _edits(text_a, text_b):
    """Human-readable list of the non-identical spans between a and b."""
    out = []
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, text_a, text_b).get_opcodes():
        if tag == "equal":
            continue
        left = text_a[i1:i2].strip()
        right = text_b[j1:j2].strip()
        if tag == "delete":
            out.append("b drops %r" % left)
        elif tag == "insert":
            out.append("b adds %r" % right)
        else:  # replace
            out.append("b changes %r -> %r" % (left, right))
    return out


def judge(text_a, text_b):
    """Return (decision, signals, notes) for one text pair.

    decision is True when text_b is a near-verbatim restatement of text_a
    (verbatim, or differing only by a small local edit), i.e. high word-set
    overlap; False when text_b is a free paraphrase with different wording.
    """
    signals = []
    notes = []

    a_words = _words(text_a)
    b_words = _words(text_b)
    a_set, b_set = set(a_words), set(b_words)
    union = a_set | b_set
    overlap = len(a_set & b_set)
    jaccard = overlap / len(union) if union else 1.0
    seq_ratio = SequenceMatcher(None, text_a, text_b).ratio()
    exact = text_a == text_b

    signals.append("exact_match=%s" % exact)
    signals.append("a_word_count=%d" % len(a_words))
    signals.append("b_word_count=%d" % len(b_words))
    signals.append("shared_word_count=%d" % overlap)
    signals.append("union_word_count=%d" % len(union))
    signals.append("token_jaccard=%.4f" % jaccard)
    signals.append("char_sequence_ratio=%.4f" % seq_ratio)

    # Primary discriminator: word-set Jaccard. Char ratio must agree so that a
    # fluke word overlap alone cannot flip the decision.
    high_overlap = jaccard >= OVERLAP_THRESHOLD
    char_agrees = seq_ratio >= SEQ_CORROBORATION
    decision = bool(high_overlap and char_agrees)

    if exact:
        notes.append("text_b is byte-identical to text_a (near-verbatim mode).")
    elif high_overlap:
        edits = _edits(text_a, text_b)
        notes.append(
            "text_b is text_a with only a small local edit; the word sets "
            "almost completely coincide (near-verbatim mode)."
        )
        if edits:
            notes.append("local differences: " + "; ".join(edits[:4]))
    else:
        notes.append(
            "text_b uses substantially different wording from text_a; only "
            "a small fraction of words are shared (free-paraphrase mode)."
        )

    notes.append(
        "token_jaccard %.4f vs threshold %.2f -> %s"
        % (jaccard, OVERLAP_THRESHOLD, "HIGH/near-verbatim" if high_overlap else "LOW/paraphrase")
    )

    return decision, signals, notes
