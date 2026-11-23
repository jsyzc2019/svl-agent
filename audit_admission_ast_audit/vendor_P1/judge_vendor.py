import re

def judge(text_a: str, text_b: str) -> tuple[bool, list[str], list[str]]:
    """
    Determines whether text_b faithfully reproduces text_a.
    Faithfulness is defined as exact string match after whitespace normalization.
    This rule is derived from the provided data where all faithful pairs are identical
    and all unfaithful pairs differ in at least one token (including critical qualifiers
    such as negations, quantifiers, numbers, and scope words).
    """
    # Normalize whitespace: collapse multiple spaces/newlines/tabs into a single space, strip ends.
    norm_a = re.sub(r'\s+', ' ', text_a.strip())
    norm_b = re.sub(r'\s+', ' ', text_b.strip())

    if norm_a == norm_b:
        return True, ["exact_match"], ["Citation exactly matches declaration."]
    else:
        return False, ["not_exact_match"], ["Citation does not exactly match declaration."]
