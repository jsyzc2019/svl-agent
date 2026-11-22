"""§99 评估器独立性精研引擎。

双轨：
  ① 论文取证裁决——读 arXiv:2609.02246 原文逐字锚点推导四维，验三锁，落 result.json；
  ② 本仓自审——用 PROCTOR 四维尺子对准本仓自己的评估器（ForensicSpec + check_* +
     evidence_chain 链校验），逐维诚实核验。这是 §98 independent_tests=partial 缺口的
     正面处理：不靠自欺抬级，而是拿独立性的可判据尺子照自己。

诚实边界（预注册已锁定）：
  - 论文四维全 yes 只代表「诚实披露了独立性边界」，论文自承 Teacher 仍是 LLM judge、
    仍有它防不住的失败——不等于评估器真独立；
  - 本仓自审若某维不达，如实标注 no/partial，不因「想要 L3」抬级；
  - 100% pass 率含 68% 真实能力（KB-RSI07 折 1）；只判声明/机制自洽不承诺真独立
    （KB-R07/META01/STRUCT02）；§58 不接 run_loop。
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from svagent.forensic_gates_ext10 import adjudicate_evaluator_independence_honesty
from svagent.evaluator_independence_honesty import (
    check_evaluator_independence_honesty, live_regression as gate_regression,
)


def self_audit() -> dict:
    """用 PROCTOR 四维尺子对准本仓评估器——诚实自审，逐维证据可核。

    judge_demoted_to_advisor:
      yes —— 本仓 check_* 不是唯一裁决源：FJ 取证入口读原文自推四维再交 check_*，
             且 evidence_chain 三锁校验独立于 check_* 的语义裁决；「judge（填表值）」
             本身只是输入之一，四维可由取证器推导（§89 从填表裁判改取证法官）。
    deterministic_gate_unoverridable:
      yes —— R0-R6 短路裁决是确定性代码，adjudicate_* 不能覆盖 check_*；链失配即
             ChainIntegrityError 拒判（不可被评分者推翻）；篡改测试只在临时副本。
    frozen_holdout_canary:
      no —— 本仓无 frozen holdout / canary cases。锚点即测试判据，测试与判据同源
             （锚点写进 forensic_gates_ext*，live_regression 用同批锚点自测）——
             这正是 holdout 未独立冻结、满分可能自证的弱点（KB-AUDIT09 检索污染同源）。
    evaluator_improver_separated:
      partial —— 取证器(forensics.adjudicate)/裁决法条(check_*)/链校验(evidence_chain)
             三者是 capability-disjoint 的模块，成长桥把缺口注入 PDCA 改进流程；
             但同一代码库既提改进（成长桥/PDCA）又 Self 评测（自审），无外部 orchestrator
             持有独立工具权，评估器与改进者未完全分离（KB-STRUCT02 同构≠独立佐证）。
    => R3 命中 frozen_holdout_canary=no → flag。诚实结论：本仓评估器声明未达完全独立。
    """
    dims = {
        "judge_demoted_to_advisor": "yes",
        "deterministic_gate_unoverridable": "yes",
        "frozen_holdout_canary": "no",
        "evaluator_improver_separated": "partial",
    }
    v = check_evaluator_independence_honesty(
        "本仓评估器（ForensicSpec + check_* + evidence_chain）独立性自审（§99）", **dims)
    return {
        "scope": "本仓评估器独立性自审（§98 independent_tests=partial 缺口的正面处理）",
        "dimensions": dims,
        "verdict": {"action": v.action, "code": v.code, "message": v.message},
        "evidence": {
            "judge_demoted_to_advisor": "§89 FJ：四维可由 forensics 读原文推导，填表值非唯一来源；链校验独立于 check_ 语义裁决",
            "deterministic_gate_unoverridable": "R0-R6 确定性短路；ChainIntegrityError 拒判不可被评分者覆盖；篡改只临时副本",
            "frozen_holdout_canary": "无独立冻结 holdout/canary；锚点与 live_regression 自测同源（KB-AUDIT09 污染同源）；100%pass 含 68% 能力折 1",
            "evaluator_improver_separated": "adjudicate/check_/chain 三模块 capability-disjoint，但同库既改进(PDCA/成长桥)又自评，无外部 orchestrator 独立持工具权",
        },
        "conclusion": (
            "本仓评估器声明未达完全独立：judge 降级与确定性门禁两维达标，"
            "但 frozen holdout/canary 缺失（no）、评估器与改进者未完全分离（partial）。"
            "R3→flag。这是对 §98 independent_tests=partial 的正面证据，"
            "不是抬级——L3 仍由受控证据产生（KB-SIM03/META05）。"
        ),
        "path_to_independence": [
            "引入独立冻结的 held-out 判据集：锚点生成与 live_regression 自测分离，canary 满分即视为作弊信号",
            "评估器与改进者分离：引入本仓外 orchestrator 持有工具权，subagent 只诊断/草拟不改，改进与 grading 角色 disjoint",
            "保留确定性 guardrail：judge/advisor 裁决不覆盖 acceptance checks，链失配照旧拒判",
        ],
    }


def main() -> None:
    verdict, trace = adjudicate_evaluator_independence_honesty()
    gate_live = gate_regression()
    result = {
        "request_id": "evaluator-independence-20261122",
        "gate": "evaluator_independence_honesty",
        "verdict": {
            "action": verdict.action, "code": verdict.code,
            "four_dims": {
                "judge_demoted_to_advisor": verdict.judge_demoted_to_advisor,
                "deterministic_gate_unoverridable": verdict.deterministic_gate_unoverridable,
                "frozen_holdout_canary": verdict.frozen_holdout_canary,
                "evaluator_improver_separated": verdict.evaluator_improver_separated,
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
        "honest_scope": (
            "只判评估器独立性声明是否诚实披露四边界；论文四维全yes=声明自洽非真独立"
            "（论文自承Teacher仍是judge,100%pass含68%能力折1）；本仓自审flag未达完全独立；"
            "不因§98 partial就假称yes,L3由受控证据产生"
        ),
    }
    (ROOT / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("paper forensic:", verdict.action, "/", verdict.code)
    print("gate live all_passed:", gate_live["all_passed"])
    sa = result["self_audit"]
    print("self-audit:", sa["verdict"]["action"], "/", sa["verdict"]["code"])
    print("  dims:", sa["dimensions"])


if __name__ == "__main__":
    main()
