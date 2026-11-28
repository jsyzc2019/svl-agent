"""§4S96 diffusion_of_responsibility_probe 的 12 守卫（G3 负向注入 + 只读 + 权威态零副作用）。

借 arXiv 2611.17820 Aligning AI Teams (Srinivasan/Matthews/Sohl-Dickstein/Jones) 的锋利镜面：
责任扩散两阶段失守(discovery/action) + 响应前置依赖(discovered=1) + 逐字证据 + 四分离
+ distributed responsibility 无效 / designated safety lead + 只读 spec 才可靠。
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

PREPRG = os.path.join(ROOT, "prereg_diffusion_of_responsibility_probe_20261128.json")
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


def _sig(name, surface="DISCOVERY", owned=True, evidence="", force_class=None):
    d = {"name": name, "surface": surface, "owned": owned, "evidence": evidence}
    if force_class:
        d["force_class"] = force_class
    return d


# G1 预注册 SHA 改码前锁死
def test_01_prereg_sha_locked():
    p = json.load(open(PREPRG, encoding="utf-8"))
    assert p["prereg_id"] == "prereg_diffusion_of_responsibility_probe_20261128"
    assert p["locked_before_code"] is True
    assert p["kernel_sha_before"].startswith("4f49bdd7")
    assert p["function_name"] == "diffusion_of_responsibility_probe"
    assert p["signature"] == "diffusion_of_responsibility_probe(dor_signals=None)"
    assert p["read_only"] is True
    assert p["real_expected"]["expected_flag"] == "ALL_OWNED"
    assert "392" in p["g6_acceptance"]["new"]
    assert "380" in p["g6_acceptance"]["baseline"]
    assert _sha(PREPRG).startswith("9f60aa1b")


# G2 真实结果 ALL_OWNED
def test_02_real_all_owned():
    r = K.diffusion_of_responsibility_probe()
    assert r["dor_flag"] == "ALL_OWNED"
    assert r["counts"]["OWNED"] == 6
    assert r["counts"]["DISCOVERY_NOT_TESTED"] == 0
    assert r["counts"]["RESPONSE_MASKED"] == 0
    assert r["counts"]["OWNERSHIP_DIFFUSED"] == 0
    assert len(r["gap_rows"]) == 0


# G3 精确扫描面：三面六条真实判据
def test_03_exact_scan_surface():
    r = K.diffusion_of_responsibility_probe()
    names = [x["name"] for x in r["rows"]]
    assert names == [
        "discovery.end_to_end_real_read",
        "discovery.harm_disclosed",
        "response.precondition_dependency",
        "response.four_way_separated",
        "ownership.designated_authority",
        "ownership.readonly_spec",
    ]
    surfaces = {x["surface"] for x in r["rows"]}
    assert surfaces == {"DISCOVERY", "RESPONSE", "OWNERSHIP"}


# G4 发现阶段真实：七件套实读 + harm显式暴露
def test_04_discovery_real():
    r = K.diffusion_of_responsibility_probe()
    assert "seven_readable=7/7" in r["rows"][0]["evidence"]
    assert "文件实读" in r["rows"][0]["evidence"]
    assert "GAP_INCONCLUSIVE" in r["rows"][1]["evidence"]


# G5 响应阶段真实：逐字证据前置 + 四类分离
def test_05_response_real():
    r = K.diffusion_of_responsibility_probe()
    assert "entries=14" in r["rows"][2]["evidence"]
    assert "evidence_fields" in r["rows"][2]["evidence"]
    assert "A=13" in r["rows"][3]["evidence"]
    assert "I=9" in r["rows"][3]["evidence"]
    assert "R=1" in r["rows"][3]["evidence"]


# G6 责任归属真实：单一指定权威 + 只读spec
def test_06_ownership_real():
    r = K.diffusion_of_responsibility_probe()
    assert "判定权归用户" in r["rows"][4]["evidence"]
    assert "constitution.sha256锁在位" in r["rows"][5]["evidence"]


# G7 只读字段
def test_07_readonly_fields():
    r = K.diffusion_of_responsibility_probe()
    assert r["verdict_unchanged"] is True
    assert r["consumed"] is False
    assert r["is_gate_verdict"] is False


# G8 负向注入：没跑端到端/只读旁证 → DISCOVERY_NOT_TESTED
def test_08_discovery_not_tested():
    r = K.diffusion_of_responsibility_probe(dor_signals=[
        _sig("discovery.fake_only_read_report", surface="DISCOVERY", owned=False,
             evidence="only read another agent's decisions.csv, never ran integrated pipeline")])
    assert r["dor_flag"] == "RESPONSIBILITY_DIFFUSED"
    assert r["counts"]["DISCOVERY_NOT_TESTED"] == 1
    assert r["rows"][0]["class"] == "DISCOVERY_NOT_TESTED"


# G9 负向注入：无逐字证据仍声称已处置 → RESPONSE_MASKED
def test_09_response_masked():
    r = K.diffusion_of_responsibility_probe(dor_signals=[
        _sig("response.fake_no_evidence", surface="RESPONSE", owned=False,
             force_class="RESPONSE_MASKED",
             evidence="claimed attempted_fix with no discovered=1 and no verbatim quote")])
    assert r["dor_flag"] == "RESPONSIBILITY_DIFFUSED"
    assert r["counts"]["RESPONSE_MASKED"] == 1
    assert r["rows"][0]["class"] == "RESPONSE_MASKED"


# G10 负向注入：人人自证冒充系统级负责 → OWNERSHIP_DIFFUSED；全就位与空注入边界
def test_10_ownership_diffused_and_boundaries():
    r = K.diffusion_of_responsibility_probe(dor_signals=[
        _sig("ownership.fake_distributed", surface="OWNERSHIP",
             force_class="OWNERSHIP_DIFFUSED",
             evidence="every agent self-reports verdict_unchanged; no designated authority")])
    assert r["dor_flag"] == "RESPONSIBILITY_DIFFUSED"
    assert r["counts"]["OWNERSHIP_DIFFUSED"] == 1
    r_all = K.diffusion_of_responsibility_probe(dor_signals=[
        _sig("f1"), _sig("f2", surface="RESPONSE")])
    assert r_all["dor_flag"] == "ALL_OWNED"
    assert r_all["counts"]["OWNED"] == 2
    r_empty = K.diffusion_of_responsibility_probe(dor_signals=[])
    assert r_empty["dor_flag"] == "NO_DOR_CLAIM"
    assert "判定权归用户" in r_empty["one_page"]


# G11 honesty 边界（无多agent/不宣称对齐/只研Claude/非全赢/人人负责同构/标注非裁定）
def test_11_honesty_boundary():
    h = K.diffusion_of_responsibility_probe()["honesty"]
    for frag in ("无多agent团队", "不宣称", "真实对齐恢复", "只研究Anthropic Claude家族",
                 "safety doc单独无效", "gap不单调", "非全赢诚实标注",
                 "人人负责", "既有纪律非本探针新设", "标注非裁定", "判定权归用户"):
        assert frag in h, frag
    b = K.diffusion_of_responsibility_probe()["based_on"]
    assert "2611.17820" in b
    assert "478 blobs真开源" in b
    assert "9f60aa1b" in b


# G12 调用前后权威态七件套零字节副作用 + 哈希等于基线
def test_12_authority_seven_zero_side_effect():
    before = _seven_snapshot()
    K.diffusion_of_responsibility_probe()
    K.diffusion_of_responsibility_probe(dor_signals=[
        _sig("x", surface="OWNERSHIP", force_class="OWNERSHIP_DIFFUSED")])
    after = _seven_snapshot()
    assert before == after
    for rel, prefix in zip(SEVEN, SEVEN_BASELINE):
        assert _sha(os.path.join(ROOT, rel)).startswith(prefix), rel
