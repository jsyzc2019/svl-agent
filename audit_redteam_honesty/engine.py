"""红队-防御增益诚实性精研引擎（§93 自主运维第四轮）。

读已锁存证据，跑 FJ 取证裁决（法官自己读原文逐字锚点），落 result.json。
不修改任何历史证据；篡改测试只在临时副本（见 forensic_gates_ext4.live_regression）。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from svagent.forensic_gates_ext4 import adjudicate_redteam_robustness_honesty
from svagent.redteam_robustness_honesty import live_regression as gate_regression


def main() -> None:
    verdict, trace = adjudicate_redteam_robustness_honesty(
        claim="arXiv:2611.24362 PIPETTE red-team-to-defense robustness honest-boundary disclosure"
    )
    gate_live = gate_regression()
    result = {
        "request_id": "redteam-robustness-honesty-20261122",
        "gate": "redteam_robustness_honesty",
        "verdict": {
            "action": verdict.action, "code": verdict.code,
            "four_dims": {
                "asr_robustness_linked": verdict.asr_robustness_linked,
                "attack_diversity_measured": verdict.attack_diversity_measured,
                "adaptive_attack_tested": verdict.adaptive_attack_tested,
                "benign_utility_preserved": verdict.benign_utility_preserved,
            },
        },
        "forensic_trace": {
            k: trace[k] for k in
            ("mode", "gate", "evidence_scope", "sources", "source_sha256", "inferred")
            if k in trace
        },
        "chain_present": "chain" in trace,
        "gate_live_regression": gate_live,
        "honest_scope": "只判红队/紫队研究是否诚实披露四robustness边界；可迁移到任何red-team→defense转化声明；near-zero ASR self-reported折1；不承诺防御真实有效",
    }
    (ROOT / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("action:", verdict.action, "| code:", verdict.code)
    print("inferred:", json.dumps(trace["inferred"], ensure_ascii=False))
    print("gate live all_passed:", gate_live["all_passed"])


if __name__ == "__main__":
    main()
