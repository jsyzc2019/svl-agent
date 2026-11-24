#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§L3 文档一致性审计：机械比对权威源真值 vs 当前态文档断言，防数字漂移。

只读：从 result.json / 台账 / KB 提取权威真值，扫描当前态文档的关键断言，
检查是否自相矛盾。历史时间点的快照叙述（如"KB172→174"）不作为当前态核对，
只核对明确标注"当前/基线/全量/191条/31点"的断言。不产生新判定、不改任何文件。

运行：python3.11 audit_l3_gap_targeted/audit_current_state_consistency.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _load(p):
    return json.load(open(os.path.join(ROOT, p), encoding="utf-8"))


def build_report():
    led = _load("audit_l3_gap_targeted/L3_EVIDENCE_LEDGER.json")
    kb = _load("knowledge_base_store.json")
    r2 = _load("audit_l3_gap_targeted/result.json")
    l3 = _load("audit_l3_fullchain_external/result.json")

    truths = {
        "n_rounds": led["n_rounds"],
        "explicit_l3_flags": led["stats"]["explicit_l3_flags"],
        "all_l3_false": led["stats"]["all_l3_false"],
        "confirmed": led["stats"]["verdict_distribution"].get("CONFIRMED"),
        "kb_count": len(kb["items"]),
        "r2_verdict": r2["verdict"],
        "l3_verdict": l3["verdict"],
        "r2_l3": r2["l3_claimed"],
        "l3_l3": l3["l3_claimed"],
        "r2_abs": r2["absolute_claimed"],
        "l3_abs": l3["absolute_claimed"],
    }
    # 断言集合：这些必须成立，否则审计 FAIL
    assertions = {
        "台账21轮": truths["n_rounds"] == 21,
        "18显式l3全false": truths["explicit_l3_flags"] == 18 and truths["all_l3_false"] is True,
        "3个CONFIRMED": truths["confirmed"] == 3,
        "KB无重复": len(set(x["item_id"] for x in kb["items"])) == truths["kb_count"],
        "L3-R2裁决不变": truths["r2_verdict"] == "GAP_INCONCLUSIVE",
        "OperationL3裁决不变": truths["l3_verdict"] == "FULLCHAIN_PARTIAL",
        "l3/absolute恒false": not any([truths["r2_l3"], truths["l3_l3"],
                                      truths["r2_abs"], truths["l3_abs"]]),
    }

    # 当前态文档断言扫描：速查表的 KB 数字必须等于权威值
    handoff = open(os.path.join(ROOT, "SESSION_HANDOFF.md"), encoding="utf-8").read()
    import re
    m = re.search(r"knowledge_base_store\.json`（(\d+) 条", handoff)
    handoff_kb = int(m.group(1)) if m else None
    assertions["handoff速查表KB数字一致"] = handoff_kb == truths["kb_count"]

    all_ok = all(assertions.values())
    return {
        "boundary": "纯只读一致性审计；不改任何文件；历史快照叙述不作当前态核对；不产生新判定。",
        "authoritative_truths": truths,
        "current_state_assertions": assertions,
        "handoff_kb_declared": handoff_kb,
        "all_consistent": all_ok,
        "failed": [k for k, v in assertions.items() if not v],
        "note": "今日四份诊断报告刻意不写死 KB 数字，只引用脚本/判定，从源头避免数字漂移。",
    }


def main():
    print(json.dumps(build_report(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
