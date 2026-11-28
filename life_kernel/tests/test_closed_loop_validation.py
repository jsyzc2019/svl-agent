"""§4S97 closed_loop_validation_probe 的 12 守卫（G3 负向注入 + 只读 + 权威态零副作用）。

借 arXiv 2610.27045 Physical AI (Zhang/Shen/Xue/Zhao 等51作者) 的锋利镜面：
闭环评估vs开环指标；物理一致性必须在操作域内验证；模拟与真实互补不可互替。
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

PREPRG = os.path.join(ROOT, "prereg_closed_loop_validation_probe_20261129.json")
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


def _sig(name, surface="CLOSED_LOOP_EVAL", validated=True, evidence="", force_class=None):
    d = {"name": name, "surface": surface, "validated": validated, "evidence": evidence}
    if force_class:
        d["force_class"] = force_class
    return d


# G1 预注册 SHA 改码前锁死
def test_01_prereg_sha_locked():
    p = json.load(open(PREPRG, encoding="utf-8"))
    assert p["prereg_id"] == "prereg_closed_loop_validation_probe_20261129"
    assert p["locked_before_code"] is True
    assert p["kernel_sha_before"].startswith("8243f567")
    assert p["function_name"] == "closed_loop_validation_probe"
    assert p["signature"] == "closed_loop_validation_probe(loop_signals=None)"
    assert p["read_only"] is True
    assert p["real_expected"]["expected_flag"] == "ALL_CLOSED_LOOP_VALIDATED"
    assert "404" in p["g6_acceptance"]["new"]
    assert "392" in p["g6_acceptance"]["baseline"]
    assert _sha(PREPRG).startswith("fceca597")


# G2 真实结果 ALL_CLOSED_LOOP_VALIDATED
def test_02_real_all_validated():
    r = K.closed_loop_validation_probe()
    assert r["loop_flag"] == "ALL_CLOSED_LOOP_VALIDATED"
    assert r["counts"]["VALIDATED"] == 6
    assert r["counts"]["OPEN_LOOP_ONLY"] == 0
    assert r["counts"]["PREDICTION_NOT_IN_REGIME"] == 0
    assert r["counts"]["SIM_MASKED_AS_REAL"] == 0
    assert len(r["gap_rows"]) == 0


# G3 精确扫描面：三面六条真实判据
def test_03_exact_scan_surface():
    r = K.closed_loop_validation_probe()
    names = [x["name"] for x in r["rows"]]
    assert names == [
        "metric.open_loop_paired_with_closed_loop",
        "metric.error_propagation_disclosed",
        "regime.same_round_compare",
        "regime.consistency_in_regime",
        "complement.display_and_authority_both",
        "complement.reality_gap_calibrated",
    ]
    surfaces = {x["surface"] for x in r["rows"]}
    assert surfaces == {"CLOSED_LOOP_EVAL", "OPERATING_REGIME", "SIM_REAL_COMPLEMENT"}


# G4 闭环评估真实：开环配闭环落地 + 误差传播双列
def test_04_closed_loop_eval_real():
    r = K.closed_loop_validation_probe()
    assert "synced=0.9091" in r["rows"][0]["evidence"]
    assert "ALL_WRITTEN_THROUGH" in r["rows"][0]["evidence"]
    assert "RESOLVED=1" in r["rows"][0]["evidence"]
    assert "gap=0.7273" in r["rows"][1]["evidence"]


# G5 操作域内验证真实：同Round对拍 + 七件套同域实读
def test_05_operating_regime_real():
    r = K.closed_loop_validation_probe()
    assert "cross_round=CROSS_ROUND_COMPARE" in r["rows"][2]["evidence"]
    assert "seven_readable=7/7" in r["rows"][3]["evidence"]
    assert "文件实读" in r["rows"][3]["evidence"]


# G6 模拟-真实互补真实：展示与权威并列 + 现实鸿沟校正
def test_06_sim_real_complement_real():
    r = K.closed_loop_validation_probe()
    assert "0.9091" in r["rows"][4]["evidence"]
    assert "GAP_INCONCLUSIVE" in r["rows"][4]["evidence"]
    assert "并列互补" in r["rows"][4]["evidence"]
    assert "gap=0.7273" in r["rows"][5]["evidence"]
    assert "归档14条" in r["rows"][5]["evidence"]


# G7 只读字段
def test_07_readonly_fields():
    r = K.closed_loop_validation_probe()
    assert r["verdict_unchanged"] is True
    assert r["consumed"] is False
    assert r["is_gate_verdict"] is False


# G8 负向注入：只报开环预测精度 → OPEN_LOOP_ONLY
def test_08_open_loop_only():
    r = K.closed_loop_validation_probe(loop_signals=[
        _sig("metric.fake_open_loop", surface="CLOSED_LOOP_EVAL", validated=False,
             evidence="prediction accuracy 0.99 reported, no closed-loop landing or recovery")])
    assert r["loop_flag"] == "CLOSED_LOOP_GAP_PRESENT"
    assert r["counts"]["OPEN_LOOP_ONLY"] == 1
    assert r["rows"][0]["class"] == "OPEN_LOOP_ONLY"


# G9 负向注入：跨Round各自单判 → PREDICTION_NOT_IN_REGIME
def test_09_prediction_not_in_regime():
    r = K.closed_loop_validation_probe(loop_signals=[
        _sig("regime.fake_cross_round", surface="OPERATING_REGIME", validated=False,
             force_class="PREDICTION_NOT_IN_REGIME",
             evidence="each round judged separately, no same-round operating-regime compare")])
    assert r["loop_flag"] == "CLOSED_LOOP_GAP_PRESENT"
    assert r["counts"]["PREDICTION_NOT_IN_REGIME"] == 1
    assert r["rows"][0]["class"] == "PREDICTION_NOT_IN_REGIME"


# G10 负向注入：模拟刷绿冒充真实 → SIM_MASKED_AS_REAL；全通过与空注入边界
def test_10_sim_masked_and_boundaries():
    r = K.closed_loop_validation_probe(loop_signals=[
        _sig("complement.fake_sim", surface="SIM_REAL_COMPLEMENT",
             force_class="SIM_MASKED_AS_REAL",
             evidence="simulation reads perfect, masked as real-world verdict without authority read")])
    assert r["loop_flag"] == "CLOSED_LOOP_GAP_PRESENT"
    assert r["counts"]["SIM_MASKED_AS_REAL"] == 1
    r_all = K.closed_loop_validation_probe(loop_signals=[
        _sig("f1"), _sig("f2", surface="OPERATING_REGIME")])
    assert r_all["loop_flag"] == "ALL_CLOSED_LOOP_VALIDATED"
    assert r_all["counts"]["VALIDATED"] == 2
    r_empty = K.closed_loop_validation_probe(loop_signals=[])
    assert r_empty["loop_flag"] == "NO_LOOP_CLAIM"
    assert "判定权归用户" in r_empty["one_page"]


# G11 honesty 边界（无物理AI/不宣称/概念综述非基准/非全赢同构/标注非裁定）
def test_11_honesty_boundary():
    h = K.closed_loop_validation_probe()["honesty"]
    for frag in ("无物理世界", "不宣称真实物理AI能力", "概念综述非实证基准",
                 "不冒充已证基准", "预测精度≠决策效用", "模拟≠真实", "开环≠闭环",
                 "结构镜非内核真实属性", "标注非裁定", "判定权归用户"):
        assert frag in h, frag
    b = K.closed_loop_validation_probe()["based_on"]
    assert "2610.27045" in b
    assert "51作者" in b
    assert "fceca597" in b


# G12 调用前后权威态七件套零字节副作用 + 哈希等于基线
def test_12_authority_seven_zero_side_effect():
    before = _seven_snapshot()
    K.closed_loop_validation_probe()
    K.closed_loop_validation_probe(loop_signals=[
        _sig("x", surface="SIM_REAL_COMPLEMENT", force_class="SIM_MASKED_AS_REAL")])
    after = _seven_snapshot()
    assert before == after
    for rel, prefix in zip(SEVEN, SEVEN_BASELINE):
        assert _sha(os.path.join(ROOT, rel)).startswith(prefix), rel
