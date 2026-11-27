#!/usr/bin/env python3
"""§4hf 守卫：裁定回执一致性器官 + 补录边界。"""
import hashlib
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(rel):
    return json.load(open(os.path.join(ROOT, rel), encoding="utf-8"))


def test_01_prereg_hash_lock():
    d = _load("prereg_decision_receipt_20261127.json")
    locked = d.pop("sha256")
    actual = hashlib.sha256(json.dumps(d, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    assert locked == actual == "8c02729b0a50a4c0b155ea336b1d13221151fbe1cae8b41d6044aa5d1be9fcff"


def test_02_negative_self_bite():
    from life_kernel.decision_receipt import negative_self_bite
    r = negative_self_bite()
    assert r["passed"] is True and all(r["detail"].values())


def test_03_probes_read_live_files():
    """探针只读现场文件、不硬编码结论：篡改现场应改探针结果（负向）。"""
    from life_kernel import decision_receipt as dr
    assert dr.probe_d1() == "EXECUTED" and dr.probe_d2() == "EXECUTED" and dr.probe_d3() == "EXECUTED"
    # 反向探针：喂一个根本不存在的 status / 探针组合应被判失配
    r = dr.check([{"id": "D1-provenance-backfill", "status": "PENDING_EXECUTION"}],
                 probe_results={"D1-provenance-backfill": "EXECUTED"})
    assert r["signal"] == "RECEIPT_MISMATCH"


def test_04_first_use_mismatch_preserved():
    """首用 MISMATCH 快照不随重跑改写（不追认失败）。"""
    r = _load("audit_decision_receipt/result.json")
    assert r["receipt_check_before"]["signal"] == "RECEIPT_MISMATCH"
    assert len(r["receipt_check_before"]["mismatch_ids"]) == 3
    assert r["receipt_check_after_backfill"]["signal"] == "ALL_RECEIPTS_CONSISTENT"


def test_05_backfill_content_unchanged():
    """补录只改 status+加 receipt，裁定实质内容未改。"""
    d = _load("DECISIONS_20261127.json")
    assert len(d["decisions"]) == 3
    for x in d["decisions"]:
        assert x["status"] == "EXECUTED"
        rc = x["receipt"]
        assert "§4hf 补录" in rc["note"] and "非新裁定" in rc["note"]
        assert rc["evidence_probe"]  # 回执带现场证据锚点，非空口无凭
        # 裁定实质字段仍在
        for k in ("user_verdict", "agent_recommendation", "execution", "source"):
            assert k in x


def test_06_live_consistency():
    """当前 DECISIONS status 与现场探针一致。"""
    from life_kernel.decision_receipt import PROBE_IDS, PROBES, check
    d = _load("DECISIONS_20261127.json")
    r = check(d["decisions"], probe_results={p: PROBES[p]() for p in PROBE_IDS})
    assert r["signal"] == "ALL_RECEIPTS_CONSISTENT"


def test_07_self_bite_recorded():
    r = _load("audit_decision_receipt/result.json")
    assert any("§4he 自身制造" in b for b in r["self_bites"])


def test_08_triplet_unchanged():
    a = _load("audit_l3_gap_targeted/result.json")
    assert (a["verdict"], a["l3_claimed"], a["absolute_claimed"]) == ("GAP_INCONCLUSIVE", False, False)
