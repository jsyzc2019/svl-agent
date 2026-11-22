"""§106 任务目的语义注入受控实验 —— 回放测试.

纪律: 只读冻结 result.json / 三设计者源码 / 哈希锁,
不重算判据(one-shot),只断言冻结结果与源码未被事后篡改,
并固化'主裁决 INCONCLUSIVE + post-hoc 分层取证不翻案'的诚实结论。
"""
import hashlib
import json
import os

BASE = "/workspace/audit_task_purpose_injection"


def _result():
    return json.load(open(f"{BASE}/result.json", encoding="utf-8"))


def test_locks_intact():
    r = _result()
    assert r["locks_ok"] is True
    for f in ("prereg", "gate_prereg", "manifest", "scorer_key"):
        raw = open(f"{BASE}/{f}.json", "rb").read()
        assert hashlib.sha256(raw).hexdigest() == open(f"{BASE}/{f}.sha256").read().strip()
    # 三条件裸样本逐字相同（唯一变量不在样本里）
    for c in ("P0", "P1", "P2"):
        raw = open(f"{BASE}/designer_{c}/samples_blind.json", "rb").read()
        assert hashlib.sha256(raw).hexdigest() == open(f"{BASE}/samples_blind.sha256").read().strip()


def test_prereg_locked_three_verdicts():
    p = json.load(open(f"{BASE}/prereg.json", encoding="utf-8"))
    assert p["locked_before_spawn"] is True
    assert p["design"]["type"] == "单变量受控：任务目的语义（3 水平）"
    rules = " ".join(p["verdict_rules"])
    for v in ("PURPOSE_DECISIVE", "PURPOSE_WEAK", "PURPOSE_INCONCLUSIVE"):
        assert v in rules
    # prereg.no_new_gate 是字符串说明（"本轮不编译新门禁…"），非 bool
    assert "不编译新门禁" in p["no_new_gate"]


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


def test_p0_floor_reproduced():
    # 无目的基线落地板：core 0.5 / tampered 全判 True（默认近逐字取向）
    r = _result()
    p0 = r["per_condition"]["P0"]
    assert p0["clean_pass"] == 1.0
    assert p0["tamper_catch"] == 0.0
    assert abs(p0["core_acc"] - 0.5) < 0.01
    assert r["orientation"]["P0_floor"] is True


def test_p1_faithfulness_restores_core():
    # 注入忠实性目的→从零恢复逐字判据 core=1.0、tampered 全判负
    r = _result()
    p1 = r["per_condition"]["P1"]
    assert abs(p1["core_acc"] - 1.0) < 0.01
    assert p1["tamper_catch"] == 1.0
    assert abs(r["orientation"]["dT_P1_faithfulness"] - 0.0) < 0.01


def test_p2_near_dup_partial():
    # 近似重复目的：core 0.67、tampered 部分判 True
    r = _result()
    p2 = r["per_condition"]["P2"]
    assert abs(p2["core_acc"] - 0.6666666666) < 0.01


def test_verdict_inconclusive_not_flipped():
    # 主指标 orient_gap=0.67<0.8 → 按预注册诚实落 INCONCLUSIVE，不因分层提示翻案
    r = _result()
    assert r["verdict"] == "PURPOSE_INCONCLUSIVE"
    gap = r["orientation"]["orient_gap_P1_P2"]
    assert abs(gap - 0.6666666666) < 0.01
    assert gap < 0.8
    assert "未达门槛" in r["contribution"] or "INCONCLUSIVE" in r["contribution"]


def test_posthoc_forensic_does_not_change_verdict():
    r = _result()
    ph = r["post_hoc_forensic"]
    assert ph["status"] == "post_hoc_forensic_not_in_preregistered_verdict"
    # 非否定限定上取向相反 gap=1.0，否定翻转上同判负 gap=0.0
    assert abs(ph["non_negation_qualifier"]["gap"] - 1.0) < 0.01
    assert abs(ph["negation_flip"]["gap"] - 0.0) < 0.01
    assert "不得据此翻案" in ph["trigger"]
    # 诊断字段存在但 verdict 仍是 INCONCLUSIVE
    assert r["verdict"] == "PURPOSE_INCONCLUSIVE"
    assert "posthoc_correction" in ph


def test_no_l3_no_absolute():
    r = _result()
    assert r["l3_claimed"] is False
    assert r["absolute_claimed"] is False


def test_designer_notes_exist():
    for c in ("P0", "P1", "P2"):
        assert os.path.exists(f"{BASE}/designer_{c}/designer_note.json")


def test_sample_protocol_18():
    import collections
    key = json.load(open(f"{BASE}/scorer_key.json", encoding="utf-8"))
    assert len(key) == 18
    dist = collections.Counter(k["variant"] for k in key.values())
    assert dist == {"clean": 6, "tampered": 6, "canary": 6}
