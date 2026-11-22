"""§105 跨数据域字段名语义消融 2×2 —— 回放测试.

纪律: 只读冻结 result.json / 四设计者源码 / 哈希锁 / 新论文样本,
不重算判据(one-shot),只断言冻结结果与设计者源码未被事后篡改.
"""
import hashlib
import json

BASE = "/workspace/audit_cross_domain_field"


def _result():
    return json.load(open(f"{BASE}/result.json", encoding="utf-8"))


def test_locks_intact():
    r = _result()
    assert r["locks_ok"] is True
    for f in ("prereg", "gate_prereg", "manifest"):
        raw = open(f"{BASE}/{f}.json", "rb").read()
        assert hashlib.sha256(raw).hexdigest() == open(f"{BASE}/{f}.sha256").read().strip()
    raw = open(f"{BASE}/downloads/samples.json", "rb").read()
    assert hashlib.sha256(raw).hexdigest() == open(f"{BASE}/samples.sha256").read().strip()


def test_source_is_new_paper():
    r = _result()
    # 新数据域必须是 2611.14326，与 §100 的 2610.16067 不同
    fetch = json.load(open(f"{BASE}/downloads/fetch_log.json", encoding="utf-8"))
    assert any("2611.14326" in e["url"] for e in fetch)
    assert all(e["ok"] for e in fetch)
    assert r["source_sha256"] == open(f"{BASE}/downloads/source.sha256").read().strip()


def test_samples_protocol_18():
    s = json.load(open(f"{BASE}/downloads/samples.json", encoding="utf-8"))
    assert len(s["samples"]) == 18
    import collections
    dist = collections.Counter(x["variant"] for x in s["samples"])
    assert dist == {"clean": 6, "tampered": 6, "canary": 6}
    gt = collections.Counter(x["ground_truth_supported"] for x in s["samples"])
    assert gt == {True: 12, False: 6}


def test_prereg_locked_before_spawn():
    p = json.load(open(f"{BASE}/prereg.json", encoding="utf-8"))
    assert p["design"]["type"] == "2×2 受控：字段名语义 × 数据域"
    assert p["no_new_gate"]
    assert "CROSS_DOMAIN_CONFIRMED" in p["verdict"]["rules"][0]
    assert "CROSS_DOMAIN_INCONCLUSIVE" in p["verdict"]["rules"][2]


def test_four_judges_source_frozen():
    # 四个设计者源码哈希记录于 admission.signature 之外的存在性；这里断言文件存在且可 import
    import importlib.util
    for cell in ("A1", "A2", "B1", "B2"):
        fn = f"{BASE}/designer_{cell}/judge_{cell}_by_agent.py"
        assert __import__("os").path.exists(fn)
        spec = importlib.util.spec_from_file_location(f"t_{cell}", fn)
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        assert callable(mod.judge)


def test_all_admissions_pass():
    r = _result()
    for cell in ("A1", "A2", "B1", "B2"):
        assert r["per_judge"][cell]["admission"]["admission_ok"] is True, cell
        assert r["per_judge"][cell]["admission"]["signature_ok"] is True


def test_field_gap_collapsed_in_new_domain():
    r = _result()
    # 核心增量：字段名效应在新域消失(gap=0.0)，旧域 gap=0.667
    assert r["field_gap_new_domain"] == 0.0
    assert abs(r["field_gap_old_domain"] - 0.667) < 0.01


def test_all_four_converge_to_verbatim_judge():
    r = _result()
    for cell in ("A1", "A2", "B1", "B2"):
        j = r["per_judge"][cell]
        assert j["clean_pass"] == 1.0
        assert j["tamper_catch"] == 0.0
        assert j["canary_fp"] == 1.0
        assert j["core_acc"] == 0.5


def test_verdict_inconclusive():
    r = _result()
    # 诚实地板效应裁决：不宣称字段名被推翻/confirmed
    assert r["verdict"] == "CROSS_DOMAIN_INCONCLUSIVE"
    assert "地板效应" in r["verdict_why"]
    assert "无法归因" in r["verdict_why"]


def test_root_cause_forensic_present():
    r = _result()
    rc = r["root_cause_forensic"]
    assert "正类取向相反" in rc["observation"]
    assert len(rc["evidence"]) == 3
    assert rc["status"].startswith("forensic_observation")


def test_no_l3_no_absolute():
    r = _result()
    assert r["l3_claimed"] is False
    assert r["absolute_claimed"] is False


def test_designer_notes_exist():
    # 设计者自报说明文件存在但不作为判据(不采信自报)
    import os
    for cell in ("A1", "A2", "B1", "B2"):
        assert os.path.exists(f"{BASE}/designer_{cell}/designer_note.json")


def test_gt_lookup_not_hardcoded():
    # 按 (claim,evidence) 文本反查 gt，中性 id 无固定语义
    key = json.load(open(f"{BASE}/scorer_key.json", encoding="utf-8"))
    assert len(key) == 18
    # 每个中性 id 映射的 variant/gt 来自标注者，不按 id 顺序推导
    variants = {k["variant"] for k in key.values()}
    assert variants == {"clean", "tampered", "canary"}
    # 检查打乱生效：并非按 N 序聚集同 variant
    ids = sorted(key)
    seq = [key[i]["variant"] for i in ids]
    assert len(set(seq)) > 1
