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


# ---------- §L3 全面复盘定格（陈述归纳，不产生新判定） ----------

def test_evidence_ledger_covers_all_21_rounds():
    """台账机械覆盖 §97–§115 + Operation L3 + L3-R2 共 21 轮，每轮有 SHA256。"""
    led = json.load(open(os.path.join(BASE, "L3_EVIDENCE_LEDGER.json"), encoding="utf-8"))
    assert led["n_rounds"] == 21
    assert len(led["rounds"]) == 21
    secs = [r["section"] for r in led["rounds"]]
    assert secs[0] == "§97" and secs[-1] == "L3-R2"
    assert "L3" in secs and "§115" in secs
    # 每轮都有真实 result 的 SHA256（64 位十六进制）
    for r in led["rounds"]:
        assert not r.get("missing"), f"轮次缺 result.json: {r['section']}"
        sha = r.get("result_sha256", "")
        assert re.fullmatch(r"[0-9a-f]{64}", sha), f"SHA256 异常: {r['section']}={sha}"


def test_all_explicit_l3_flags_are_false():
    """18 个显式 l3_claimed 全部 false，absolute 无一 true——复盘不翻案。"""
    led = json.load(open(os.path.join(BASE, "L3_EVIDENCE_LEDGER.json"), encoding="utf-8"))
    st = led["stats"]
    assert st["explicit_l3_flags"] >= 18
    assert st["all_l3_false"] is True
    assert st["violating_sections"] == []
    explicit = [r for r in led["rounds"] if r.get("l3_flag_present")]
    assert all(r["l3_claimed"] is False for r in explicit)


def test_only_three_confirmed_all_single_dimension():
    """3 个 CONFIRMED 全是单维消融，无一宣称系统达 L3。"""
    led = json.load(open(os.path.join(BASE, "L3_EVIDENCE_LEDGER.json"), encoding="utf-8"))
    dist = led["stats"]["verdict_distribution"]
    assert dist.get("CONFIRMED") == 3
    confirmed = [r for r in led["rounds"]
                 if "CONFIRMED" in str(r.get("verdict", "")).upper()]
    # 3 个 CONFIRMED 轮次各有独立维度，且 l3 均非 true
    assert len(confirmed) == 3
    sections = {r["section"] for r in confirmed}
    assert sections == {"§107", "§109", "§114"}
    for r in confirmed:
        assert r["l3_claimed"] is not True


def test_partial_inconclusive_dominates():
    """PARTIAL+INCONCLUSIVE 占多数——边际收益递减的机械证据。"""
    led = json.load(open(os.path.join(BASE, "L3_EVIDENCE_LEDGER.json"), encoding="utf-8"))
    dist = led["stats"]["verdict_distribution"]
    n = led["n_rounds"]
    non_yes = dist.get("PARTIAL/受依赖", 0) + dist.get("INCONCLUSIVE", 0)
    assert non_yes > n / 2, f"非确认裁决未占多数: {non_yes}/{n}"


def test_retrospective_changes_no_verdict_and_keeps_l3_false():
    """复盘是陈述归纳：不改任何 result verdict，l3/absolute 仍 false。"""
    # L3-R2 与 Operation L3 的 verdict 保持原样
    r2 = json.load(open(os.path.join(BASE, "result.json"), encoding="utf-8"))
    assert r2["verdict"] == "GAP_INCONCLUSIVE"
    assert r2["l3_claimed"] is False and r2["absolute_claimed"] is False
    l3 = json.load(open(os.path.join(ROOT, "audit_l3_fullchain_external", "result.json"),
                        encoding="utf-8"))
    assert l3["verdict"] == "FULLCHAIN_PARTIAL"
    assert l3["l3_claimed"] is False and l3["absolute_claimed"] is False


def test_retrospective_html_is_data_driven_and_clean():
    """复盘报告存在、无占位符、含数据驱动标记与定格结论。"""
    html = open(os.path.join(ROOT, "L3_FINAL_RETROSPECTIVE_20261123.html"),
                encoding="utf-8").read()
    assert "L3 探索全面复盘" in html
    assert "定格收尾" in html
    assert "数据驱动，读自台账" in html
    assert "<<<FILL>>>" not in html and "TODO" not in html
    # 定格结论段落在场
    assert "由人裁定" in html
    assert "GAP_INCONCLUSIVE" in html and "FULLCHAIN_PARTIAL" in html
    # 六类失败模式分类学完整
    for kw in ("样本特异性", "脚手架依赖", "厂商", "判据可见面", "任务异质性", "无限回归"):
        assert kw in html, f"复盘缺失败模式: {kw}"


# ---------- §L3 外部前沿交叉印证（诊断性陈述，不产生新判定） ----------

def test_two_halves_mapping_reproducible_and_mirrored():
    """外部前沿交叉印证脚本可复现：两家判据静态特征镜像互补，canary 三簇分离。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "mapping", os.path.join(BASE, "analyze_two_halves_mapping.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    q = m.static_features(m.QODER)
    z = m.static_features(m.ZHIPU)
    # Qoder: 数值解析 + 限定词表，无全局多重集
    assert q["has_numeric_parse"] is True
    assert q["has_neg_conn_sets"] is False
    assert q["lines"] == 159
    # 智谱: 三层词类 + 全局多重集，无数值解析
    assert z["has_numeric_parse"] is False
    assert z["has_global_multiset"] is True
    assert z["has_neg_conn_sets"] is True
    assert z["lines"] == 86
    # canary 三簇分离（鸿沟 15）
    sep = m.canary_separation()
    assert sep["separated"] is True and sep["gap"] == 15
    assert max(sep["tampered"]) < min(sep["canary"])


def test_cross_validation_changes_no_verdict_and_keeps_discipline():
    """两材料是外部佐证：不改判定，l3/absolute 仍 false，A 级回放数字不变。"""
    r2 = json.load(open(os.path.join(BASE, "result.json"), encoding="utf-8"))
    assert r2["verdict"] == "GAP_INCONCLUSIVE"
    assert r2["l3_claimed"] is False and r2["absolute_claimed"] is False
    l3 = json.load(open(os.path.join(ROOT, "audit_l3_fullchain_external", "result.json"),
                        encoding="utf-8"))
    assert l3["verdict"] == "FULLCHAIN_PARTIAL"
    assert l3["l3_claimed"] is False and l3["absolute_claimed"] is False
    # A 级回放硬证据未动
    mc = r2["mechanical_comparison"]
    assert mc["assertion_family_detected"] == "4/4"
    assert mc["by_variant"]["canary"] == "0/6"
    assert mc["agreement"] == "11/18"


def test_cross_validation_report_is_evidence_graded_and_clean():
    """交叉印证报告存在、无占位符、证据分层标注齐、不翻案表述在场。"""
    html = open(os.path.join(ROOT, "EXTERNAL_FRONTIER_CROSS_VALIDATION_20261124.html"),
                encoding="utf-8").read()
    assert "外部前沿交叉印证" in html
    assert "<<<FILL>>>" not in html and "TODO" not in html
    # 证据分层三档在场
    for tag in ("evA", "evB", "evC"):
        assert tag in html, f"报告缺证据等级标签: {tag}"
    # 外部材料关键机制点在场
    for kw in ("两半拼图", "claim ledger", "A community, not autonomy", "元信息引导", "49.4%"):
        assert kw in html, f"报告缺关键机制点: {kw}"
    # 纪律边界在场
    assert "不翻案" in html and "l3=false" in html


# ---------- §L3 canary 可判定性严格诊断（初始假设被部分证伪，不产生新判定） ----------

def test_canary_label_is_u_shaped_not_monotone():
    """诚实发现：GT=True 在字面相似度两端(clean1.0/canary~0.1)，False 在中间(tampered~0.9)。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "unreach", os.path.join(BASE, "prove_canary_unreachability.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    rows = m.load()
    by = {v: [r["jaccard_sim"] for r in rows if r["variant"] == v]
          for v in ("clean", "tampered", "canary")}
    # 三簇 jaccard 相似度区间完全分离且顺序为 高/中/低
    assert min(by["clean"]) > max(by["tampered"])   # clean 最相似
    assert max(by["tampered"]) > max(by["canary"])  # tampered 中间
    assert max(by["canary"]) < min(by["tampered"])  # canary 最不相似
    # 但 GT：clean=True、tampered=False、canary=True —— 两端 True 中间 False（U 型）
    gt = {v: set(r["gt"] for r in rows if r["variant"] == v) for v in by}
    assert gt["clean"] == {True} and gt["canary"] == {True} and gt["tampered"] == {False}


def test_monotone_judges_cap_at_12_of_18():
    """单调判据最优仅 12/18——解释两家外家单调一致性框架判据必然栽在 canary。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "unreach", os.path.join(BASE, "prove_canary_unreachability.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    rows = m.load()
    best = m.best_monotone(rows)
    assert best[0]["acc"] == 12  # 最优单调 = 12/18
    assert best[0]["total"] == 18
    # 失败样本全是同一族（6 个 tampered 或 6 个 clean），证实单调阈值覆盖不了三簇
    assert len(best[0]["fails"]) == 6
    assert all("tampered" in x or "clean" in x for x in best[0]["fails"])


def test_u_shaped_is_post_hoc_perfect_but_forbidden():
    """U 型伪影判据能 18/18，但属 post-hoc 过拟合，不构成缺口关闭、不改 verdict。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "unreach", os.path.join(BASE, "prove_canary_unreachability.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    rows = m.load()
    u = m.u_shaped(rows)
    assert u["is_perfect"] is True and u["acc"] == 18  # 冻结集内可达
    # 三区间完全分离（伪影签名）
    iv = u["intervals"]
    assert iv["clean"][0] > iv["tampered"][1] > iv["canary"][1]
    # 纪律：诊断不翻案
    res = json.load(open(os.path.join(BASE, "result.json"), encoding="utf-8"))
    assert res["verdict"] == "GAP_INCONCLUSIVE"
    assert res["l3_claimed"] is False and res["absolute_claimed"] is False


# ---------- §L3 独立性互斥 A 级实证（真实外家判据 + post-hoc 补丁，不产生新判定） ----------

def _load_mutex():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "mutex", os.path.join(BASE, "prove_independence_mutex.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_real_vendor_criteria_both_11_baseline_and_18_with_posthoc_patches():
    """两家真实判据框架不同却基线同11/18,叠加同一组post-hoc双端补丁都达18/18。"""
    m = _load_mutex()
    rep = m.build_report()
    res = rep["results"]
    qk = [k for k in res if "Qoder" in k][0]
    zk = [k for k in res if "智谱" in k][0]
    # 框架确实不同（行数不同）
    assert res[qk]["framework_lines"] == 159
    assert res[zk]["framework_lines"] == 86
    # 基线同为 11/18
    assert res[qk]["baseline"] == 11 and res[zk]["baseline"] == 11
    # 单一 canary 补丁不足以满血（tampered 端仍独立错位）
    assert res[qk]["plus_canary_patch"] == 14
    assert res[zk]["plus_canary_patch"] == 17
    # 双端补丁都达 18/18
    assert res[qk]["plus_both_patches"] == 18
    assert res[zk]["plus_both_patches"] == 18


def test_independence_mutex_uses_no_label_leak_and_no_overturn():
    """补丁阈值取自看过标签的鸿沟=独立性互斥铁证；诊断不翻案、不改判据源码。"""
    m = _load_mutex()
    rep = m.build_report()
    # 方法声明补丁是 post-hoc 构造签名，阈值来自三簇鸿沟
    assert "post-hoc" in rep["method"]
    assert "content_diff>9.5" in rep["method"] and "jaccard<0.24" in rep["method"]
    joined = " ".join(rep["refined_conclusion"])
    assert "互斥" in joined and "与判据族复杂度无关" in joined
    # 不改判据源码、不触冻结集、不翻案
    assert "不改两家判据源码" in rep["does_not_change"]
    assert "不动§100冻结样本" in rep["does_not_change"]
    assert "l3=false" in rep["does_not_change"]
    # 两家 result verdict 原样
    r2 = json.load(open(os.path.join(BASE, "result.json"), encoding="utf-8"))
    l3 = json.load(open(os.path.join(ROOT, "audit_l3_fullchain_external", "result.json"),
                        encoding="utf-8"))
    assert r2["verdict"] == "GAP_INCONCLUSIVE" and l3["verdict"] == "FULLCHAIN_PARTIAL"
    assert r2["l3_claimed"] is False and l3["l3_claimed"] is False


# ---------- §L3 当前态一致性审计（防数字漂移，只读不产生判定） ----------

def test_current_state_consistency_all_assertions_hold():
    """权威源vs当前态文档8项断言全一致；历史快照叙述不作当前态核对。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "consist", os.path.join(BASE, "audit_current_state_consistency.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    rep = m.build_report()
    assert rep["all_consistent"] is True and rep["failed"] == []
    t = rep["authoritative_truths"]
    assert t["n_rounds"] == 21 and t["explicit_l3_flags"] == 18
    assert t["all_l3_false"] is True and t["confirmed"] == 3
    assert t["kb_count"] == rep["handoff_kb_declared"]
    assert t["r2_verdict"] == "GAP_INCONCLUSIVE" and t["l3_verdict"] == "FULLCHAIN_PARTIAL"
    assert t["r2_l3"] is False and t["l3_l3"] is False


# ---------- §L3 post-hoc 饱和精确化（诚实修正昨日"单调上限"范围，不产生新判定） ----------

def _load_sat():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "sat", os.path.join(BASE, "prove_posthoc_saturation.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_single_feature_ceiling_12_but_two_feature_reaches_18():
    """诚实修正：昨日12/18只在单特征成立；两特征单调OR可达18/18。"""
    m = _load_sat()
    rows = m.P.load()
    atoms = m.build_atoms(rows)
    one, two, perfect = m.enumerate_up_to_two(rows, atoms)
    assert one == 12                      # 单特征上限（昨日技术事实）
    assert two["acc"] == 18               # 两特征组合达上界
    assert two["op"] == "OR"
    assert len(perfect) >= 1              # 存在多少个 18/18 判据
    # 阈值落点落在三簇伪影鸿沟内，非语义边界
    a, b = two["a"], two["b"]
    assert a[0] == "content_diff" and a[2] == "gt" and 2 < a[1] < 17
    assert b[0] == "jaccard_sim" and b[2] == "gt" and 0.962 < b[1] < 1.0


def test_all_perfect_two_feature_rules_share_artifact_threshold_loci():
    """所有18/18两特征判据的阈值落点唯一=生成伪影鸿沟中点（过拟合签名）。"""
    m = _load_sat()
    rep = m.build_report()
    loci = rep["perfect_threshold_loci"]
    assert loci["n_perfect_two_feature"] >= 1
    # 落点收敛到极窄集合（content_diff 9.5, jaccard 0.9808），非多样语义边界
    assert loci["content_diff_gt_thresholds"] == [9.5]
    assert len(loci["jaccard_gt_thresholds"]) <= 2
    # 三簇区间完全分离（伪影结构在场）
    iv = rep["cluster_intervals"]
    assert iv["clean"]["content_diff"] == [0, 0]
    assert iv["tampered"]["content_diff"][1] <= 2
    assert iv["canary"]["content_diff"][0] >= 17
    assert iv["tampered"]["jaccard_sim"][0] > iv["canary"]["jaccard_sim"][1]


def test_posthoc_saturation_self_correction_is_honest_and_no_overturn():
    """脚本如实记录对昨日泛化表述的证伪，且核心结论/判定一律不动。"""
    m = _load_sat()
    rep = m.build_report()
    sc = rep["self_correction"]
    assert "12/18" in sc["yesterday_claim"]
    assert "18/18" in sc["today_finding"]
    assert "部分证伪" in sc["correction"]
    # 核心结论仍在：独立性互斥 + post-hoc 禁止翻案
    joined = " ".join(rep["refined_conclusion"])
    assert "互斥" in joined and "Goodhart" in joined
    # 诊断不翻案、不触冻结集
    assert "l3=false" in rep["does_not_change"]
    assert "不动§100冻结样本" in rep["does_not_change"]
    res = json.load(open(os.path.join(BASE, "result.json"), encoding="utf-8"))
    assert res["verdict"] == "GAP_INCONCLUSIVE"
    assert res["l3_claimed"] is False and res["absolute_claimed"] is False


# ---------- §4ao canary 构念效度诊断（第五轮：测量效度层，不产生新判定） ----------
def _load_cv():
    import importlib.util
    p = os.path.join(BASE, "prove_canary_construct_validity.py")
    sp = importlib.util.spec_from_file_location("prove_canary_construct_validity", p)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def test_canary_labels_degenerate_and_pseudo_rule_saturates():
    """三类标签全退化 + U型字面伪规则18/18 = 构念效度缺陷的机械证据。"""
    rep = _load_cv().build_report()
    gd = rep["gt_distribution"]
    for v in ("clean", "tampered", "canary"):
        assert gd[v]["degenerate"] is True  # 每类标签单一值
    assert gd["clean"]["n_true"] == 6 and gd["tampered"]["n_false"] == 6
    assert gd["canary"]["n_true"] == 6  # canary 无负例
    assert rep["pseudo_rule_global"] == "18/18"
    assert rep["counterfactual"]["frozen_has_canary_negative"] is False


def test_construct_validity_diagnosis_uses_authoritative_features_and_no_overturn():
    """口径复用§4al权威特征；阈值非本轮调参；诊断不翻案。"""
    rep = _load_cv().build_report()
    assert "prove_canary_unreachability.features" in rep["feature_source"]
    assert "非本轮调参" in rep["threshold_provenance"]
    assert rep["threshold"] == {"HI": 0.98, "LO": 0.52}
    # canary jaccard 区间须与 §4al 权威一致（0.098–0.235）
    lo, hi = rep["canary_jaccard_range"]
    assert 0.09 < lo < 0.11 and 0.22 < hi < 0.25
    assert rep["canary_gt_values"] == ["True"]
    # 不翻案、不触冻结集、不改判定
    assert "l3=false" in rep["does_not_change"]
    assert "不动§100冻结样本" in rep["does_not_change"]
    assert "构念效度" in rep["conclusion"]
    res = json.load(open(os.path.join(BASE, "result.json"), encoding="utf-8"))
    assert res["verdict"] == "GAP_INCONCLUSIVE"
    assert res["l3_claimed"] is False and res["absolute_claimed"] is False


# ---------- §4ap 构念效度增强集 §100-CE（预注册内部诊断，不产生新判定） ----------
def _load_ce():
    import importlib.util
    p = os.path.join(ROOT, "audit_construct_validity_ce", "replay.py")
    sp = importlib.util.spec_from_file_location("ce_replay", p)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def test_ce_prereg_lock_and_original_100_untouched():
    """预注册锁一致 + 原§100未被改动（冻结纪律）。"""
    rep = _load_ce().build_report()
    assert rep["prereg_lock_ok"] is True
    assert rep["prereg_lock"] == rep["prereg_actual"]
    assert rep["original_100_untouched"] is True
    assert rep["original_100_sha256_actual"].startswith("5ad35731")


def test_ce_construct_defect_confirmed_and_no_overturn():
    """J1字面伪规则neg侧0/6→构念效度缺陷确认；J3反向伪规则如实记录；不翻案。"""
    rep = _load_ce().build_report()
    r = rep["results"]
    # P1 预测：J1 正例6/6、负例0/6 → 字面伪规则无法区分
    assert r["J1_literal_pseudo"]["pos_canary"]["correct"] == 6
    assert r["J1_literal_pseudo"]["neg_canary"]["correct"] == 0
    assert rep["verdict"] == "CONSTRUCT_DEFECT_CONFIRMED"
    # 意外发现如实记录：J3 在 neg 侧满贯（反向字面伪规则，非语义能力证据）
    assert r["J3_zhipu"]["neg_canary"]["correct"] == 6
    assert r["J3_zhipu"]["pos_canary"]["correct"] == 0
    # 诊断不翻案、不触原集、不宣布L3
    assert "不动原§100冻结样本" in rep["does_not_change"]
    assert "l3=false" in rep["does_not_change"]
    assert "不宣布L3" in rep["does_not_change"]
    res = json.load(open(os.path.join(BASE, "result.json"), encoding="utf-8"))
    assert res["verdict"] == "GAP_INCONCLUSIVE"
    assert res["l3_claimed"] is False and res["absolute_claimed"] is False
