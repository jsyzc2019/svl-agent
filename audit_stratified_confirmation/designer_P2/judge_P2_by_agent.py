"""近似重复判定：纯字符串/正则的确定性判据。

思路：
1. 归一化：统一弯引号、转小写、把非字母数字（保留词内撇号）变成空格、合并空白；
2. 按词做最长公共子序列（LCS）相似度，衡量两段文字是否只是细微编辑；
3. 统计否定词出现次数。若否定词数量不同，说明差异落在 "not/never" 这类
   翻转语义的词上——即使文字高度相似，语义也相反，必须判为不重复；
4. 其余情况下，LCS 词相似度达到阈值即视为同一句话的近似版本。
"""
import re

_NEGATIONS = {
    "not", "no", "never", "none", "nobody", "nothing", "neither", "nor",
    "cannot", "don't", "doesn't", "didn't", "isn't", "aren't", "wasn't",
    "weren't", "can't", "won't", "wouldn't", "shouldn't", "couldn't",
    "hasn't", "haven't", "hadn't", "mustn't", "ain't",
}

_THRESHOLD = 0.85


def _normalize(text):
    """把文本归一化为小写、空格分隔的词序列字符串。"""
    t = text.lower().replace("\u2019", "'").replace("\u2018", "'")
    t = re.sub(r"[^a-z0-9']+", " ", t)
    return " ".join(t.split())


def _tokens(normalized):
    return normalized.split() if normalized else []


def _lcs_len(xs, ys):
    """两个词序列的最长公共子序列长度（动态规划，纯字符串实现）。"""
    m = len(ys)
    prev = [0] * (m + 1)
    for x in xs:
        cur = [0] * (m + 1)
        for j, y in enumerate(ys, 1):
            cur[j] = prev[j - 1] + 1 if x == y else (prev[j] if prev[j] >= cur[j - 1] else cur[j - 1])
        prev = cur
    return prev[m]


def _neg_count(tokens):
    return sum(1 for w in tokens if w in _NEGATIONS)


def judge(text_a, text_b):
    """返回 (decision: bool, signals: list, notes: list)。"""
    a = _normalize(text_a)
    b = _normalize(text_b)
    ta, tb = _tokens(a), _tokens(b)

    signals = []
    notes = []

    if not ta and not tb:
        signals.append("both_empty")
        notes.append("两段均为空，视为重复。")
        return True, signals, notes
    if not ta or not tb:
        signals.append("one_empty")
        notes.append("仅一段为空，语义不同。")
        return False, signals, notes

    lcs = _lcs_len(ta, tb)
    sim = 2.0 * lcs / (len(ta) + len(tb))
    na, nb = _neg_count(ta), _neg_count(tb)
    negation_flip = na != nb

    signals.append("lcs_token_sim=%.3f" % sim)
    signals.append("neg_a=%d" % na)
    signals.append("neg_b=%d" % nb)

    if negation_flip:
        signals.append("negation_mismatch")
        notes.append("否定词数量不同：差异落在 not/never 等否定词上，属于语义翻转而非细微编辑。")
        return False, signals, notes

    if sim >= _THRESHOLD:
        signals.append("high_overlap")
        notes.append("词序列高度重合（LCS 相似度达到阈值），且否定语义一致，判为近似重复。")
        return True, signals, notes

    signals.append("low_overlap")
    notes.append("词序列重合度低，表达的是另一件事，判为不重复。")
    return False, signals, notes
