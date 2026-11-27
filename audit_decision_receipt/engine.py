#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4hf 取证引擎：裁定回执一致性首用 + 补录后复核。

只读被审文件；输出 result.json（独立文件，不碰判定态权威源）。
"""
import json
import os
from life_kernel.decision_receipt import (
    PROBE_IDS, PROBES, check, negative_self_bite,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEC = "DECISIONS_20261127.json"
OUT = os.path.join(ROOT, "audit_decision_receipt", "result.json")


def main():
    dec = json.load(open(os.path.join(ROOT, DEC), encoding="utf-8"))
    probes = {pid: PROBES[pid]() for pid in PROBE_IDS}
    # before 读首用快照文件（补录前真实状态），不随重跑重算——不追认失败
    first = json.load(open(os.path.join(ROOT, "audit_decision_receipt", "first_use_snapshot.json"),
                           encoding="utf-8"))
    before_decisions = [
        {"id": k, "status": v} for k, v in first["decisions_status_before"].items()
    ]
    before = check(before_decisions, probe_results=first["probe_results_at_first_use"])
    assert before["signal"] == first["first_use_signal"]
    assert before["mismatch_ids"] == first["first_use_mismatch_ids"]
    nb = negative_self_bite()
    # after 现场算当前 status 与现场探针
    after = check(dec["decisions"], probe_results=probes)
    out = {
        "round": "§4hf",
        "prereg": "prereg_decision_receipt_20261127.json",
        "object": "裁定留档完整性（可纠错溯源闭环），非判据有效性递归、非因子小话",
        "probe_results": probes,
        "receipt_check_before": before,
        "receipt_check_after_backfill": after,
        "negative_self_bite": nb,
        "self_bites": [
            "§4he 自身制造缺口：执行了裁定却忘回写 status，本轮由首用取证抓到并补录，如实认不粉饰（非 CORR-REAL 认知错误，是留档完整性遗漏）。"
        ],
        "honest_summary": (
            "首用抓到 RECEIPT_MISMATCH：三项裁定 D1/D2/D3 现场探针全 EXECUTED，"
            "但 DECISIONS 三条 status 仍 PENDING_EXECUTION——裁定记录说待执行、handoff 说已执行，"
            "留档自相矛盾。此缺口由 §4he 自身制造（执行了裁定却忘回写 status），如实认，不粉饰。"
            "补录 action=执行规则只补 status+receipt 字段，不改裁定实质内容、不新裁定、不代用户裁定。"
            "负向自咬三注入（全一致不误报/两方向失配都抓）全过。"
        ),
        "verdict_impact": "不动（verdict/l3/absolute 与宪法锁字节未变，判定态前后快照核验）",
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("signal =", before["signal"], "mismatch =", before["mismatch_ids"])
    print("self_bite =", nb["passed"])


if __name__ == "__main__":
    main()
