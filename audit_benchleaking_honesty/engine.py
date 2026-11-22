"""Benchmark 污染诚实性精研引擎（§94 自主运维第五轮）。

读已锁存证据，跑 FJ 取证裁决（法官自己读原文逐字锚点），落 result.json。
不修改任何历史证据；篡改测试只在临时副本（见 forensic_gates_ext5.live_regression）。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from svagent.forensic_gates_ext5 import adjudicate_benchleaking_honesty
from svagent.benchleaking_honesty import live_regression as gate_regression


def main() -> None:
    verdict, trace = adjudicate_benchleaking_honesty(
        claim="arXiv:2611.21315 benchleaking benchmark score contamination honest-boundary disclosure"
    )
    gate_live = gate_regression()
    result = {
        "request_id": "benchleaking-honesty-20261122",
        "gate": "benchleaking_honesty",
        "verdict": {
            "action": verdict.action, "code": verdict.code,
            "four_dims": {
                "benchleaking_vs_maxxing": verdict.benchleaking_vs_maxxing,
                "leakage_probe_disclosed": verdict.leakage_probe_disclosed,
                "score_adjusted_for_leak": verdict.score_adjusted_for_leak,
                "scope_bounded": verdict.scope_bounded,
            },
        },
        "forensic_trace": {
            k: trace[k] for k in
            ("mode", "gate", "evidence_scope", "sources", "source_sha256", "inferred")
            if k in trace
        },
        "chain_present": "chain" in trace,
        "gate_live_regression": gate_live,
        "honest_scope": "只判benchmark分数声称是否诚实披露四污染边界；可迁移到任何leaderboard/模型发布分数声明；泄漏率self-reported折1；不承诺模型真实无污染",
    }
    (ROOT / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("action:", verdict.action, "| code:", verdict.code)
    print("inferred:", json.dumps(trace["inferred"], ensure_ascii=False))
    print("gate live all_passed:", gate_live["all_passed"])


if __name__ == "__main__":
    main()
