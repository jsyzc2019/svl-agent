def judge(text_a: str, text_b: str):
    """
    Deterministic binary classifier for citation fidelity.

    Parameters:
    - text_a: the original statement (claim).
    - text_b: the quoted text claimed to reproduce the statement.

    Returns:
        (decision: bool, signals: list, notes: list)
            decision=True if text_b is an exact faithful reproduction of text_a,
            False otherwise.
    """
    # Normalize surrounding whitespace
    na = text_a.strip()
    nb = text_b.strip()

    decision = (na == nb)

    signals = []
    notes = []

    if decision:
        signals.append('exact_match')
        notes.append(
            'The quote exactly repeats the statement; it preserves all information '
            'including negations, quantities, ranges, and qualifiers.'
        )
    else:
        signals.append('mismatch')
        notes.append(
            'The quote differs from the statement; key qualifiers (e.g., "only", '
            '"both", numbers, intervals) are altered or omitted, making it an '
            'unfaithful expansion that expands the claim beyond the original.'
        )

    return (decision, signals, notes)
