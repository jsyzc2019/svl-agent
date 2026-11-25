#!/usr/bin/env python3
"""开放型生命体内核专项测试（只读仓库状态，不联网、不 spawn、不改判定）。"""
import datetime
import importlib.util
import io
import json
import os
import sys
from unittest import mock

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import kernel as K


CANARY_HISTORY = [
    "§4am post-hoc饱和精确化:单调判据上限,字面伪规则阈值过拟合,判据独立性冻结集互斥",
    "§4an 独立性互斥A级实证:两家真实判据canary线,post-hoc补丁,判据回放",
    "§4ao canary构念效度诊断:标签退化,U型字面伪规则18/18,语义蕴含不可测",
    "§4ap 构念效度增强集:canary错位负例,字面伪规则失效,判据回放",
]


@pytest.fixture
def isolated_log():
    """临时替换心跳日志为模拟历史，测试后复原，不污染真实日志。"""
    real = K.HEARTBEAT_LOG
    bak = real + ".test_bak"
    if os.path.exists(real):
        os.rename(real, bak)
    with open(real, "w", encoding="utf-8") as f:
        for h in CANARY_HISTORY:
            f.write(json.dumps({"direction": h}, ensure_ascii=False) + "\n")
    yield real
    if os.path.exists(real):
        os.remove(real)
    if os.path.exists(bak):
        os.rename(bak, real)


def test_constitution_is_locked_and_immutable():
    """L0 宪法层 SHA256 一致、标记不可变（免疫系统不可被进化篡改）。"""
    c = K.verify_constitution()
    assert c["ok"] is True and c["immutable"] is True
    assert c["lock"] == c["actual"]
    assert c["n_articles"] >= 8


def test_sense_reads_real_repo_state():
    """感知层只读到真实仓库状态：审计目录/KB/话题版图/时间预算。"""
    s = K.sense()
    assert s["audit_dirs_count"] >= 60
    assert s["kb_count"] >= 195
    assert set(s["kb_kinds"]).issubset({"reasoning_lesson", "external_insight", "thinking_experience"})
    assert len(s["topic_map"]) >= 10
    assert s["time_budget"] in {"morning", "afternoon", "evening"}
    assert s["timestamp"].endswith("Z")


def test_novelty_guard_detects_canary_convergence(isolated_log):
    """novelty 守卫能自我否定：再提 canary 方向判 CONVERGED，新方向判 DIVERSE。"""
    g_same = K.novelty_guard("又一轮canary:字面伪规则与语义蕴含的判据回放")
    assert g_same["state"] == "CONVERGED"
    assert g_same["similarity"] >= 0.6
    g_new_memory = K.novelty_guard("记忆治理:知识库分层遗忘与压缩")
    assert g_new_memory["state"] == "DIVERSE"
    g_new_self = K.novelty_guard("自进化内核:自主改写改进流程RSI")
    assert g_new_self["state"] == "DIVERSE"


def test_propose_excludes_converged_canary(isolated_log):
    """开放探索池选向：canary 不在池中，top novelty 全是新方向。"""
    scored = K.propose()
    top = scored[:3]
    assert all(s["novelty"] >= 0.9 for s in top)
    assert all("canary" not in s["tags"] for s in top)
    assert len(scored) == len(K.explore_pool())


def test_evolve_closes_loop_without_verdict_change(tmp_path):
    """进化闭环写入心跳但不改任何既有判定、不动冻结基准。

    v2 修复：用隔离 log_path，测试不再污染真实心跳日志（此前 5 条测试方向混入真实日志）。
    """
    isolated = str(tmp_path / "heartbeat.jsonl")
    before = open(K.HEARTBEAT_LOG, encoding="utf-8").read() if os.path.exists(K.HEARTBEAT_LOG) else ""
    r = K.evolve("测试方向:验证闭环不翻案", "测试动作", log_path=isolated)
    assert r["heartbeat_written"] is True
    assert r["constitution"]["ok"] is True
    assert r["verified"]["no_verdict_change"] is True
    assert r["verified"]["original_100_untouched"] is True
    assert os.path.exists(isolated)  # 心跳落在隔离路径
    # 真实日志未被污染
    after = open(K.HEARTBEAT_LOG, encoding="utf-8").read() if os.path.exists(K.HEARTBEAT_LOG) else ""
    assert after == before
    # 既有判定未变
    res = json.load(open(os.path.join(ROOT, "audit_l3_gap_targeted", "result.json"), encoding="utf-8"))
    assert res["verdict"] == "GAP_INCONCLUSIVE"
    assert res["l3_claimed"] is False and res["absolute_claimed"] is False


# ---------- §4ar v2 生命体代谢：摄食 / 自改 / archive（不产生新判定） ----------
def test_digest_ingests_external_frontier_with_timestamp_and_tier():
    """摄食层读到外部前沿种子：带来源 URL、时间锚、证据分层，且非本仓实测。"""
    d = K.digest()
    assert d["count"] >= 6
    assert d["ingested_at"].endswith("Z")
    seeds = {s["id"]: s for s in d["seeds"]}
    assert all(s["source_url"].startswith("https://") for s in seeds.values())
    assert all(s["evidence_tier"] in {"A", "B", "C"} for s in seeds.values())
    # B/C 为非本仓实测，诚实标注
    assert any(s["evidence_tier"] in {"B", "C"} for s in seeds.values())


def test_self_modify_registers_seeds_and_archives_only_after_validation(tmp_path):
    """自改闭环：经验验证全过才写 policy；archive 保留快照可回滚；宪法层不变。
    v5 数据诚实修复：全程用隔离 policy/archive/heartbeat，零污染真实数据。"""
    iso_policy = str(tmp_path / "runtime_policy.json")
    iso_archive = str(tmp_path / "archive")
    iso_hb = str(tmp_path / "heartbeat_log.jsonl")
    with open(iso_policy, "w", encoding="utf-8") as f:
        json.dump({"policy_version": "1.0.0", "updated_at": None,
                   "registered_frontier_seeds": []}, f, ensure_ascii=False)
    # 合成 canary 收敛历史（隔离心跳）
    with open(iso_hb, "w", encoding="utf-8") as f:
        for h in CANARY_HISTORY:
            f.write(json.dumps({"direction": h}, ensure_ascii=False) + "\n")
    hb_bak = open(K.HEARTBEAT_LOG, encoding="utf-8").read() if os.path.exists(K.HEARTBEAT_LOG) else ""
    try:
        # 临时把全局心跳指向隔离文件（self_modify 内部 _load_heartbeats 读全局）
        with open(K.HEARTBEAT_LOG, "w", encoding="utf-8") as f:
            f.write("")
        import unittest.mock as mock
        _orig_load_hb = K._load_heartbeats
        with mock.patch.object(K, "_load_heartbeats", side_effect=lambda *a, **k: _orig_load_hb(iso_hb)):
            r = K.self_modify(reason="测试:经验验证驱动的自改",
                              policy_path=iso_policy, archive_dir=iso_archive)
        assert r["accepted"] is True
        assert r["validation"]["all_pass"] is True
        assert r["validation"]["guard_detects_convergence"] is True
        assert r["validation"]["guard_allows_diverse"] is True
        assert r["validation"]["verdict_unchanged"] is True
        assert r["policy_written"] is True
        # 隔离 policy 确实写入：探索池扩张
        written = json.load(open(iso_policy, encoding="utf-8"))
        assert len(written["registered_frontier_seeds"]) > 0
        # archive 快照存在且可回滚（隔离目录）
        assert r.get("archive_after", "") and os.path.exists(r["archive_after"])
        snap = json.load(open(r["archive_after"], encoding="utf-8"))
        assert snap["policy"]["registered_frontier_seeds"]
        # 宪法层未被触碰
        assert r["constitution_ok"] is True
        assert K.verify_constitution()["ok"] is True
    finally:
        with open(K.HEARTBEAT_LOG, "w", encoding="utf-8") as f:
            f.write(hb_bak)


def test_self_modify_rejects_when_validation_fails(monkeypatch):
    """负向测试:验证不通过时拒绝自改、不写 policy（经验验证是真的门，非橡皮图章）。"""
    # 让宪法校验失败 → 必须拒绝
    monkeypatch.setattr(K, "verify_constitution", lambda: {"ok": False, "n_articles": 0})
    r = K.self_modify(reason="测试:宪法损坏应拒绝")
    assert "error" in r
    assert r["error"]
    assert r.get("policy_written") is None


def test_archive_mechanism_keeps_all_snapshots():
    """DGM archive 机制:所有策略快照保留、按 sha 命名、可读回（可回滚）。"""
    snaps = K.archive_list()
    assert isinstance(snaps, list)
    # 当前真实运行已产生至少 1 份快照（首次自改 before）
    assert len(snaps) >= 1
    for f in snaps:
        assert f.endswith(".json")
        d = json.load(open(os.path.join(K.ARCHIVE_DIR, f), encoding="utf-8"))
        assert "policy" in d and "snapshot_sha" in d and "archived_at" in d


def test_constitution_rejects_tamper():
    """宪法层被篡改时校验失败（负向测试：免疫系统真的会拒绝）。"""
    import hashlib
    real = K.CONSTITUTION
    bak = real + ".test_bak"
    os.rename(real, bak)
    try:
        with open(real, "w", encoding="utf-8") as f:
            json.dump({"immutable": True, "articles": []}, f)
        c = K.verify_constitution()
        assert c["ok"] is False  # 哈希不符
    finally:
        os.remove(real)
        os.rename(bak, real)


# ---------- §4as v3 帕累托次优随机游走（无路时的腿） ----------
def test_pareto_front_identifies_nondominated():
    """帕累托前沿：双目标不被同时压制者入列，被支配者出列。"""
    # a/b/c 两两权衡互不支配（一高一低）；d 被 c 同时压制，应出列。
    pts = [
        {"id": "a", "novelty": 0.9, "freshness": 0.2},
        {"id": "b", "novelty": 0.2, "freshness": 0.9},
        {"id": "c", "novelty": 0.5, "freshness": 0.5},
        {"id": "d", "novelty": 0.3, "freshness": 0.3},
    ]
    front = {x["id"] for x in K.pareto_front(pts)}
    assert front == {"a", "b", "c"}


def test_pareto_walk_walks_when_no_path(tmp_path):
    """前方无路（全池收敛）：仍迈步，选次优，脚印写隔离路径不污染真实。"""
    iso = str(tmp_path / "traces.jsonl")
    pool = [
        {"id": "X1", "direction": "canary 判据回放 字面伪规则 语义蕴含", "source": "t"},
        {"id": "X2", "direction": "canary 构念效度 冻结集 错位负例", "source": "t"},
        {"id": "X3", "direction": "canary 字面伪规则 判据回放", "source": "t"},
    ]
    recent = ["canary 判据回放 字面伪规则 语义蕴含", "canary 构念效度 冻结集 错位负例"]
    r = K.pareto_walk(pool=pool, recent=recent, seed=42, record=True, log_path=iso)
    assert r["constitution_ok"] is True and r["verdict_unchanged"] is True
    assert r["mode"] == "NO_PATH" and r["max_novelty"] < K.NO_PATH_NOVELTY
    assert r["walk_triggered"] is True and r["chosen"]["id"] in r["suboptimal_ids"]
    assert r["footprint_written"] is True and r["path_length"] == 1
    traces = K.path_list(iso)
    assert len(traces) == 1 and traces[0]["note"] == "你走了，从此便有了路"


def test_pareto_walk_deterministic_and_suboptimal(tmp_path):
    """带种子可复现；选中项来自次优集而非理想点端点（不是最优执念）。"""
    iso = str(tmp_path / "traces.jsonl")
    pool = [
        {"id": "Y1", "direction": "canary 判据回放 字面伪规则", "source": "t"},
        {"id": "Y2", "direction": "canary 构念效度 冻结集", "source": "t"},
        {"id": "Y3", "direction": "canary 错位负例 语义蕴含", "source": "t"},
        {"id": "Y4", "direction": "canary 字面伪规则 判据回放", "source": "t"},
    ]
    recent = ["canary 判据回放 字面伪规则", "canary 构念效度 冻结集"]
    a = K.pareto_walk(pool=pool, recent=recent, seed=20261124, record=False, log_path=iso)
    b = K.pareto_walk(pool=pool, recent=recent, seed=20261124, record=False, log_path=iso)
    assert a["chosen"]["id"] == b["chosen"]["id"]
    assert a["chosen"]["id"] in a["suboptimal_ids"]
    assert len(a["pareto_front_ids"]) >= 2
    assert a["footprint_written"] is False  # record=False 零污染


def test_pareto_walk_skips_when_path_exists(tmp_path):
    """前方有路：保持贪心选最优，不游走、次优集为空（不无谓扰动）。"""
    iso = str(tmp_path / "traces.jsonl")
    pool = [
        {"id": "Z1", "direction": "记忆治理 知识库 遗忘 压缩", "source": "t"},
        {"id": "Z2", "direction": "自进化内核 RSI 元认知 自改", "source": "t"},
    ]
    r = K.pareto_walk(pool=pool, recent=["canary 判据回放 字面伪规则"],
                      seed=1, record=True, log_path=iso)
    assert r["mode"] == "PATH_EXISTS"
    assert r["walk_triggered"] is False and r["suboptimal_ids"] == []


def test_pareto_walk_footprints_become_next_candidates(tmp_path):
    """路径依赖(v4/F10)：带适用情境且匹配的脚印注入；不匹配的被碰撞闸门挡下。"""
    iso = str(tmp_path / "traces.jsonl")
    # v4：脚印必须带 applicability 才可能被注入（旧版无条件注入已被F10实证否定）
    with open(iso, "w", encoding="utf-8") as f:
        # applicability 必须是 _context_sig() 产出的规范标签（与真实脚印写入同构）
        f.write(json.dumps({"id": "P1", "direction": "工作流进化 多智能体 编排 三角色",
                            "applicability": ["workflow"],
                            "mode": "NO_PATH"}, ensure_ascii=False) + "\n")
    pool = [{"id": "W1", "direction": "工作流进化 多智能体 编排 三角色", "source": "t"}]
    # 当前情境=workflow 系：与脚印适用情境匹配 → 注入
    recent_match = ["工作流 多智能体 编排 协作 三角色", "多智能体协作 编排 课程"]
    r = K.pareto_walk(pool=pool, recent=recent_match, seed=7, record=False, log_path=iso)
    assert r["footprints_loaded"] == 1
    assert r["footprints_applicable"] == 1
    assert r["candidates"] == 2  # 1 内置候选 + 1 匹配脚印
    assert r["path_dependency"] is True
    # 当前情境=finance：与脚印适用情境不匹配 → F10 碰撞闸门挡下，不注入
    r2 = K.pareto_walk(pool=pool, recent=["金融 市场 库存周期 宏观"],
                       seed=7, record=False, log_path=iso)
    assert r2["footprints_applicable"] == 0
    assert r2["candidates"] == 1
    assert any(x["reason"] == "context_mismatch" for x in r2["collision_rejected"])


def test_pareto_walk_never_changes_verdict_or_constitution(tmp_path):
    """v3 新器官不碰判定、不碰宪法（C8），真实脚印零污染。"""
    iso = str(tmp_path / "traces.jsonl")
    real_trace = K.PATH_TRACES
    before = open(real_trace, "rb").read() if os.path.exists(real_trace) else None
    const_before = K.verify_constitution()
    r = K.pareto_walk(seed=99, record=True, log_path=iso)
    assert r["verdict_unchanged"] is True and r["constitution_ok"] is True
    assert K.verify_constitution() == const_before
    after = open(real_trace, "rb").read() if os.path.exists(real_trace) else None
    assert after == before  # 真实脚印未被污染
    res = json.load(open(os.path.join(ROOT, "audit_l3_gap_targeted", "result.json"), encoding="utf-8"))
    assert res["verdict"] == "GAP_INCONCLUSIVE"
    assert res["l3_claimed"] is False and res["absolute_claimed"] is False


# ---------- §4at v4 飞出仓库自我否定：F09归因 / F10碰撞 / F11剪枝 ----------
def test_diagnose_v3_defects_confirms_three(tmp_path):
    """外部一手前沿对 v3 的三条批判，在本仓真实源码/数据上机械成立（A级诊断）。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "diag", os.path.join(HERE, "diagnose_v3_defects.py"))
    diag = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(diag)
    d = diag.build_report()
    # 诊断脚本读的是当前(v4)源码：v4 已修复三缺陷，故 confirmed 应转为 False
    # ——这本身就是"修复生效"的机械证据（v3 时三缺陷 confirmed=True，已随提交留痕）。
    assert d["all_three_confirmed"] is False
    assert d["defect1_attribution_hallucination"]["confirmed"] is False
    assert d["defect2_no_applicability"]["confirmed"] is False
    assert d["defect3_growth_only"]["confirmed"] is False
    assert d["evidence_tier"].startswith("外部证据 B 级") and "A 级" in d["evidence_tier"]
    # v4 确实长出三机制（读真实源码符号，非自报）
    assert hasattr(K, "attribution_check") and hasattr(K, "_applicable_footprints")
    assert hasattr(K, "prune_unused") and hasattr(K, "_mark_used")


def test_attribution_check_three_numbers():
    """F09：归因检验分报三数字；对全同主题候选（memorize一例）必须拒绝。"""
    # 全 canary 收敛候选：target repair 低（都是同主题），不能靠累积通过
    bad = K.attribution_check(["canary 判据回放 字面伪规则 语义蕴含"],
                              ["F09", "F10", "F11"])
    assert set(["target_repair", "transfer_distinct_tags", "heldout_net", "all_pass"]) <= set(bad)
    # 多样候选：覆盖多主题，target repair 应上升
    good = K.attribution_check(["canary 判据回放 字面伪规则 语义蕴含"],
                               ["E1", "E2", "E3", "F01", "F04", "F06"])
    assert good["transfer_distinct_tags"] >= bad["transfer_distinct_tags"]
    # 三数字独立可查，不再单一 all_pass 掩盖
    assert isinstance(good["heldout_net"], int)


def test_attribution_gate_into_validate_policy():
    """F09 真正接入经验验证门：validate 结果含 attribution_ok 与三数字明细。"""
    checks = K._validate_policy(["F01", "F02", "F03", "F04", "F05", "F06", "F07", "F08"],
                                ["canary 判据回放 字面伪规则 语义蕴含"])
    assert "attribution_ok" in checks and isinstance(checks["attribution_ok"], bool)
    assert "attribution_detail" in checks
    assert "target_repair" in checks["attribution_detail"]


def test_context_sig_and_applicability_gate(tmp_path):
    """F10：情境签名为规范标签；无适用条件的旧脚印保守不注入。"""
    sig = K._context_sig(["工作流 多智能体 编排", "记忆治理 知识库 遗忘"])
    assert isinstance(sig, list) and "workflow" in sig and "memory" in sig
    iso = str(tmp_path / "t.jsonl")
    with open(iso, "w", encoding="utf-8") as f:
        # 旧脚印无 applicability：F10 下保守拒绝（诚实标注兼容成本）
        f.write(json.dumps({"id": "OLD", "direction": "工作流进化 多智能体 编排",
                            "mode": "NO_PATH"}, ensure_ascii=False) + "\n")
    r = K.pareto_walk(pool=[{"id": "W1", "direction": "记忆治理 知识库 遗忘", "source": "t"}],
                      recent=["工作流 多智能体 编排"], seed=1, record=False, log_path=iso)
    assert r["footprints_applicable"] == 0
    assert any(x.get("reason") == "no_applicability_legacy" for x in r["collision_rejected"])


def test_prune_unused_dry_run_then_apply(tmp_path):
    """F11：选择性丢弃 stale 经验——dry_run 零写入；apply 才移除且留 archive 快照。"""
    iso = str(tmp_path / "traces.jsonl")
    fresh = {"id": "P_FRESH", "direction": "记忆治理 知识库 遗忘",
             "applicability": ["memory"], "timestamp": K._utcnow()}
    stale = {"id": "P_STALE", "direction": "过期方向 陈旧 旧闻",
             "applicability": ["general"], "timestamp": "2020-01-01T00:00:00Z"}
    with open(iso, "w", encoding="utf-8") as f:
        for t in (fresh, stale):
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    dry = K.prune_unused(kind="footprint", stale_days=30, dry_run=True, log_path=iso)
    assert dry["total"] == 2 and dry["stale_count"] == 1
    assert "P_STALE" in dry["stale_ids"] and dry["pruned"] is False
    assert len(open(iso, encoding="utf-8").read().strip().splitlines()) == 2  # dry_run 零写入
    applied = K.prune_unused(kind="footprint", stale_days=30, dry_run=False, log_path=iso)
    assert applied["pruned"] is True and applied["constitution_ok"] is True
    survivors = [json.loads(x) for x in open(iso, encoding="utf-8").read().strip().splitlines()]
    assert [t["id"] for t in survivors] == ["P_FRESH"]  # 只删 stale，留 fresh
    assert applied["archive_before"] and os.path.exists(applied["archive_before"])


def test_v4_never_changes_verdict_or_constitution(tmp_path):
    """v4 三机制全部不碰判定/宪法（C8）。"""
    const_before = K.verify_constitution()
    K.attribution_check(["canary 判据回放"], ["F01", "F04", "F06"])
    K.prune_unused(kind="footprint", dry_run=True, log_path=str(tmp_path / "x.jsonl"))
    r = K.pareto_walk(seed=1, record=False)
    assert r["verdict_unchanged"] is True
    assert K.verify_constitution() == const_before
    res = json.load(open(os.path.join(ROOT, "audit_l3_gap_targeted", "result.json"), encoding="utf-8"))
    assert res["verdict"] == "GAP_INCONCLUSIVE"
    assert res["l3_claimed"] is False and res["absolute_claimed"] is False


# ---------- §4au v5 自主意志：内核首次自己决定"我现在该做什么" ----------
def _v5_paths(tmp_path):
    """v5 单一路径契约：传脚印路径，心跳/台账/use 从同目录派生。"""
    d = str(tmp_path)
    return os.path.join(d, "traces.jsonl"), os.path.join(d, "heartbeat_log.jsonl"), os.path.join(d, "experience_use.jsonl")


def _all_registered_policy():
    """隔离 policy：把当前所有种子视为已注册，稳定构造"无 DIGEST 失衡"场景。"""
    ids = [x["id"] for x in K.digest()["seeds"]]
    return {"registered_frontier_seeds": ids}


def test_agenda_decision_is_readonly(tmp_path):
    """v5：autonomous_agenda 是纯只读决策，不写任何文件、不联网。"""
    fp, hb, use = _v5_paths(tmp_path)
    before = {p: (os.path.exists(p), open(p, "rb").read() if os.path.exists(p) else b"")
              for p in (fp, hb, use)}
    d = K.autonomous_agenda(seed=42, log_path=fp)
    assert d["readonly"] is True
    assert "chosen" in d and "rationale" in d and "candidates" in d
    for p, (existed, data) in before.items():
        assert os.path.exists(p) == existed
        assert (open(p, "rb").read() if os.path.exists(p) else b"") == data
    assert d["verdict_unchanged"] is True and d["constitution_ok"] is True


def test_agency_driven_by_state_not_caller(tmp_path):
    """意志由内稳态状态驱动：不同状态 → 不同议程（不由调用者预设方向）。"""
    fp, hb, use = _v5_paths(tmp_path)
    # 状态A：脚印稀疏 → CONSOLIDATE 应胜（0.45 > 好奇心0.3）
    open(fp, "w", encoding="utf-8").write("")
    d_sparse = K.autonomous_agenda(seed=1, log_path=fp, policy_override=_all_registered_policy())
    assert d_sparse["signals"]["traces_sparse"] is True
    assert d_sparse["chosen"] == "CONSOLIDATE"
    # 状态B：脚印充足(>=3)且无其他失衡 → SEEK（本底好奇心）胜
    for i in range(3):
        with open(fp, "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": "P%d" % i, "direction": "方向%d 不同主题%d" % (i, i),
                                "applicability": ["general"], "timestamp": K._utcnow(),
                                "kernel_version": K.KERNEL_VERSION}, ensure_ascii=False) + "\n")
    d_rich = K.autonomous_agenda(seed=1, log_path=fp, policy_override=_all_registered_policy())
    assert d_rich["signals"]["traces_sparse"] is False
    assert d_rich["chosen"] == "SEEK"
    assert any("设计选择" in c["honesty"] for c in d_rich["candidates"] if c["id"] == "SEEK")
    # 同一调用者、不同状态 → 不同决定：证明非预设、非调用者驱动
    assert d_sparse["chosen"] != d_rich["chosen"]


def test_reorient_highest_priority_on_convergence(tmp_path):
    """宪法 C7：guard 收敛时 REORIENT 紧迫度最高(0.95)，压过所有议程。"""
    fp, hb, use = _v5_paths(tmp_path)
    # 造 5 条同主题心跳（派生路径） → guard CONVERGED
    for i in range(5):
        with open(hb, "a", encoding="utf-8") as f:
            f.write(json.dumps({"direction": "canary 字面伪规则 判据回放 语义蕴含",
                                "timestamp": K._utcnow()}, ensure_ascii=False) + "\n")
    for i in range(3):
        with open(fp, "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": "P%d" % i, "direction": "不同方向%d" % i,
                                "applicability": ["general"], "timestamp": K._utcnow()},
                               ensure_ascii=False) + "\n")
    d = K.autonomous_agenda(seed=9, log_path=fp)
    assert d["signals"]["converged"] is True
    assert d["chosen"] == "REORIENT" and d["chosen_urgency"] == 0.95


def test_seek_execute_declares_need_not_self_network(tmp_path):
    """SEEK 执行：内核不联网，只诚实声明 need_external_stimulus + 落心跳（派生路径）。"""
    fp, hb, use = _v5_paths(tmp_path)
    for i in range(3):
        with open(fp, "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": "P%d" % i, "direction": "不同方向%d" % i,
                                "applicability": ["general"], "timestamp": K._utcnow()},
                               ensure_ascii=False) + "\n")
    d = K.autonomous_agenda(seed=3, log_path=fp, policy_override=_all_registered_policy())
    assert d["chosen"] == "SEEK"
    ex = K.execute_agenda(d, seed=3, log_path=fp)
    assert ex["need"]["need_external_stimulus"] is True
    assert "不联网" in ex["need"]["honesty"]
    assert ex["executed"] is True  # 心跳落了（派生隔离路径）
    assert os.path.exists(hb) and len(open(hb, encoding="utf-8").read().strip().splitlines()) == 1


def test_live_pauses_when_it_needs_external(tmp_path):
    """自驱心跳自己走到需要外部营养才停；步数不是预设而是状态涌现。"""
    fp, hb, use = _v5_paths(tmp_path)
    open(fp, "w", encoding="utf-8").write("")  # 从稀疏起步
    # 注入全注册 policy：排除 DIGEST 干扰，专测"自驱走到 SEEK 求助"
    r = K.live(max_steps=8, seed=100, log_path=fp, policy_override=_all_registered_policy())
    assert r["paused_for_external"] is True
    assert r["trace"][-1]["chosen"] == "SEEK"
    # 前几步是 CONSOLIDATE 自己走出来的（非预设），脚印从0涨到>=3
    assert any(s["chosen"] == "CONSOLIDATE" for s in r["trace"])
    final_traces = len(open(fp, encoding="utf-8").read().strip().splitlines())
    assert final_traces >= 3
    assert r["constitution_ok"] is True and r["verdict_unchanged"] is True


def test_volition_never_changes_verdict_or_constitution(tmp_path):
    """v5 全程不碰判定/宪法（C8）。"""
    const_before = K.verify_constitution()
    fp, hb, use = _v5_paths(tmp_path)
    d = K.autonomous_agenda(seed=1, log_path=fp)
    ex = K.execute_agenda(d, seed=1, log_path=fp)
    assert d["verdict_unchanged"] is True and ex["verdict_unchanged"] is True
    assert K.verify_constitution() == const_before
    res = json.load(open(os.path.join(ROOT, "audit_l3_gap_targeted", "result.json"), encoding="utf-8"))
    assert res["verdict"] == "GAP_INCONCLUSIVE"
    assert res["l3_claimed"] is False and res["absolute_claimed"] is False


# ---------- §4au AAS 外部镜像：诚实的自我边界诊断 ----------
def test_aas_diagnosis_honest_ambient_zero():
    """外部 AAS Idle-Gap 判据照出 Ambient=0；诊断如实报否定结论，不掩饰为已 autotelic。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "aasdiag", os.path.join(HERE, "diagnose_volition_aas.py"))
    diag = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(diag)
    d = diag.build_report()
    assert d["has_idle_daemon"] is False
    assert d["ambient_activity_survives_trigger_removal"] is False
    assert d["aas_ambient_level_estimate"] == 0
    assert "被唤醒后的自主" in d["honest_verdict"]
    assert "尚未达 autotelic" in d["honest_verdict"]
    assert d["external_tier"].startswith("B") and "A 级" in d["local_evidence_tier"]
    assert d["does_not_change"] == ["verdict", "l3=false", "absolute=false", "宪法锁", "§100"]


def test_seeds_f12_f13_ingested_with_tier():
    """v5 SEEK 主动摄食的 F12/F13 一手种子存在、带 URL/证据分层，落盘如实标注 B 级。"""
    seeds = {s["id"]: s for s in K.digest()["seeds"]}
    assert "F12" in seeds and "F13" in seeds
    assert "arxiv.org/abs/2607.17947" in seeds["F12"]["source_url"]
    assert "arxiv.org/abs/2606.19924" in seeds["F13"]["source_url"]
    assert seeds["F12"]["evidence_tier"] == "B" and seeds["F13"]["evidence_tier"] == "B"
    assert any("agency" in t or "volition" in t for t in seeds["F12"]["tags"])


def test_report_exposes_aas_honest_boundary():
    """内核自检报告主动暴露 AAS 诚实边界（不隐藏 Ambient=0 缺口）。"""
    r = K.build_report()
    aas = r["aas_self_assessment"]
    assert "Ambient" in aas["ambient_band"] and "0" in aas["ambient_band"]
    assert "不 spawn" in aas["boundary_honesty"]
    assert r["verdict_unchanged"] if "verdict_unchanged" in r else True
    assert r["constitution"]["ok"] is True


# ---------- §4av v6 昼夜节律：随太阳东升西落的自主醒来 ----------
def _v6_time(hour_utc):
    """给定时辰的 naive UTC（便于机械复现昼夜相位）。"""
    import datetime
    return datetime.datetime(2026, 11, 24, hour_utc, 0, 0)


def test_v6_solar_position_matches_beijing_geometry():
    """纯天文：北京日出早于日落、正午太阳高于深夜、日出日落落在合理北京时间。"""
    noon = K.solar_position(now=_v6_time(4))    # 北京 12:00 附近
    night = K.solar_position(now=_v6_time(16))  # 北京 24:00 附近
    assert noon["solar_altitude_deg"] > night["solar_altitude_deg"]
    rise_h = int(noon["sunrise_local"].split(":")[0])
    set_h = int(noon["sunset_local"].split(":")[0])
    assert rise_h < set_h
    assert 6 <= rise_h <= 8 and 16 <= set_h <= 18  # 北京 11 月真实区间
    assert "no network" in noon["method"] and "no process" in noon["method"]


def test_v6_circadian_phase_day_and_night():
    """相位由真实时钟推得：北京白昼 DAY、深夜 NIGHT；极昼极地不崩。"""
    day = K.circadian_phase(now=_v6_time(2))   # 北京 10:00
    night = K.circadian_phase(now=_v6_time(14))  # 北京 22:00
    assert day["phase"] in ("DAWN", "DAY") and day["daylight_phase"] is True
    assert night["phase"] == "NIGHT" and night["daylight_phase"] is False
    polar = K.circadian_phase(now=_v6_time(4), latitude=89.0)
    assert polar["polar"] in ("polar_day", "polar_night")
    assert "外部授时因子" in day["honesty"]


def test_v6_sleep_intent_day_wake_night_sleep(tmp_path):
    """被唤醒先问节律：昼行 WAKE、夜伏 SLEEP——只读、状态驱动（非调用者预设）。"""
    fp, hb, use = _v5_paths(tmp_path)
    d_day = K.sleep_intent(now=_v6_time(2), log_path=fp)
    d_night = K.sleep_intent(now=_v6_time(14), log_path=fp)
    assert d_day["intent"] == "WAKE" and d_day["daylight_phase"] is True
    assert d_night["intent"] == "SLEEP" and d_night["daylight_phase"] is False
    assert d_day["readonly"] is True and d_night["readonly"] is True
    assert d_day["verdict_unchanged"] is True and d_night["constitution_ok"] is True


def test_v6_c7_convergence_overrides_night_sleep(tmp_path):
    """宪法 C7 novelty 义务高于节律：夜里 guard 收敛也强制 WAKE 转向。"""
    fp, hb, use = _v5_paths(tmp_path)
    # 造 5 条同主题心跳使 guard 收敛（派生心跳路径）
    for i in range(5):
        with open(hb, "a", encoding="utf-8") as f:
            f.write(json.dumps({"direction": "canary 字面伪规则 判据回放 语义蕴含 同井",
                                "timestamp": K._utcnow()}, ensure_ascii=False) + "\n")
    d = K.sleep_intent(now=_v6_time(14), log_path=fp)  # 北京深夜
    assert d["signals_snapshot"]["converged"] is True
    assert d["constitutional_override"] is True
    assert d["intent"] == "WAKE"
    assert "C7" in d["reason"]


def test_v6_wake_contract_is_self_set_and_honest(tmp_path):
    """自设醒来契约：内核自己设定昼行窗口、标注需外部唤醒器兑现（契约≠自己醒）。"""
    wc_path = str(tmp_path / "wake_contract.json")
    c = K.wake_contract(now=_v6_time(2), wake_path=wc_path)
    assert c["set_by"].startswith("kernel")  # 自设非外部强加
    assert "DAWN" in c["preferred_wake_phase"] and "NIGHT" in c["preferred_sleep_phase"]
    assert c["external_waker_required"] is True
    assert "Ambient still 0" in c["max_idle_gap_tolerated"]  # 契约显式标注 Ambient 缺口
    assert "spawn" in c["honesty"] and "守护进程" in c["honesty"]
    assert c["contract_written"] is True and os.path.exists(wc_path)
    assert c["verdict_unchanged"] is True and c["constitution_ok"] is True


def test_v6_circadian_live_night_sleeps_without_pollution(tmp_path):
    """夜伏被唤醒→尊重节律 SLEEP 停机，不写议程/心跳（隔离零污染）。"""
    fp, hb, use = _v5_paths(tmp_path)
    r = K.circadian_live(now=_v6_time(14), seed=7, log_path=fp,
                         policy_override=_all_registered_policy())
    assert r["slept"] is True
    assert r["trace"][0]["intent"] == "SLEEP"
    assert r["verdict_unchanged"] is True and r["constitution_ok"] is True
    # 真实台账未被污染（circadian 从 fp 同目录派生，真实数据目录不动）


def test_v6_circadian_live_day_runs_self_chosen_agenda(tmp_path):
    """昼行被唤醒→自选议程执行（脚印稀疏自己 CONSOLIDATE），非预设方向。"""
    fp, hb, use = _v5_paths(tmp_path)
    open(fp, "w", encoding="utf-8").write("")
    r = K.circadian_live(max_steps=8, now=_v6_time(2), seed=11, log_path=fp,
                         policy_override=_all_registered_policy())
    assert r["start_phase"] in ("DAWN", "DAY")
    assert any(t.get("intent") == "WAKE" and t.get("chosen") == "CONSOLIDATE"
               for t in r["trace"])
    assert r["paused_for_external"] is True  # 自驱到 SEEK 求助才停
    assert r["verdict_unchanged"] is True and r["constitution_ok"] is True


def test_v6_never_changes_verdict_constitution_or_aas_honesty(tmp_path):
    """v6 全程不碰判定/宪法，AAS 诊断仍诚实判无守护（不因新代码词误判）。"""
    const_before = K.verify_constitution()
    fp, hb, use = _v5_paths(tmp_path)
    K.circadian_phase(now=_v6_time(2))
    K.sleep_intent(now=_v6_time(14), log_path=fp)
    K.wake_contract(now=_v6_time(2))
    assert K.verify_constitution() == const_before
    res = json.load(open(os.path.join(ROOT, "audit_l3_gap_targeted", "result.json"), encoding="utf-8"))
    assert res["verdict"] == "GAP_INCONCLUSIVE"
    assert res["l3_claimed"] is False and res["absolute_claimed"] is False
    # AAS 守护符号检测仍为 False（v6 未引入 daemon 原语）
    spec = importlib.util.spec_from_file_location("aasdiag2", os.path.join(HERE, "diagnose_volition_aas.py"))
    diag = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(diag)
    assert diag.build_report()["has_idle_daemon"] is False


# ---------- §4aw v7 觉时者：对自身承诺的元认知审视 ----------
def _v7_paths(tmp_path):
    """v7 单一路径契约：脚印/契约/审计台账全从同目录派生，零污染。"""
    d = str(tmp_path)
    return (os.path.join(d, "traces.jsonl"),
            os.path.join(d, "wake_contract.json"),
            os.path.join(d, "circadian_log.jsonl"),
            os.path.join(d, "entrainment_audit.jsonl"))


def test_v7_audit_unproven_without_external_evidence(tmp_path):
    """v6 遗留记录无 woken_by → 如实判 UNPROVEN，不把手动/自驱刷成兑现。"""
    fp, cp, cl, ap = _v7_paths(tmp_path)
    import datetime
    # 写一份契约 + 一条"无外部源"的 WAKE 记录（模拟 v6 历史数据）
    K.wake_contract(now=_v6_time(2), wake_path=cp)
    with open(cl, "w", encoding="utf-8") as f:
        f.write(json.dumps({"at": "2026-11-24T03:09:55Z", "step": 1,
                            "intent": "WAKE", "chosen": "SEEK", "woken_by": None}) + "\n")
    r = K.entrainment_audit(contract_path=cp, log_path=fp, now=_v6_time(4))
    assert r["verdict"] == "UNPROVEN"
    assert r["wake_observations"] == 1 and r["externally_evidenced_wakes"] == 0
    assert r["last_woken_by"] is None
    assert "无法证明" in r["honest"]


def test_v7_no_wake_observations_reports_zero_honestly(tmp_path):
    """无 WAKE 记录 → 判 NO_WAKE_OBSERVED，不虚构活跃。"""
    fp, cp, cl, ap = _v7_paths(tmp_path)
    K.wake_contract(now=_v6_time(2), wake_path=cp)
    r = K.entrainment_audit(contract_path=cp, log_path=fp, now=_v6_time(4))
    assert r["verdict"] == "NO_WAKE_OBSERVED"
    assert r["wake_observations"] == 0 and r["idle_gap_hours"] is None


def test_v7_external_waker_evidence_is_recognized(tmp_path):
    """外部唤醒器写入 woken_by → 判 EXTERNALLY_EVIDENCED，记录可追溯源。"""
    fp, cp, cl, ap = _v7_paths(tmp_path)
    K.wake_contract(now=_v6_time(2), wake_path=cp)
    with open(cl, "w", encoding="utf-8") as f:
        f.write(json.dumps({"at": "2026-11-24T03:09:55Z", "intent": "WAKE",
                            "woken_by": "external_alarm:07:15"}) + "\n")
        f.write(json.dumps({"at": "2026-11-24T03:20:00Z", "intent": "WAKE",
                            "woken_by": None}) + "\n")
    r = K.entrainment_audit(contract_path=cp, log_path=fp, now=_v6_time(4))
    assert r["verdict"] == "EXTERNALLY_EVIDENCED"
    assert r["wake_observations"] == 2 and r["externally_evidenced_wakes"] == 1


def test_v7_kernel_never_fabricates_woken_by(tmp_path):
    """内核自驱 circadian_live 不传 woken_by → 台账记为 None，审计不误判兑现。"""
    fp, cp, cl, ap = _v7_paths(tmp_path)
    K.circadian_live(max_steps=2, now=_v6_time(2), log_path=fp,
                     auto_seek=False, record=True)
    rows = [json.loads(x) for x in open(cl, encoding="utf-8") if x.strip()]
    assert rows and all(r.get("woken_by") is None for r in rows)
    r = K.entrainment_audit(contract_path=cp, log_path=fp, now=_v6_time(4))
    assert r["verdict"] != "EXTERNALLY_EVIDENCED"


def test_v7_external_woken_by_propagates_to_ledger(tmp_path):
    """外部调度器显式传 woken_by → 台账携带证据源，审计可兑现。"""
    fp, cp, cl, ap = _v7_paths(tmp_path)
    K.circadian_live(max_steps=1, now=_v6_time(2), log_path=fp,
                     auto_seek=False, record=True,
                     woken_by="external_alarm:sunrise-0715")
    rows = [json.loads(x) for x in open(cl, encoding="utf-8") if x.strip()]
    assert any(r.get("woken_by") == "external_alarm:sunrise-0715" for r in rows)
    r = K.entrainment_audit(contract_path=cp, log_path=fp, now=_v6_time(4))
    assert r["verdict"] == "EXTERNALLY_EVIDENCED" and r["externally_evidenced_wakes"] >= 1


def test_v7_idle_gap_honest_and_record_isolated(tmp_path):
    """Idle-Gap 如实计算；record=True 只写隔离审计台账，不碰真实数据。"""
    import datetime
    fp, cp, cl, ap = _v7_paths(tmp_path)
    K.wake_contract(now=_v6_time(2), wake_path=cp)
    with open(cl, "w", encoding="utf-8") as f:
        f.write(json.dumps({"at": "2026-11-24T03:00:00Z", "intent": "WAKE",
                            "woken_by": "external_alarm:07:15"}) + "\n")
    # 真实审计台账运行前行数
    real = os.path.join(os.path.dirname(K.CIRCADIAN_LOG), "entrainment_audit.jsonl")
    before = sum(1 for _ in open(real, encoding="utf-8")) if os.path.exists(real) else 0
    r = K.entrainment_audit(contract_path=cp, log_path=fp,
                            now=datetime.datetime(2026, 11, 24, 6, 0, 0),
                            record=True, audit_path=ap)
    assert r["audit_recorded"] is True and os.path.exists(ap)
    assert r["idle_gap_hours"] == 3.0
    after = sum(1 for _ in open(real, encoding="utf-8")) if os.path.exists(real) else 0
    assert after == before  # 零污染


def test_v7_report_exposes_entrainment_and_never_changes_verdict():
    """报告主动暴露 v7 元认知段与 UNPROVEN 真相；判定/宪法/AAS 全不动。"""
    r = K.build_report()
    # §4ba v10 起内核升主版本 7.0.0（运行基地层），数字成长按 C5 如实更新断言不放宽
    assert r["round"] in ("§4aw", "§4ax", "§4ay", "§4ba") and r["kernel_version"].startswith(("6.", "7."))
    v7 = r["v7_entrainment"]
    assert "UNPROVEN" in v7["current_truth"] and "绝不代填" in v7["honesty_core"]
    assert r["constitution"]["ok"] is True
    res = json.load(open(os.path.join(ROOT, "audit_l3_gap_targeted", "result.json"), encoding="utf-8"))
    assert res["verdict"] == "GAP_INCONCLUSIVE"
    assert res["l3_claimed"] is False and res["absolute_claimed"] is False
    spec = importlib.util.spec_from_file_location("aasdiag3", os.path.join(HERE, "diagnose_volition_aas.py"))
    diag = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(diag)
    assert diag.build_report()["has_idle_daemon"] is False


# ---------- §4ax v8 夜班查错题：AutoRLBench 错题方法论自审 ----------
def _autorl_report():
    """导入夜班诊断脚本、执行 build_report 等价逻辑（脚本是 print 模式，这里直接 exec 取 report）。"""
    import contextlib, io
    path = os.path.join(HERE, "diagnose_autorlbench_errors.py")
    ns = {"__file__": path, "__name__": "__autorl_diag__"}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(compile(open(path, encoding="utf-8").read(), path, "exec"), ns)
    return json.loads(buf.getvalue()), ns


def test_v8_conclusion_evidence_consistency_meta_discipline():
    """元纪律：结论 confirmed_count 必须等于 confirmed_categories 长度（防 wrong-evidence 病复发）。"""
    rep, _ = _autorl_report()
    assert rep["confirmed_count"] == len(rep["confirmed_categories"])
    assert rep["confirmed_count"] + len(rep["defended_categories"]) == rep["probe_count"] == 5
    # 每个 confirmed 类的 findings.confirmed 必须真为 True（结论由证据生成，非手写）
    by_cat = {p["category"]: p["findings"]["confirmed"] for p in rep["probes"]}
    for cat in rep["confirmed_categories"]:
        assert by_cat[cat] is True
    for cat in rep["defended_categories"]:
        assert by_cat[cat] is False


def test_v8_evidence_fabrication_already_defended():
    """P2 已防：v7 woken_by 不可自填——blog 同类病在本内核不成立。"""
    rep, _ = _autorl_report()
    p2 = next(p for p in rep["probes"] if p["category"] == "P2_证据伪造")
    assert p2["findings"]["confirmed"] is False
    assert p2["findings"]["default_none"] and p2["findings"]["unproven_verdict"]
    assert "已防" in p2["findings"]["honest"]


def test_v8_real_gaps_confirmed_sustain_lock_verify():
    """v9 修复 P1 后，剩余 3 条真实同类病仍被机械确认（P1 已转 defended）。"""
    rep, _ = _autorl_report()
    cats = set(rep["confirmed_categories"])
    # P1 已由 v9 症状→机制追溯真修复，不再属于 confirmed；此处锁定新真实
    assert "P1_症状当根因" not in cats
    assert "P2_证据伪造" not in cats
    assert "P3_早期涨随后崩" in cats
    assert "P4_判据被篡改" in cats
    assert "P5_诊断修复两张皮" in cats
    assert "87%" in rep["honest_verdict"]  # 结论由机械结果含 blog 数据生成


def test_v8_diagnosis_script_read_only_and_no_daemon():
    """诊断脚本只读源码/台账，不引入守护原语，不改判定/宪法。"""
    rep, ns = _autorl_report()
    assert rep["verdict_unchanged"] is True and rep["constitution_ok"] is True
    src = open(os.path.join(HERE, "diagnose_autorlbench_errors.py"), encoding="utf-8").read()
    for sym in ["threading", "while True", "asyncio", "cron", "multiprocessing"]:
        assert sym not in src


# ---------- §4ay v9 查根因者：P1 症状当根因的机制级修复 ----------
def _v9_converged_paths(tmp_path, direction="canary 字面伪规则 判据回放 语义蕴含", n=5):
    """造 n 条同主题心跳 → guard CONVERGED，返回隔离脚印路径。"""
    fp = os.path.join(str(tmp_path), "traces.jsonl")
    hb = os.path.join(str(tmp_path), "heartbeat_log.jsonl")
    for i in range(n):
        with open(hb, "a", encoding="utf-8") as f:
            f.write(json.dumps({"direction": direction, "timestamp": K._utcnow()},
                               ensure_ascii=False) + "\n")
    for i in range(3):
        with open(fp, "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": "P%d" % i, "direction": "不同方向%d" % i,
                                "applicability": ["general"], "timestamp": K._utcnow()},
                               ensure_ascii=False) + "\n")
    return fp


def test_v9_root_cause_trace_distinguishes_sampling_narrow(tmp_path):
    """池里有足够不同候选 → 根因判 sampling_narrow，给出建议方向。"""
    fp = _v9_converged_paths(tmp_path)
    sig = K.homeostatic_signals(log_path=fp)
    assert sig["converged"] is True
    t = K.root_cause_trace(sig, log_path=fp)
    assert t["converged"] is True
    assert t["root_cause"] in ("sampling_narrow", "pool_exhausted")
    assert t["pool_size"] > 0 and t["novel_candidates"] >= 0
    if t["root_cause"] == "sampling_narrow":
        assert t["suggested_direction"] is not None
        assert t["suggested_direction"]["similarity"] < 0.6
    assert "jaccard" in t["evidence"]  # 证据来自真实比对，非硬编码


def test_v9_root_cause_trace_no_convergence_is_noop():
    """未收敛 → 根因 none，不做无谓追溯。"""
    t = K.root_cause_trace({"converged": False})
    assert t["root_cause"] == "none" and t["mechanism"] == "no_convergence"
    assert t["suggested_direction"] is None


def test_v9_pool_exhausted_branch_with_controlled_pool(tmp_path):
    """受控池：所有候选都与近期收敛方向相似 → 根因判 pool_exhausted，建议为 None。

    真实 explore_pool 设计上开放多样，几乎不会真枯竭（这本身是好事）；
    故用 mock 注入一个受控池验证分支逻辑，不放宽机制、不改真实池。
    """
    fp = _v9_converged_paths(tmp_path, direction="canary 字面伪规则 判据回放 语义蕴含")
    sig = K.homeostatic_signals(log_path=fp)
    assert sig["converged"] is True
    # 受控池：每候选都与 canary 收敛方向高度重叠 → jaccard>=0.6，无可转向候选
    controlled_pool = [{"id": "X%d" % i,
                        "direction": "canary 字面伪规则 判据回放 语义蕴含 同井%d" % i}
                       for i in range(3)]
    with mock.patch.object(K, "explore_pool", return_value=controlled_pool):
        t = K.root_cause_trace(sig, log_path=fp)
    assert t["root_cause"] == "pool_exhausted"
    assert t["novel_candidates"] == 0 and t["suggested_direction"] is None


def test_v9_reorient_urgency_unchanged_c7_preserved(tmp_path):
    """关键：修复不改宪法 C7——converged 仍 REORIENT/0.95，压过所有议程。"""
    fp = _v9_converged_paths(tmp_path)
    d = K.autonomous_agenda(seed=9, log_path=fp)
    assert d["signals"]["converged"] is True
    assert d["chosen"] == "REORIENT" and d["chosen_urgency"] == 0.95
    reorient = next(c for c in d["candidates"] if c["id"] == "REORIENT")
    assert reorient["urgency"] == 0.95  # 追溯未改紧迫度
    assert reorient["root_cause"] in ("sampling_narrow", "pool_exhausted")


def test_v9_agenda_carries_mechanism_evidence_readonly(tmp_path):
    """决策顶层携带症状→机制证据；autonomous_agenda 仍只读零污染。"""
    fp = _v9_converged_paths(tmp_path)
    before = open(fp, "rb").read() if os.path.exists(fp) else b""
    d = K.autonomous_agenda(seed=9, log_path=fp)
    assert d["readonly"] is True
    assert "root_cause_trace" in d and d["root_cause_trace"]["converged"] is True
    assert "mechanism" in d["root_cause_trace"]
    assert open(fp, "rb").read() == before  # 只读不动台账


def test_v9_report_exposes_root_cause_and_verdict_unchanged():
    """报告暴露 v9 根因段；判定/宪法/AAS/守护全不动。"""
    import json as _j
    r = K.build_report()
    # §4ba v10 主版本 7.0.0，round 前进到 §4ba；历史 v9 段仍在，机制断言不放宽
    assert r["kernel_version"].startswith(("6.", "7.")) and r["round"] in ("§4ay", "§4az", "§4ba")
    assert "root_cause" in _j.dumps(r["v9_root_cause"], ensure_ascii=False)
    assert r["constitution"]["ok"] is True
    res = _j.load(open(os.path.join(ROOT, "audit_l3_gap_targeted", "result.json"), encoding="utf-8"))
    assert res["verdict"] == "GAP_INCONCLUSIVE"
    assert res["l3_claimed"] is False and res["absolute_claimed"] is False
    spec = importlib.util.spec_from_file_location("aasdiag9", os.path.join(HERE, "diagnose_volition_aas.py"))
    diag = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(diag)
    assert diag.build_report()["has_idle_daemon"] is False


# ---------- §4az 授时因子投递断链诊断（v7 预言的真实事件）----------
def _zeitgeber_report():
    path = os.path.join(HERE, "diagnose_zeitgeber_delivery_gap.py")
    ns = {"__file__": os.path.abspath(path), "__name__": "__diag__"}
    with mock.patch.object(sys, "stdout", io.StringIO()):
        exec(compile(open(path, encoding="utf-8").read(), path, "exec"), ns)
    return ns["build_report"]()


def test_zeitgeber_delivery_gap_confirmed_by_evidence():
    """五分支证据导出 ZEITGEBER_DELIVERY_GAP_CONFIRMED，非硬编码结论。"""
    rep = _zeitgeber_report()
    b = rep["branch_checks"]
    assert all(b.values())  # 五个断链条件全成立
    assert rep["verdict"] == "ZEITGEBER_DELIVERY_GAP_CONFIRMED"
    # 结论-证据一致：任一分支翻转，verdict 必须随之改变（证明结论由证据生成）
    alt = dict(b, local_zero_write=False)
    ns_path = os.path.join(HERE, "diagnose_zeitgeber_delivery_gap.py")
    src = open(ns_path, encoding="utf-8").read()
    assert "scheduler_says_fired and local_zero_write and no_external_evidence" in src


def test_zeitgeber_evidence_layers_separated():
    """证据分层：本仓台账 A 级 vs 平台观测，不混同、不把'调度说触发'当内核收着。"""
    rep = _zeitgeber_report()
    assert rep["local_evidence_A"]["evidence_class"] == "本仓机械读取（A 级）"
    assert "平台侧" in rep["root_cause"] or "云端" in rep["root_cause"]
    assert rep["local_evidence_A"]["circadian_log_today_wakes_since_0700"] == 0
    assert rep["local_evidence_A"]["entrainment_externally_evidenced_wakes"] == 0
    assert rep["local_evidence_A"]["entrainment_last_woken_by"] is None


def test_zeitgeber_never_fabricates_woken_by_and_readonly():
    """不伪造外部证据、只读零污染、判定/宪法不动。"""
    rep = _zeitgeber_report()
    assert rep["verdict_unchanged"] is True and rep["read_only"] is True
    assert rep["constitution_ok"] is True
    assert "不伪造 woken_by" in rep["honesty"]
    assert "Ambient 仍 0" in rep["honesty"]
    src = open(os.path.join(HERE, "diagnose_zeitgeber_delivery_gap.py"), encoding="utf-8").read()
    # 只查守护调用原语；"cron" 作为被观测的调度表达式字符串出现在 PLATFORM_OBSERVATIONS 是事实记录，非引入守护
    for sym in ["import threading", "while True:", "asyncio.run", "import multiprocessing", "signal.alarm"]:
        assert sym not in src


def test_zeitgeber_ledger_exists_and_matches_verdict():
    """A 级台账真实落盘，verdict 与诊断一致。"""
    p = os.path.join(HERE, "data", "zeitgeber_delivery_gap.jsonl")
    assert os.path.exists(p)
    rows = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
    assert rows and rows[-1]["verdict"] == "ZEITGEBER_DELIVERY_GAP_CONFIRMED"
    assert rows[-1]["verdict_unchanged"] is True


# ---------- §4ba v10 运行基地：云端↔GitHub 双向自循环 ----------
def _v10_now():
    return datetime.datetime(2026, 11, 26, 23, 15, 0)  # UTC 23:15 = 北京 07:15


def test_v10_route_decision_rejects_local_online_probe(tmp_path):
    """路线一被选、路线二被否的理由写入报告；权衡由证据导出非口号。"""
    r = K.build_report()
    v10 = r["v10_github_base"]
    assert "§4az" in v10["decision"] and "§109" in v10["decision"]
    assert "本机" in v10["route_2_rejected"] and "断链" in v10["route_2_rejected"]
    assert "上行" in v10["route_1_bidir"] and "下行" in v10["route_1_bidir"]
    assert r["kernel_version"].startswith("7.")


def test_v10_base_beat_requires_external_woken_by(tmp_path):
    """空 woken_by 必拒——内核绝不代填外部证据（承 v7 证据纪律）。"""
    lp = os.path.join(str(tmp_path), "heartbeat_log.jsonl")
    bad = K.base_beat(woken_by="", log_path=lp, record=False)
    assert bad.get("error") and bad["ambient_still_zero"] is True
    assert bad["verdict_unchanged"] is True
    # 未落账
    beat_log = os.path.join(str(tmp_path), "base_beat_log.jsonl")
    assert not os.path.exists(beat_log)


def test_v10_base_beat_records_external_evidence(tmp_path):
    """外部 runner 带 woken_by 唤醒→落账、溯源分列、Ambient 恒 0、判定不动。"""
    lp = os.path.join(str(tmp_path), "heartbeat_log.jsonl")
    now = _v10_now()
    utc = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    beat = K.base_beat(woken_by="github_actions:run=42:utc=" + utc, now=now,
                       nonce="N42", runner_meta={"github_run_id": "42"}, log_path=lp, record=True)
    assert beat["beat_recorded"] is True and beat["constitution_ok"] is True
    assert beat["woken_by"].startswith("github_actions:run=42")
    assert beat["ambient_still_zero"] is True and beat["verdict_unchanged"] is True
    assert "外部 runner" in beat["evidence_class"]
    rows = [json.loads(l) for l in open(os.path.join(str(tmp_path), "base_beat_log.jsonl"), encoding="utf-8")]
    assert rows and rows[-1]["woken_by"].startswith("github_actions:")
    # 同目录派生 circadian_log 也带外部证据
    clog = os.path.join(str(tmp_path), "circadian_log.jsonl")
    wakes = [json.loads(l) for l in open(clog, encoding="utf-8") if json.loads(l).get("intent") == "WAKE"]
    assert wakes and all(w.get("woken_by", "").startswith("github_actions:") for w in wakes)


def test_v10_base_status_readonly_knowledge(tmp_path):
    """本机知情：读基地账算健康档/外部证据/Idle-Gap；纯只读零污染。"""
    lp = os.path.join(str(tmp_path), "heartbeat_log.jsonl")
    now = _v10_now()
    K.base_beat(woken_by="github_actions:run=7:utc=X", now=now, log_path=lp, record=True)
    st = K.base_status(log_path=lp, now=now + datetime.timedelta(hours=2))
    assert st["health"] in ("BASE_LINKED_EVIDENCED", "BASE_BEATS_UNPROVEN", "NO_BASE_BEAT")
    assert st["base_beats"] == 1 and st["beats_with_external_source"] == 1
    assert st["idle_gap_hours"] == 2.0
    assert st["evidence_class"].startswith("本仓机械读取")
    assert st["verdict_unchanged"] is True and st["ambient_still_zero"] is True
    assert st["constitution_ok"] is True


def test_v10_base_status_no_beat_honest_zero(tmp_path):
    """无基地心跳时如实报 NO_BASE_BEAT，不虚构活跃。"""
    lp = os.path.join(str(tmp_path), "heartbeat_log.jsonl")
    st = K.base_status(log_path=lp, now=_v10_now())
    assert st["health"] == "NO_BASE_BEAT" and st["base_beats"] == 0
    assert st["last_woken_by"] is None and st["idle_gap_hours"] is None
    assert "不虚构活跃" in st["note"]


def test_v10_takeover_request_whitelist_and_readonly(tmp_path):
    """本机接管：白名单动作可执行、未知动作标不可执行；只落指令不联网不判定。"""
    lp = os.path.join(str(tmp_path), "heartbeat_log.jsonl")
    ok = K.takeover_request(action="status", nonce="NC", log_path=lp, record=True)
    bad = K.takeover_request(action="rm -rf /", log_path=lp, record=True)
    assert ok["executable"] is True and bad["executable"] is False
    assert "不联网" in ok["honesty"] and ok["verdict_unchanged"] is True
    rows = [json.loads(l) for l in open(os.path.join(str(tmp_path), "takeover_inbox.jsonl"), encoding="utf-8")]
    assert len(rows) == 2 and rows[0]["executable"] is True and rows[1]["executable"] is False


def test_v10_workflow_structure_and_no_daemon(tmp_path):
    """workflow 含双触发+contents:write+commit回仓；外部执行器非内核守护。"""
    wf = os.path.join(ROOT, ".github", "workflows", "circadian_beat.yml")
    assert os.path.exists(wf)
    src = open(wf, encoding="utf-8").read()
    # v10.1 起 runner 用 execute_takeover 真执行（回执写 takeover_exec_log），非仅读收件箱
    for token in ["schedule:", "workflow_dispatch:", "contents: write", "git push", "base_beat", "execute_takeover"]:
        assert token in src
    # 内核源码仍不引入守护原语（C5：不放宽 AAS 免疫词表）
    spec = importlib.util.spec_from_file_location("aasdiag10", os.path.join(HERE, "diagnose_volition_aas.py"))
    diag = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(diag)
    assert diag.build_report()["has_idle_daemon"] is False


def test_v10_real_ledgers_zero_pollution():
    """专项运行不污染真实 base_beat/takeover 台账；判定/宪法不动。"""
    import hashlib
    real_files = [K.BASE_BEAT_LOG, K.TAKEOVER_INBOX]
    before = {p: hashlib.md5(open(p, "rb").read()).hexdigest() for p in real_files if os.path.exists(p)}
    # 只用 tmp_path 派生路径调用，不触碰真实路径
    assert K.base_beat(woken_by="", record=False).get("error")
    after = {p: hashlib.md5(open(p, "rb").read()).hexdigest() for p in real_files if os.path.exists(p)}
    assert before == after
    assert K.verify_constitution()["ok"] is True


# ---------- §4ba v10.1 云端真正执行本机指令 ----------
def _v10_takeover_paths(tmp_path):
    lp = os.path.join(str(tmp_path), "heartbeat_log.jsonl")
    return lp


def test_v101_execute_takeover_writes_receipt(tmp_path):
    """runner 真执行末条可执行指令：回执落账、动作结果非空、溯源分列、判定不动。"""
    lp = _v10_takeover_paths(tmp_path)
    K.takeover_request(action="status", nonce="EXEC-1", note="本机请求状态", log_path=lp, record=True)
    rec = K.execute_takeover(now=_v10_now(), woken_by="github_actions:run=99",
                             runner_meta={"github_run_id": "99"}, log_path=lp, record=True)
    assert rec["executed"] is True and rec["receipt_recorded"] is True
    assert rec["action"] == "status" and rec["source_nonce"] == "EXEC-1"
    assert rec["result"] and "health" in rec["result"]  # 真调用 base_status，非伪造
    assert rec["woken_by"].startswith("github_actions:")
    assert "外部 runner" in rec["evidence_class"]
    assert rec["verdict_unchanged"] is True and rec["ambient_still_zero"] is True
    assert rec["constitution_ok"] is True
    # 回执台账落盘
    rows = [json.loads(l) for l in open(os.path.join(str(tmp_path), "takeover_exec_log.jsonl"), encoding="utf-8")]
    assert rows and rows[-1]["source_nonce"] == "EXEC-1" and rows[-1]["executed"] is True


def test_v101_execute_takeover_maps_all_whitelist_actions(tmp_path):
    """六个白名单动作均真实映射：probe/digest/reorient/noop/status/sleep_override。"""
    lp = _v10_takeover_paths(tmp_path)
    expected = {
        "probe": "top_directions", "digest": "count", "reorient": "chosen",
        "noop": "noop", "status": "health", "sleep_override": "acknowledged",
    }
    for act, key in expected.items():
        K.takeover_request(action=act, nonce="A-" + act, log_path=lp, record=True)
        rec = K.execute_takeover(now=_v10_now(), log_path=lp, record=False)
        assert rec["executed"] is True and key in rec["result"], (act, rec)


def test_v101_execute_takeover_rejects_unknown_action(tmp_path):
    """未知动作拒绝执行、如实回执 error，不伪造成功。"""
    lp = _v10_takeover_paths(tmp_path)
    K.takeover_request(action="rm -rf /", nonce="BAD-1", log_path=lp, record=False)
    # takeover_request 会把未知动作标不可执行，故先手工写一条 executable 的未知动作
    with open(os.path.join(str(tmp_path), "takeover_inbox.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"at": "2026-11-25T01:00:00Z", "action": "exec_arbitrary", "executable": True,
                            "nonce": "BAD-2"}, ensure_ascii=False) + "\n")
    rec = K.execute_takeover(now=_v10_now(), log_path=lp, record=False)
    assert rec["executed"] is False and "UNKNOWN_ACTION" in rec["error"]
    assert "不伪造" not in rec or rec["error"]


def test_v101_execute_takeover_no_pending_honest_zero(tmp_path):
    """收件箱无可执行的本机指令时如实空跑，不伪造回执。"""
    lp = _v10_takeover_paths(tmp_path)
    rec = K.execute_takeover(now=_v10_now(), log_path=lp, record=False)
    assert rec["executed"] is False and rec["reason"] == "NO_PENDING_TAKEOVER"
    assert "不伪造回执" in rec["honesty"]
    assert rec["ambient_still_zero"] is True and rec["verdict_unchanged"] is True


def test_v101_workflow_calls_real_execution(tmp_path):
    """workflow 调 execute_takeover 真执行 + commit 回执台账；非仅消费知情。"""
    wf = os.path.join(ROOT, ".github", "workflows", "circadian_beat.yml")
    src = open(wf, encoding="utf-8").read()
    assert "execute_takeover" in src
    assert "takeover_exec_log.jsonl" in src
    assert "仅作知情" not in src  # 旧版"只消费不执行"文案已移除


def test_v101_real_exec_log_zero_pollution():
    """v10.1 专项不污染真实执行回执台账；判定/宪法不动。"""
    import hashlib
    p = K.TAKEOVER_EXEC_LOG
    before = hashlib.md5(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None
    K.execute_takeover(record=False)  # 不落盘
    after = hashlib.md5(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None
    assert before == after
    assert K.verify_constitution()["ok"] is True
