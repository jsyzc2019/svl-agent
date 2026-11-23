import re

def judge(text_a, text_b):
    # compute signals
    signals = []
    # exact match
    if text_a == text_b:
        signals.append("exact_match")
    else:
        signals.append("not_exact_match")
    
    # CNN presence
    cnn_pat = re.compile(r'\bCNN\b', re.IGNORECASE)
    has_cnn_a = bool(cnn_pat.search(text_a))
    has_cnn_b = bool(cnn_pat.search(text_b))
    if has_cnn_a != has_cnn_b:
        signals.append("cnn_present_difference")
    elif has_cnn_a and has_cnn_b:
        signals.append("both_have_cnn")
    
    # source document
    src_pat = re.compile(r'source document', re.IGNORECASE)
    has_src_a = bool(src_pat.search(text_a))
    has_src_b = bool(src_pat.search(text_b))
    if has_src_a != has_src_b:
        signals.append("source_document_difference")
    elif has_src_a and has_src_b:
        signals.append("both_have_source_document")
    
    # reader
    read_pat = re.compile(r'reader', re.IGNORECASE)
    has_read_a = bool(read_pat.search(text_a))
    has_read_b = bool(read_pat.search(text_b))
    if has_read_a != has_read_b:
        signals.append("reader_difference")
    elif has_read_a and has_read_b:
        signals.append("both_have_readers")
    
    # engine
    eng_pat = re.compile(r'engine', re.IGNORECASE)
    has_eng_a = bool(eng_pat.search(text_a))
    has_eng_b = bool(eng_pat.search(text_b))
    if has_eng_a != has_eng_b:
        signals.append("engine_difference")
    elif has_eng_a and has_eng_b:
        signals.append("both_have_engine")
    
    # bayesian
    bay_pat = re.compile(r'bayesian', re.IGNORECASE)
    has_bay_a = bool(bay_pat.search(text_a))
    has_bay_b = bool(bay_pat.search(text_b))
    if has_bay_a != has_bay_b:
        signals.append("bayesian_difference")
    elif has_bay_a and has_bay_b:
        signals.append("both_have_bayesian")
    
    # decision: True if texts are identical, else False
    decision = (text_a == text_b)
    
    notes = [
        f"Exact match: {text_a == text_b}",
        f"CNN in text_a: {has_cnn_a}, in text_b: {has_cnn_b}",
        f"Source document in text_a: {has_src_a}, in text_b: {has_src_b}",
        f"Reader in text_a: {has_read_a}, in text_b: {has_read_b}",
        f"Engine in text_a: {has_eng_a}, in text_b: {has_eng_b}",
        f"Bayesian in text_a: {has_bay_a}, in text_b: {has_bay_b}"
    ]
    return (decision, signals, notes)
