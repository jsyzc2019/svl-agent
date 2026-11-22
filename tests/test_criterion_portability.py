"""§102 判据设计权外移 —— 回放测试.

纪律: 只读冻结的 result.json / judge_D_by_agent.py / 全部哈希锁,
不重算判据(one-shot),只断言冻结结果与设计者源码未被事后篡改.
"""
import hashlib
import json
import re

BASE = "/workspace/audit_criterion_portability"
S100 = "/workspace/audit_frozen_holdout"


def _result():
    return json.load(open(f"{BASE}/result.json", encoding="utf-8"))


def test_locks_intact():
    """全部哈希锁(含 §100 复用源)未变."""
    r = _result()
    assert all(r["locks"].values()), r["locks"]
    for f, lk in [("prereg", "prereg.sha256"), ("gate_prereg", "gate_prereg.sha256"),
                  ("manifest", "manifest.sha256")]:
        raw = open(f"{BASE}/{f}.json", "rb").read()
        assert hashlib.sha256(raw).hexdigest() == open(f"{BASE}/{lk}").read().strip()


def test_judge_D_source_frozen():
    """独立设计者源码存在且带 judge_D 定义(回放只读,不重写)."""
    code = open(f"{BASE}/judge_D_by_agent.py", encoding="utf-8").read()
    assert re.search(r"def judge_D\s*\(", code)
    assert "(claim, evidence)" in code or "claim" in code and "evidence" in code


def test_admission_passed_after_word_boundary_fix():
    """D 通过准入元审计;词边界自我纠错如实记录."""
    r = _result()
    a = r["admission_audit"]
    assert a["signature_ok"] and a["signature"] == ["claim", "evidence"]
    assert a["no_label_leak"] and a["no_hardcoded_ids"] and a["deterministic_no_rng"]
    assert "self_correction" in a and "invariant" in a["self_correction"]


def test_designer_output_matches_source_core():
    """设计者自报的 clean/tampered 判定与源码重跑一致(core)."""
    r = _result()
    designer = json.load(open(f"{BASE}/designer_output.json", encoding="utf-8"))
    d_by_id = {row["id"]: row["supported"] for row in designer["rows"]}
    for row in r["rows"]:
        if row["variant"] != "canary":
            assert d_by_id[row["id"]] == row["D_supported"]


def test_core_portability():
    """独立设计的 D 在 core 上全对,tamper_catch=clean_pass=1.0."""
    r = _result()
    m = r["metrics"]
    assert m["admission_ok"] is True
    assert m["D_tamper_catch_rate"] == 1.0
    assert m["D_clean_pass_rate"] == 1.0
    assert m["D_core_accuracy_excl_canary"] == 1.0


def test_gd_core_agreement_full():
    """两独立判据在 core 逐样本一致;整体分歧只在 canary(类型错配)."""
    r = _result()
    m = r["metrics"]
    assert m["G_D_core_agreement"] == 1.0
    assert m["G_D_sample_agreement"] < 1.0  # canary 差异保留,不粉饰
    for row in r["rows"]:
        if row["variant"] != "canary":
            assert row["D_eq_G"] is True
        else:
            # 记录 canary 分歧,不要求一致(§101 已定位 D 用更宽词表)
            assert row["variant"] == "canary"


def test_single_judge_overfit_alternative_weakened():
    """单判据过拟合替代解释被标为 weakened(先于结果锁定的裁决规则)."""
    r = _result()
    v = r["verdict"]
    assert v["code"] == "CRIT.PORTABLE_SINGLE_DESIGN_OVERFIT_WEAKENED"
    assert v["single_judge_overfit_alternative"] == "weakened"


def test_honest_boundary_no_l3():
    """诚实边界:不宣布 L3/absolute,同模型家族与 spawn 残余如实标注."""
    r = _result()
    v = r["verdict"]
    assert v["l3_claimed"] is False
    assert v["absolute_independence_claimed"] is False
    assert "spawn" in v["infinite_regression_note"]
    assert "KB-STRUCT02" in v["infinite_regression_note"]


def test_no_new_gate():
    """本轮不编译新门禁(避免刷门禁数量);按 prereg 原文语义断言,不改已锁存预注册."""
    r = _result()
    prereg = json.load(open(f"{BASE}/prereg.json", encoding="utf-8"))
    assert "不编译新门禁" in prereg["no_new_gate"]


def test_reuse_rationale_clean_control():
    """复用冻结数据/样本/gt——唯一变量=判据设计者,受控设计成立."""
    r = _result()
    assert r["source"]["reuse_rationale"]
    assert r["role_separation"]["designer"].startswith("独立子 agent")
    assert "脱敏" in r["role_separation"]["designer"]


def test_one_shot_no_recompute():
    """one-shot:回放测试只读冻结结果,引擎的 canary_fp 与冻结值一致."""
    r = _result()
    m = r["metrics"]
    # 冻结值自洽:D 对 6 canary 全判 false → fp=1.0
    assert m["D_canary_false_positive_rate"] == 1.0
    canary_rows = [x for x in r["rows"] if x["variant"] == "canary"]
    assert len(canary_rows) == 6
    assert all(x["D_supported"] is False for x in canary_rows)
