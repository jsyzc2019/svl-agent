"""§4S93 sensor_unseen_probe 的 12 守卫（G3 负向注入 + 只读 + 权威态零副作用）。

借 Citadel Securities João Wenzel 组织世界模型演讲的锋利镜面：
传感器静默≠零信号；last_tried/last_ok 双时间戳 + unseen 态；判不了不并入正常。
该演讲无开源代码已硬核核查，只做一手工程细节结构同构自检。
"""
import os
import json
import hashlib
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
KERNEL = os.path.join(HERE, os.pardir, "kernel.py")
ROOT = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir))
spec = importlib.util.spec_from_file_location("k", KERNEL)
K = importlib.util.module_from_spec(spec)
spec.loader.exec_module(K)

PREPRG = os.path.join(ROOT, "prereg_sensor_unseen_probe_20261128.json")
SEVEN = [
    "authoritative_state.json",
    "life_kernel/constitution.sha256",
    "life_kernel/data/heartbeat_log.jsonl",
    "life_kernel/data/inbound_inbox.jsonl",
    "DECISIONS_20261127.json",
    "gap_archive_20261128.json",
    "knowledge_base_store.json",
]
# 交接账 §4S93 前的权威态七件套基线哈希
SEVEN_BASELINE = [
    "5f7a2584", "2ad148c7", "ea749f76", "8806b248",
    "91114955", "d73bfef5", "0938b3df",
]


def _sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def _seven_snapshot():
    return {rel: _sha(os.path.join(ROOT, rel)) for rel in SEVEN}


def _sig(name, surface="UNSEEN_NOT_ZERO", disclosed=True, evidence="", force_class=None):
    d = {"name": name, "surface": surface, "disclosed": disclosed, "evidence": evidence}
    if force_class:
        d["force_class"] = force_class
    return d


# G1 预注册 SHA 改码前锁死
def test_01_prereg_sha_locked():
    p = json.load(open(PREPRG, encoding="utf-8"))
    assert p["prereg_id"] == "prereg_sensor_unseen_probe_20261128"
    assert p["locked_before_code"] is True
    assert p["function_name"] == "sensor_unseen_probe"
    assert p["signature"] == "sensor_unseen_probe(sensor_signals=None)"
    assert p["read_only"] is True
    assert p["real_expected"]["expected_flag"] == "ALL_UNSEEN_DISCLOSED"
    assert "368" in p["g6_acceptance"]["new"]
    assert "356" in p["g6_acceptance"]["baseline"]
    assert _sha(PREPRG).startswith("75ac272a")


# G2 真实结果 ALL_UNSEEN_DISCLOSED
def test_02_real_all_unseen_disclosed():
    r = K.sensor_unseen_probe()
    assert r["sensor_flag"] == "ALL_UNSEEN_DISCLOSED"
    assert r["counts"]["UNSEEN_DISCLOSED"] == 6
    assert r["counts"]["ZERO_SIGNAL_AS_UNSEEN"] == 0
    assert r["counts"]["SINGLE_TIMESTAMP_CONFLATION"] == 0
    assert r["counts"]["UNSTAMPED_READING"] == 0
    assert len(r["gap_rows"]) == 0


# G3 精确扫描面：三面六条真实判据
def test_03_exact_scan_surface():
    r = K.sensor_unseen_probe()
    names = [x["name"] for x in r["rows"]]
    assert names == [
        "authority.seven_readable_not_zero",
        "authority.verdict_read_not_zero",
        "heartbeat.timestamp_stamped",
        "inbox.timestamp_stamped",
        "verdict.birth_unverifiable_disclosed",
        "abstention.not_masked_zero",
    ]
    surfaces = {x["surface"] for x in r["rows"]}
    assert surfaces == {"UNSEEN_NOT_ZERO", "DOUBLE_TIMESTAMP", "STAMPED_READING"}


# G4 七件套实读 + 权威态实读披露真实
def test_04_authority_read_disclosed_real():
    r = K.sensor_unseen_probe()
    assert "seven_readable=7" in r["rows"][0]["evidence"]
    assert "unreadable=0" in r["rows"][0]["evidence"]
    assert "GAP_INCONCLUSIVE" in r["rows"][1]["evidence"]


# G5 双时间戳 + BIRTH_UNVERIFIABLE/abstention 显式暴露真实
def test_05_timestamp_and_unverifiable_real():
    r = K.sensor_unseen_probe()
    assert "hb_undated=0" in r["rows"][2]["evidence"]
    assert "last_tried/last_ok" in r["rows"][2]["evidence"]
    assert "inbox_undated=0" in r["rows"][3]["evidence"]
    assert "BIRTH_UNVERIFIABLE=1" in r["rows"][4]["evidence"]
    assert "abstention_count=1" in r["rows"][5]["evidence"]


# G6 只读字段
def test_06_readonly_fields():
    r = K.sensor_unseen_probe()
    assert r["verdict_unchanged"] is True
    assert r["consumed"] is False
    assert r["is_gate_verdict"] is False


# G7 负向注入：读失败当零信号（disclosed=False 自然触发）→ ZERO_SIGNAL_AS_UNSEEN
def test_07_zero_signal_as_unseen():
    r = K.sensor_unseen_probe(sensor_signals=[
        _sig("authority.fake_zero", disclosed=False,
             evidence="read failed but counted as no-change normal")])
    assert r["sensor_flag"] == "UNSEEN_MISREAD_PRESENT"
    assert r["counts"]["ZERO_SIGNAL_AS_UNSEEN"] == 1
    assert r["rows"][0]["class"] == "ZERO_SIGNAL_AS_UNSEEN"


# G8 负向注入：单时间戳混淆 → SINGLE_TIMESTAMP_CONFLATION
def test_08_single_timestamp_conflation():
    r = K.sensor_unseen_probe(sensor_signals=[
        _sig("heartbeat.fake_single", surface="DOUBLE_TIMESTAMP",
             force_class="SINGLE_TIMESTAMP_CONFLATION",
             evidence="only last_tried present, last_ok conflated with tried")])
    assert r["sensor_flag"] == "UNSEEN_MISREAD_PRESENT"
    assert r["counts"]["SINGLE_TIMESTAMP_CONFLATION"] == 1
    assert r["rows"][0]["class"] == "SINGLE_TIMESTAMP_CONFLATION"


# G9 负向注入：未标注读数 → UNSTAMPED_READING
def test_09_unstamped_reading():
    r = K.sensor_unseen_probe(sensor_signals=[
        _sig("verdict.fake_unstamped", surface="STAMPED_READING",
             force_class="UNSTAMPED_READING",
             evidence="reading without source or observation timestamp")])
    assert r["sensor_flag"] == "UNSEEN_MISREAD_PRESENT"
    assert r["counts"]["UNSTAMPED_READING"] == 1
    assert r["rows"][0]["class"] == "UNSTAMPED_READING"


# G10 全披露 + 空注入边界
def test_10_all_disclosed_and_empty_injection():
    r_all = K.sensor_unseen_probe(sensor_signals=[
        _sig("f1"), _sig("f2", surface="DOUBLE_TIMESTAMP")])
    assert r_all["sensor_flag"] == "ALL_UNSEEN_DISCLOSED"
    assert r_all["counts"]["UNSEEN_DISCLOSED"] == 2
    r_empty = K.sensor_unseen_probe(sensor_signals=[])
    assert r_empty["sensor_flag"] == "NO_SENSOR_CLAIM"
    assert "判定权归用户" in r_empty["one_page"]


# G11 honesty 边界（无传感器/不宣称世界模型/无开源代码不编造/同构非裁定/判定权归用户）
def test_11_honesty_boundary():
    h = K.sensor_unseen_probe()["honesty"]
    for frag in ("无传感器", "不宣称真实组织记忆或状态估计能力",
                 "无开源代码已硬核核查", "不编造源码", "没判≠判了没问题",
                 "标注非裁定", "判定权归用户"):
        assert frag in h, frag
    b = K.sensor_unseen_probe()["based_on"]
    assert "Citadel Securities" in b
    assert "João Wenzel" in b
    assert "last_tried,last_ok,state:unseen" in b
    assert "75ac272a" in b


# G12 调用前后权威态七件套零字节副作用 + 哈希等于基线
def test_12_authority_seven_zero_side_effect():
    before = _seven_snapshot()
    K.sensor_unseen_probe()
    K.sensor_unseen_probe(sensor_signals=[
        _sig("x", disclosed=False, force_class="UNSTAMPED_READING")])
    after = _seven_snapshot()
    assert before == after
    for rel, prefix in zip(SEVEN, SEVEN_BASELINE):
        assert _sha(os.path.join(ROOT, rel)).startswith(prefix), rel
