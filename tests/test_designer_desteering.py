"""§103 设计者约束消融（de-steering）—— 回放测试.

纪律: 只读冻结 result.json / 两设计者源码 / 哈希锁 / 去引导样本,
不重算判据(one-shot),只断言冻结结果与设计者源码未被事后篡改.
"""
import hashlib
import json

BASE = "/workspace/audit_designer_desteering"


def _result():
    return json.load(open(f"{BASE}/result.json", encoding="utf-8"))


def test_locks_intact():
    """全部哈希锁未变."""
    r = _result()
    assert all(r["locks"].values()), r["locks"]
    for f in ("prereg", "gate_prereg", "manifest"):
        raw = open(f"{BASE}/{f}.json", "rb").read()
        assert hashlib.sha256(raw).hexdigest() == open(f"{BASE}/{f}.sha256").read().strip()
    raw = open(f"{BASE}/downloads/samples_desteer.json", "rb").read()
    assert hashlib.sha256(raw).hexdigest() == open(f"{BASE}/samples_desteer.sha256").read().strip()


def test_no_label_mapping_leaked_to_designer_dir():
    """设计者可见目录只有裸样本(gt 映射不落盘,物理隔离)."""
    import os
    files = os.listdir(f"{BASE}/downloads")
    assert files == ["samples_desteer.json"], files
    # 裸样本不含 variant / gt / 判定规则词 / 原始 id
    blind = json.load(open(f"{BASE}/downloads/samples_desteer.json", encoding="utf-8"))
    text = json.dumps(blind, ensure_ascii=False)
    for bad in ("variant", "ground_truth", "tampered", "clean", "canary", "支撑", "逐字", "限定成分"):
        assert bad not in text, bad
    assert all(p["id"].startswith("N") for p in blind["pairs"])
    assert len(blind["pairs"]) == 18


def test_prereg_locked_before_spawn():
    """预注册含去引导设计与三情形裁决规则,且声明先于结果锁定."""
    p = json.load(open(f"{BASE}/prereg.json", encoding="utf-8"))
    assert "DESTEER_ROBUST" in p["honest_precommit"]
    assert "DESTEER_PARTIAL" in p["honest_precommit"]
    assert "DESTEER_DEPENDENT" in p["honest_precommit"]
    assert p["design"]["role_1_designers"]
    assert "无规则描述" in p["source"]["revealed_to_designer"] or "不含" in p["source"]["revealed_to_designer"]


def test_no_new_gate():
    """本轮不编译新门禁(延续 §102,避免刷数量)."""
    p = json.load(open(f"{BASE}/prereg.json", encoding="utf-8"))
    assert "不编译新门禁" in p["no_new_gate"]


def test_both_designer_sources_frozen():
    """两份设计者源码存在且含 judge_D1 定义."""
    for n in ("a", "b"):
        code = open(f"{BASE}/judge_D1{n}_by_agent.py", encoding="utf-8").read()
        assert "def judge_D1" in code


def test_admission_both_ok():
    """两设计者均通过准入元审计(即使注释出现 tampered 一词也不算标签泄漏)."""
    r = _result()
    for n in ("D1a", "D1b"):
        a = r["admission_audits"][n]
        assert r["per_judge_metrics"][n]["admission_ok"] is True
        assert a["signature_ok"] and a["no_label_leak"]
        assert a["no_hardcoded_ids"] and a["deterministic_no_rng"]
        assert not a["leaked_label_tokens"]


def test_comment_concept_name_not_label_leak():
    """D1b 注释里的 tampered 是自主概念命名,不算标签泄漏(判据:只看注释剥离后代码)."""
    a = _result()["admission_audits"]["D1b"]
    # 源码注释确实出现该词,但 no_label_leak 仍为真
    code = open(f"{BASE}/judge_D1b_by_agent.py", encoding="utf-8").read()
    assert "tampered" in code
    assert a["no_label_leak"] is True
    assert "tampered" not in a["leaked_label_tokens"]


def test_D1b_core_perfect_and_matches_upstream():
    """D1b(去引导)核心全对且与 G/D0 逐样本一致——判据可无引导重新发现."""
    m = _result()["per_judge_metrics"]["D1b"]
    assert m["tamper_catch_rate"] == 1.0
    assert m["clean_pass_rate"] == 1.0
    assert m["core_accuracy_excl_canary"] == 1.0
    assert m["vs_G_core_agreement"] == 1.0
    assert m["vs_D0_core_agreement"] == 1.0


def test_D1a_task_interpretation_freedom():
    """D1a 抓全 tamper 但 clean 全错——暴露'正类取哪层'的任务解释自由度."""
    m = _result()["per_judge_metrics"]["D1a"]
    assert m["tamper_catch_rate"] == 1.0
    assert m["clean_pass_rate"] == 0.0
    assert m["core_accuracy_excl_canary"] == 0.5


def test_designer_disagreement_recorded():
    """两设计者核心一致率 0.5,如实记录分歧."""
    d = _result()["designer_agreement"]
    assert d["D1a_D1b_core_agreement"] == 0.5


def test_verdict_partial_no_l3():
    """裁决=DESTEER_PARTIAL,不宣布 L3/absolute."""
    r = _result()
    assert r["verdict"]["code"] == "DESTEER_PARTIAL"
    assert r["verdict"]["designer_interpretation_freedom"] == "exposed"
    assert r["verdict"]["l3_claimed"] is False
    assert r["verdict"]["absolute_independence_claimed"] is False


def test_gt_lookup_not_hardcoded_to_ids():
    """去引导核心:gt 按文本反查,中性 id 与 gt 无固定映射(顺序已打乱)."""
    s100 = json.load(open("/workspace/audit_frozen_holdout/downloads/samples.json", encoding="utf-8"))
    gt_by_text = {(s["claim"], s["evidence"]): s["ground_truth_supported"] for s in s100["samples"]}
    rows = _result()["per_judge_rows"]["D1b"]
    s100_rows = {s["id"]: s for s in s100["samples"]}
    # 每行的 gt 由文本决定(与上游一致),而非由中性 id 决定
    for row in rows:
        src = s100_rows[row["orig_id"]]
        assert row["gt"] == gt_by_text[(src["claim"], src["evidence"])]
    # 中性 id 已打乱:N 编号递增时,gt 非单调递增(若按 id 排序原样本则不会出现这种交错)
    by_neutral = sorted(rows, key=lambda r: r["neutral_id"])
    gt_seq = [int(r["gt"]) for r in by_neutral]
    assert gt_seq != sorted(gt_seq), gt_seq  # 存在 True 出现在 False 之后 => 打乱生效
