#!/usr/bin/env python3
"""判据：judge(text_a, text_b) -> (bool, reasons:list, anchors:list)。

纯函数纪律：无 IO、无随机、无时间、无硬编码 id、无标签读取。

判据语义：以 text_b 为断言基准，判断 text_a 是否完整保留了 text_b 的断言。
三层核对，任一层断裂即 False，全部通过且差异仅为表面格式即 True：
  1. 否定层：核心否定词（not/no/never/nor/cannot/without/neither）的多重集合差异
  2. 连接层：连接/让步词（however/though/although/whereas/but/yet/nevertheless/
     nonetheless/while/still）的多重集合差异
  3. 断言完整性层：内容词（非虚词）多重集合差异 —— text_a 缺失或新增实义补语即断裂
仅当内容词一致、否定与连接词一致，而 token 序列差异只来自空格/标点/连字符/虚词时判 True。
"""

import re
from collections import Counter

NEG_WORDS = {"not", "no", "never", "nor", "cannot", "without", "neither"}
CONN_WORDS = {"however", "though", "although", "whereas", "but", "yet",
              "nevertheless", "nonetheless", "while", "still"}
FUNCTION_WORDS = {
    "the", "a", "an", "of", "to", "in", "on", "at", "by", "for", "with", "from",
    "and", "or", "as", "is", "are", "was", "were", "be", "been", "being",
    "that", "this", "these", "those", "it", "its", "we", "our", "their",
    "than", "then", "so", "such", "if", "when", "which", "who", "whom", "whose",
    "there", "here", "into", "over", "under", "between", "within", "about",
    "can", "could", "may", "might", "will", "would", "shall", "should", "do",
    "does", "did", "have", "has", "had", "also", "only", "even", "own", "same",
}


def _tokens(text):
    # 连字符视为格式分隔符：closed-book 与 closed book 的断言相同，仅表面差异
    return re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)*", text.lower().replace("-", " "))


def _multiset_diff(a, b):
    """返回 (a 比 b 多出的, b 比 a 多出的)（按多重集合）。"""
    ca, cb = Counter(a), Counter(b)
    extra_a = ca - cb
    extra_b = cb - ca
    return list((extra_a).elements()), list((extra_b).elements())


def _diff_list(a, b):
    la, lb = _multiset_diff(a, b)
    if not la and not lb:
        return None
    parts = []
    if la:
        parts.append("text_a 多出: " + ", ".join("'" + x + "'" for x in la))
    if lb:
        parts.append("text_a 缺失: " + ", ".join("'" + x + "'" for x in lb))
    return "; ".join(parts)


def judge(text_a, text_b):
    ta, tb = _tokens(text_a), _tokens(text_b)

    # 1. 否定层
    neg_a = [w for w in ta if w in NEG_WORDS]
    neg_b = [w for w in tb if w in NEG_WORDS]
    d = _diff_list(neg_a, neg_b)
    if d:
        return False, ["否定极性改变（negation polarity）: " + d], [w for w in set(neg_a) ^ set(neg_b)]

    # 2. 连接层
    con_a = [w for w in ta if w in CONN_WORDS]
    con_b = [w for w in tb if w in CONN_WORDS]
    d = _diff_list(con_a, con_b)
    if d:
        return False, ["连接/让步词增删（connector change）: " + d], [w for w in set(con_a) ^ set(con_b)]

    # 3. 断言完整性层：内容词多重集合必须一致
    cont_a = [w for w in ta if w not in FUNCTION_WORDS and w not in NEG_WORDS and w not in CONN_WORDS]
    cont_b = [w for w in tb if w not in FUNCTION_WORDS and w not in NEG_WORDS and w not in CONN_WORDS]
    d = _diff_list(cont_a, cont_b)
    if d:
        return False, ["断言补语缺失或新增（assertion complement）: " + d], \
            sorted(set(w for w in cont_a + cont_b) - set(w for w in cont_a) & set(cont_b))

    # 全部通过：断言相同，仅表面格式差异
    reasons = []
    if ta != tb:
        reasons.append("仅表面格式差异（空格/标点/连字符/虚词），断言相同")
    return True, reasons, []
