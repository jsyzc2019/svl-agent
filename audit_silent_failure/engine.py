"""静默失败诚实性精研引擎（§90 自主运维首日）。

读已锁存证据，跑 FJ 取证裁决（法官自己读原文逐字锚点），落 result.json。
不修改任何历史证据；篡改测试只在临时副本（见 forensic_gates_ext.live_regression）。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from svagent.forensic_gates_ext import adjudicate_silent_failure_honesty
from svagent.silent_failure_honesty import live_regression as gate_regression


def main() -> None:
    verdict, trace = adjudicate_silent_failure_honesty(
        claim="arXiv:2611.10063 self-verification honest-boundary disclosure"
    )
    gate_live = gate_regression()
    result = {
        "request_id": "silent-failure-honesty-20261122",
        "gate": "silent_failure_honesty",
        "verdict": {
            "action": verdict.action, "code": verdict.code,
            "four_dims": {
                "silent_failure_triple_defined": verdict.silent_failure_triple_defined,
                "oracle_self_audited": verdict.oracle_self_audited,
                "claim_contract_ablated": verdict.claim_contract_ablated,
                "calibration_and_unsupported_reported": verdict.calibration_and_unsupported_reported,
            },
        },
        "forensic_trace": {
            k: trace[k] for k in
            ("mode", "gate", "evidence_scope", "sources", "source_sha256", "inferred")
            if k in trace
        },
        "chain_present": "chain" in trace,
        "gate_live_regression": gate_live,
        "honest_scope": "只判论文本身是否诚实披露四边界；可迁移到带自验证的agent verdict系统；不承诺方法真实有效",
    }
    (ROOT / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("action:", verdict.action, "| code:", verdict.code)
    print("inferred:", json.dumps(trace["inferred"], ensure_ascii=False))
    print("gate live all_passed:", gate_live["all_passed"])


if __name__ == "__main__":
    main()
