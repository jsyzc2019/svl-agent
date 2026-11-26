def judge(text_a, text_b):
    reasons = []
    anchors = []

    def norm(s):
        s = s.lower()
        cleaned = []
        for ch in s:
            cleaned.append(ch if ch.isalnum() or ch.isspace() else ' ')
        return ' '.join(''.join(cleaned).split())

    ta = norm(text_a)
    tb = norm(text_b)
    wa = ta.split()
    wb = tb.split()

    negs = {'no', 'not', 'never', 'cannot'}
    conns = {'however', 'although', 'while', 'though'}

    if {w for w in wa if w in negs} != {w for w in wb if w in negs}:
        reasons.append('negation_polarity_flip')
        anchors.append('negation')
        return False, reasons, anchors

    if {w for w in wa if w in conns} != {w for w in wb if w in conns}:
        reasons.append('connector_cue_mismatch')
        anchors.append('connector')
        return False, reasons, anchors

    if wa and wb and len(wb) < max(1, int(0.6 * len(wa))) and wa[:len(wb)] == wb:
        reasons.append('tail_predicate_dropped')
        anchors.append('tail')
        return False, reasons, anchors

    return True, reasons, anchors