"""§4S74 守卫：GREEN_TESTS_BUT_UNVERIFIED_TRUTH 落差收敛（补锚点+只读清单）。

预注册 prereg_gap_convergence_20261128.json SHA 5953c18d… 改码前锁死。
纪律：补锚点不改verdict(非刷绿)；收敛清单逐条摊开不替裁定；负向注入反刷绿；零副作用。
"""
import hashlib
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kernel as K

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(HERE)


# ---------------- G2: 补锚点非刷绿 + 真实数据 ----------------

def test_new_tags_exist_and_fix_three_directions():
    """3个新tag确实命中那3个真实机制方向。"""
    assert K._tags_of("帕累托次优随机游走，脚印成路") - {"general"} >= {"pareto_walk"}
    assert K._tags_of("向外求新刺激，本底好奇心驱动") - {"general"} >= {"restless_seek"}
    assert K._tags_of("听到外部世界的呼唤，1条未读消息") - {"general"} >= {"external_call"}


def test_backfill_anchors_did_not_change_any_verdict():
    """铁证:补锚点前后11条心跳verdict逐条零改变(verdict只读guard.state)。"""
    pre = json.load(open(os.path.join(HERE, "pre_patch_gap_convergence",
                                      "verdict_baseline.json"), encoding="utf-8"))["verdicts"]
    now = [K._direction_content_verdict(
        hb.get("phase_analyze_guard"), hb.get("direction"))["verdict"]
        for hb in K._load_heartbeats()]
    assert now == pre, (now, pre)


def test_weak_evidence_reduced_real():
    """弱证据 5→0,但补判8/缺口14如实保留,flag未刷绿。"""
    ce = K.conclusion_evidence_probe()
    assert ce["pass_weak_count"] == 0
    b = K.verdict_at_birth_probe()
    assert b["authentic_birth_count"] == 2
    assert b["backfilled_sync_count"] == 8
    assert K.regression_vs_gap_probe()["unresolved_gap_count"] == 14
    assert K.test_green_vs_production_probe()["gap_flag"] == "GREEN_TESTS_BUT_UNVERIFIED_TRUTH"


def test_convergence_probe_four_gaps_intact():
    """收敛清单四类齐全,actionability标注正确,口径区分清楚。"""
    r = K.gap_convergence_probe()
    ids = {g["id"] for g in r["four_gaps"]}
    assert ids == {"post_hoc_backfill", "unresolved_gaps", "weak_evidence", "test_green"}
    amap = {g["id"]: g["actionability"] for g in r["four_gaps"]}
    assert amap["post_hoc_backfill"] == "IMMUTABLE"
    assert amap["unresolved_gaps"] == "USER_DECISION"
    assert amap["weak_evidence"] == "MECHANICAL_FIXED"
    assert amap["test_green"] == "TEST_SIDE"
    bf = [g for g in r["four_gaps"] if g["id"] == "post_hoc_backfill"][0]
    assert bf["count_synced"] == 8  # 与 backfilled_sync_count 同口径
    assert bf["count"] == bf["count_synced"] + bf["count_other_state"]
    assert "判定权归用户" in r["one_page"]
    assert r["verdict_unchanged"] is True and r["consumed"] is False
    assert r["is_gate_verdict"] is False


# ---------------- G3: 负向注入——反刷绿/非恒真 ----------------

def test_no_greenwash_when_only_weak_fixed(monkeypatch):
    """即使弱证据已修为0,只要补判/缺口仍在,flag必须还是GREEN_TESTS_BUT_UNVERIFIED_TRUTH。"""
    monkeypatch.setattr(K, "conclusion_evidence_probe", lambda: {"pass_weak_count": 0})
    r = K.test_green_vs_production_probe()
    assert r["weak_evidence"] == 0
    assert r["gap_flag"] == "GREEN_TESTS_BUT_UNVERIFIED_TRUTH"  # 补判8>就位2 仍触发


def test_flag_flips_only_when_ledger_truly_aligned(monkeypatch):
    """只有当补判≤就位、零缺口、零弱证据全满足,flag才翻ALIGNED。"""
    monkeypatch.setattr(K, "verdict_at_birth_probe", lambda: {
        "authentic_birth_count": 10, "backfilled_sync_count": 0, "per_heartbeat": []})
    monkeypatch.setattr(K, "regression_vs_gap_probe", lambda: {
        "unresolved_gap_count": 0, "unresolved_gap_verdict_dist": {}})
    monkeypatch.setattr(K, "conclusion_evidence_probe", lambda: {
        "pass_weak_count": 0, "per_heartbeat": []})
    r = K.test_green_vs_production_probe()
    assert r["gap_flag"] == "ALIGNED"


def test_convergence_snapshot_reads_ledger(monkeypatch, tmp_path):
    """注入历史快照账本,trend从NO_PRIOR变CHANGED/UNCHANGED,非恒真。"""
    ledger = tmp_path / "gap_ledger.jsonl"
    with open(ledger, "w", encoding="utf-8") as f:
        f.write(json.dumps({"gap_flag": "OLD_FLAG", "backfilled": 99,
                            "unresolved_gaps": 99, "weak_evidence": 99}) + "\n")
    r = K.gap_convergence_probe(ledger_path=str(ledger))
    assert r["snapshot"]["trend"] == "CHANGED"
    assert r["snapshot"]["prior"]["backfilled"] == 99

    with open(ledger, "w", encoding="utf-8") as f:
        f.write(json.dumps(r["snapshot"] | {"prior": None, "trend": None}) + "\n")
    r2 = K.gap_convergence_probe(ledger_path=str(ledger))
    assert r2["snapshot"]["trend"] == "UNCHANGED"


def test_dirty_gap_key_exposed_not_parsed():
    """缺口里的脏key(dict字符串化)必须dirty_key=true原样保留。"""
    r = K.gap_convergence_probe()
    gap = [g for g in r["four_gaps"] if g["id"] == "unresolved_gaps"][0]
    dirty = [row for row in gap["rows"] if row["dirty_key"]]
    assert len(dirty) >= 1
    assert any("DESTEER_PARTIAL" in row["verdict_key"] for row in dirty)


# ---------------- 零副作用 ----------------

def test_authoritative_state_untouched():
    expected = {
        "authoritative_state.json": "5f7a258483810bda4c5ea37dd5eb613bb17aea50807ec84379475952947091ee",
        "life_kernel/constitution.json": "fe56291b3aa036b6c14664bf7c6dc855dc2bf945fccb7ed8633c9dcd7e6b254e",
        "life_kernel/data/heartbeat_log.jsonl": "ea749f76826dc59c0a964f22a4563e38120c062fb18c9093806395b26110ad35",
        "life_kernel/data/inbound_inbox.jsonl": "8806b248883658a160aabd4450a20588f01420169894b95df5b6f0de810a34e7",
    }
    for rel, exp in expected.items():
        p = os.path.join(ROOT, rel)
        assert hashlib.sha256(open(p, "rb").read()).hexdigest() == exp, rel


def test_prereg_sha_locked():
    p = os.path.join(ROOT, "prereg_gap_convergence_20261128.json")
    assert hashlib.sha256(open(p, "rb").read()).hexdigest() == \
        "5953c18d11934ed6ac6efeeba5e50ae2d826759ff336430921f56f5ef72ec679"
