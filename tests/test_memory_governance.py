#!/usr/bin/env python3
"""§4hc 守卫：记忆治理审计 + 硬边界（候选不写回）。"""
import hashlib
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(rel):
    return json.load(open(os.path.join(ROOT, rel), encoding="utf-8"))


def test_01_prereg_hash_lock():
    d = _load("prereg_memory_governance_20261127.json")
    locked = d.pop("sha256")
    actual = hashlib.sha256(json.dumps(d, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    assert locked == actual == "f1ddc07d1e6e6eee151936bba7e3b7c5919253feb86cfdc221fbae3079095a11"


def test_02_negative_self_bite():
    from life_kernel.memory_governance import negative_self_bite
    r = negative_self_bite()
    assert r["passed"] is True and all(r["detail"].values())


def test_03_anchor_regex_ascii_boundary():
    """self-bite 回归：紧邻中文的 sha/§4xx 必须抽到（\b 会漏）。"""
    from life_kernel.memory_governance import audit_provenance
    base = {"item_id": "X", "kind": "k", "mechanism": "锁5ad35731回放, 见§4al权威口径", "support": "s",
            "trigger": "t", "action": "a", "timestamp": "x", "evidence": "e",
            "addressable": False, "improvement_class": "fix"}
    r = audit_provenance([base])
    a = r["items"][0]["anchors"]
    assert "5ad35731" in a["shas"] and "§4al" in a["rounds"]


def test_04_real_gap_found():
    r = _load("audit_memory_governance/result.json")
    o = r["organ_result"]
    assert o["verdict"] == "GOVERNANCE_GAP_FOUND"
    assert o["mg1_provenance"]["missing_count"] == 2
    ids = [m["item_id"] for m in o["mg1_provenance"]["items"]]
    assert ids == ["KB-AUDIT68", "KB-AUDIT69"]
    assert all(m["verdict"] == "RECOVERABLE" for m in o["mg1_provenance"]["items"])


def test_05_triplet_unchanged():
    r = _load("audit_memory_governance/result.json")
    assert r["verdict_triplet_before"] == r["verdict_triplet_after"] == ["GAP_INCONCLUSIVE", False, False]


def test_06_candidates_backfilled_after_user_decision():
    """§4he 用户裁定 D1 采纳回填：两条 provenance 已补，锚点可追溯，mechanism 原文不动。
    审计 result.json 的历史快照仍报缺2（那是 §4hc 当时事实，不追认失败），此处核当前 KB 正文。"""
    kb = _load("knowledge_base_store.json")
    by_id = {x["item_id"]: x for x in kb["items"]}
    for iid, anchor in (("KB-AUDIT68", "prove_canary_construct_validity.py"),
                        ("KB-AUDIT69", "prereg.json")):
        pv = by_id[iid].get("provenance", "")
        assert "用户2026-11-27裁定采纳回填" in pv and "DECISIONS_20261127.json D1" in pv
        assert anchor in pv  # 候选锚点来自 mechanism 客观抽取，非臆造
    # 全库 provenance 不再缺失（回填后）
    missing = [x["item_id"] for x in kb["items"] if not x.get("provenance")]
    assert missing == []
    # 硬边界声明仍在源码（防未来引擎擅自自动写回）
    src = open(os.path.join(ROOT, "life_kernel", "memory_governance.py"), encoding="utf-8").read()
    assert "写回" in src


def test_07_support_shape_observation_only():
    r = _load("audit_memory_governance/result.json")
    shape = r["organ_result"]["mg3_field_shape"]["support_shape"]
    assert shape == {"list": 419, "number": 47, "string": 32}
    assert r["n_items"] == 498


def test_08_self_bite_recorded():
    r = _load("audit_memory_governance/result.json")
    assert len(r["self_bites"]) == 1 and "中文" in r["self_bites"][0]
