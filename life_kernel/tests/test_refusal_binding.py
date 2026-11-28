"""§4S85 refusal_binding_probe 只读自检守卫（DSH fork_tool_guard 纪律同构）。
预注册 prereg_refusal_binding_probe_20261128.json SHA 7b9cd732… 改码前锁死。
"""
import os
import hashlib
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
KERNEL = os.path.join(HERE, os.pardir, "kernel.py")
ROOT = os.path.join(HERE, os.pardir, os.pardir)
spec = importlib.util.spec_from_file_location("kernel_under_test", KERNEL)
K = importlib.util.module_from_spec(spec)
spec.loader.exec_module(K)


def _sig(name, surface="SOURCE_BINDING", held=True, evidence=""):
    return {"name": name, "surface": surface, "held": held, "evidence": evidence}


def test_01_prereg_sha_locked():
    prereg = os.path.join(ROOT, "prereg_refusal_binding_probe_20261128.json")
    assert hashlib.sha256(open(prereg, "rb").read()).hexdigest() == \
        "7b9cd732d938519fdb2a555facdff9e44dfb921d5d7974fb8bf2b8da216af072"


def test_02_real_all_bound_no_fabricated_weakness():
    """真实:三类纪律载体全在位,零松动(不刷松动也不刷保证)。"""
    r = K.refusal_binding_probe()
    assert r["binding_flag"] == "ALL_BOUND"
    assert r["counts"]["BOUND_IN_PLACE"] == 3
    assert r["counts"]["UNBOUND_WEAK"] == 0
    assert len(r["rows"]) == 3
    assert "判定权归用户" in r["one_page"]


def test_03_real_three_surfaces_exact_scope():
    """真实扫描面精确:两类SOURCE_BINDING + 一类UNKNOWN_REFUSAL。"""
    rows = K.refusal_binding_probe()["rows"]
    names = [r["name"] for r in rows]
    assert names == [
        "source_binding.woken_by_not_self_filled",
        "source_binding.verdict_anchors_from_decisions",
        "unknown_refusal.unknown_not_counted_as_zero",
    ]
    assert sum(1 for r in rows if r["surface"] == "SOURCE_BINDING") == 2
    assert sum(1 for r in rows if r["surface"] == "UNKNOWN_REFUSAL") == 1


def test_04_real_evidence_is_actual_readings():
    """真实evidence来自真读数非空,不是占位。"""
    for row in K.refusal_binding_probe()["rows"]:
        assert row["evidence"].strip()
    ev = " ".join(r["evidence"] for r in K.refusal_binding_probe()["rows"])
    assert "内核绝不代填" in ev
    assert "D1-provenance-backfill" in ev
    assert "masked_zero=1" in ev and "attributable=True" in ev


def test_05_readonly_struct_fields():
    r = K.refusal_binding_probe()
    for k in ("binding_flag", "rows", "counts", "unbound_rows", "one_page", "honesty"):
        assert k in r
    assert r["verdict_unchanged"] is True
    assert r["consumed"] is False
    assert r["is_gate_verdict"] is False


def test_06_empty_source_self_filled_becomes_unbound():
    """负向:空woken_by被放行(可自填)必 UNBOUND_PRESENT + UNBOUND_WEAK。"""
    r = K.refusal_binding_probe(binding_signals=[
        _sig("X", held=False, evidence="empty woken_by allowed")])
    assert r["binding_flag"] == "UNBOUND_PRESENT"
    assert r["counts"]["UNBOUND_WEAK"] == 1
    assert r["unbound_rows"][0]["name"] == "X"


def test_07_anchor_self_filled_becomes_unbound():
    """负向:判定锚点自填(非权威ID)必 UNBOUND_WEAK。"""
    r = K.refusal_binding_probe(binding_signals=[
        _sig("anchor-self-filled", surface="SOURCE_BINDING", held=False)])
    assert r["binding_flag"] == "UNBOUND_PRESENT"
    assert r["counts"]["UNBOUND_WEAK"] == 1


def test_08_unknown_counted_as_zero_becomes_unbound():
    """负向:UNKNOWN被算进measured_zero必 UNBOUND_WEAK。"""
    r = K.refusal_binding_probe(binding_signals=[
        _sig("unknown-as-zero", surface="UNKNOWN_REFUSAL", held=False)])
    assert r["binding_flag"] == "UNBOUND_PRESENT"
    assert r["counts"]["UNBOUND_WEAK"] == 1


def test_09_all_held_becomes_all_bound():
    """负向:全held必 ALL_BOUND。"""
    r = K.refusal_binding_probe(binding_signals=[
        _sig("a", held=True), _sig("b", held=True)])
    assert r["binding_flag"] == "ALL_BOUND"
    assert r["counts"]["BOUND_IN_PLACE"] == 2


def test_10_empty_signals_no_binding_claim():
    """负向:空载体必 NO_BINDING_CLAIM(不伪造保证也不伪造松动)。"""
    r = K.refusal_binding_probe(binding_signals=[])
    assert r["binding_flag"] == "NO_BINDING_CLAIM"
    assert r["rows"] == []


def test_11_honesty_boundary_disclaims_runtime_equivalence():
    """honesty明确:非fork runtime/无tool路径/无replay攻击面/非等价安全机制/标注非裁定。"""
    h = K.refusal_binding_probe()["honesty"]
    for kw in ("非fork runtime", "无tool路径", "无真实replay攻击面",
               "不宣称等价安全机制", "dirty_keys当前=0", "标注非裁定", "判定权归用户"):
        assert kw in h


def test_12_zero_side_effect_on_authoritative_state():
    """调用前后权威态四件套+DECISIONS+归档账+KB哈希不变(含base_beat record=False零污染)。"""
    files = ["authoritative_state.json",
             "life_kernel/constitution.sha256",
             "life_kernel/data/heartbeat_log.jsonl",
             "life_kernel/data/inbound_inbox.jsonl",
             "DECISIONS_20261127.json",
             "gap_archive_20261128.json",
             "knowledge_base_store.json"]
    before = {f: hashlib.sha256(open(os.path.join(ROOT, f), "rb").read()).hexdigest()
              for f in files}
    K.refusal_binding_probe()
    after = {f: hashlib.sha256(open(os.path.join(ROOT, f), "rb").read()).hexdigest()
             for f in files}
    assert before == after
