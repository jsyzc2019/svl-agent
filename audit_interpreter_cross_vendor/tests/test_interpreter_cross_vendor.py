"""§115 解释者跨厂商交叉确认专项测试。"""
import json, os, hashlib, subprocess, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S114 = os.path.join(os.path.dirname(BASE), "audit_interpreter_independence")


def load(p):
    return json.load(open(p, encoding="utf-8"))


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def test_all_locks_intact():
    for f, lk in (("prereg.json", "prereg.sha256"), ("manifest.json", "manifest.sha256"),
                  ("cases_blind.json", "cases_blind.json.sha256"), ("gt_private.json", "gt_private.json.sha256"),
                  ("gen_fixtures.py", "gen_fixtures.py.sha256"), ("call_interpreter.py", "call_interpreter.py.sha256"),
                  ("run_all.py", "run_all.py.sha256")):
        assert os.path.exists(f"{BASE}/{lk}") and sha(f"{BASE}/{f}") == open(f"{BASE}/{lk}").read().strip()


def test_byte_identical_reuse_from_114():
    for f in ("cases_blind.json", "gt_private.json", "gen_fixtures.py", "call_interpreter.py"):
        assert sha(f"{BASE}/{f}") == sha(f"{S114}/{f}")


def test_vendors_genuinely_diverse():
    p = load(f"{BASE}/prereg.json")
    vendors = p["selected_vendors"]
    assert len(vendors) == 3
    prefixes = [v.split("/")[0] for v in vendors]
    assert len(set(prefixes)) == 3
    assert not set(prefixes) & {"baidu", "nvidia", "tencent", "hunyuan"}


def test_blind_no_source_leak():
    s = json.dumps(load(f"{BASE}/cases_blind.json"), ensure_ascii=False)
    for banned in ("STRATIFIED", "CROSS_SET", "AST_V2", "CROSS_VENDOR", "source_round", "historical_verdict", "audit_"):
        assert banned not in s


def test_verdict_tree_has_four_tiers():
    p = load(f"{BASE}/prereg.json")
    joined = " ".join(p["verdict_rules"])
    for t in ("INTERPRETER_CROSS_CONFIRMED", "INTERPRETER_CROSS_PARTIAL",
              "INTERPRETER_CROSS_DIVERGENT", "INTERPRETER_CROSS_INCONCLUSIVE"):
        assert t in joined


def test_no_new_gate_l3_false_overturn_8():
    p = load(f"{BASE}/prereg.json")
    assert p["no_new_gate"] is True and p["l3_claimed"] is False and p["absolute_claimed"] is False
    assert len(p["does_not_overturn"]) == 8
    assert "§114 INTERPRETER_CONFIRMED" in p["does_not_overturn"]


def test_vendor_traces_no_key_no_gt():
    for tag in ("dots", "ling", "liquid"):
        p = f"{BASE}/runs/{tag}/interpreter_call_manifest.json"
        if os.path.exists(p):
            mf = load(p)
            assert mf.get("gt_private_in_prompt") is False
            rec = mf.get("calls", [{}])[0]
            if rec.get("status") != "ok":
                assert "tiers" not in rec


def test_verify_script_all_ok():
    r = subprocess.run([sys.executable, f"{BASE}/verify.py"], capture_output=True, text=True)
    assert r.returncode == 0 and "ALL_OK" in r.stdout


def test_result_if_executed_keeps_boundaries():
    p = f"{BASE}/result.json"
    if os.path.exists(p):
        res = load(p)
        assert res.get("l3_claimed") is False and res.get("absolute_claimed") is False
        if res.get("status") == "EXECUTED":
            assert len(res.get("does_not_overturn", [])) == 8
