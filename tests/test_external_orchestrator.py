"""§109 外部 orchestrator 执行者独立性验证器测试（不编译门禁，验证取证工具正确性）。"""
import json, hashlib, os
BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "audit_external_orchestrator")
REPO = os.path.dirname(BASE)

def load(p): return json.load(open(p, encoding="utf-8"))

def test_external_result_three_way_hash_identical():
    r = load(f"{BASE}/result.json")
    assert r["hashes"]["three_way_identical"] is True
    assert r["hashes"]["external_runner_result"] == r["hashes"]["local_recompute"]
    assert r["hashes"]["external_runner_result"] == r["hashes"]["repo_archive"]
    assert r["hashes"]["external_runner_result"] == r["hashes"]["local_recheck"]

def test_verdict_is_executor_independence_confirmed():
    r = load(f"{BASE}/result.json")
    assert r["verdict"] == "EXECUTOR_INDEPENDENCE_CONFIRMED"
    assert r["all_checks_pass"] is True
    assert all(r["checks"].values())

def test_runner_is_externally_attested():
    r = load(f"{BASE}/result.json")
    ex = r["external_runner"]
    assert ex["whoami"] == "runner"
    assert "azure" in ex["uname"]
    assert ex["hostname"].startswith("runnervm")
    assert ex["run_id"] and ex["nonce"]
    # 本沙箱身份与外部 runner 不同
    assert r["local_sandbox"]["whoami"] != ex["whoami"]
    assert r["local_sandbox"]["hostname"] != ex["hostname"]

def test_nonce_bound():
    r = load(f"{BASE}/result.json")
    injected = load(f"{BASE}/runs/injected_nonces.json")
    assert r["external_runner"]["nonce"] == injected["recompute_run_45013693112"]
    # 执行侧证据（外部 runner 写回）与注入侧证据（本 Agent 记录）双向一致
    ext = load(f"{BASE}/runs/recompute_45013693112.json")
    assert ext["injected_nonce"] == injected["recompute_run_45013693112"]

def test_l3_not_claimed_despite_confirmation():
    r = load(f"{BASE}/result.json")
    assert r["l3_claimed"] is False
    assert r["absolute_claimed"] is False
    assert "不宣布 L3" in r["honest_boundary"]

def test_core_and_verdict_consistency_with_local():
    r = load(f"{BASE}/result.json")
    ext = load(f"{BASE}/runs/recompute_45013693112.json")
    local = load(f"{REPO}/audit_stratified_confirmation/result.json")
    assert ext["external_verdict"] == local["verdict"]
    for k in ("P0", "P1", "P2"):
        assert abs(ext["external_core"][k] - local["core"][k]) < 1e-12

def test_prereg_locks_frozen_before_spawn():
    p = load(f"{BASE}/prereg.json")
    lk = p["locks_frozen_before_spawn"]
    assert lk["engine_py_sha256"] == hashlib.sha256(
        open(f"{REPO}/audit_stratified_confirmation/engine.py","rb").read()).hexdigest()
    assert p["l3_claimed"] is False
