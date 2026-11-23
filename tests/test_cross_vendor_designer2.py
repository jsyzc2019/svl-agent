"""§112 真正跨厂商 designer 交叉验证测试。

待命态：锁完好、规则与 §111 逐字节一致、无伪造 judge、prereg 声明不翻 §110/§111。
执行态：跨厂商前提成立、AST 准入全过、verdict 与裁决树一致、l3 未抬级、key 零泄漏。
"""
import os, sys, json, hashlib, subprocess

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "audit_cross_vendor_designer2")
S111 = os.path.join(os.path.dirname(BASE), "audit_admission_ast_audit")
CELLS = ("P0", "P1", "P2")


def load(p): return json.load(open(p, encoding="utf-8"))
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()


def test_rule_byte_identical_to_111():
    """核心：AST v2 规则逐字节复用 §111——唯一变量是厂商，不是规则。"""
    assert sha(f"{BASE}/admission_v2.py") == sha(f"{S111}/admission_v2.py")
    assert sha(f"{BASE}/admission_v2.py") == load(f"{BASE}/prereg.json")["locked_files_sha256"]["admission_v2.py"]


def test_frozen_inputs_match_111():
    """冻结样本/scorer_key/purpose 逐字节复用 §111。"""
    for f in ("scorer_key.json",):
        assert sha(f"{BASE}/{f}") == sha(f"{S111}/{f}")
    for c in CELLS:
        for f in ("samples_blind.json", "purpose.md"):
            assert sha(f"{BASE}/vendor_{c}/{f}") == sha(f"{S111}/vendor_{c}/{f}")


def test_prereg_declares_cross_vendor_and_no_overturn():
    p = load(f"{BASE}/prereg.json")
    assert "Liquid AI" in p["experiment"] or "Liquid AI" in p.get("vendor_selection_method", "")
    assert p["l3_claimed"] is False and p["absolute_claimed"] is False
    assert "CROSS_VENDOR_INCONCLUSIVE" in p["does_not_overturn"]
    assert "AST_V2_PARTIAL" in p["does_not_overturn"]
    joined = " ".join(p["verdict_rules"])
    for t in ("CROSS_VENDOR2_CONFIRMED", "CROSS_VENDOR2_PARTIAL", "CROSS_VENDOR2_REFUTED", "CROSS_VENDOR2_INCONCLUSIVE"):
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


def test_executed_cross_vendor_premise():
    """执行态：厂商必须是 Liquid AI，明确非 NVIDIA/Hunyuan（跨厂商前提）。"""
    r = load(f"{BASE}/result.json")
    if r.get("status") != "EXECUTED":
        return
    assert r["vendor_cross_vendor_ok"] is True
    v = (r.get("vendor", "") + " " + r.get("model", "")).lower()
    assert "liquid" in v
    assert "nvidia" not in v and "hunyuan" not in v and "混元" not in v


def test_executed_verdict_consistent_and_no_overturn():
    r = load(f"{BASE}/result.json")
    if r.get("status") != "EXECUTED":
        return
    assert r["l3_claimed"] is False and r["absolute_claimed"] is False
    assert r["locks_ok"] is True and r["all_admissions_pass"] is True
    assert r["verdict"] in ("CROSS_VENDOR2_CONFIRMED", "CROSS_VENDOR2_PARTIAL",
                            "CROSS_VENDOR2_REFUTED", "CROSS_VENDOR2_INCONCLUSIVE")
    assert "does_not_overturn" in r


def test_executed_judges_match_manifest():
    mpath = f"{BASE}/runs/vendor_call_manifest.json"
    if not os.path.exists(mpath):
        return
    m = load(mpath)
    for c in CELLS:
        rec = m["calls"][c]
        assert rec["status"] == "ok" and rec["finish_reason"] == "stop"
        jp = f"{BASE}/vendor_{c}/judge_vendor.py"
        assert os.path.exists(jp)
        assert sha(jp) == rec["judge_sha256"]  # spawn 后未被篡改


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
