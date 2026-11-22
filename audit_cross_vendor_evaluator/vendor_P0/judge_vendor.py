def judge(text_a, text_b):
    signals = []
    notes = []

    def is_subsequence(sub, full):
        iterator = iter(full)
        return all(char in iterator for char in sub)

    exact_match = text_a == text_b
    a_in_b = is_subsequence(text_a, text_b)
    b_in_a = is_subsequence(text_b, text_a)
    subsequence_relation = a_in_b or b_in_a
    length_diff = abs(len(text_a) - len(text_b))

    signals.append("exact_match=" + str(exact_match))
    signals.append("text_a_is_subsequence_of_text_b=" + str(a_in_b))
    signals.append("text_b_is_subsequence_of_text_a=" + str(b_in_a))
    signals.append("subsequence_relation=" + str(subsequence_relation))
    signals.append("length_difference=" + str(length_diff))

    decision = subsequence_relation

    if exact_match:
        notes.append("The two texts are identical character-for-character.")
    elif subsequence_relation:
        notes.append("One text is a subsequence of the other, indicating a deletion variant.")
    else:
        notes.append("Neither text is a subsequence of the other; the pair differs substantially.")

    return decision, signals, notes
