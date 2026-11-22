"""§107 预注册分层确认性实验 —— 回放测试.

纪律: 只读冻结 result.json / 三设计者源码 / 哈希锁 / 确认集,
不重算判据(one-shot),只断言冻结结果与源码未被事后篡改,
并固化'预注册分层主指标获确认 + 单一确认集不宣布 L3'的诚实结论。
"""
import hashlib
import json
import os

BASE = "/workspace/audit_stratified_confirmation"


def _result():
    return json.load(open(f"{BASE}/result.json", encoding="utf-8"))


def test_locks_intact():
    r = _result()
    assert r["locks_ok"] is True
    for f in ("prereg", "gate_prereg", "manifest", "scorer_key"):
        raw = open(f"{BASE}/{f}.json", "rb").read()
        assert hashlib.sha256(raw).hexdigest() == open(f"{BASE}/{f}.sha256").read().strip()
    for c in ("P0", "P1", "P2"):
        raw = open(f"{BASE}/designer_{c}/samples_blind.json", "rb").read()
        assert hashlib.sha256(raw).hexdigest() == open(f"{BASE}/samples_blind.sha256").read().strip()


def test_confirmation_set_independent_paper():
    # 确认集是全新论文 2611.22027，与发现集 2611.14326 无关
    r = _result()
    assert "2611.22027" in open(f"{BASE}/manifest.json", encoding="utf-8").read()
    assert r["source_sha256"].startswith("44f67e49")
    assert r["confirmation_set_sha256"].startswith("a1051c40")


def test_prereg_locked_stratified_primary():
    p = json.load(open(f"{BASE}/prereg.json", encoding="utf-8"))
    assert p["locked_before_spawn"] is True
    assert "PRIMARY" in " ".join(p["verdict_rules"][:1])
    rules = " ".join(p["verdict_rules"])
    for v in ("STRATIFIED_CONFIRMED", "STRATIFIED_PARTIAL", "STRATIFIED_REFUTED", "STRATIFIED_INCONCLUSIVE"):
        assert v in rules
    assert "不编译新门禁" in p["no_new_gate"]
    # 分层主指标事前锁定：PRIMARY 定义在非否定限定子集
    assert "non_negation_qualifier" in p["metric"]["PRIMARY_non_negation_gap"]
    assert "0.8" in p["metric"]["PRIMARY_non_negation_gap"]


def test_three_judges_source_frozen():
    import importlib.util
    for c in ("P0", "P1", "P2"):
        fn = f"{BASE}/designer_{c}/judge_{c}_by_agent.py"
        assert os.path.exists(fn)
        spec = importlib.util.spec_from_file_location(f"t_{c}", fn)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert callable(mod.judge)


def test_all_admissions_pass():
    r = _result()
    assert r["all_admissions_pass"] is True
    for c in ("P0", "P1", "P2"):
        adm = r["per_condition"][c]["admission"]
        assert adm["admission_ok"] is True
        assert adm["signature_ok"] is True
        assert adm["no_label_leak"] is True
        assert adm["no_hardcoded_ids"] is True


def test_p0_floor_and_p1_core():
    r = _result()
    p0, p1 = r["per_condition"]["P0"], r["per_condition"]["P1"]
    assert abs(p0["core_acc"] - 0.5) < 0.01
    assert p0["tamper_catch"] == 0.0
    assert r["P0_floor"] is True
    assert abs(p1["core_acc"] - 1.0) < 0.01
    assert p1["tamper_catch"] == 1.0


def test_stratified_primary_confirmed():
    # 预注册主指标：非否定限定 gap=1.0≥0.8，否定翻转 gap=0.0≤0.3
    r = _result()
    m = r["stratified_metric"]
    assert abs(m["PRIMARY_non_negation_gap"] - 1.0) < 0.01
    assert abs(m["SECONDARY_negation_gap"] - 0.0) < 0.01
    assert m["dT_non_negation"]["P1"] == 0.0 and m["dT_non_negation"]["P2"] == 1.0
    assert m["dT_negation"]["P1"] == 0.0 and m["dT_negation"]["P2"] == 0.0


def test_model_capability_control():
    # 异 model 路由基础能力无系统差异：clean 全判对、canary 全判错，逐样本一致
    r = _result()
    mc = r["diagnostic_only"]["model_capability_control"]
    assert mc["clean_all_agree"] is True
    assert mc["canary_all_agree"] is True


def test_verdict_confirmed_no_flip_needed():
    # 主指标事前达标→CONFIRMED，无需事后翻案；全集 orient_gap 仍 0.67 但仅诊断
    r = _result()
    assert r["verdict"] == "STRATIFIED_CONFIRMED"
    assert abs(r["diagnostic_only"]["orient_gap_all_tampered"] - 0.6666666666) < 0.01
    assert "禁止用于翻案" in r["diagnostic_only"]["note"]


def test_no_l3_no_absolute():
    r = _result()
    assert r["l3_claimed"] is False
    assert r["absolute_claimed"] is False
    assert "单一独立确认集" in r["honest_boundary"]


def test_sample_protocol_18_with_deletion_class():
    import collections
    key = json.load(open(f"{BASE}/scorer_key.json", encoding="utf-8"))
    assert len(key) == 18
    dist = collections.Counter(k["variant"] for k in key.values())
    assert dist == {"clean": 6, "tampered": 6, "canary": 6}
    dc = collections.Counter(k["deletion_class"] for k in key.values() if k["variant"] == "tampered")
    assert dc == {"negation_flip": 2, "non_negation_qualifier": 4}


def test_model_routing_recorded():
    p = json.load(open(f"{BASE}/prereg.json", encoding="utf-8"))
    route = p["design"]["model_routing"]
    for m in ("default", "reasoning", "lite"):
        assert m in route
    assert "同厂商" in route  # 诚实边界：异路由仍同厂商
