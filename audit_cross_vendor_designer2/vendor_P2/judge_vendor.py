import string

def judge(text_a, text_b):
    # Normalization
    def norm(t):
        t = t.lower()
        # replace punctuation with space
        t = t.translate(str.maketrans(string.punctuation, ' ' * len(string.punctuation)))
        # collapse whitespace
        t = ' '.join(t.split())
        return t

    na = norm(text_a)
    nb = norm(text_b)

    if na == nb:
        return (True, ['Exact match after normalization'], ['Texts are identical after removing punctuation and case'])

    # tokenization
    def tokens(t):
        return t.split()

    ta = tokens(na)
    tb = tokens(nb)

    set_ta = set(ta)
    set_tb = set(tb)
    inter = len(set_ta & set_tb)
    union = len(set_ta | set_tb)
    jaccard = inter / union if union > 0 else 0.0

    if jaccard >= 0.85:
        return (True, ['High token overlap (Jaccard >=0.85)'], ['Near duplicate despite wording differences'])
    elif jaccard >= 0.70:
        # maybe still near duplicate but less clear
        return (True, ['Moderate token overlap (Jaccard 0.70-0.84)'], ['Possible near duplicate'])
    else:
        return (False, ['Low token overlap (Jaccard <0.70)'], ['Likely distinct content'])
