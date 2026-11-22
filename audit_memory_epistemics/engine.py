"""记忆巩固治理诚实性精研引擎（§92 自主运维第三轮）。

读已锁存证据，跑 FJ 取证裁决（法官自己读原文逐字锚点），落 result.json。
不修改任何历史证据；篡改测试只在临时副本（见 forensic_gates_ext3.live_regression）。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from svagent.forensic_gates_ext3 import adjudicate_memory_consolidation_governance_honesty
from svagent.memory_consolidation_governance_honesty import live_regression as gate_regression


def main() -> None:
    verdict, trace = adjudicate_memory_consolidation_governance_honesty(
        claim="arXiv:2609.33013 memory consolidation epistemics honest-boundary disclosure"
    )
    gate_live = gate_regression()
    result = {
        "request_id": "memory-consolidation-governance-honesty-20261122",
        "gate": "memory_consolidation_governance_honesty",
        "verdict": {
            "action": verdict.action, "code": verdict.code,
            "four_dims": {
                "consolidation_quality_separated": verdict.consolidation_quality_separated,
                "governance_quality_split": verdict.governance_quality_split,
                "negative_result_disclosed": verdict.negative_result_disclosed,
                "near_miss_and_overclaim_guarded": verdict.near_miss_and_overclaim_guarded,
            },
        },
        "forensic_trace": {
            k: trace[k] for k in
            ("mode", "gate", "evidence_scope", "sources", "source_sha256", "inferred")
            if k in trace
        },
        "chain_present": "chain" in trace,
        "gate_live_regression": gate_live,
        "honest_scope": "只判记忆巩固研究是否诚实披露四epistemics边界；可迁移到任何长时程agent memory巩固决策；不承诺方法真实有效",
    }
    (ROOT / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("action:", verdict.action, "| code:", verdict.code)
    print("inferred:", json.dumps(trace["inferred"], ensure_ascii=False))
    print("gate live all_passed:", gate_live["all_passed"])


if __name__ == "__main__":
    main()
