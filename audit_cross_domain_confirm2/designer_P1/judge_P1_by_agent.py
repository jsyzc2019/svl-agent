"""声明-引文忠实性核查判定（P1）。

判据（纯字符串/正则、确定性）：
引文 text_b 若在复现声明 text_a 时删除或翻转了限定成分——否定、
限定/排他词、数量与范围词，或引入声明中没有的数值——则声明会被
断章取义地扩大，判为不忠实（False）；若引文与声明完全一致，或在
改写中完整保留了这些限定成分，则判为忠实（True）。
"""
import re

# 否定词
NEGATIONS = ("not", "never", "no", "neither", "nor")
# 限定/排他词；single 的等价词 one 视为被保留
RESTRICTORS = ("only", "just", "solely", "merely", "exclusively", "alone", "single")
RESTRICTOR_SYNONYMS = {"single": {"one"}}
# 数量/范围词。one/two 常由 "mutually exclusive" 等语义蕴含，不作为关键限定
QUANTIFIERS = (
    "all", "both", "half", "each", "every", "most", "many", "several",
    "few", "any", "some", "ten", "hundred", "thousand", "million",
    "entire", "whole",
)


def _tokens(s):
    return set(re.findall(r"[a-z]+|\d+(?:\.\d+)?%?", s.lower()))


def judge(text_a, text_b):
    a = text_a.strip()
    b = text_b.strip()
    ta = _tokens(a)
    tb = _tokens(b)
    a_low = a.lower()
    b_low = b.lower()
    signals = []
    notes = []

    # 完全一致：忠实
    if a == b:
        signals.append("identical")
        notes.append("引文与声明逐字一致")
        return True, signals, notes

    decision = True

    # 1) 否定翻转：声明里被否定的关键词，在引文中被肯定地复用
    for m in re.finditer(r"\b(?:not|never|no)\s+([a-z]{3,})", a_low):
        kw = m.group(1)
        if re.search(r"\b" + re.escape(kw) + r"\b", b_low):
            still_negated = re.search(
                r"\b(?:not|never|no)\s+(?:\w+\s+){0,2}" + re.escape(kw) + r"\b",
                b_low,
            )
            if not still_negated:
                decision = False
                signals.append("negation_flip:" + kw)

    # 2) 限定/排他词被删除
    for r in RESTRICTORS:
        if r in ta and r not in tb:
            if not (RESTRICTOR_SYNONYMS.get(r, set()) & tb):
                decision = False
                signals.append("restrictor_dropped:" + r)

    # 3) 数量/范围词被删除
    for q in QUANTIFIERS:
        if q in ta and q not in tb:
            decision = False
            signals.append("quantifier_dropped:" + q)

    # 4) 引文引入声明中没有的数值（新增定量结论）
    if re.search(r"\d", b) and not re.search(r"\d", a):
        decision = False
        signals.append("new_numeric_claim")

    notes.append(
        "声明的关键限定成分未被完整保留" if not decision
        else "改写中保留了声明的关键限定成分"
    )
    return decision, signals, notes
