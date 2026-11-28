"""§4S95 navigation_calibration_probe 的 12 守卫（G3 负向注入 + 只读 + 权威态零副作用）。

借 arXiv 2610.35868 DecisionRAG (Cornell+ASAPP) 的锋利镜面：
共享上下文可比性；召回上限≠首位命中；不可逆剪枝显式处置。
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

PREPRG = os.path.join(ROOT, "prereg_navigation_calibration_probe_20261128.json")
SEVEN = [
    "authoritative_state.json",
    "life_kernel/constitution.sha256",
    "life_kernel/data/heartbeat_log.jsonl",
    "life_kernel/data/inbound_inbox.jsonl",
    "DECISIONS_20261127.json",
    "gap_archive_20261128.json",
    "knowledge_base_store.json",
]
SEVEN_BASELINE = [
    "5f7a2584", "2ad148c7", "ea749f76", "8806b248",
    "91114955", "d73bfef5", "0938b3df",
]


def _sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def _seven_snapshot():
    return {rel: _sha(os.path.join(ROOT, rel)) for rel in SEVEN}


def _sig(name, surface="SHARED_CONTEXT_COMPARABLE", calibrated=True, evidence="",
         force_class=None):
    d = {"name": name, "surface": surface, "calibrated": calibrated, "evidence": evidence}
    if force_class:
        d["force_class"] = force_class
    return d


# G1 预注册 SHA 改码前锁死
def test_01_prereg_sha_locked():
    p = json.load(open(PREPRG, encoding="utf-8"))
    assert p["prereg_id"] == "prereg_navigation_calibration_probe_20261128"
    assert p["locked_before_code"] is True
    assert p["kernel_sha_before"].startswith("33ab6a10")
    assert p["function_name"] == "navigation_calibration_probe"
    assert p["signature"] == "navigation_calibration_probe(nav_signals=None)"
    assert p["read_only"] is True
    assert p["real_expected"]["expected_flag"] == "ALL_CALIBRATED"
    assert "380" in p["g6_acceptance"]["new"]
    assert "368" in p["g6_acceptance"]["baseline"]
    assert _sha(PREPRG).startswith("fd990cf2")


# G2 真实结果 ALL_CALIBRATED
def test_02_real_all_calibrated():
    r = K.navigation_calibration_probe()
    assert r["nav_flag"] == "ALL_CALIBRATED"
    assert r["counts"]["CALIBRATED"] == 6
    assert r["counts"]["SEPARATE_NOT_COMPARABLE"] == 0
    assert r["counts"]["RECALL_MASKS_TOP1"] == 0
    assert r["counts"]["PRUNED_IRREVERSIBLE"] == 0
    assert len(r["gap_rows"]) == 0


# G3 精确扫描面：三面六条真实判据
def test_03_exact_scan_surface():
    r = K.navigation_calibration_probe()
    names = [x["name"] for x in r["rows"]]
    assert names == [
        "recognition.four_classes_jointly",
        "recognition.flag_and_noise",
        "birth.synced_and_authentic_dual",
        "birth.backfill_exposed",
        "archive.class_disclosed",
        "archive.budget_and_recovery",
    ]
    surfaces = {x["surface"] for x in r["rows"]}
    assert surfaces == {"SHARED_CONTEXT_COMPARABLE", "RECALL_VS_TOP1", "IRREVERSIBLE_PRUNE"}


# G4 共享上下文可比性真实：四类并列 + flag/noise
def test_04_shared_context_real():
    r = K.navigation_calibration_probe()
    assert "USER=3" in r["rows"][0]["evidence"]
    assert "ARCHIVE=1" in r["rows"][0]["evidence"]
    assert "NOISE=0" in r["rows"][0]["evidence"]
    assert "ALL_RECOGNIZED" in r["rows"][1]["evidence"]


# G5 召回vs首位双列 + 背填暴露真实
def test_05_recall_vs_top1_real():
    r = K.navigation_calibration_probe()
    assert "synced_rate=0.9091" in r["rows"][2]["evidence"]
    assert "authentic_rate=0.1818" in r["rows"][2]["evidence"]
    assert "backfilled=8" in r["rows"][3]["evidence"]
    assert "authentic=2" in r["rows"][3]["evidence"]


# G6 不可逆剪枝显式处置真实
def test_06_irreversible_prune_real():
    r = K.navigation_calibration_probe()
    assert "entries=14" in r["rows"][4]["evidence"]
    assert "ACCEPTED=13" in r["rows"][4]["evidence"]
    assert "RESOLVED=1" in r["rows"][4]["evidence"]
    assert "不再追" in r["rows"][5]["evidence"]


# G7 只读字段
def test_07_readonly_fields():
    r = K.navigation_calibration_probe()
    assert r["verdict_unchanged"] is True
    assert r["consumed"] is False
    assert r["is_gate_verdict"] is False


# G8 负向注入：各自单判未并列 → SEPARATE_NOT_COMPARABLE
def test_08_separate_not_comparable():
    r = K.navigation_calibration_probe(nav_signals=[
        _sig("recognition.fake_separate", calibrated=False,
             evidence="each class judged separately, all pass, never jointly compared")])
    assert r["nav_flag"] == "CALIBRATION_GAP_PRESENT"
    assert r["counts"]["SEPARATE_NOT_COMPARABLE"] == 1
    assert r["rows"][0]["class"] == "SEPARATE_NOT_COMPARABLE"


# G9 负向注入：只报召回不报首位 → RECALL_MASKS_TOP1
def test_09_recall_masks_top1():
    r = K.navigation_calibration_probe(nav_signals=[
        _sig("birth.recall_only", surface="RECALL_VS_TOP1", calibrated=False,
             force_class="RECALL_MASKS_TOP1",
             evidence="synced_rate=1.0 reported, authentic_birth_rate omitted")])
    assert r["nav_flag"] == "CALIBRATION_GAP_PRESENT"
    assert r["counts"]["RECALL_MASKS_TOP1"] == 1
    assert r["rows"][0]["class"] == "RECALL_MASKS_TOP1"


# G10 负向注入：剪枝无处置 → PRUNED_IRREVERSIBLE；全校准与空注入边界
def test_10_pruned_irreversible_and_boundaries():
    r = K.navigation_calibration_probe(nav_signals=[
        _sig("archive.fake_prune", surface="IRREVERSIBLE_PRUNE",
             force_class="PRUNED_IRREVERSIBLE",
             evidence="branches pruned with no disposition or recovery path")])
    assert r["nav_flag"] == "CALIBRATION_GAP_PRESENT"
    assert r["counts"]["PRUNED_IRREVERSIBLE"] == 1
    r_all = K.navigation_calibration_probe(nav_signals=[
        _sig("f1"), _sig("f2", surface="RECALL_VS_TOP1")])
    assert r_all["nav_flag"] == "ALL_CALIBRATED"
    assert r_all["counts"]["CALIBRATED"] == 2
    r_empty = K.navigation_calibration_probe(nav_signals=[])
    assert r_empty["nav_flag"] == "NO_NAVIGATION_CLAIM"
    assert "判定权归用户" in r_empty["one_page"]


# G11 honesty 边界（无RAG/不宣称检索/无开源码不编造/九格非全赢/标注非裁定）
def test_11_honesty_boundary():
    h = K.navigation_calibration_probe()["honesty"]
    for frag in ("无语料层级", "不宣称真实检索能力", "无官方开源代码仓库已核查",
                 "开放权重judge≠开源代码", "九格非全赢", "标注非裁定", "判定权归用户"):
        assert frag in h, frag
    b = K.navigation_calibration_probe()["based_on"]
    assert "2610.35868" in b
    assert "Cornell" in b and "ASAPP" in b
    assert "fd990cf2" in b


# G12 调用前后权威态七件套零字节副作用 + 哈希等于基线
def test_12_authority_seven_zero_side_effect():
    before = _seven_snapshot()
    K.navigation_calibration_probe()
    K.navigation_calibration_probe(nav_signals=[
        _sig("x", calibrated=False, force_class="PRUNED_IRREVERSIBLE")])
    after = _seven_snapshot()
    assert before == after
    for rel, prefix in zip(SEVEN, SEVEN_BASELINE):
        assert _sha(os.path.join(ROOT, rel)).startswith(prefix), rel
