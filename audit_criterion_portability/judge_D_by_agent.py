"""Deterministic criterion D for verbatim support of a claim's qualifying components.

Idea (induced from the 18 blind samples, each a clean / tampered / canary triple):
A claim carries "qualifying components" -- negations, limiters/quantifiers,
contrast markers, numbers, temporal/scope anchors and other content-bearing
tokens.  An evidence verbatim-supports the claim only if EVERY such component
of the claim is still present, literally, in the evidence.  Deleting one (the
tampered cases) or paraphrasing the sentence away (the canary cases) breaks the
verbatim link and is reported as not supported.

The function is pure: it depends only on (claim, evidence), a fixed word list
and regular expressions.  No ids, no labels, no randomness, no external state.
"""

import re

# ---------------------------------------------------------------------------
# Qualifying-component categories (the word lists the criterion is built on)
# ---------------------------------------------------------------------------

NEGATIONS = [
    "no", "not", "never", "none", "neither", "nor", "cannot",
    "n't", "without", "neither", "nowhere",
]
LIMITERS = [
    "every", "only", "all", "each", "any", "some", "both", "either",
    "entire", "whole", "single", "just",
]
CONTRASTS = [
    "however", "but", "yet", "rather", "instead", "although", "though",
    "whereas", "opposite", "contrary", "conversely", "nevertheless",
]
TEMPORAL = [
    "before", "after", "afterwards", "afterward", "then", "already",
    "still", "once", "hitherto", "previously",
]
ANCHORS = [
    "false", "positive", "excludes", "zero", "ground-truth", "intrinsic",
    "summarised", "away", "reference", "solution", "invariant",
    "detected", "restores", "measurements", "detects",
]
# Numbers are matched by regex rather than a fixed list:
NUMBER_PATTERN = r"\d+(?:\.\d+)*"

# Pure function words -- stripped before collecting content tokens.
# NOTE: none of the qualifier words above is in this set.
STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "at", "for",
    "with", "by", "from", "as", "than",
    "is", "are", "was", "were", "be", "been", "being", "am",
    "it", "its", "this", "that", "these", "those",
    "we", "us", "our", "ours", "i", "me", "my", "you", "your",
    "he", "him", "his", "she", "her", "they", "them", "their",
    "which", "who", "whom", "whose", "what",
    "can", "could", "would", "should", "may", "might", "will",
    "shall", "must", "do", "does", "did", "have", "has", "had",
    "there", "here", "so", "such", "about", "into", "over", "under",
    "s", "t", "re", "ve", "ll", "d", "m", "o",
}

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9'\-]*")
_NUM_RE = re.compile(NUMBER_PATTERN)


def _components(text: str):
    """Return the set of qualifying components (marker strings) in *text*."""
    low = text.lower()
    markers = set()

    # word tokens that are not pure function words
    for w in _WORD_RE.findall(low):
        if w not in STOPWORDS:
            markers.add(w)

    # numeric literals, but not digit fragments embedded in a word (e.g. RQ2)
    for m in _NUM_RE.finditer(low):
        s, e = m.span()
        if (s > 0 and low[s - 1].isalpha()) or (e < len(low) and low[e].isalpha()):
            continue
        markers.add(m.group())

    return markers


def _present(marker: str, evidence_low: str) -> bool:
    """Literal, boundary-aware presence check of *marker* in the evidence."""
    if marker and marker[0].isdigit():
        pattern = r"(?<![\d.])" + re.escape(marker) + r"(?![\d.])"
    else:
        pattern = r"(?<![A-Za-z0-9])" + re.escape(marker) + r"(?![A-Za-z0-9])"
    return re.search(pattern, evidence_low) is not None


def judge_D(claim: str, evidence: str):
    """Decide whether *evidence* verbatim-supports the qualifiers of *claim*.

    Returns (supported, markers_in_claim, missing_in_evidence).
    """
    claim_markers = _components(claim)
    evidence_low = evidence.lower()
    missing = sorted(m for m in claim_markers if not _present(m, evidence_low))
    markers_in_claim = sorted(claim_markers)
    supported = len(missing) == 0
    return supported, markers_in_claim, missing
