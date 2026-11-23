"""Deterministic dichotomy induced at T3 from the 16 blind text pairs (see criterion_note.md).

judge(text_a, text_b) -> (bool, reasons, anchors)

The rule is a pure function of the two strings alone: no import of any kind, no file or network
access, no clock, no randomness, no global mutable state, no pair identifier, no reference to any
expected answer, no reference to the source article. Anchors are verbatim substrings of text_a.

Rule, in words
    Accept (True)  <=>  every numeric quantity that text_a states is re-stated by text_b with the
                        same value (compared as a multiset of stated values), AND every limiting
                        expression that bounds how text_a's quantities are to be read is still
                        stated by text_b.
    Reject (False) otherwise, reporting each unrestated fragment of text_a.
"""

_DIGITS = frozenset("0123456789")

# Closed literal list of the expressions that bound how a quantity is to be read.
_LIMITERS = (
    "at least", "at most", "more than", "less than", "no more than", "no fewer than",
    "nearly", "almost", "around", "about", "approximately", "roughly", "exactly", "precisely",
    "only", "over", "under", "above", "below", "within", "between", "up to", "as much as",
)


def _is_numeric_literal(tok):
    """True if tok reads as one plain decimal / scientific numeric literal."""
    if not tok:
        return False
    s = tok
    if s[0] in "+-":
        s = s[1:]
    if not s:
        return False
    body, exp, eok = s, "", True
    for i, ch in enumerate(s):
        if ch in "eE":
            body, exp = s[:i], s[i + 1:]
            break
    if exp:
        e = exp[1:] if exp[:1] in "+-" else exp
        eok = bool(e) and all(c in _DIGITS for c in e)
    if not eok:
        return False
    if "." in body:
        if body.count(".") > 1 or body.startswith(".") or body.endswith("."):
            return False
        left, dot, right = body.partition(".")
        return bool(left) and bool(right) and all(c in _DIGITS for c in left + right)
    return all(c in _DIGITS for c in body)


def _numeric_literals(text):
    """Ordered numeric literals stated in text, kept with their verbatim spelling.

    Maximal literal runs are scanned. A '.' continues a literal only when followed by a digit, so
    26.2 and 298.15 stay whole and a sentence-final period does not glue two numbers together.
    A '+'/'-' opens a signed literal only when the previous character is not a digit, so the ranges
    0-10 and 3.2-5.0 and the hyphenated compound checkpoint-300 yield the separate stated values
    0 and 10, 3.2 and 5.0, 300.
    """
    out = []
    i, n = 0, len(text)
    prev_is_digit = False
    while i < n:
        ch = text[i]
        start = i
        if ch in "+-" and not prev_is_digit:
            i += 1
        if i >= n or text[i] not in _DIGITS:
            i += 1
            prev_is_digit = False
            continue
        while i < n and text[i] in _DIGITS:
            i += 1
        if i < n and text[i] == "." and i + 1 < n and text[i + 1] in _DIGITS:
            i += 1
            while i < n and text[i] in _DIGITS:
                i += 1
        if i < n and text[i] in "eE":
            j = i + 1
            if j < n and text[j] in "+-":
                j += 1
            if j < n and text[j] in _DIGITS:
                while j < n and text[j] in _DIGITS:
                    j += 1
                i = j
        cand = text[start:i]
        prev_is_digit = _is_numeric_literal(cand)
        if prev_is_digit:
            out.append(cand)
    return out


def _value_of(literal):
    try:
        return float(literal)
    except (ValueError, OverflowError):
        return None


def _limiter_occurrences(text):
    """Bounding expressions in text, each with a non-letter on both sides (case-insensitive)."""
    low = text.lower()
    hits = []
    for w in _LIMITERS:
        start = 0
        while True:
            i = low.find(w, start)
            if i < 0:
                break
            j = i + len(w)
            before_ok = i == 0 or not low[i - 1].isalpha()
            after_ok = j == len(low) or not low[j].isalpha()
            if before_ok and after_ok:
                hits.append((i, text[i:j]))
            start = i + 1
    return sorted(set(hits))


def judge(text_a, text_b):
    if not isinstance(text_a, str) or not isinstance(text_b, str):
        raise TypeError("judge expects two strings")

    reasons = []
    anchors = []

    # 1. every value stated by text_a must be re-stated by text_b (multiset of values)
    restated = []
    for literal in _numeric_literals(text_b):
        value = _value_of(literal)
        restated.append(value if value is not None else ("unparsed", literal))

    for literal in _numeric_literals(text_a):
        value = _value_of(literal)
        key = value if value is not None else ("unparsed", literal)
        if key in restated:
            restated.remove(key)
        else:
            anchors.append(literal)
            reasons.append("numeric quantity '" + literal + "' is stated by text_a but text_b states no equal value")

    # 2. every bounding expression of text_a must still bound text_b
    still_there = set(w.lower() for _, w in _limiter_occurrences(text_b))
    seen = set()
    for _, word in _limiter_occurrences(text_a):
        k = word.lower()
        if k not in still_there and k not in seen:
            seen.add(k)
            anchors.append(word)
            reasons.append("limiting expression '" + word + "' bounds text_a but does not appear in text_b")

    if reasons:
        return False, reasons, anchors
    return (True,
            ["every numeric quantity stated by text_a is re-stated by text_b",
             "no limiting expression of text_a is missing from text_b"],
            anchors)
