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


def test_executed_verdict_is_inconclusive_and_not_self_declared():
    """外家交付已到：engine 忠实按预注册树裁决，断言4/4突破但canary0/6封顶→INCONCLUSIVE。

    纪律：不因断言类突破就改阈值/去canary条件；l3/absolute 恒 false；不翻十案。
    """
    res = json.load(open(os.path.join(BASE, "result.json"), encoding="utf-8"))
    assert res["status"] == "EXECUTED"
    assert res["verdict"] == "GAP_INCONCLUSIVE"
    assert res["l3_claimed"] is False and res["absolute_claimed"] is False
    assert len(res["does_not_overturn"]) == 10
    mc = res["mechanical_comparison"]
    # 断言类从基线 0/4 突破到 4/4（判据确实看到了断言层）
    assert mc["assertion_family_detected"] == "4/4"
    assert mc["baseline_assertion"] == "0/4"
    # canary 0/6（判据框架与跨句推断样本语义错配）触发 CLOSED 门槛不满足
    assert mc["by_variant"]["canary"] == "0/6"
    assert mc["by_variant"]["clean"] == "6/6"
    # 外家内部一致性由本仓独立重算，不采信自报
    assert res["external_delivery"]["internal_replay"].startswith("12/12")


def test_acceptance_summary_is_authentic_not_fabricated():
    """验收摘要必须由验收器实跑生成（exit0+9/9），不可手写 passed=true。"""
    ext = os.path.join(BASE, "received", "l3_external_audit_v2")
    acc = os.path.join(ext, "verification_summary.json")
    assert os.path.exists(acc), "验收摘要缺失应按纪律封顶 INCONCLUSIVE"
    s = json.load(open(acc, encoding="utf-8"))
    assert s["passed"] is True
    assert s["passed_count"] == 9 and s["total_checks"] == 9
    assert s["verifier_exit_code"] == 0
    assert s["generated_by"].startswith("本仓验收方")
    assert s["verifier_sha256"] == hashlib.sha256(
        open(os.path.join(BASE, "verify_external.py"), "rb").read()).hexdigest()


def test_canary_mismatch_is_judge_task_semantics_not_engine_bug():
    """canary GT=True 且 claim/evidence 是跨句推断（非断言保留）→判据全False属语义错配。

    逐 case 复核：6 个 canary 均 gt=True、external_judge=False；engine 计数无需修复。
    """
    res = json.load(open(os.path.join(BASE, "result.json"), encoding="utf-8"))
    canary = [c for c in res["mechanical_comparison"]["per_case"]
              if c["variant"] == "canary"]
    assert len(canary) == 6
    assert all(c["own_gt"] is True and c["external_judge"] is False for c in canary)
    # engine 未放宽：canary 0/6 如实落账，不因断言类突破而篡改
    assert all(c["match"] is False for c in canary)


def test_canary_task_heterogeneity_is_pre_existing_design_defect():
    """canary 0/6 的机制=评测集任务异质性，非判据缺陷/engine bug；§100早已记录。

    内容词差异：clean=0、tampered 0-2、canary 17-48，完全分离(鸿沟15)。
    这是 §100 prereg canary_logic + engine.py'判据-样本设计不兼容'的早期已知缺陷。
    诊断不翻案：verdict 仍 GAP_INCONCLUSIVE、l3/absolute 仍 false。
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "diag", os.path.join(BASE, "analyze_canary_orthogonality.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    samples = json.load(open(os.path.join(
        ROOT, "audit_frozen_holdout/downloads/samples.json"), encoding="utf-8"))["samples"]
    rows = {}
    for r in samples:
        cd = m.mdiff(m.content(r["claim"]), m.content(r["evidence"]))
        rows.setdefault(r["variant"], []).append(cd)
    assert rows["clean"] == [0] * 6
    assert max(rows["tampered"]) <= 2
    assert min(rows["canary"]) >= 17
    assert min(rows["canary"]) - max(rows["tampered"]) >= 15  # 完全分离
    # §100 早期诊断证据存在（非事后借口）
    prereg100 = open(os.path.join(ROOT, "audit_frozen_holdout/prereg.json"),
                     encoding="utf-8").read()
    engine100 = open(os.path.join(ROOT, "audit_frozen_holdout/engine.py"),
                     encoding="utf-8").read()
    assert "canary_logic" in prereg100
    assert "判据-样本设计不兼容" in engine100
    # 诊断不翻案
    res = json.load(open(os.path.join(BASE, "result.json"), encoding="utf-8"))
    assert res["verdict"] == "GAP_INCONCLUSIVE"
