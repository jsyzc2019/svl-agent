"""声明-引文忠实性核查的确定性判定函数。

判定思路：引文必须逐项保留声明中出现的全部内容词与限定标记
（否定、数量、范围、程度、转折等）。只要声明中的任一标记在引文中
缺失，即视为关键限定丢失、声明被断章取义地扩大，判为不忠实。
"""

import re
from collections import Counter

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:['\u2019\u2018-][a-z0-9]+)*(?:%)?")


def _normalize(text):
    return (
        text.lower()
        .replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
    )


def _tokens(text):
    return _TOKEN_RE.findall(_normalize(text))


def judge(text_a, text_b):
    """返回 (decision, signals, notes)。

    decision=True  引文忠实复现、可采信；
    decision=False 引文丢失了声明中的限定/内容标记，不可采信。
    """
    tokens_a = _tokens(text_a)
    tokens_b = _tokens(text_b)

    count_a = Counter(tokens_a)
    count_b = Counter(tokens_b)

    missing = []
    for token, need in count_a.items():
        lack = need - count_b.get(token, 0)
        if lack > 0:
            missing.extend([token] * lack)

    decision = len(missing) == 0

    signals = [
        "tokens_a=%d" % len(tokens_a),
        "tokens_b=%d" % len(tokens_b),
        "missing_count=%d" % len(missing),
        "missing_tokens=%s" % ",".join(missing[:30]),
    ]

    if decision:
        notes = [
            "引文保留了声明中的全部内容词与限定标记，信息完整，判为忠实。"
        ]
    else:
        notes = [
            "引文缺失了声明中的标记（含否定、数量、范围、程度、转折等限定），"
            "声明被扩大，判为不忠实。"
        ]

    return decision, signals, notes
