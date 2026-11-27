#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4hf 裁定回执一致性器官（纯函数，只读现场文件）。

对象=裁定留档的完整性（可纠错溯源闭环），不是判据有效性递归。
预注册 prereg_decision_receipt_20261127.json (sha 8c02729b) 先于取证锁定探针与判据。
探针只读现场文件、不硬编码"已执行"结论；阴性/阳性都落档。
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROBE_IDS = (
    "D1-provenance-backfill",
    "D2-falsification-merge",
    "D3-judgment-fork-defer",
)


def _read_json(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return json.load(f)


def probe_d1():
    """KB-AUDIT68/69 provenance 非空且含『裁定采纳回填』→EXECUTED。"""
    kb = _read_json("knowledge_base_store.json")
    by_id = {x["item_id"]: x for x in kb["items"]}
    ok = all(
        "裁定采纳回填" in str(by_id.get(iid, {}).get("provenance", ""))
        for iid in ("KB-AUDIT68", "KB-AUDIT69")
    )
    return "EXECUTED" if ok else "NOT_EXECUTED"


def probe_d2():
    """falsification_log 行数>=6 且三条 FALSIFY-CV* id 均在→EXECUTED。"""
    path = os.path.join(ROOT, "falsification_log.jsonl")
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    ids = {r["id"] for r in rows}
    need = {
        "FALSIFY-CV1-PROXY-NOT-CONSTRUCT",
        "FALSIFY-CV2-PRECISION-CI-WIDE",
        "FALSIFY-CV3-BASE-RATE-ENRICHMENT",
    }
    ok = len(rows) >= 6 and need.issubset(ids)
    return "EXECUTED" if ok else "NOT_EXECUTED"


def probe_d3():
    """result.json judgment_fork.user_verdict 以 DEFERRED 开头→EXECUTED。"""
    r = _read_json("audit_vanity_selfaudit/result.json")
    v = str(r.get("judgment_fork", {}).get("user_verdict", ""))
    return "EXECUTED" if v.startswith("DEFERRED") else "NOT_EXECUTED"


PROBES = {
    "D1-provenance-backfill": probe_d1,
    "D2-falsification-merge": probe_d2,
    "D3-judgment-fork-defer": probe_d3,
}

# 预注册锁定的 status 期望映射
EXPECT = {
    "PENDING_EXECUTION": "NOT_EXECUTED",
    "EXECUTED": "EXECUTED",
}


def check(decisions, probe_results=None):
    """核心判据：比对每条 decision 的 status 期望与现场探针结果。

    decisions: list of dict，每条含 id/status。
    probe_results: dict[id]->'EXECUTED'/'NOT_EXECUTED'，缺省则现场跑探针。
    """
    if probe_results is None:
        probe_results = {pid: PROBES[pid]() for pid in PROBE_IDS}
    mismatch = []
    rows = []
    for d in decisions:
        did = d.get("id", "")
        status = d.get("status", "")
        actual = probe_results.get(did, "NO_PROBE")
        expected = EXPECT.get(status, "UNKNOWN_STATUS")
        consistent = (expected == actual)
        if not consistent:
            mismatch.append(did)
        rows.append({
            "id": did,
            "status": status,
            "expected_by_status": expected,
            "actual_probe": actual,
            "consistent": consistent,
        })
    signal = "RECEIPT_MISMATCH" if mismatch else "ALL_RECEIPTS_CONSISTENT"
    return {
        "signal": signal,
        "mismatch_ids": mismatch,
        "rows": rows,
        "n": len(rows),
    }


def negative_self_bite():
    """三注入：全一致不该误报；两种方向失配都该抓。"""
    r1 = check(
        [{"id": p, "status": "EXECUTED"} for p in PROBE_IDS],
        probe_results={p: "EXECUTED" for p in PROBE_IDS},
    )
    r2 = check(
        [{"id": p, "status": ("PENDING_EXECUTION" if p == PROBE_IDS[0] else "EXECUTED")} for p in PROBE_IDS],
        probe_results={p: "EXECUTED" for p in PROBE_IDS},
    )
    r3 = check(
        [{"id": p, "status": ("EXECUTED" if p == PROBE_IDS[0] else "PENDING_EXECUTION")} for p in PROBE_IDS],
        probe_results={p: ("NOT_EXECUTED" if p == PROBE_IDS[0] else "NOT_EXECUTED") for p in PROBE_IDS},
    )
    passed = (
        r1["signal"] == "ALL_RECEIPTS_CONSISTENT"
        and r2["signal"] == "RECEIPT_MISMATCH" and r2["mismatch_ids"] == [PROBE_IDS[0]]
        and r3["signal"] == "RECEIPT_MISMATCH" and PROBE_IDS[0] in r3["mismatch_ids"]
    )
    return {
        "passed": passed,
        "detail": {
            "all_consistent_not_flagged": r1["signal"] == "ALL_RECEIPTS_CONSISTENT",
            "pending_but_done_caught": r2["signal"] == "RECEIPT_MISMATCH",
            "executed_but_not_done_caught": r3["signal"] == "RECEIPT_MISMATCH",
        },
    }


if __name__ == "__main__":
    dec = _read_json("DECISIONS_20261127.json")
    probes = {pid: PROBES[pid]() for pid in PROBE_IDS}
    r = check(dec["decisions"], probe_results=probes)
    print("signal =", r["signal"])
    print("probes =", json.dumps(probes, ensure_ascii=False))
    for row in r["rows"]:
        print(" ", row["id"], row["status"], "expected=", row["expected_by_status"],
              "actual=", row["actual_probe"], "consistent=", row["consistent"])
    print("negative_self_bite =", negative_self_bite()["passed"])
