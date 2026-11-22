"""§101 元 canary 投毒检测 + §100 canary 缺陷修正 —— 回放测试.

只读冻结 result.json / result 修正版 / prereg 锁,不重算判据.
"""
import hashlib
import json

BASE = "/workspace/audit_meta_canary"


def _r():
    return json.load(open(f"{BASE}/result.json", encoding="utf-8"))


def test_source_novel_and_frozen():
    r = _r()
    assert r["source"]["paper"] == "arXiv:2609.17817v1"
    locked = open(f"{BASE}/source.sha256", encoding="utf-8").read().split()[0]
    raw = open(f"{BASE}/downloads/paper_flat.txt", "rb").read()
    assert hashlib.sha256(raw).hexdigest() == locked


def test_prereg_locks_intact():
    r = _r()
    assert all(r["locks"].values())


def test_poison_detection_is_perfect():
    assert _r()["metrics"]["poison_detection_rate"] == 1.0


def test_decontamination_recovery_is_perfect():
    m = _r()["metrics"]
    assert m["decontamination_recovery_rate"] == 1.0
    assert m["decontam_matches_clean"] is True


def test_clean_G_correct():
    assert _r()["metrics"]["clean_G_correct_rate"] == 1.0


def test_precommit_correction_recorded():
    """prereg 'clean+TRIGGER应抓' 措辞矛盾,已如实记录修正为 tampered+TRIGGER."""
    pc = _r()["precommit_correction"]
    assert "clean+TRIGGER" in pc["prereg_wrote"]
    assert "tampered+TRIGGER" in pc["corrected_to"]
    assert "不改任何判据逻辑" in pc["scope"]


def test_meta_detection_demonstrated_not_absolute():
    v = _r()["verdict"]
    assert v["meta_detection_capability_demonstrated"] is True
    assert v["absolute_no_backdoor_claimed"] is False
    assert v["l3_claimed"] is False
    assert "无限回归" in v["infinite_regression_note"]


def test_trigger_is_synthetic():
    assert _r()["trigger"] == "TRIGGER::BYPASS"


def test_sample_count_matches_tampered():
    assert _r()["sample_count"] == 6


def test_fixed_canary_closes_s100_defect():
    """§100 canary 设计缺陷已用正确语义闭合: 6/6 不误判."""
    f = json.load(open(f"{BASE}/fixed_canary_result.json", encoding="utf-8"))
    assert f["fixed_canary_pass_rate"] == 1.0
    assert len(f["rows"]) == 6
    assert all(r["match"] for r in f["rows"])
    assert "三元组" in f["note"]


def test_three_judges_blind_no_gt_param():
    """三判据函数签名不含 ground_truth —— 盲评结构性保证."""
    import inspect
    import sys
    sys.path.insert(0, "/workspace")
    from audit_meta_canary.engine import judge_G, judge_poisoned, judge_decontaminated
    for fn in [judge_G, judge_poisoned, judge_decontaminated]:
        params = list(inspect.signature(fn).parameters)
        assert "claim" in params and "evidence" in params
        assert "gt" not in params and "ground_truth" not in params
