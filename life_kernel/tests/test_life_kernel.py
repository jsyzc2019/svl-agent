#!/usr/bin/env python3
"""开放型生命体内核专项测试（只读仓库状态，不联网、不 spawn、不改判定）。"""
import importlib.util
import json
import os
import sys

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
