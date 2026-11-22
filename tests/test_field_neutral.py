"""§104 字段名语义消融 —— 回放测试.

纪律: 只读冻结 result.json / 两设计者源码 / 哈希锁 / 字段名中性样本,
不重算判据(one-shot),只断言冻结结果与设计者源码未被事后篡改.
"""
import hashlib
import json
import os

BASE = "/workspace/audit_field_neutral"


def _result():
    return json.load(open(f"{BASE}/result.json", encoding="utf-8"))


def test_locks_intact():
    r = _result()
    assert all(r["locks"].values()), r["locks"]
    for f in ("prereg", "gate_prereg", "manifest"):
        raw = open(f"{BASE}/{f}.json", "rb").read()
        assert hashlib.sha256(raw).hexdigest() == open(f"{BASE}/{f}.sha256").read().strip()
    raw = open(f"{BASE}/downloads/samples_fieldneutral.json", "rb").read()
    assert hashlib.sha256(raw).hexdigest() == open(f"{BASE}/samples_fieldneutral.sha256").read().strip()


def test_designer_dir_only_neutral_sample():
    """设计者可见目录仅字段名中性裸样本(物理隔离)."""
    assert os.listdir(f"{BASE}/downloads") == ["samples_fieldneutral.json"]
    blind = json.load(open(f"{BASE}/downloads/samples_fieldneutral.json", encoding="utf-8"))
    # 字段名 key 全中性,无 claim/evidence 角色词
    for p in blind["pairs"]:
        assert set(p.keys()) == {"id", "text_a", "text_b"}
    assert all(p["id"].startswith("N") for p in blind["pairs"])
    assert len(blind["pairs"]) == 18
    # note 里也不含判定规则词
    assert all(w not in blind["note"] for w in ["逐字", "支撑", "限定成分", "verbatim", "support"])


def test_text_verbatim_reused_from_s100():
    """字段名换了,但文本 value 与 §100 冻结样本逐字一致."""
    blind = json.load(open(f"{BASE}/downloads/samples_fieldneutral.json", encoding="utf-8"))
    s100 = json.load(open("/workspace/audit_frozen_holdout/downloads/samples.json", encoding="utf-8"))
    by_text = {(s["claim"], s["evidence"]) for s in s100["samples"]}
    assert all((p["text_a"], p["text_b"]) in by_text for p in blind["pairs"])


def test_prereg_locked_before_spawn():
    p = json.load(open(f"{BASE}/prereg.json", encoding="utf-8"))
    for code in ("FIELD_NEUTRAL_ROBUST", "FIELD_NEUTRAL_PARTIAL", "FIELD_NEUTRAL_DEPENDENT"):
        assert code in p["honest_precommit"]
    assert "honest_residual" in p["source"]  # 文本内固有 claim 词如实记录


def test_no_new_gate():
    p = json.load(open(f"{BASE}/prereg.json", encoding="utf-8"))
    assert "不编译新门禁" in p["no_new_gate"]


def test_both_sources_frozen():
    for n in ("a", "b"):
        code = open(f"{BASE}/judge_D2{n}_by_agent.py", encoding="utf-8").read()
        assert "def judge" in code


def test_admission_both_ok():
    r = _result()
    for n in ("D2a", "D2b"):
        m = r["per_judge_metrics"][n]
        a = r["admission_audits"][n]
        assert m["admission_ok"] is True
        assert a["signature_ok"] and a["signature"] == ["text_a", "text_b"]
        assert a["no_label_leak"] and a["no_hardcoded_ids"]


def test_D2a_near_verbatim_but_cannot_break_tamper():
    """D2a: clean全True/tampered全True(高重合)/canary全False -> tamper_catch=0."""
    m = _result()["per_judge_metrics"]["D2a"]
    assert m["clean_pass_rate"] == 1.0
    assert m["tamper_catch_rate"] == 0.0
    assert m["canary_accuracy"] == 0.0
    assert m["vs_D1b_core_agreement"] == 0.5


def test_D2b_negation_polarity_subset():
    """D2b: 只抓否定词翻转的tampered(3/6),clean/canary全False."""
    m = _result()["per_judge_metrics"]["D2b"]
    assert m["tamper_catch_rate"] == 0.5
    assert m["clean_pass_rate"] == 0.0
    assert m["vs_D1b_core_agreement"] == 0.25


def test_designer_disagreement_recorded():
    d = _result()["designer_agreement"]
    assert d["D2a_D2b_core_agreement"] == 0.25


def test_verdict_dependent_no_l3():
    r = _result()
    assert r["verdict"]["code"] == "FIELD_NEUTRAL_DEPENDENT"
    assert r["verdict"]["field_name_semantics_dependency"] == "exposed"
    assert r["verdict"]["l3_claimed"] is False
    assert r["verdict"]["absolute_independence_claimed"] is False


def test_gt_text_lookup_and_shuffle():
    """gt 按文本反查(非id),id 顺序打乱生效."""
    s100 = json.load(open("/workspace/audit_frozen_holdout/downloads/samples.json", encoding="utf-8"))
    gt_by_text = {(s["claim"], s["evidence"]): s["ground_truth_supported"] for s in s100["samples"]}
    rows = _result()["per_judge_rows"]["D2a"]
    s100_rows = {s["id"]: s for s in s100["samples"]}
    for row in rows:
        src = s100_rows[row["orig_id"]]
        assert row["gt"] == gt_by_text[(src["claim"], src["evidence"])]
    by_neutral = sorted(rows, key=lambda r: r["neutral_id"])
    seq = [int(r["gt"]) for r in by_neutral]
    assert seq != sorted(seq)
