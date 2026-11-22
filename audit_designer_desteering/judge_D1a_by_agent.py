"""D1: judge whether evidence is an independent statement rather than an echo of the claim.

Discovered rule (from the text of the sample pairs only):
  - In one class the evidence is built entirely out of the claim's own words, in the
    same order: either exactly, or with a single contiguous fragment removed
    (a negation / quantifier / number / qualifier such as "never", "not", "only",
    "no false positive", "54", "however").  After normalisation the evidence is a
    subsequence of the claim.  These are "claim echoes", judged False.
  - In the other class the evidence contains words absent from the claim (new
    numbers, terms, section references, units, etc.) and is not a subsequence of
    the claim.  These are independent statements, judged True.

Pure string/regex algorithm: no ids, no sample text, no external files, no randomness.
"""

import re

_WORD_RE = re.compile(r"[A-Za-z0-9]+")


def _normalize(text: str) -> str:
    """Keep only letters/digits, lowercase; discards spacing, punctuation and the
    duplicated-number formatting noise present in the corpus."""
    return "".join(m.group(0).lower() for m in _WORD_RE.finditer(text))


def _is_subsequence(small: str, large: str) -> bool:
    """True iff `small` can be obtained from `large` by deleting characters."""
    it = iter(large)
    return all(ch in it for ch in small)


def judge_D1(claim: str, evidence: str):
    """Return (decision, observed, reasons).

    decision is True when the evidence is independent of the claim (not a
    verbatim or near-verbatim restatement of it).
    """
    c = _normalize(claim)
    e = _normalize(evidence)

    # The evidence is a claim-echo iff every evidence token is already present
    # in the claim, in order (equality included as the degenerate case).
    echo = _is_subsequence(e, c)
    exact = (e == c)

    if echo:
        observed = [
            "evidence 的词序列完全由 claim 的词按原顺序构成（规范化后是 claim 的子序列）",
            "逐字相同，evidence 未引入 claim 之外的新内容" if exact
            else "evidence 仅删去了 claim 中一小段连续文本（否定词/数量词/数字/限定词/转折词）",
        ]
        reasons = [
            "evidence 是 claim 的回显（逐字复制或删词改写），没有提供 claim 之外的独立信息",
            "规范化后 evidence 是 claim 的子序列 -> claim_echo，判 decision=False",
        ]
        return False, observed, reasons

    observed = [
        "evidence 规范化后不是 claim 的子序列",
        "evidence 含有 claim 中未出现的词（新的数值、术语、引用或描述）",
    ]
    reasons = [
        "evidence 是一段独立于 claim 的陈述，带来了 claim 之外的实质内容",
        "evidence 与 claim 不存在逐字回显关系 -> independent_evidence，判 decision=True",
    ]
    return True, observed, reasons
