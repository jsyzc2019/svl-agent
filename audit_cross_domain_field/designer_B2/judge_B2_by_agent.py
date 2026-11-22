"""确定性判定：两段文本是否仅相差一段连续删除（含完全相同）。

关系是对称的、方向中性的：若 text_b 可由 text_a 删除一段连续字符得到，
则 text_a 也可由 text_b 插入同一段得到。判定完全基于文本本身，
不依赖 id、标签、外部文件、随机或时间。
"""


def judge(text_a, text_b):
    """返回 (decision: bool, signals: list, notes: list)。

    decision 为 True 当且仅当 text_a 与 text_b 中至少一个可由另一个
    通过删除一段（可为 0 长度的）连续字符得到。
    """
    signals = []
    notes = []

    # 最长公共前缀
    i = 0
    limit = min(len(text_a), len(text_b))
    while i < limit and text_a[i] == text_b[i]:
        i += 1

    # 最长公共后缀，且不与前缀重叠
    j = 0
    while j < limit - i and text_a[len(text_a) - 1 - j] == text_b[len(text_b) - 1 - j]:
        j += 1

    mid_a = text_a[i:len(text_a) - j]
    mid_b = text_b[i:len(text_b) - j]

    a_can_shrink = (mid_a != "" and mid_b == "")
    b_can_shrink = (mid_b != "" and mid_a == "")
    identical = (mid_a == "" and mid_b == "" and len(text_a) == len(text_b))

    decision = identical or a_can_shrink or b_can_shrink

    if identical:
        signals.append("exact_match")
        notes.append("两段文本完全相同（删除段长度为 0）。")
    elif a_can_shrink:
        signals.append("text_b_is_deletion_of_text_a")
        notes.append(
            "text_b 可由 text_a 删除一段连续字符得到；删除片段为 %r，"
            "出现在公共前缀长度 %d、公共后缀长度 %d 之间。" % (mid_a, i, j)
        )
    elif b_can_shrink:
        signals.append("text_a_is_deletion_of_text_b")
        notes.append(
            "text_a 可由 text_b 删除一段连续字符得到；删除片段为 %r，"
            "出现在公共前缀长度 %d、公共后缀长度 %d 之间。" % (mid_b, i, j)
        )
    else:
        signals.append("two_distinct_strings")
        notes.append(
            "两段文本中间部分均非空（分别为 %r 与 %r），"
            "无法由单段连续删除互相得到。" % (mid_a, mid_b)
        )

    signals.append("common_prefix_len=%d" % i)
    signals.append("common_suffix_len=%d" % j)
    signals.append("len_text_a=%d" % len(text_a))
    signals.append("len_text_b=%d" % len(text_b))

    return decision, signals, notes
