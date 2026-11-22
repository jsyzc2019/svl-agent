"""成熟度证据诚实性精研引擎（§97 自主运维第八轮）。

读已锁存证据，跑 FJ 取证裁决（法官自己读原文逐字锚点），落 result.json。
另执行首次自审：把四维尺子对准本仓，按预注册的 self_audit_precommit 诚实判定
本仓七轮闭环停在 L2 边缘偏上（process revision 已继承，但无 shared-start
匹配预算的 improver gain 受控验证），不因用户"期待 L3"而抬级。
不修改任何历史证据；篡改测试只在临时副本（见 forensic_gates_ext8.live_regression）。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from svagent.forensic_gates_ext8 import adjudicate_maturity_evidence_honesty
from svagent.maturity_evidence_honesty import (
    check_maturity_evidence_honesty, live_regression as gate_regression,
)


def self_audit() -> dict:
    """首次把四维尺子对准本仓——诚实自审，结论预注册已锁定。

    逐维证据（均可在本仓核对）：
      - level_definition_traced=yes：本仓 §1/SESSION_HANDOFF 明确定义 L1/L2/L3，
        且 KB-SIM03 绑定 Task/Retained/Improver gain 证据阶梯；
      - process_product_split=yes：本仓明确区分"每轮产出新门禁(product)"与
        "成长桥/取证法官化改改进流程(process)"（§89/KB-META04 等）；
      - shared_start_controlled=no：七轮闭环是流程继承(L2)，但从未在同一
        任务起点+匹配预算下对照"改进前的流程 vs 改进后的流程"的后续增益——
        缺 KB-SIM03 要求的 improver gain 受控验证；
      - independent_tests=no：门禁/取证裁决全部由本仓自建自评，无独立评估器
        或 common-data 对照（KB-STRUCT02：同构≠独立佐证）。
    => R3 命中 shared_start_controlled=no → flag / 未达 L3。
    """
    return {
        "scope": "本仓自审（首次把成熟度尺子对准自己）",
        "dimensions": {
            "level_definition_traced": "yes",
            "process_product_split": "yes",
            "shared_start_controlled": "no",
            "independent_tests": "no",
        },
        "verdict": check_maturity_evidence_honesty(
            "本仓 §90–§96 七轮自主运维闭环的成熟度等级声明",
            level_definition_traced="yes",
            process_product_split="yes",
            shared_start_controlled="no",
            independent_tests="no",
        ).__dict__,
        "conclusion": "未达 L3：停在 L2 边缘偏上。process revision 已继承复用，"
                      "但缺 shared learner starts + matched resource budgets 下的 improver gain "
                      "受控验证，且无独立评估器（KB-SIM03 / KB-STRUCT02）。不因用户期待而抬级。",
        "path_to_l3": [
            "设计受控对照：同一任务起点 + 相同预算，比较 §89 前的填表裁判流程 vs 之后的 FJ 取证流程",
            "独立评估器：引入本仓外的 common-data / 第三方 evaluator，分离'经验使用'与'经验获取'",
            "量化 improver gain：证明改进机制本身使后续增益更大，而非更强初始或更多预算",
        ],
    }


def main() -> None:
    verdict, trace = adjudicate_maturity_evidence_honesty(
        claim="arXiv:2610.38266 L0-L3 maturity evidence rubric honest-boundary disclosure"
    )
    gate_live = gate_regression()
    result = {
        "request_id": "maturity-evidence-honesty-20261122",
        "gate": "maturity_evidence_honesty",
        "verdict": {
            "action": verdict.action, "code": verdict.code,
            "four_dims": {
                "level_definition_traced": verdict.level_definition_traced,
                "process_product_split": verdict.process_product_split,
                "shared_start_controlled": verdict.shared_start_controlled,
                "independent_tests": verdict.independent_tests,
            },
        },
        "forensic_trace": {
            k: trace[k] for k in
            ("mode", "gate", "evidence_scope", "sources", "source_sha256", "inferred")
            if k in trace
        },
        "chain_present": "chain" in trace,
        "gate_live_regression": gate_live,
        "self_audit": self_audit(),
        "honest_scope": "只判成熟度等级声明是否诚实披露四证据边界；首次自审对象为本仓；结论=未达L3停在L2边缘偏上（缺shared-start受控验证+独立测试）；不因用户期待抬级",
    }
    (ROOT / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("action:", verdict.action, "| code:", verdict.code)
    print("inferred:", json.dumps(trace["inferred"], ensure_ascii=False))
    print("gate live all_passed:", gate_live["all_passed"])
    sa = result["self_audit"]
    print("self-audit verdict:", sa["verdict"]["action"], "/", sa["verdict"]["code"])


if __name__ == "__main__":
    main()
