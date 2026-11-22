"""RSI 声称审计诚实性精研引擎（§91 自主运维第二轮）。

读已锁存证据，跑 FJ 取证裁决（法官自己读原文逐字锚点），落 result.json。
不修改任何历史证据；篡改测试只在临时副本（见 forensic_gates_ext2.live_regression）。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from svagent.forensic_gates_ext2 import adjudicate_rsi_claim_audit_honesty
from svagent.rsi_claim_audit_honesty import live_regression as gate_regression


def main() -> None:
    verdict, trace = adjudicate_rsi_claim_audit_honesty(
        claim="arXiv:2610.27610 RSI evaluation-evidence honest-boundary disclosure"
    )
    gate_live = gate_regression()
    result = {
        "request_id": "rsi-claim-audit-honesty-20261122",
        "gate": "rsi_claim_audit_honesty",
        "verdict": {
            "action": verdict.action, "code": verdict.code,
            "four_dims": {
                "product_process_split": verdict.product_process_split,
                "repeatability_audited": verdict.repeatability_audited,
                "improver_gain_isolated": verdict.improver_gain_isolated,
                "selection_unused_eval": verdict.selection_unused_eval,
            },
        },
        "forensic_trace": {
            k: trace[k] for k in
            ("mode", "gate", "evidence_scope", "sources", "source_sha256", "inferred")
            if k in trace
        },
        "chain_present": "chain" in trace,
        "gate_live_regression": gate_live,
        "honest_scope": "只判RSI声称是否诚实披露四评估边界；可迁移到任何RSI/self-improvement系统；不承诺改进真实有效",
    }
    (ROOT / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("action:", verdict.action, "| code:", verdict.code)
    print("inferred:", json.dumps(trace["inferred"], ensure_ascii=False))
    print("gate live all_passed:", gate_live["all_passed"])


if __name__ == "__main__":
    main()
