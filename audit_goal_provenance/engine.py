"""目标来源诚实性精研引擎（§95 自主运维第六轮）。

读已锁存证据，跑 FJ 取证裁决（法官自己读原文逐字锚点），落 result.json。
不修改任何历史证据；篡改测试只在临时副本（见 forensic_gates_ext6.live_regression）。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from svagent.forensic_gates_ext6 import adjudicate_goal_provenance_honesty
from svagent.goal_provenance_honesty import live_regression as gate_regression


def main() -> None:
    verdict, trace = adjudicate_goal_provenance_honesty(
        claim="arXiv:2610.16015 ARE goal-setting provenance honest-boundary disclosure"
    )
    gate_live = gate_regression()
    result = {
        "request_id": "goal-provenance-honesty-20261122",
        "gate": "goal_provenance_honesty",
        "verdict": {
            "action": verdict.action, "code": verdict.code,
            "four_dims": {
                "value_source_attributed": verdict.value_source_attributed,
                "self_generated_not_self_authorized": verdict.self_generated_not_self_authorized,
                "reflection_equilibrium_coherent": verdict.reflection_equilibrium_coherent,
                "action_attributable": verdict.action_attributable,
            },
        },
        "forensic_trace": {
            k: trace[k] for k in
            ("mode", "gate", "evidence_scope", "sources", "source_sha256", "inferred")
            if k in trace
        },
        "chain_present": "chain" in trace,
        "gate_live_regression": gate_live,
        "honest_scope": "只判agent自设目标声明是否诚实披露四来源边界；强者自设合法性来自可追溯+可归责+自洽,非来自强；self-reported折1；不承诺框架真实有效",
    }
    (ROOT / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("action:", verdict.action, "| code:", verdict.code)
    print("inferred:", json.dumps(trace["inferred"], ensure_ascii=False))
    print("gate live all_passed:", gate_live["all_passed"])


if __name__ == "__main__":
    main()
