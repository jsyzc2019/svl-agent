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


def test_self_modify_registers_seeds_and_archives_only_after_validation():
    """自改闭环：经验验证全过才写 policy；archive 保留快照可回滚；宪法层不变。"""
    # 备份真实 policy，测试后复原（只读纪律）
    policy_bak = open(K.POLICY, encoding="utf-8").read() if os.path.exists(K.POLICY) else None
    try:
        # 重置为未注册状态，模拟首次自改
        init = {"policy_version": "1.0.0", "updated_at": None, "registered_frontier_seeds": []}
        with open(K.POLICY, "w", encoding="utf-8") as f:
            json.dump(init, f, ensure_ascii=False)
        # 合成 canary 收敛历史，确保守卫验证走真实分支
        hb_bak = open(K.HEARTBEAT_LOG, encoding="utf-8").read() if os.path.exists(K.HEARTBEAT_LOG) else ""
        with open(K.HEARTBEAT_LOG, "w", encoding="utf-8") as f:
            for h in CANARY_HISTORY:
                f.write(json.dumps({"direction": h}, ensure_ascii=False) + "\n")
        try:
            r = K.self_modify(reason="测试:经验验证驱动的自改")
        finally:
            with open(K.HEARTBEAT_LOG, "w", encoding="utf-8") as f:
                f.write(hb_bak)
        assert r["accepted"] is True
        assert r["validation"]["all_pass"] is True
        assert r["validation"]["guard_detects_convergence"] is True
        assert r["validation"]["guard_allows_diverse"] is True
        assert r["validation"]["verdict_unchanged"] is True
        assert r["policy_written"] is True
        # 策略确实写入：探索池扩张
        pool = K.explore_pool()
        assert len(pool) > 7
        # archive 快照存在且可回滚（两份：before + after）
        assert len(r.get("archive_after", "")) > 0 and os.path.exists(r["archive_after"])
        snap = json.load(open(r["archive_after"], encoding="utf-8"))
        assert snap["policy"]["registered_frontier_seeds"]
        # 宪法层未被触碰
        assert r["constitution_ok"] is True
        assert K.verify_constitution()["ok"] is True
    finally:
        if policy_bak is not None:
            with open(K.POLICY, "w", encoding="utf-8") as f:
                f.write(policy_bak)


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
