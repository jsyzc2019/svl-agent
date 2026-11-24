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


def test_evolve_closes_loop_without_verdict_change():
    """进化闭环写入心跳但不改任何既有判定、不动冻结基准。"""
    r = K.evolve("测试方向:验证闭环不翻案", "测试动作")
    assert r["heartbeat_written"] is True
    assert r["constitution"]["ok"] is True
    assert r["verified"]["no_verdict_change"] is True
    assert r["verified"]["original_100_untouched"] is True
    # 既有判定未变
    res = json.load(open(os.path.join(ROOT, "audit_l3_gap_targeted", "result.json"), encoding="utf-8"))
    assert res["verdict"] == "GAP_INCONCLUSIVE"
    assert res["l3_claimed"] is False and res["absolute_claimed"] is False


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
