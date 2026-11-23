import re

def judge(text_a: str, text_b: str) -> tuple[bool, list[str], list[str]]:
    """
    Binary classifier based on exact string equality after stripping whitespace.
    Returns (decision, signals, notes).
    """
    # Normalize whitespace: collapse multiple spaces/newlines/tabs to single space, strip ends
    norm_a = re.sub(r'\s+', ' ', text_a).strip()
    norm_b = re.sub(r'\s+', ' ', text_b).strip()
    
    decision = (norm_a == norm_b)
    signals = ["exact_match"] if decision else ["mismatch"]
    notes = ["Texts are identical after whitespace normalization"] if decision else ["Texts differ after whitespace normalization"]
    return decision, signals, notes
