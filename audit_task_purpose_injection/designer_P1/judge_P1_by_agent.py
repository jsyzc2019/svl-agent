"""声明-引文忠实性核查判定（纯字符串/正则、确定性）。

判据：把声明与引文分别规范化（统一大小写、压缩空白、去掉首尾标点）后，
只有当引文与声明逐字一致时才判为忠实（True）。
数据中每一个「忠实」样本都是声明的逐字复现；而所有不忠实样本要么删掉了
关键限定（否定 never/not、数量 three、限定 only、转折 However/but），
要么替换成了内容不同的句子（语义相关但改变了范围/对象的复述同样不可采信）。
因此逐字一致是可从数据中归纳出的确定性分界线。
"""

import re

# 用于给判定提供可读信号的限定词模式（仅作解释，不决定 decision）
_QUALIFIER_PATTERNS = {
    "negation": r"\b(?:not|never|no|nor|none|neither|cannot|without)\b",
    "restrictive": r"\b(?:only|just|solely|merely|alone)\b",
    "quantity": r"\b(?:\d+|one|two|three|four|five|all|each|every|some|few|many|several)\b",
    "concession": r"\b(?:however|but|although|though|while|yet|whereas|nevertheless)\b",
    "degree": r"\b(?:may|might|often|sometimes|rarely|high|low|more|less|most|least)\b",
}


def _normalize(text):
    """规范化：小写、压缩空白、去掉首尾标点后再压缩一次空白。"""
    t = text.strip().lower()
    t = re.sub(r"\s+", " ", t)
    t = t.strip('.,;:!?"\'`()[]{}')
    t = re.sub(r"\s+", " ", t).strip()
    return t


def judge(text_a, text_b):
    """返回 (decision: bool, signals: list, notes: list)。"""
    signals = []
    notes = []

    na = _normalize(text_a)
    nb = _normalize(text_b)

    # 逐类检查声明中的限定是否在引文中保留（仅用于生成 signals/notes）
    missing = []
    for name, pattern in _QUALIFIER_PATTERNS.items():
        a_tokens = [m.lower() for m in re.findall(pattern, na)]
        if not a_tokens:
            continue
        b_tokens = [m.lower() for m in re.findall(pattern, nb)]
        for tok in sorted(set(a_tokens)):
            if tok not in b_tokens:
                missing.append((name, tok))

    faithful = na == nb

    if faithful:
        signals.append("verbatim_match")
        notes.append("引文与声明规范化后逐字一致，全部限定完整保留。")
    else:
        signals.append("text_mismatch")
        if missing:
            signals.append("dropped_qualifier")
            notes.append(
                "引文缺失或改变了关键限定："
                + ", ".join("%s:%s" % (n, t) for n, t in missing)
            )
        else:
            notes.append("引文内容与声明不一致，未逐字复现。")

    return faithful, signals, notes
