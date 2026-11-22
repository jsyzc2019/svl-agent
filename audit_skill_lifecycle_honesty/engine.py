"""技能演化生命周期诚实性精研引擎（§96 自主运维第七轮）。

读已锁存证据，跑 FJ 取证裁决（法官自己读原文逐字锚点），落 result.json。
不修改任何历史证据；篡改测试只在临时副本（见 forensic_gates_ext7.live_regression）。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from svagent.forensic_gates_ext7 import adjudicate_skill_lifecycle_honesty
from svagent.skill_lifecycle_honesty import live_regression as gate_regression


def main() -> None:
    verdict, trace = adjudicate_skill_lifecycle_honesty(
        claim="arXiv:2610.09832 SkillForge skill-lifecycle honest-boundary disclosure"
    )
    gate_live = gate_regression()
    result = {
        "request_id": "skill-lifecycle-honesty-20261122",
        "gate": "skill_lifecycle_honesty",
        "verdict": {
            "action": verdict.action, "code": verdict.code,
            "four_dims": {
                "lifecycle_stages_disclosed": verdict.lifecycle_stages_disclosed,
                "credit_assignment_audited": verdict.credit_assignment_audited,
                "mutation_teacher_controlled": verdict.mutation_teacher_controlled,
                "retirement_failure_attributed": verdict.retirement_failure_attributed,
            },
        },
        "forensic_trace": {
            k: trace[k] for k in
            ("mode", "gate", "evidence_scope", "sources", "source_sha256", "inferred")
            if k in trace
        },
        "chain_present": "chain" in trace,
        "gate_live_regression": gate_live,
        "honest_scope": "只判技能库自演化声明是否诚实披露四演化治理边界；self-reported 7.8%折1；不承诺lifecycle真实有效",
    }
    (ROOT / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("action:", verdict.action, "| code:", verdict.code)
    print("inferred:", json.dumps(trace["inferred"], ensure_ascii=False))
    print("gate live all_passed:", gate_live["all_passed"])


if __name__ == "__main__":
    main()
