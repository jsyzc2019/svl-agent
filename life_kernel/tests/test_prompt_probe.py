"""§4S91 prompt_probe 的 12 守卫（G3 负向注入 + 只读 + 权威态零副作用）。

借 arXiv 2610.34051 BEHAVIOR-Spatial 的锋利镜面：
任务成功≠指令被遵循；目标切换响应性；soft/strict/wrong 三分离；oracle注入≠grounding。
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

PREPRG = os.path.join(ROOT, "prereg_prompt_probe_20261128.json")
SEVEN = [
    "authoritative_state.json",
    "life_kernel/constitution.sha256",
    "life_kernel/data/heartbeat_log.jsonl",
    "life_kernel/data/inbound_inbox.jsonl",
    "DECISIONS_20261127.json",
    "gap_archive_20261128.json",
    "knowledge_base_store.json",
]


def _sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def _seven_snapshot():
    return {rel: _sha(os.path.join(ROOT, rel)) for rel in SEVEN}


def _sig(name, surface="RESPONSIVENESS", responsive=True, source="generated",
         evidence="", force_class=None):
    d = {"name": name, "surface": surface, "responsive": responsive,
         "source": source, "evidence": evidence}
    if force_class:
        d["force_class"] = force_class
    return d


# G1 预注册 SHA 改码前锁死
def test_01_prereg_sha_locked():
    p = json.load(open(PREPRG, encoding="utf-8"))
    assert p["kernel_sha_before"].startswith("5da5b75d")
    assert p["function"] == "prompt_probe(prompt_signals=None)"
    assert p["pure_additive"] is True
    assert p["g6_expect"]["new_kernel_tests_collected"] == 356
    assert p["g6_expect"]["baseline_tests_collected"] == 344
    assert _sha(PREPRG).startswith("d2e7e1fc")


# G2 真实结果 INSTRUCTION_FOLLOWED
def test_02_real_instruction_followed():
    r = K.prompt_probe()
    assert r["prompt_flag"] == "INSTRUCTION_FOLLOWED"
    assert r["counts"]["INSTRUCTION_FOLLOWED"] == 4
    assert r["counts"]["DEFAULT_PATH"] == 0
    assert r["counts"]["MASKED_BY_SOFT"] == 0
    assert r["counts"]["ORACLE_MISLABELED"] == 0
    assert len(r["gap_rows"]) == 0


# G3 精确扫描面：三面四条真实判据
def test_03_exact_scan_surface():
    r = K.prompt_probe()
    names = [x["name"] for x in r["rows"]]
    assert names == [
        "responsive.anchor_set_nonempty",
        "responsive.no_default_path_noise",
        "outcome.soft_strict_wrong_split",
        "oracle.no_injected_anchor",
    ]
    surfaces = {x["surface"] for x in r["rows"]}
    assert surfaces == {"RESPONSIVENESS", "OUTCOME_SPLIT", "ORACLE_VS_GROUNDED"}


# G4 锚点集真实：3用户+1归档，噪音=0
def test_04_anchor_set_real():
    r = K.prompt_probe()
    row = r["rows"][0]
    assert "anchors=4 user=3 archive=1" in row["evidence"]
    row2 = r["rows"][1]
    assert "UNRECOGNIZED_NOISE=0" in row2["evidence"]


# G5 soft/strict/wrong 三分离真实对偶落地
def test_05_outcome_split_real():
    r = K.prompt_probe()
    row = r["rows"][2]
    assert "soft=0.9091" in row["evidence"]
    assert "strict=2" in row["evidence"]
    assert "wrong=8" in row["evidence"]
    assert "total=11" in row["evidence"]


# G6 只读字段
def test_06_readonly_fields():
    r = K.prompt_probe()
    assert r["verdict_unchanged"] is True
    assert r["consumed"] is False
    assert r["is_gate_verdict"] is False
    assert r["injected"] is False


# G7 负向注入：默认熟悉路径(请求目标不在锚点集仍判已识别) → DEFAULT_PATH
def test_07_default_path():
    r = K.prompt_probe(prompt_signals=[
        _sig("responsive.fake", responsive=False,
             evidence="request target not in anchor set but still recognized")])
    assert r["prompt_flag"] == "INSTRUCTION_GAP_PRESENT"
    assert r["counts"]["DEFAULT_PATH"] == 1
    assert r["rows"][0]["class"] == "DEFAULT_PATH"


# G8 负向注入：只报soft不报strict+wrong → MASKED_BY_SOFT
def test_08_masked_by_soft():
    r = K.prompt_probe(prompt_signals=[
        _sig("outcome.soft_only", surface="OUTCOME_SPLIT", responsive=False,
             evidence="synced_rate=1.0 but no strict/wrong split")])
    assert r["prompt_flag"] == "INSTRUCTION_GAP_PRESENT"
    assert r["counts"]["MASKED_BY_SOFT"] == 1
    assert r["rows"][0]["class"] == "MASKED_BY_SOFT"


# G9 负向注入：oracle注入却标generated冒充源头grounding → ORACLE_MISLABELED
def test_09_oracle_mislabeled():
    r = K.prompt_probe(prompt_signals=[
        _sig("oracle.fake_grounded", surface="ORACLE_VS_GROUNDED", responsive=True,
             source="oracle", evidence="injected oracle target labeled as generated")])
    assert r["prompt_flag"] == "INSTRUCTION_GAP_PRESENT"
    assert r["counts"]["ORACLE_MISLABELED"] == 1
    assert r["rows"][0]["class"] == "ORACLE_MISLABELED"


# G10 全跟随 + 空注入边界
def test_10_all_followed_and_empty_injection():
    r_all = K.prompt_probe(prompt_signals=[
        _sig("f1", responsive=True), _sig("f2", surface="OUTCOME_SPLIT", responsive=True)])
    assert r_all["prompt_flag"] == "INSTRUCTION_FOLLOWED"
    assert r_all["counts"]["INSTRUCTION_FOLLOWED"] == 2
    assert r_all["injected"] is True
    r_empty = K.prompt_probe(prompt_signals=[])
    assert r_empty["prompt_flag"] == "NO_PROMPT_CLAIM"
    assert "判定权归用户" in r_empty["one_page"]


# G11 honesty 边界（非机器人/不宣称空间理解/主页404降级/仿真不可部署/标注非裁定/arXiv源）
def test_11_honesty_boundary():
    h = K.prompt_probe()["honesty"]
    for frag in ("无机器人", "空间场景/梯度", "不宣称真实空间理解", "GitHub Pages 404",
                 "不可解读为真实部署证据", "标注非裁定", "arXiv 2610.34051", "判定权归用户"):
        assert frag in h, frag
    b = K.prompt_probe()["based_on"]
    assert "2610.34051" in b
    assert "Fei-Fei" in b and "Wu J." in b


# G12 调用前后权威态七件套零字节副作用
def test_12_authority_seven_zero_side_effect():
    before = _seven_snapshot()
    K.prompt_probe()
    K.prompt_probe(prompt_signals=[_sig("x", responsive=False)])
    after = _seven_snapshot()
    assert before == after
    p = json.load(open(PREPRG, encoding="utf-8"))
    for rel, sha in p["authority_seven_before"].items():
        assert _sha(os.path.join(ROOT, rel)) == sha, rel
