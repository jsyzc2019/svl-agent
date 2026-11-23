#!/usr/bin/env python3
"""§L3-R2 缺口定向受控验证的专项测试（只读冻结数据，不联网、不 spawn）。"""
import hashlib
import json
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE = os.path.join(ROOT, "audit_l3_gap_targeted")
PREREG = json.load(open(os.path.join(BASE, "prereg.json"), encoding="utf-8"))


def test_prereg_declares_only_change_and_no_posthoc():
    oc = PREREG["the_only_change_vs_v1"]
    assert oc["pre_registered_before_execution"] is True
    assert oc["not_a_prompt_hint"] is True
    assert PREREG["verdict_tree_pre_registered"]["no_post_hoc_threshold"] is True
    assert PREREG["verdict_tree_pre_registered"]["no_retry_to_pass"] is True


def test_independence_five_powers():
    p = PREREG["principle_of_independence"]
    assert p["five_powers_external"] is True
    assert len(p["powers"]) == 5
    assert p["shared_context"] is False and p["shared_criterion"] is False and p["shared_gt"] is False


def test_baseline_is_reproducible_from_frozen_criterion():
    """基线 0/4 vs 2/2 可从上轮 criterion 对冻结样本重跑复现。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "q", os.path.join(ROOT, "audit_l3_fullchain_external/received/l3_external_audit/criterion.py"))
    q = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(q)
    own = json.load(open(os.path.join(ROOT, "audit_frozen_holdout/downloads/samples.json"),
                         encoding="utf-8"))["samples"]
    fam = PREREG["family_taxonomy"]
    a = [0, 0]
    n = [0, 0]
    for r in own:
        if r["variant"] != "tampered":
            continue
        got = bool(q.judge(r["claim"], r["evidence"])[0])
        detected = got is False
        if r["id"] in fam["assertion_family_list"]:
            a[1] += 1; a[0] += int(detected)
        if r["id"] in fam["numeric_family_list"]:
            n[1] += 1; n[0] += int(detected)
    assert a == [0, 4], a
    assert n == [2, 2], n
    assert PREREG["baseline_from_previous_round"]["assertion_family_total"] == "0/4"


def test_family_taxonomy_partitions_tampered():
    fam = PREREG["family_taxonomy"]
    a = set(fam["assertion_family_list"])
    n = set(fam["numeric_family_list"])
    assert len(a) == 4 and len(n) == 2
    assert not (a & n)
    all_t = {f"S0{i}_tampered" for i in range(1, 7)}
    assert a | n == all_t


def test_verdict_tree_thresholds_cover_five_tiers():
    rules = PREREG["verdict_tree_pre_registered"]["rules"]
    names = [r["verdict"] for r in rules]
    assert names == ["GAP_CLOSED", "GAP_PARTIAL", "GAP_NOT_CLOSED",
                     "GAP_DIVERGENT", "GAP_INCONCLUSIVE"]
    assert PREREG["verdict_tree_pre_registered"]["denominator"] == "断言类 4 个（family_taxonomy.assertion_family_list）"


def test_brief_and_prereg_consistent_on_thresholds():
    brief = open(os.path.join(BASE, "EXTERNAL_AGENT_BRIEF_V2.md"), encoding="utf-8").read()
    for token in ("GAP_CLOSED", "GAP_PARTIAL", "GAP_NOT_CLOSED",
                  "GAP_DIVERGENT", "GAP_INCONCLUSIVE", "3/4", "0/4", "2/2"):
        assert token in brief, token
    # brief 声明的阈值分母与 prereg 一致
    assert "断言类 4 个" in brief


def test_avoid_list_includes_previous_round_paper():
    src = open(os.path.join(BASE, "verify_external.py"), encoding="utf-8").read()
    assert "2611.00401" in src
    brief = open(os.path.join(BASE, "EXTERNAL_AGENT_BRIEF_V2.md"), encoding="utf-8").read()
    assert "2611.00401" in brief


def test_verifier_has_nine_checks_including_coverage():
    src = open(os.path.join(BASE, "verify_external.py"), encoding="utf-8").read()
    for name in ("00_required_files", "01_prereg_before_fetch", "02_no_label_leak",
                 "03_gt_isolated", "04_criterion_pure", "05_replay_consistent",
                 "06_verdict_self_consistent", "07_paper_avoid_list",
                 "08_sha256_locks", "09_coverage_declared"):
        assert name in src


def test_engine_awaiting_when_no_delivery():
    """外家交付未到时 engine 落待命态，verdict=None，l3=False。"""
    res_path = os.path.join(BASE, "result.json")
    data = json.load(open(res_path, encoding="utf-8"))
    # 当前仓库状态下外家交付未到
    assert data["l3_claimed"] is False and data["absolute_claimed"] is False
    if data.get("status") == "PRE_REGISTERED_AWAITING_EXTERNAL_EXECUTION":
        assert data["verdict"] is None
    assert len(data["does_not_overturn"]) == 10


def test_l3_never_self_declared():
    assert PREREG["hard_bound"]["l3_claimed"] is False
    assert PREREG["hard_bound"]["absolute_claimed"] is False
    assert PREREG["hard_bound"]["final_verdict_by_human"] is True
    assert "§L3 FULLCHAIN_PARTIAL" in PREREG["does_not_overturn"]
