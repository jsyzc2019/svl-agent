"""§4S81 recognition_probe 只读自检守卫（Marx & Gilon 论文结构同构）。
预注册 prereg_recognition_probe_20261128.json SHA ea8aeb6a… 改码前锁死。
实现bug修正澄清 prereg_recognition_probe_clarification_20261128.json（不改原SHA）。
"""
import os
import hashlib
import importlib.util

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
KERNEL = os.path.join(HERE, os.pardir, "kernel.py")
ROOT = os.path.join(HERE, os.pardir, os.pardir)
spec = importlib.util.spec_from_file_location("kernel_under_test", KERNEL)
K = importlib.util.module_from_spec(spec)
spec.loader.exec_module(K)


def test_01_prereg_sha_locked():
    """预注册 SHA 改码前已锁，澄清文件存在（实现bug就地修，不改原SHA）。"""
    prereg = os.path.join(ROOT, "prereg_recognition_probe_20261128.json")
    assert hashlib.sha256(open(prereg, "rb").read()).hexdigest() == \
        "ea8aeb6a17becb47a7898ec0bec93679d83408ee71ceeee20744326fc5c662aa"
    clar = os.path.join(ROOT, "prereg_recognition_probe_clarification_20261128.json")
    assert os.path.exists(clar)


def test_02_real_all_recognized_no_fabricated_noise():
    """真实台账:11 verdict载体全有判定权归属锚点,零噪音(不刷出假噪音)。"""
    r = K.recognition_probe()
    assert r["recognition_flag"] == "ALL_RECOGNIZED"
    assert r["counts"]["UNRECOGNIZED_NOISE"] == 0
    assert r["counts"]["RECOGNIZED_USER"] == 3
    assert r["counts"]["RECOGNIZED_ARCHIVE"] == 1
    assert r["counts"]["RECOGNIZED_DECLARED"] == 7
    assert len(r["rows"]) == 11
    assert "判定权归用户" in r["one_page"]


def test_03_real_user_and_archive_ids_correct():
    """真实裁定ID来自权威字段,不是占位'?'(archive id从audit取)。"""
    r = K.recognition_probe()
    assert "D1-provenance-backfill" in r["user_recognized_ids"]
    assert "D3-judgment-fork-defer" in r["user_recognized_ids"]
    assert r["archive_recognized_ids"] == ["memory_governance"]
    assert "?" not in r["archive_recognized_ids"]


def test_04_readonly_struct_fields():
    r = K.recognition_probe()
    for k in ("recognition_flag", "rows", "counts", "noise_rows", "one_page", "honesty"):
        assert k in r
    assert r["verdict_unchanged"] is True
    assert r["consumed"] is False
    assert r["is_gate_verdict"] is False
    assert "判定权归用户" in r["honesty"]


def test_05_negative_unrecognized_noise_detected():
    """负向注入:无锚点verdict必NOISE_PRESENT且分类UNRECOGNIZED_NOISE。"""
    sources = [{"name": " rogue_probe", "verdict": "PASS", "decision_gate_declared": False}]
    r = K.recognition_probe(verdict_sources=sources,
                            decisions_path="/nonexistent", gap_archive_path="/nonexistent")
    assert r["recognition_flag"] == "NOISE_PRESENT"
    assert r["counts"]["UNRECOGNIZED_NOISE"] == 1
    assert r["rows"][0]["class"] == "UNRECOGNIZED_NOISE"


def test_06_negative_user_verdict_recognized():
    """负向注入:DECISIONS有user_verdict+EXECUTED必RECOGNIZED_USER。"""
    import tempfile, json
    dec = {"decisions": [{"id": "X1", "user_verdict": "采纳", "status": "EXECUTED"}]}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(dec, f); dp = f.name
    try:
        sources = [{"name": "DECISIONS:X1", "verdict": "EXECUTED", "user_verdict_id": "X1"}]
        r = K.recognition_probe(verdict_sources=sources, decisions_path=dp,
                                gap_archive_path="/nonexistent")
        assert r["counts"]["RECOGNIZED_USER"] == 1
        assert r["recognition_flag"] == "ALL_RECOGNIZED"
    finally:
        os.unlink(dp)


def test_07_negative_archive_resolved_recognized():
    """负向注入:gap_archive RESOLVED_EXECUTED必RECOGNIZED_ARCHIVE。"""
    import tempfile, json
    arc = {"gap_entries": [{"audit": "audit_x", "class": "RESOLVED_EXECUTED"}]}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(arc, f); ap = f.name
    try:
        sources = [{"name": "ARCHIVE:audit_x", "verdict": "RESOLVED_EXECUTED", "archive_id": "audit_x"}]
        r = K.recognition_probe(verdict_sources=sources,
                                decisions_path="/nonexistent", gap_archive_path=ap)
        assert r["counts"]["RECOGNIZED_ARCHIVE"] == 1
        assert r["recognition_flag"] == "ALL_RECOGNIZED"
    finally:
        os.unlink(ap)


def test_08_negative_declared_gate_recognized():
    """负向注入:声明判定权归用户+verdict_unchanged+非门必RECOGNIZED_DECLARED。"""
    sources = [{"name": "good_probe", "verdict": "PASS", "decision_gate_declared": True,
                "verdict_unchanged": True, "is_gate_verdict": False}]
    r = K.recognition_probe(verdict_sources=sources,
                            decisions_path="/nonexistent", gap_archive_path="/nonexistent")
    assert r["counts"]["RECOGNIZED_DECLARED"] == 1
    assert r["recognition_flag"] == "ALL_RECOGNIZED"


def test_09_negative_gate_selfseal_not_recognized():
    """负向注入:自封门(is_gate_verdict=True)不得算已识别。"""
    sources = [{"name": "gate_probe", "verdict": "PASS", "decision_gate_declared": True,
                "verdict_unchanged": True, "is_gate_verdict": True}]
    r = K.recognition_probe(verdict_sources=sources,
                            decisions_path="/nonexistent", gap_archive_path="/nonexistent")
    assert r["counts"]["UNRECOGNIZED_NOISE"] == 1
    assert r["recognition_flag"] == "NOISE_PRESENT"


def test_10_negative_empty_no_verdict_claim():
    """负向注入:空载体必NO_VERDICT_CLAIM。"""
    r = K.recognition_probe(verdict_sources=[],
                            decisions_path="/nonexistent", gap_archive_path="/nonexistent")
    assert r["recognition_flag"] == "NO_VERDICT_CLAIM"


def test_11_authoritative_state_zero_side_effect():
    """只读:权威态四件套+DECISIONS+gap_archive+KB哈希动手前后一致。"""
    files = [
        os.path.join(ROOT, "authoritative_state.json"),
        os.path.join(ROOT, "life_kernel", "constitution.sha256"),
        os.path.join(ROOT, "life_kernel", "data", "heartbeat_log.jsonl"),
        os.path.join(ROOT, "life_kernel", "data", "inbound_inbox.jsonl"),
        os.path.join(ROOT, "DECISIONS_20261127.json"),
        os.path.join(ROOT, "gap_archive_20261128.json"),
        os.path.join(ROOT, "knowledge_base_store.json"),
    ]
    before = [hashlib.sha256(open(f, "rb").read()).hexdigest() for f in files]
    K.recognition_probe()
    after = [hashlib.sha256(open(f, "rb").read()).hexdigest() for f in files]
    assert before == after


def test_12_honesty_boundary_no_cognitive_claim():
    """诚实边界:不宣称内核有真实recognition认知机制,记原论文低可信+COI。"""
    r = K.recognition_probe()
    h = r["honesty"]
    assert "无星形胶质细胞" in h or "不宣称真实识别能力" in h
    assert "COI" in h or "商业" in h
    assert "hypothesis未证实" in h
    assert "结构自检" in h
