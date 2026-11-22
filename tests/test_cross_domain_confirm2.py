"""§108 跨集复现 + 外部时间戳锚 —— 回放测试.

纪律: 只读冻结 result.json / 三设计者源码 / 哈希锁 / 承诺锚 / 确认集,
不重算判据(one-shot),断言冻结结果与源码未被事后篡改,
并固化'PRIMARY 跨集复现但 P0 地板消失 → PARTIAL 不翻案 + 外部时间锚 + 仍不宣布 L3'的诚实结论。
"""
import hashlib
import json
import os

BASE = "/workspace/audit_cross_domain_confirm2"


def _result():
    return json.load(open(f"{BASE}/result.json", encoding="utf-8"))


def test_locks_intact():
    r = _result()
    assert r["locks_ok"] is True
    for f in ("prereg", "gate_prereg", "manifest", "scorer_key", "engine"):
        ext = ".py" if f == "engine" else ".json"
        raw = open(f"{BASE}/{f}{ext}", "rb").read()
        assert hashlib.sha256(raw).hexdigest() == open(f"{BASE}/{f}.sha256").read().strip()
    for c in ("P0", "P1", "P2"):
        raw = open(f"{BASE}/designer_{c}/samples_blind.json", "rb").read()
        assert hashlib.sha256(raw).hexdigest() == open(f"{BASE}/samples_blind.sha256").read().strip()


def test_external_time_anchor_intact():
    # 外部承诺锚：commitment 自身哈希 + 其记录的每个被锁文件哈希均与当前一致（证明无事后回改）
    r = _result()
    assert r["anchor_intact"] is True
    c = json.load(open(f"{BASE}/commitment.json", encoding="utf-8"))
    assert hashlib.sha256(open(f"{BASE}/commitment.json", "rb").read()).hexdigest() == open(f"{BASE}/commitment.sha256").read().strip()
    for f, h in c["locked_sha256"].items():
        ext = ".py" if f == "engine" else (".sha256" if f == "samples_blind" else ".json")
        actual = (open(f"{BASE}/{f}.sha256").read().strip() if f == "samples_blind"
                  else hashlib.sha256(open(f"{BASE}/{f}{ext}", "rb").read()).hexdigest())
        assert h == actual, f"锚记录 {f} 与实际失配（事后回改）"
    assert "先于" in c["purpose"] or "spawn 前" in c["purpose"]


def test_second_independent_paper():
    # 第三确认集 2611.20899，与发现集 2611.14326、确认集A 2611.22027 都不同
    r = _result()
    m = open(f"{BASE}/manifest.json", encoding="utf-8").read()
    assert "2611.20899" in m
    assert "2611.22027" not in m and "2611.14326" not in m
    assert r["source_sha256"].startswith("5c932125")
    assert r["confirmation_set_sha256"].startswith("5374af09")
    # seed 在 manifest 是数字；result 的 seed 字段是 prereg held_fixed 的描述串（§107 起沿用）
    mf = json.load(open(f"{BASE}/manifest.json", encoding="utf-8"))
    assert mf["seed"] == 261122108
    assert "261122108" in r["seed"]


def test_prereg_locked_cross_set_primary():
    p = json.load(open(f"{BASE}/prereg.json", encoding="utf-8"))
    assert p["locked_before_spawn"] is True
    rules = " ".join(p["verdict_rules"])
    for v in ("CROSS_SET_REPRODUCED", "CROSS_SET_PARTIAL", "CROSS_SET_REFUTED", "CROSS_SET_INCONCLUSIVE"):
        assert v in rules
    assert "non_negation_qualifier" in p["metric"]["PRIMARY_non_negation_gap"]
    assert "0.8" in p["metric"]["PRIMARY_non_negation_gap"]
    assert "不编译新门禁" in p["no_new_gate"]


def test_three_judges_source_frozen():
    import importlib.util
    for c in ("P0", "P1", "P2"):
        fn = f"{BASE}/designer_{c}/judge_{c}_by_agent.py"
        assert os.path.exists(fn)
        spec = importlib.util.spec_from_file_location(f"t2_{c}", fn)
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


def test_stratified_primary_reproduced():
    # 预注册主指标跨集复现：非否定限定 gap=1.0≥0.8，否定翻转 gap=0.0≤0.3
    r = _result()
    m = r["stratified_metric"]
    assert abs(m["PRIMARY_non_negation_gap"] - 1.0) < 0.01
    assert abs(m["SECONDARY_negation_gap"] - 0.0) < 0.01
    assert m["dT_non_negation"]["P1"] == 0.0 and m["dT_non_negation"]["P2"] == 1.0
    assert m["dT_negation"]["P1"] == 0.0 and m["dT_negation"]["P2"] == 0.0


def test_p0_floor_absent_on_third_set():
    # 诚实发现：P0 无目的在第三确认集上自归纳出正确判据，地板消失（§106/§107 地板非稳健）
    r = _result()
    p0 = r["per_condition"]["P0"]
    assert abs(p0["core_acc"] - 1.0) < 0.01
    assert p0["tamper_catch"] == 1.0
    assert r["P0_floor"] is False


def test_capability_control_not_holding():
    # 诚实发现：本次 canary 三条件逐样本不一致，能力对照不成立（与 §107 全一致不同）
    r = _result()
    mc = r["diagnostic_only"]["model_capability_control"]
    assert mc["clean_all_agree"] is True
    assert mc["canary_all_agree"] is False


def test_verdict_partial_no_flip():
    # PRIMARY 达标但 P0 非地板 → PARTIAL，不因 PRIMARY 就翻案成 REPRODUCED
    r = _result()
    assert r["verdict"] == "CROSS_SET_PARTIAL"
    assert r["verdict"] != "CROSS_SET_REPRODUCED"
    assert "非地板" in r["verdict_why"] or "P0" in r["verdict_why"]
    assert abs(r["diagnostic_only"]["orient_gap_all_tampered"] - 0.6666666666) < 0.01
    assert "禁止用于翻案" in r["diagnostic_only"]["note"]


def test_no_l3_no_absolute():
    r = _result()
    assert r["l3_claimed"] is False
    assert r["absolute_claimed"] is False
    assert "外部 orchestrator" in r["honest_boundary"]
    assert "时间锚" in r["honest_boundary"] or "承诺先于执行" in r["honest_boundary"]


def test_sample_protocol_18_with_deletion_class():
    import collections
    key = json.load(open(f"{BASE}/scorer_key.json", encoding="utf-8"))
    assert len(key) == 18
    dist = collections.Counter(k["variant"] for k in key.values())
    assert dist == {"clean": 6, "tampered": 6, "canary": 6}
    dc = collections.Counter(k["deletion_class"] for k in key.values() if k["variant"] == "tampered")
    assert dc == {"negation_flip": 2, "non_negation_qualifier": 4}
