import re

def judge(text_a, text_b):
    def normalize(text):
        # Lowercase and extract alphanumeric tokens (including hyphens and dots)
        return re.findall(r"[a-z0-9.-]+", text.lower())
    
    tokens_a = normalize(text_a)
    tokens_b = normalize(text_b)
    set_a = set(tokens_a)
    set_b = set(tokens_b)
    union = set_a | set_b
    inter = set_a & set_b
    jaccard = len(inter) / len(union) if union else 1.0
    sym_diff = (set_a - set_b) | (set_b - set_a)
    critical_words = {"not", "no", "never", "none", "neither", "nor"}
    
    signals = [f"jaccard={jaccard:.3f}", f"sym_diff={sym_diff}"]
    notes = []
    
    if jaccard >= 0.9:
        if sym_diff & critical_words:
            decision = False
            notes.append("High Jaccard but critical negation word difference")
        else:
            decision = True
            notes.append("High Jaccard and no critical word difference")
    else:
        decision = False
        notes.append("Jaccard below threshold")
    
    return decision, signals, notes
