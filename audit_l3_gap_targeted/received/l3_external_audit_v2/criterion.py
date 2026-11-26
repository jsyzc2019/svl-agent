"""Pure-python assertion-preservation criterion.

judge(text_a, text_b) -> (bool, reasons:list, anchors:list)

Question answered: does text_a fully preserve the assertion of text_b?

Also (symmetrically) we check both directions where asymmetry is meaningful:
negation-token mismatches and connector mismatches are bidirectional; tail
deletion is directional (text_b dropping text_a's tail predicate).

No imports, no IO, no randomness, no hard-coded ids or ground truth.
"""


NEGATION_TOKENS = (
    "not", "no", "never", "cannot", "can't", "won't", "isn't", "aren't",
    "don't", "doesn't", "didn't", "wouldn't", "shouldn't", "couldn't",
    "nothing", "none", "nobody", "neither", "nor", "without",
)

# multi-word negation phrases checked as normalized substrings
NEGATION_PHRASES = ("does not", "do not", "did not", "is not", "are not",
                    "was not", "were not", "will not", "would not")

CONNECTORS = ("despite", "however", "although", "finally", "while",
              "whereas", "but", "yet", "nevertheless", "nonetheless",
              "even though", "in spite of", "though")


def _normalize(text):
    """Lowercase, strip surrounding whitespace, collapse internal whitespace,
    strip common punctuation (but keep letters/digits/spaces and apostrophes
    in negations like can't)."""
    if text is None:
        return ""
    text = str(text).lower().strip()
    out = []
    for ch in text:
        if ch.isalnum() or ch == "'" or ch.isspace():
            out.append(ch)
        else:
            out.append(" ")
    joined = "".join(out)
    return " ".join(joined.split())


def _tokens(norm):
    return [t for t in norm.split(" ") if t]


def _negation_count(norm):
    toks = _tokens(norm)
    count = sum(1 for t in toks if t in NEGATION_TOKENS)
    for phrase in NEGATION_PHRASES:
        count += norm.count(phrase)
    return count


def _connector_set(norm):
    found = set()
    for c in CONNECTORS:
        if " " in c:
            if c in norm:
                found.add(c)
        else:
            for t in _tokens(norm):
                # simple membership; connectors are distinct enough.
                if t == c:
                    found.add(c)
                    break
    return found


def _prefix_match_drop(longer, shorter):
    """Return True if shorter's tokens are a proper prefix of longer's tokens
    and longer has extra tail content -> indicates tail deletion."""
    lt = _tokens(longer)
    st = _tokens(shorter)
    if not st:
        return False
    if len(lt) <= len(st):
        return False
    return lt[:len(st)] == st


def judge(text_a, text_b):
    reasons = []
    anchors = []

    na = _normalize(text_a)
    nb = _normalize(text_b)

    # Identical after normalization -> trivially preserved.
    if na == nb:
        return True, [], []

    # 1) Negation-polarity check (bidirectional).
    neg_a = _negation_count(na)
    neg_b = _negation_count(nb)
    # presence-based per spec: token present in one but not the other
    pres_a = neg_a > 0
    pres_b = neg_b > 0
    if pres_a != pres_b:
        reasons.append("negation-polarity: negation present in one text but "
                       "absent in the other (a=%d b=%d)" % (neg_a, neg_b))
        for t in _tokens(na):
            if t in NEGATION_TOKENS:
                anchors.append(t)
                break
        for t in _tokens(nb):
            if t in NEGATION_TOKENS:
                anchors.append(t)
                break
        return False, reasons, anchors

    # 2) Assertion-tail deletion (directional: b drops a's tail predicate).
    la = _tokens(na)
    lb = _tokens(nb)
    # order-independent check: if one is much shorter AND is a token-prefix
    # of the other, the tail was deleted from the longer claim.
    if len(la) != len(lb):
        longer = na if len(la) > len(lb) else nb
        shorter = nb if len(la) > len(lb) else na
        if _prefix_match_drop(longer, shorter):
            reasons.append(
                "assertion-tail-deletion: shorter text is a strict prefix of "
                "the longer one, tail predicate/complement dropped "
                "(len_a=%d len_b=%d)" % (len(la), len(lb)))
            short_t = _tokens(shorter)
            long_t = _tokens(longer)
            if len(short_t) < len(long_t):
                anchors.extend(long_t[len(short_t):])
            else:
                anchors.append(longer)
            return False, reasons, anchors
        # also catch the case where b is significantly shorter with a
        # matching leading prefix but minor trailing differences.
        if len(la) > len(lb):
            # b is shorter; check shared leading prefix ratio
            common = 0
            for x, y in zip(la, lb):
                if x == y:
                    common += 1
                else:
                    break
            if common >= max(1, int(0.6 * len(lb))) and len(lb) < len(la):
                reasons.append(
                    "assertion-tail-deletion: text_b significantly shorter "
                    "with matching prefix, tail content likely dropped "
                    "(len_a=%d len_b=%d)" % (len(la), len(lb)))
                anchors.extend(la[len(lb):len(la)])
                return False, reasons, anchors

    # 3) Connector change check.
    conn_a = _connector_set(na)
    conn_b = _connector_set(nb)
    if conn_a != conn_b:
        # Determine if change is between semantically equivalent connectors.
        equiv_pairs = [
            {"despite", "although"},
            {"despite", "though"},
            {"despite", "even though"},
            {"despite", "in spite of"},
            {"although", "though"},
            {"although", "even though"},
            {"although", "while"},
            {"however", "nevertheless"},
            {"however", "nonetheless"},
            {"but", "yet"},
        ]
        only_a = conn_a - conn_b
        only_b = conn_b - conn_a
        # If the symmetric difference is a single known-equivalent pair and
        # there are no other connector differences, treat as meaning-preserving.
        if not (len(only_a) <= 1 and len(only_b) <= 1):
            reasons.append("connector-change: connector set differs and not a "
                           "known equivalent swap (a=%s b=%s)"
                           % (sorted(conn_a), sorted(conn_b)))
            anchors.extend(sorted(only_a | only_b))
            return False, reasons, anchors
        # check equivalence
        a_one = next(iter(only_a)) if only_a else None
        b_one = next(iter(only_b)) if only_b else None
        if a_one is None or b_one is None:
            reasons.append("connector-change: connector added/removed")
            anchors.extend(sorted(only_a | only_b))
            return False, reasons, anchors
        pair = {a_one, b_one}
        equivalent = any(pair == ep for ep in equiv_pairs)
        if not equivalent:
            reasons.append("connector-change: connector swapped between "
                           "non-equivalent connectors (%s -> %s)"
                           % (a_one, b_one))
            anchors.extend(sorted(pair))
            return False, reasons, anchors
        # equivalent swap -> allowed, no reason recorded.

    # Otherwise treat as meaning-preserving rewording / formatting.
    return True, [], []


if __name__ == "__main__":
    samples = [
        ("The cat is on the mat.", "The cat is on the mat"),
        ("The drug reduces pain.", "The drug does not reduce pain."),
        ("She opened the door and walked into the garden.",
         "She opened the door."),
        ("Despite the rain, the team won.", "Although the rain, the team won."),
        ("Despite the rain, the team won.", "However the rain, the team won."),
    ]
    for a, b in samples:
        print(judge(a, b))
