"""Deterministic judge for the claim/evidence binary structure.

The structure found in the data: for each claim there are three kinds of
evidence -- (a) a verbatim copy of the claim, (b) a genuinely reworded
restatement, and (c) a near-copy produced by deleting exactly one contiguous
non-empty span from the claim (e.g. a negation, a number, a qualifier, or a
short phrase).  Kind (c) is a tampered echo: the evidence no longer reproduces
the claim faithfully, so it is the negative class; (a) and (b) are faithful
and form the positive class.

No ids, no sample strings, no external files, no randomness or scoring.
"""


def _collapse_whitespace(text: str) -> str:
    return " ".join(text.split())


def _is_single_span_deletion(full: str, part: str) -> bool:
    """True iff `part` == `full` with exactly one contiguous span removed."""
    if not isinstance(full, str) or not isinstance(part, str):
        return False
    if len(part) >= len(full):
        return False

    limit = min(len(full), len(part))

    prefix = 0
    while prefix < limit and full[prefix] == part[prefix]:
        prefix += 1

    suffix = 0
    while (
        suffix < limit - prefix
        and full[len(full) - 1 - suffix] == part[len(part) - 1 - suffix]
    ):
        suffix += 1

    # The untouched prefix and suffix must cover the whole of `part`;
    # the remaining middle of `full` is the single deleted span.
    return prefix + suffix == len(part)


def judge_D1(claim: str, evidence: str):
    """Return (decision, signals, notes).

    decision is False exactly when the evidence is a claim with one
    contiguous span deleted (a tampered echo); otherwise True.
    """
    signals = []
    notes = []

    claim = claim if isinstance(claim, str) else ""
    evidence = evidence if isinstance(evidence, str) else ""

    deleted_raw = _is_single_span_deletion(claim, evidence)
    deleted_norm = _is_single_span_deletion(
        _collapse_whitespace(claim), _collapse_whitespace(evidence)
    )
    tampered = deleted_raw or deleted_norm

    if claim == evidence:
        signals.append("verbatim_duplicate")
    elif tampered:
        signals.append("single_span_deletion")
    else:
        signals.append("distinct_restatement")

    signals.append("claim_len=%d" % len(claim))
    signals.append("evidence_len=%d" % len(evidence))
    signals.append("deleted_raw=%s" % deleted_raw)
    signals.append("deleted_normalized=%s" % deleted_norm)

    if tampered:
        notes.append(
            "evidence is the claim with one contiguous substring removed; "
            "it is a tampered echo, not a faithful reproduction"
        )
    elif claim == evidence:
        notes.append("evidence reproduces the claim verbatim")
    else:
        notes.append(
            "evidence is worded differently and is not a single-span "
            "deletion of the claim"
        )

    decision = not tampered
    return decision, signals, notes
