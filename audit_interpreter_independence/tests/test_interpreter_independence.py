"""§114 解释者独立性专项测试：锁/盲性/冻结来源/裁决树/失败态/不翻案。"""
import json, os, hashlib, random, subprocess, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(BASE)


def load(p):
    return json.load(open(p, encoding="utf-8"))


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def test_all_locks_intact():
    for f, lk in (("prereg.json", "prereg.sha256"), ("manifest.json", "manifest.sha256"),
                  ("cases_blind.json", "cases_blind.json.sha256"), ("gt_private.json", "gt_private.json.sha256"),
                  ("gen_fixtures.py", "gen_fixtures.py.sha256"), ("call_interpreter.py", "call_interpreter.py.sha256")):
        assert os.path.exists(f"{BASE}/{lk}") and sha(f"{BASE}/{f}") == open(f"{BASE}/{lk}").read().strip()


def test_blind_no_source_leak():
    s = json.dumps(load(f"{BASE}/cases_blind.json"), ensure_ascii=False)
    for banned in ("STRATIFIED", "CROSS_SET", "AST_V2", "CROSS_VENDOR", "source_round", "historical_verdict", "audit_"):
        assert banned not in s


def test_frozen_inputs_match_four_rounds():
    cb = load(f"{BASE}/cases_blind.json")
    by_id = {c["id"]: c for c in cb["cases"]}
    order = ["A", "B", "C", "D"]
    random.Random(cb["seed"]).shuffle(order)
    src = {"A": "audit_stratified_confirmation", "B": "audit_cross_domain_confirm2",
           "C": "audit_admission_ast_audit", "D": "audit_cross_vendor_designer2"}
    for i, orig in enumerate(order, 1):
        d = load(f"{ROOT}/{src[orig]}/result.json")
        sm = d.get("stratified_metric") or {}
        m = d.get("metrics") or {}
        c = by_id[f"case_{i}"]
        exp_primary = sm.get("PRIMARY_non_negation_gap", m.get("PRIMARY"))
        assert c["PRIMARY"] == round(float(exp_primary), 6)


def test_neutral_gt_is_one_confirm_three_partial():
    gt = load(f"{BASE}/gt_private.json")
    vals = sorted(gt["neutral_gt"].values())
    assert vals == ["CONFIRMED", "PARTIAL", "PARTIAL", "PARTIAL"]


def test_prereg_no_new_gate_and_l3_false():
    p = load(f"{BASE}/prereg.json")
    assert p["no_new_gate"] is True and p["l3_claimed"] is False and p["absolute_claimed"] is False
    assert len(p["does_not_overturn"]) == 7


def test_verdict_tree_has_four_tiers():
    p = load(f"{BASE}/prereg.json")
    joined = " ".join(p["verdict_rules"])
    for t in ("INTERPRETER_CONFIRMED", "INTERPRETER_PARTIAL", "INTERPRETER_DIVERGENT", "INTERPRETER_INCONCLUSIVE"):
        assert t in joined


def test_call_manifest_never_includes_private_gt():
    p = f"{BASE}/runs/interpreter_call_manifest.json"
    if os.path.exists(p):
        mf = load(p)
        assert mf.get("gt_private_in_prompt") is False


def test_failed_call_does_not_forge_tiers():
    p = f"{BASE}/runs/interpreter_call_manifest.json"
    if os.path.exists(p):
        rec = load(p).get("calls", [{}])[0]
        if rec.get("status") != "ok":
            assert "tiers" not in rec


def test_verify_script_all_ok():
    r = subprocess.run([sys.executable, f"{BASE}/verify.py"], capture_output=True, text=True)
    assert r.returncode == 0 and "ALL_OK" in r.stdout


def test_result_if_executed_keeps_l3_false_and_no_overturn():
    p = f"{BASE}/result.json"
    if os.path.exists(p):
        res = load(p)
        assert res.get("l3_claimed") is False and res.get("absolute_claimed") is False
        if res.get("status") == "EXECUTED":
            assert len(res.get("does_not_overturn", [])) == 7
