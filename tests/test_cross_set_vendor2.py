"""§113 跨集×跨厂商 2×2 闭合验证测试。

待命态：锁完好、规则与 §111/§112 逐字节一致、确认集=第二集（非主集）、无伪造 judge、不翻四案。
执行态：跨厂商+第二集前提成立、AST 准入全过、verdict 与裁决树一致、l3 未抬级、key 零泄漏。
"""
import os, hashlib, subprocess

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "audit_cross_set_vendor2")
CELLS = ("P0", "P1", "P2")
SECOND_SHA = "82c9966b990a9b641bf7e4e36f397115e6e2284893480bf2967e6193221cd2e8"
MAIN_SHA = "e7a65f4d2df068d799040a3c0cd5f06ead87cc01584558a66aa5bcfc22c4252a"


def load(p): return __import__("json").load(open(p, encoding="utf-8"))
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()


def test_rule_byte_identical_to_111_112():
    root = os.path.dirname(BASE)
    for d in ("audit_admission_ast_audit", "audit_cross_vendor_designer2"):
        assert sha(f"{BASE}/admission_v2.py") == sha(os.path.join(root, d, "admission_v2.py"))
    assert sha(f"{BASE}/admission_v2.py") == load(f"{BASE}/prereg.json")["locked_files_sha256"]["admission_v2.py"]


def test_frozen_inputs_are_second_set():
    """核心：确认集必须是 §108 第二集，不是主集（2×2 格不错）。"""
    for c in CELLS:
        s = sha(f"{BASE}/vendor_{c}/samples_blind.json")
        assert s == SECOND_SHA and s != MAIN_SHA
    assert sha(f"{BASE}/scorer_key.json") == load(f"{BASE}/prereg.json")["what_is_HELD_FIXED"]["scorer_key_sha256"]
    # 样本与 §108 第二集逐字节一致
    root = os.path.dirname(BASE)
    assert sha(f"{BASE}/vendor_P0/samples_blind.json") == sha(os.path.join(root, "audit_cross_domain_confirm2", "designer_P0", "samples_blind.json"))


def test_prereg_declares_matrix_and_no_overturn():
    p = load(f"{BASE}/prereg.json")
    assert "2×2" in p["experiment"]
    assert p["l3_claimed"] is False and p["absolute_claimed"] is False
    dnot = p["does_not_overturn"]
    for x in ("STRATIFIED_CONFIRMED", "CROSS_SET_PARTIAL", "AST_V2_PARTIAL", "CROSS_VENDOR2_PARTIAL"):
        assert x in dnot
    joined = " ".join(p["verdict_rules"])
    for t in ("SET_VENDOR2_CONFIRMED", "SET_VENDOR2_PARTIAL", "SET_VENDOR2_REFUTED", "SET_VENDOR2_INCONCLUSIVE"):
        assert t in joined


def test_pending_state_no_forged_verdict():
    r = load(f"{BASE}/result.json")
    if r["status"] == "PRE_REGISTERED_AWAITING_SPAWN":
        assert "verdict" not in r
        assert r["missing_judges"] == list(CELLS)
        for c in CELLS:
            assert not os.path.exists(f"{BASE}/vendor_{c}/judge_vendor.py")


def test_verify_all_ok():
    p = subprocess.run(["python3", f"{BASE}/verify.py"], capture_output=True, text=True)
    assert p.returncode == 0
    assert "ALL_OK" in p.stdout


def test_executed_premises_and_verdict():
    r = load(f"{BASE}/result.json")
    if r.get("status") != "EXECUTED":
        return
    assert r["l3_claimed"] is False and r["absolute_claimed"] is False
    assert r["locks_ok"] is True and r["all_admissions_pass"] is True
    assert r["vendor_cross_vendor_ok"] is True   # Liquid AI
    assert r["second_set_confirmed"] is True     # 第二集
    assert r["samples_blind_sha256"] == SECOND_SHA
    assert r["verdict"] in ("SET_VENDOR2_CONFIRMED", "SET_VENDOR2_PARTIAL",
                            "SET_VENDOR2_REFUTED", "SET_VENDOR2_INCONCLUSIVE")
    assert "does_not_overturn" in r


def test_executed_judges_match_manifest():
    mpath = f"{BASE}/runs/vendor_call_manifest.json"
    if not os.path.exists(mpath):
        return
    m = load(mpath)
    for c in CELLS:
        rec = m["calls"][c]
        assert rec["status"] == "ok"
        assert rec["finish_reason"] in ("stop", "length")
        if rec["finish_reason"] == "length":
            assert rec.get("code_source") == "reasoning_fallback"
        jp = f"{BASE}/vendor_{c}/judge_vendor.py"
        assert os.path.exists(jp)
        assert sha(jp) == rec["judge_sha256"]


def test_no_key_leak_in_workspace():
    import re
    root = os.path.dirname(BASE)
    pat = re.compile(r"sk-or-v1-[A-Za-z0-9]{20,}")
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != ".git" and not d.startswith("__pycache__")]
        for fn in files:
            if not fn.endswith((".py", ".json", ".md", ".sha256", ".txt")):
                continue
            p = os.path.join(dirpath, fn)
            try: t = open(p, encoding="utf-8", errors="ignore").read()
            except Exception: continue
            assert not pat.search(t), f"疑似 key 泄漏: {p}"
