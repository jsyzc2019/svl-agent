"""§4S90 write_through_probe 的 12 守卫（G3 负向注入 + 只读 + 权威态零副作用）。

借知乎 BF16 主权舍入帖与 Stanford Fair Cast 的锋利镜面：
看板正常≠状态写穿；对拍不得在同一舍入下游；只读不得留半步字节。
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

PREPRG = os.path.join(ROOT, "prereg_write_through_probe_20261128.json")
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


def _sig(name, surface="WRITE_THROUGH", written=True, evidence="", force_class=None):
    d = {"name": name, "surface": surface, "written": written, "evidence": evidence}
    if force_class:
        d["force_class"] = force_class
    return d


# G1 预注册 SHA 改码前锁死
def test_01_prereg_sha_locked():
    p = json.load(open(PREPRG, encoding="utf-8"))
    assert p["kernel_sha_before"].startswith("d715d6e7")
    assert p["function"] == "write_through_probe(write_signals=None)"
    assert p["pure_additive"] is True
    assert p["g6_expect"]["new_kernel_tests_collected"] == 344
    assert p["g6_expect"]["baseline_tests_collected"] == 332
    assert _sha(PREPRG).startswith("e80b3d04")


# G2 真实结果 ALL_WRITTEN_THROUGH
def test_02_real_all_written_through():
    r = K.write_through_probe()
    assert r["write_flag"] == "ALL_WRITTEN_THROUGH"
    assert r["counts"]["WRITTEN_THROUGH"] == 5
    assert r["counts"]["SHOW_ONLY"] == 0
    assert r["counts"]["SAME_SIDE_COMPARE"] == 0
    assert r["counts"]["HALF_STEP_WRITE"] == 0
    assert len(r["gap_rows"]) == 0


# G3 精确扫描面：三面五条真实判据
def test_03_exact_scan_surface():
    r = K.write_through_probe()
    names = [x["name"] for x in r["rows"]]
    assert names == [
        "show.synced_rate_has_authority_dual",
        "show.stale_rate_has_authority_count",
        "show.abstention_has_authority_count",
        "compare.cross_round_points",
        "halfstep.authority_seven_unchanged",
    ]
    surfaces = {x["surface"] for x in r["rows"]}
    assert surfaces == {"WRITE_THROUGH", "CROSS_ROUND_COMPARE", "HALF_STEP_NO_WRITE"}


# G4 展示读数必须有权威对偶：synced_rate 配 authentic=2/11
def test_04_synced_rate_has_authority_dual():
    r = K.write_through_probe()
    row = r["rows"][0]
    assert "synced_rate=0.9091" in row["evidence"]
    assert "authentic=2/11" in row["evidence"]
    assert "backfilled=8" in row["evidence"]
    assert "GAP_INCONCLUSIVE" in row["evidence"]


# G5 权威态实读非探针自报（verdict 来自文件）
def test_05_authority_read_from_file():
    r = K.write_through_probe()
    auth = json.load(open(os.path.join(ROOT, "authoritative_state.json"), encoding="utf-8"))
    assert auth["verdict"] == "GAP_INCONCLUSIVE"
    assert "GAP_INCONCLUSIVE" in r["one_page"]
    assert len(r["authority_seven_sha"]) == 7
    assert all(v != "UNREADABLE" for v in r["authority_seven_sha"].values())


# G6 只读字段
def test_06_readonly_fields():
    r = K.write_through_probe()
    assert r["verdict_unchanged"] is True
    assert r["consumed"] is False
    assert r["is_gate_verdict"] is False


# G7 负向注入：看板高但无权威对偶 → SHOW_ONLY
def test_07_show_only_without_authority_dual():
    r = K.write_through_probe(write_signals=[
        _sig("show.fake", written=False, evidence="synced_rate=1.0 no authentic count")])
    assert r["write_flag"] == "WRITE_GAP_PRESENT"
    assert r["counts"]["SHOW_ONLY"] == 1
    assert r["rows"][0]["class"] == "SHOW_ONLY"


# G8 负向注入：同一舍入下游对拍 → SAME_SIDE_COMPARE
def test_08_same_side_compare():
    r = K.write_through_probe(write_signals=[
        _sig("compare.both_downstream", surface="CROSS_ROUND_COMPARE",
             force_class="SAME_SIDE_COMPARE",
             evidence="trainer_bf16 vs sampler_bf16 both after round")])
    assert r["write_flag"] == "WRITE_GAP_PRESENT"
    assert r["counts"]["SAME_SIDE_COMPARE"] == 1
    assert r["rows"][0]["class"] == "SAME_SIDE_COMPARE"


# G9 负向注入：半步写入 → HALF_STEP_WRITE
def test_09_half_step_write():
    r = K.write_through_probe(write_signals=[
        _sig("halfstep.mutated", surface="HALF_STEP_NO_WRITE",
             force_class="HALF_STEP_WRITE",
             evidence="authoritative_state.json byte changed after read")])
    assert r["write_flag"] == "WRITE_GAP_PRESENT"
    assert r["counts"]["HALF_STEP_WRITE"] == 1
    assert r["rows"][0]["class"] == "HALF_STEP_WRITE"


# G10 全写穿 + 空注入边界
def test_10_all_written_and_empty_injection():
    r_all = K.write_through_probe(write_signals=[
        _sig("w1", written=True), _sig("w2", written=True)])
    assert r_all["write_flag"] == "ALL_WRITTEN_THROUGH"
    assert r_all["counts"]["WRITTEN_THROUGH"] == 2
    r_empty = K.write_through_probe(write_signals=[])
    assert r_empty["write_flag"] == "NO_WRITE_CLAIM"
    assert "判定权归用户" in r_empty["one_page"]


# G11 honesty 边界（非RL/不宣称收益/归因非受控/标注非裁定/一手源）
def test_11_honesty_boundary():
    h = K.write_through_probe()["honesty"]
    for frag in ("无梯度/权重/浮点舍入", "不宣称真实BF16死区", "不冒充已证因果",
                 "隐式正则", "标注非裁定", "arXiv 2610.41073", "判定权归用户"):
        assert frag in h, frag
    b = K.write_through_probe()["based_on"]
    assert "p/2109289366338138518" in b
    assert "torch2.10" in b


# G12 调用前后权威态七件套零字节副作用
def test_12_authority_seven_zero_side_effect():
    before = _seven_snapshot()
    K.write_through_probe()
    K.write_through_probe(write_signals=[_sig("x", written=False)])
    after = _seven_snapshot()
    assert before == after
    # 与预注册基线逐一比对
    p = json.load(open(PREPRG, encoding="utf-8"))
    for rel, sha in p["authority_seven_before"].items():
        assert _sha(os.path.join(ROOT, rel)) == sha, rel
