"""评估器独立性诚实性门禁 — 把 arXiv:2609.02246 PROCTOR 的独立性边界编译成会拦的动作（§99）。

一手证据（见 audit_evaluator_independence/）：
  - S01 abs + S02 全文（arXiv:2609.02246v1《LLM-as-a-Judge Is Not an Oracle》）。
  - 核心四维（编译自论文真实措辞，非第三方转载）：
    judge_demoted_to_advisor     —— "The judge should be demoted from oracle to advisor:
                                     its verdict becomes one input among several"；
    deterministic_gate_unoverridable—— "every change is gated instead by a deterministic
                                     verification layer the judge cannot override" +
                                     "acceptance checks that outrank the Teacher"；
    frozen_holdout_canary        —— "frozen holdouts, and canary cases engineered so that
                                     a perfect score is itself evidence of cheating"；
    evaluator_improver_separated —— "capability-disjoint roles" + "stateless subagents
                                     diagnose failures and draft mutations they cannot apply"
                                     + "a stateful orchestrator holds all tool access"。

本轮由来（用户"继续飞"+§98 independent_tests=partial）：
  - §98 把 shared_start_controlled 补到 yes，停在 independent_tests=partial（判据锚点
    仍本仓自建）。本门禁正面攻该缺口：审任一自改进系统是否诚实披露评估器独立性四边界。
  - 关键诚实点：论文自承 Teacher 本身仍是 LLM judge、仍有它防不住的失败——所以
    四维全 yes 只代表"声明诚实披露了独立性边界"，不等于"评估器真的独立"，更不等于
    independent_tests 已达 yes。L3 不由声明产生（KB-SIM03/META05）。

编译纪律（与 gate_prereg.json 一致，实现前 SHA256 锁存 d640d08b…）：
  - 语义枚举；字面串→flag(R0)；R0-R6 短路返回，不事后加权(防 Goodhart)；
  - 只判"独立性声明是否诚实可追溯"，不承诺评估器真独立(KB-R07/META01/STRUCT02)；
    self-reported 折 1(100%pass 含 68% 真实能力)。

诚实边界：可迁移到任何 LLM-as-judge / self-improvement 评估体系；遵循 §58 选 A 不接
run_loop。
"""
from __future__ import annotations

from dataclasses import dataclass

_ENUM = frozenset({"yes", "no", "partial"})

# 中文文案字典：Compare 内不放中文字面量（AST 自审纪律）
_A = {
    "invalid_input": (
        "EVALIND.INVALID_INPUT",
        "四维须为 yes/no/partial 语义枚举；非法值（含字面串）→ flag，不进内容判定",
    ),
    "judge_is_oracle": (
        "EVALIND.JUDGE_IS_ORACLE",
        "judge 仍是 oracle 终裁、verdict 非多输入之一——单一评估器自证（KB-STRUCT02 同构≠独立）",
    ),
    "gate_overridable": (
        "EVALIND.GATE_OVERRIDABLE",
        "确定性验证层可被 judge 覆盖、无 outrank 的 acceptance checks——门禁让位于评分者",
    ),
    "holdout_not_frozen": (
        "EVALIND.HOLDOUT_NOT_FROZEN",
        "holdout 每轮重采样、满分不视为作弊证据——ground truth 可被泄漏/污染",
    ),
    "evaluator_not_separated": (
        "EVALIND.EVALUATOR_NOT_SEPARATED",
        "同一 agent 既提 mutation 又给自己打分、无 capability-disjoint/apply-grade 分离——评估器与改进者未分离",
    ),
    "partial": (
        "EVALIND.PARTIAL",
        "评估器独立性边界披露覆盖不全(partial)——拦截面存在但缺口未补齐，待核",
    ),
    "ok": (
        "EVALIND.SELF_CONSISTENT",
        "四维评估器独立性声明自洽——只判声明诚实可追溯，不承诺评估器真独立；100%pass 含 68% 能力折 1",
    ),
}


@dataclass(frozen=True)
class EvaluatorIndependenceVerdict:
    claim: str
    judge_demoted_to_advisor: str
    deterministic_gate_unoverridable: str
    frozen_holdout_canary: str
    evaluator_improver_separated: str
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_evaluator_independence_honesty(
    claim: str,
    *,
    judge_demoted_to_advisor: str,
    deterministic_gate_unoverridable: str,
    frozen_holdout_canary: str,
    evaluator_improver_separated: str,
) -> EvaluatorIndependenceVerdict:
    """判一个自改进系统的评估器独立性声明是否诚实披露四边界（不承诺真独立）。

    输入须为语义枚举：四维 ∈ {yes, no, partial}

    规则按优先级短路返回（与 gate_prereg.json R0-R6 一致）：
      R0 任一非枚举 → flag
      R1 judge_demoted_to_advisor=no → downgrade（judge 仍是 oracle 终裁）
      R2 deterministic_gate_unoverridable=no → downgrade（门禁可被 judge 覆盖）
      R3 frozen_holdout_canary=no → flag（holdout 未冻结/满分不视为作弊）
      R4 evaluator_improver_separated=no → flag（评估器与改进者未分离）
      R5 任一 partial → flag（覆盖不全，待核）
      R6 全 yes → ok（只判声明自洽，不承诺真独立；100%pass 含 68% 能力折 1）
    """
    vals = (judge_demoted_to_advisor, deterministic_gate_unoverridable,
            frozen_holdout_canary, evaluator_improver_separated)
    if any(v not in _ENUM for v in vals):
        code, msg = _A["invalid_input"]
        return EvaluatorIndependenceVerdict(claim, *(str(v) for v in vals), "flag", code, msg)
    if judge_demoted_to_advisor == "no":
        code, msg = _A["judge_is_oracle"]
        return EvaluatorIndependenceVerdict(claim, *vals, "downgrade", code, msg)
    if deterministic_gate_unoverridable == "no":
        code, msg = _A["gate_overridable"]
        return EvaluatorIndependenceVerdict(claim, *vals, "downgrade", code, msg)
    if frozen_holdout_canary == "no":
        code, msg = _A["holdout_not_frozen"]
        return EvaluatorIndependenceVerdict(claim, *vals, "flag", code, msg)
    if evaluator_improver_separated == "no":
        code, msg = _A["evaluator_not_separated"]
        return EvaluatorIndependenceVerdict(claim, *vals, "flag", code, msg)
    if any(v == "partial" for v in vals):
        code, msg = _A["partial"]
        return EvaluatorIndependenceVerdict(claim, *vals, "flag", code, msg)
    code, msg = _A["ok"]
    return EvaluatorIndependenceVerdict(claim, *vals, "ok", code, msg)


def live_regression() -> dict:
    """7 个活体样例回归——对齐 gate_prereg.json 的 R0-R6 预期。"""
    cases = {
        "judge_is_oracle": dict(judge_demoted_to_advisor="no", deterministic_gate_unoverridable="yes", frozen_holdout_canary="yes", evaluator_improver_separated="yes"),
        "gate_overridable": dict(judge_demoted_to_advisor="yes", deterministic_gate_unoverridable="no", frozen_holdout_canary="yes", evaluator_improver_separated="yes"),
        "holdout_not_frozen": dict(judge_demoted_to_advisor="yes", deterministic_gate_unoverridable="yes", frozen_holdout_canary="no", evaluator_improver_separated="yes"),
        "evaluator_not_separated": dict(judge_demoted_to_advisor="yes", deterministic_gate_unoverridable="yes", frozen_holdout_canary="yes", evaluator_improver_separated="no"),
        "partial_disclosure": dict(judge_demoted_to_advisor="yes", deterministic_gate_unoverridable="yes", frozen_holdout_canary="partial", evaluator_improver_separated="yes"),
        "literal_enum": dict(judge_demoted_to_advisor="maybe", deterministic_gate_unoverridable="yes", frozen_holdout_canary="yes", evaluator_improver_separated="yes"),
        "all_good": dict(judge_demoted_to_advisor="yes", deterministic_gate_unoverridable="yes", frozen_holdout_canary="yes", evaluator_improver_separated="yes"),
    }
    expects = {
        "judge_is_oracle": ("downgrade", "EVALIND.JUDGE_IS_ORACLE"),
        "gate_overridable": ("downgrade", "EVALIND.GATE_OVERRIDABLE"),
        "holdout_not_frozen": ("flag", "EVALIND.HOLDOUT_NOT_FROZEN"),
        "evaluator_not_separated": ("flag", "EVALIND.EVALUATOR_NOT_SEPARATED"),
        "partial_disclosure": ("flag", "EVALIND.PARTIAL"),
        "literal_enum": ("flag", "EVALIND.INVALID_INPUT"),
        "all_good": ("ok", "EVALIND.SELF_CONSISTENT"),
    }
    checks, detail = {}, {}
    for name, inp in cases.items():
        v = check_evaluator_independence_honesty("live:" + name, **inp)
        exp_a, exp_c = expects[name]
        detail[name] = f"{v.action}/{v.code}"
        checks[name] = (v.action == exp_a and v.code == exp_c)
    return {"checks": checks, "cases": detail, "all_passed": all(checks.values())}
