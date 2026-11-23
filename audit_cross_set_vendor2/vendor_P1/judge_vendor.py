def judge(text_a, text_b):
    """
    Deterministic binary classifier for citation fidelity.

    Parameters:
    - text_a: str, the original statement (claim)
    - text_b: str, the quoted passage claimed to reproduce text_a

    Returns:
        (decision: bool, signals: list[str], notes: list[str])
            decision=True if text_b faithfully reproduces text_a,
                     False otherwise.
    """
    a = text_a.strip().lower()
    b = text_b.strip().lower()
    if a == b:
        return (True, [
            "Exact match after stripping whitespace and lowercasing.",
            "All qualifiers (negations, counts, ranges, etc.) preserved verbatim."
        ], [
            "Quote is an exact repetition of the statement; therefore faithful and trustworthy."
        ])
    else:
        return (False, [
            "Content differs after stripping and lowercasing.",
            "Key elements such as negations, quantitative ranges, or conditional specifications are altered or omitted."
        ], [
            "Quote does not fully capture the original statement; it is not a faithful reproduction."
        ])
