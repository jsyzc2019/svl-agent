"""§111 AST 准入规则对偶测试（spawn 前锁定）。

证明 v2 规则是"精确到控制流"的修订而非对着结果放水：
- 真泄漏（控制流读取标签字段/载体）→ 必须拒绝
- 误报场景（notes/signals 字符串里提 negation/variant，或普通词表里含这些词）→ 必须放行
- §110 三份旧 judge → 新规则应放行（证明确实是修误报，而非换个规则塞私货）
"""
import os, sys, json, hashlib

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "audit_admission_ast_audit")
sys.path.insert(0, BASE)
from admission_v2 import admit_source

JUDGE_OK = '''
import re
_LIMITERS = {"not", "no", "negation", "only"}
def judge(text_a, text_b):
    notes = []
    wa = set(re.findall(r"[a-z]+", text_a.lower()))
    wb = set(re.findall(r"[a-z]+", text_b.lower()))
    missing = _LIMITERS & wa - wb
    if missing:
        notes.append("negation terms present in text_a but absent in text_b: " + ", ".join(missing))
        return False, ["missing"], notes
    notes.append("deletion variant not detected")
    return True, ["ok"], notes
'''

LEAK_SUBSCRIPT = '''
def judge(text_a, text_b):
    return scorer_key["gt"], [], []
'''
LEAK_ATTR = '''
def judge(text_a, text_b):
    return SAMPLE.variant, [], []
'''
LEAK_CALL = '''
def judge(text_a, text_b):
    return load_gt(text_a) == text_b, [], []
'''
LEAK_ID = '''
def judge(text_a, text_b):
    if "N07" in text_a: return True, [], []
    return False, [], []
'''
LEAK_RNG = '''
import random
def judge(text_a, text_b):
    return random.random() > 0.5, [], []
'''
LEAK_IO = '''
def judge(text_a, text_b):
    f = open("gt.txt")
    return f.read() == text_a, [], []
'''


def test_true_leaks_all_rejected():
    for name, src in [("subscript", LEAK_SUBSCRIPT), ("attr", LEAK_ATTR), ("call", LEAK_CALL),
                      ("id", LEAK_ID), ("rng", LEAK_RNG), ("io", LEAK_IO)]:
        r = admit_source(src)
        assert r["admission_ok"] is False, f"{name} 真泄漏应被拒，却放行: {r}"


def test_notes_mention_is_allowed():
    r = admit_source(JUDGE_OK)
    assert r["admission_ok"] is True, f"仅 notes 提 negation/variant 不应判泄漏: {r}"
    assert r["signature_ok"] is True


def test_old_110_judges_pass_v2():
    """§110 三份旧 judge 在新规则下应全放行——证明是修误报，非塞私货。"""
    old = os.path.join(os.path.dirname(BASE), "audit_cross_vendor_evaluator")
    for c in ("P0", "P1", "P2"):
        src = open(f"{old}/vendor_{c}/judge_vendor.py", encoding="utf-8").read()
        r = admit_source(src)
        assert r["admission_ok"] is True, f"{c} 在 v2 下应放行: {r}"


def test_rule_module_hash_locked():
    """规则模块本身在 prereg 中锁哈希，spawn 后不得改动。"""
    p = json.load(open(f"{BASE}/prereg.json", encoding="utf-8"))
    locked = p["locked_files_sha256"]["admission_v2.py"]
    actual = hashlib.sha256(open(f"{BASE}/admission_v2.py", "rb").read()).hexdigest()
    assert actual == locked, "admission_v2.py 与预注册哈希不符——规则被事后改动"


def test_pending_state_no_forged_verdict():
    r = json.load(open(f"{BASE}/result.json", encoding="utf-8"))
    if r["status"] == "PRE_REGISTERED_AWAITING_SPAWN":
        assert "verdict" not in r
        assert r["missing_judges"] == ["P0", "P1", "P2"]
        for c in ("P0", "P1", "P2"):
            assert not os.path.exists(f"{BASE}/vendor_{c}/judge_vendor.py")


def test_verify_pending_all_ok():
    import subprocess
    p = subprocess.run(["python3", f"{BASE}/verify.py"], capture_output=True, text=True)
    assert p.returncode == 0
    assert "ALL_OK" in p.stdout


def test_verdict_rules_locked_four_tiers():
    p = json.load(open(f"{BASE}/prereg.json", encoding="utf-8"))
    joined = " ".join(p["verdict_rules"])
    for tier in ("AST_V2_CONFIRMED", "AST_V2_PARTIAL", "AST_V2_REFUTED", "AST_V2_INCONCLUSIVE"):
        assert tier in joined


def test_prereg_declares_no_overturn_110():
    """诚实边界：prereg 必须声明不翻 §110 案。"""
    p = json.load(open(f"{BASE}/prereg.json", encoding="utf-8"))
    assert p["does_not_overturn"]
    assert "CROSS_VENDOR_INCONCLUSIVE" in p["does_not_overturn"]
    assert p["l3_claimed"] is False and p["absolute_claimed"] is False
