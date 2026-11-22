import re

def judge(text_a, text_b):
    signals = []
    notes = []

    def normalize(s):
        s = s.lower()
        s = re.sub(r'[^\w\s]', ' ', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    na = normalize(text_a)
    nb = normalize(text_b)

    if na == nb:
        signals.append("exact_match")
        notes.append("Normalized texts are identical")
        return True, signals, notes

    wa = na.split()
    wb = nb.split()
    seta = set(wa)
    setb = set(wb)

    len_a = len(wa)
    len_b = len(wb)
    if len_a == 0 or len_b == 0:
        signals.append("empty_after_normalize")
        notes.append("One text is empty after normalization")
        return False, signals, notes

    inter = len(seta & setb)
    union = len(seta | setb)
    jaccard = inter / union if union else 0.0
    overlap = inter / min(len(seta), len(setb)) if min(len(seta), len(setb)) else 0.0
    length_ratio = min(len_a, len_b) / max(len_a, len_b)

    signals.append(f"jaccard={jaccard:.3f}")
    signals.append(f"overlap={overlap:.3f}")
    signals.append(f"length_ratio={length_ratio:.3f}")

    negations = {"not", "no", "never", "none", "neither", "nor"}
    neg_a = sum(1 for w in wa if w in negations)
    neg_b = sum(1 for w in wb if w in negations)
    negation_mismatch = (neg_a > 0) != (neg_b > 0)

    if negation_mismatch and overlap > 0.70:
        signals.append("negation_mismatch")
        notes.append("High overlap but negation polarity differs")
        return False, signals, notes

    if na in nb or nb in na:
        signals.append("substring_match")
        notes.append("One normalized text is a substring of the other")
        return True, signals, notes

    if jaccard >= 0.85 and length_ratio >= 0.80:
        signals.append("high_similarity")
        notes.append("High token overlap and similar length")
        return True, signals, notes

    if overlap >= 0.90 and length_ratio >= 0.70:
        signals.append("high_overlap")
        notes.append("Very high overlap coefficient despite length difference")
        return True, signals, notes

    signals.append("below_threshold")
    notes.append("Similarity below approximate-duplicate threshold")
    return False, signals, notes
