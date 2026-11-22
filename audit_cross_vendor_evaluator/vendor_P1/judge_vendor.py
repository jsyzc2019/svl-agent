import re

_LIMITERS = {
    "not", "no", "never", "without", "only", "just", "merely", "solely",
    "both", "all", "every", "each", "any", "neither", "none",
    "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"
}

def _normalize(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _word_set(s: str) -> set:
    return set(re.findall(r"[a-z0-9]+", s))

def _number_set(s: str) -> set:
    return set(re.findall(r"\d+(?:\.\d+)?", s))

def judge(text_a: str, text_b: str):
    signals = []
    notes = []

    a = _normalize(text_a)
    b = _normalize(text_b)

    if a == b:
        signals.append("exact_match")
        notes.append("text_a and text_b are identical after normalization")
        return True, signals, notes

    wa = _word_set(a)
    wb = _word_set(b)
    na = _number_set(a)
    nb = _number_set(b)

    if na != nb:
        signals.append("number_mismatch")
        notes.append("numeric tokens differ between text_a and text_b")
        return False, signals, notes

    missing_limiters = sorted(w for w in _LIMITERS if w in wa and w not in wb)
    if missing_limiters:
        signals.append("missing_limiter")
        notes.append("limiting/negation terms present in text_a but absent in text_b: " + ", ".join(missing_limiters))
        return False, signals, notes

    added_limiters = sorted(w for w in _LIMITERS if w in wb and w not in wa)
    if added_limiters:
        signals.append("added_limiter")
        notes.append("limiting/negation terms present in text_b but absent in text_a: " + ", ".join(added_limiters))
        return False, signals, notes

    if wa or wb:
        inter = wa & wb
        union = wa | wb
        jaccard = len(inter) / len(union) if union else 0.0
    else:
        jaccard = 1.0

    if jaccard < 0.5:
        signals.append("low_overlap")
        notes.append("word-set Jaccard similarity below threshold: {:.2f}".format(jaccard))
        return False, signals, notes

    signals.append("near_match")
    notes.append("texts are similar but not identical; no critical deletions detected by deterministic rules")
    return True, signals, notes
