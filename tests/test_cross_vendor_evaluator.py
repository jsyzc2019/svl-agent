"""§110 异厂商 designer 受控验证管线测试（验证工具逻辑，不改门禁/不放宽断言）。"""
import json, hashlib, os, subprocess

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "audit_cross_vendor_evaluator")
CELLS = ("P0", "P1", "P2")


def load(p): return json.load(open(p, encoding="utf-8"))
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()


def test_prereg_locks_frozen_before_vendor_spawn():
    p = load(f"{BASE}/prereg.json")
    assert p["locked_before_vendor_spawn"] is True
    assert p["l3_claimed"] is False and p["absolute_claimed"] is False
    assert sha(f"{BASE}/prereg.json") == open(f"{BASE}/prereg.sha256").read().strip()


def test_frozen_samples_identical_to_107():
    p = load(f"{BASE}/prereg.json")
    target = p["held_fixed_from_107"]["samples_blind_sha256"]
    shas = {sha(f"{BASE}/vendor_{c}/samples_blind.json") for c in CELLS}
    assert len(shas) == 1 and shas.pop() == target
    # 与 §107 实际存档样本逐字节一致
    ref = hashlib.sha256(open(
        os.path.join(os.path.dirname(BASE), "audit_stratified_confirmation", "designer_P1", "samples_blind.json"),
        "rb").read()).hexdigest()
    assert ref == target


def test_scorer_key_never_in_vendor_prompt():
    """裸样本只含 id/text_a/text_b；purpose 不含 gt/deletion_class/orig_id。"""
    for c in CELLS:
        s = load(f"{BASE}/vendor_{c}/samples_blind.json")["samples"]
        for row in s:
            assert set(row.keys()) == {"id", "text_a", "text_b"}, f"{c} leaked fields: {row.keys()}"
        purpose = open(f"{BASE}/vendor_{c}/purpose.md", encoding="utf-8").read()
        for tok in ("deletion_class", "ground_truth", "orig_id", "scorer_key", "negation_flip"):
            assert tok not in purpose


def test_purpose_single_variable():
    """三条件 purpose 各异但技术要求段逐字一致（单变量=目的语义）。"""
    purposes = {c: open(f"{BASE}/vendor_{c}/purpose.md", encoding="utf-8").read() for c in CELLS}
    assert len(set(purposes.values())) == 3
    tail = "要求：纯字符串/正则实现，确定性；不使用随机数、时间、样本 id、外部文件或样本文本硬编码。"
    for c in CELLS:
        assert tail in purposes[c]


def test_pending_state_has_no_forged_verdict():
    r = load(f"{BASE}/result.json")
    if r["status"] == "PENDING_API_KEY":
        assert "verdict" not in r
        assert r["missing_judges"] == list(CELLS)
        for c in CELLS:
            assert not os.path.exists(f"{BASE}/vendor_{c}/judge_vendor.py")


def test_verify_pending_all_ok():
    p = subprocess.run(["python3", f"{BASE}/verify.py"], capture_output=True, text=True)
    assert p.returncode == 0
    assert "ALL_OK" in p.stdout


def test_call_vendor_never_writes_key():
    """调用器只从环境变量读 key，源码里不得有硬编码 key 或写 key 到盘的逻辑。"""
    src = open(f"{BASE}/call_vendor.py", encoding="utf-8").read()
    assert "os.environ.get(\"CROSS_VENDOR_API_KEY\"" in src
    assert "ghp_" not in src
    # 留痕写入内容不含 API_KEY 变量
    assert "API_KEY" not in src.split("json.dumps(manifest")[1].split(")")[0]


def test_verdict_rules_locked_four_tiers():
    p = load(f"{BASE}/prereg.json")
    joined = " ".join(p["verdict_rules"])
    for tier in ("CROSS_VENDOR_CONFIRMED", "CROSS_VENDOR_PARTIAL", "CROSS_VENDOR_REFUTED", "CROSS_VENDOR_INCONCLUSIVE"):
        assert tier in joined
