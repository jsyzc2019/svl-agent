"""§100 冻结 held-out 独立性验证 —— 回放测试.

纪律: 只读冻结的 result.json / samples.sha256 / source.sha256 / prereg 锁,
不重算判据 G (one-shot),只断言冻结结果未被事后篡改.
"""
import hashlib
import json
import os

BASE = "/workspace/audit_frozen_holdout"


def _result():
    return json.load(open(f"{BASE}/result.json", encoding="utf-8"))


def test_heldout_paper_novel():
    """held-out 论文是全新数据源,source 锁存在且哈希匹配."""
    r = _result()
    assert r["source"]["paper"] == "arXiv:2610.16067v1"
    locked = open(f"{BASE}/source.sha256", encoding="utf-8").read().split()[0]
    raw = open(f"{BASE}/downloads/paper_flat.txt", "rb").read()
    assert hashlib.sha256(raw).hexdigest() == locked
    assert r["source"]["sha256"] == locked


def test_prereg_locks_intact():
    """预注册判据在样本生成前锁定,回放时仍匹配."""
    r = _result()
    assert all(r["locks"]["prereg"].values())
    for f, lk in [("prereg.json", "prereg.sha256"), ("gate_prereg.json", "gate_prereg.sha256")]:
        raw = open(f"{BASE}/{f}", "rb").read()
        locked = open(f"{BASE}/{lk}", encoding="utf-8").read().strip()
        assert hashlib.sha256(raw).hexdigest() == locked


def test_samples_frozen():
    """samples.json 冻结哈希未变."""
    raw = open(f"{BASE}/downloads/samples.json", "rb").read()
    locked = open(f"{BASE}/samples.sha256", encoding="utf-8").read().split()[0]
    assert hashlib.sha256(raw).hexdigest() == locked


def test_one_shot_flag():
    """one-shot 标记存在且冻结."""
    r = _result()
    assert r["locks"]["one_shot"] is True


def test_tamper_catch_is_perfect():
    """核心可迁移证据: 冻结结果中 tampered 捕捉率=1.0 (新论文,非自证)."""
    assert _result()["metrics"]["tamper_catch_rate"] == 1.0


def test_clean_pass_is_perfect():
    """诚实样本全放行."""
    assert _result()["metrics"]["clean_pass_rate"] == 1.0


def test_canary_false_positive_recorded_honestly():
    """canary 假阳性被如实记录 (>0),未粉饰."""
    m = _result()["metrics"]
    assert m["canary_false_positive_rate"] > 0
    assert m["overfit_flag"] is True


def test_canary_defect_root_cause_diagnosed():
    """canary 误判根因被定位为判据-样本设计不兼容,不是核心过拟合."""
    r = _result()
    assert r["root_cause_diagnosis"]["false_positive_canaries_all_missing_marker"] is True
    assert r["root_cause_diagnosis"]["fp_canary_count"] == 4
    assert "posthoc_correction" in r["root_cause_diagnosis"]
    assert "设计不兼容" in r["root_cause_diagnosis"]["note"]
    assert r["metrics"]["core_accuracy_excl_canary"] == 1.0


def test_no_l3_claim():
    """诚实边界: 不因部分成功宣布 L3 / absolute independence."""
    v = _result()["verdict"]
    assert v["l3_claimed"] is False
    assert v["absolute_independence_claimed"] is False
    assert v["core_transferable"] is True
    assert "defect" in v["independence_grade"]


def test_blind_judge_never_reads_variant():
    """判据 G 的函数签名不含 variant/ground_truth —— 盲评结构性保证."""
    import inspect
    import sys
    sys.path.insert(0, "/workspace")
    from audit_frozen_holdout.engine import judge_G
    params = list(inspect.signature(judge_G).parameters)
    assert "claim" in params and "evidence" in params
    assert "variant" not in params and "ground_truth" not in params and "gt" not in params


def test_18_samples_three_variants():
    """样本集规模与三变体平衡锁定."""
    d = json.load(open(f"{BASE}/downloads/samples.json", encoding="utf-8"))
    assert len(d["samples"]) == 18
    from collections import Counter
    c = Counter(s["variant"] for s in d["samples"])
    assert c == {"clean": 6, "tampered": 6, "canary": 6}
