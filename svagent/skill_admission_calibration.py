"""技能准入校准门禁 — 把 EvoSteer 的"序贯检验 + 退役"原则编译成会判动作（§82）。

一手证据（见 audit_evosteer/，arXiv:2609.38661v2 HTML 全文，SHA256 942ac20f…）：
  - §4.3 Validated Skill Admission：
    "Validated Skill Admission lets a candidate be tried before it is promoted, and
    promotes or retires it only when paired evidence passes a sequential test under
    a shared alpha-spending budget."
    "two extra trajectories are launched from the same record and the same forced
    first role, one binding and one not, and both are continued by the reference policy"
    "A candidate whose ... clears its boundary is promoted to validated, one whose
    ... clears it is retired, and otherwise it keeps accumulating."
  - §1 (iii) Uncalibrated skill admission：
    "such point estimates cannot separate insufficient evidence from a confirmed
    effect ... and since no test tracks whether an admitted skill still helps on
    later tasks, it stays in the library and is never retired."
  - §1 贡献段：
    "paired rollouts differing only in the candidate are judged by a sequential sign
    test under a shared nominal testing budget, which promotes, retires, or defers."
  - §4.3 FWER：
    "the budget is spent only when new evidence arrives, so the total nominal level
    is at most ... By a union bound, family-wise error is at most ... whenever each
    directional p-value is valid for the selection and sampling rules in use, even
    for dependent tests."

为什么是新牙（对比现有门禁）：
  scoring_integrity 判计分是否被绕过（可写+被改+分数升→作废），非技能晋升校准；
  memory_curation(§68) 判记忆内容质量治理，非技能晋升/退役；
  criterion_origin_honesty(§77) 判评估判据来自自生成还是外部锚定，非准入序贯检验；
  component_attribution 把 Skill 当作失败归因的一个组件，不判技能准入是否校准。
  无一判"一个声称技能库可自演化的系统是否先试用、用配对反事实、共享预算序贯检验、
  且有退役/延迟机制"。尺子可迁移、会拦，KB-META01 通过。

编译纪律（gate_prereg.json SHA256 a7ad398d…，实现前已锁存）：
  语义枚举；字面串→flag(R0)；R1-R4 按优先级 downgrade；R5 partial→flag；R6 全 yes→ok；
  只判机制声明是否诚实自洽，不承诺序贯检验真控制 FWER（存在≠有效性 KB-META01/AUDIT03）；
  论文 self-reported 结果按 KB-RSI07 折1。

诚实边界：定位为审读外部"技能库自演化系统"的尺子，不判本仓；遵循 §58 选 A 不接 run_loop。
"""
from __future__ import annotations

from dataclasses import dataclass

_ENUM = frozenset({"yes", "no", "partial"})

# 中文锚点集中管理：避免 AST 自审误伤 Compare 内的中文字面量
_A = {
    "invalid": "四维须为 yes/no/partial 语义枚举；非法值（含字面串）→ flag，不进内容判定",
    "untried": "候选技能未经试用即凭 LLM judge/单次成功数晋升（admitted by LLM judgement or by counting successes）→ §1(iii)，判定打折",
    "no_paired": "无配对反事实对照，点估计无法区分证据不足与确认效果（cannot separate insufficient evidence from a confirmed effect）→ §4.3 paired rollouts 缺失，判定打折",
    "uncalibrated": "无共享名义预算的序贯检验，把成功计数当可靠信念（point estimates treated as reliable belief）→ §4.3 sequential sign test/alpha-spending 缺失，判定打折",
    "no_retire": "无退役/延迟机制，准入后永不复核是否仍有助（stays in the library and is never retired）→ §1(iii) 退役缺失，判定打折",
    "partial": "技能准入校准声明覆盖不全（partial）——拦截面存在但缺口未补齐，待核",
    "ok": "四维技能准入校准声明自洽——只判声明诚实存在，不承诺序贯检验真控制 FWER（存在≠有效性）",
}


@dataclass(frozen=True)
class SkillAdmissionVerdict:
    claim: str
    tried_before_promotion: str
    paired_counterfactual: str
    sequential_budget: str
    retire_mechanism: str
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_skill_admission_calibration(
    claim: str,
    *,
    tried_before_promotion: str,
    paired_counterfactual: str,
    sequential_budget: str,
    retire_mechanism: str,
) -> SkillAdmissionVerdict:
    """判一个声称技能库可自演化的系统是否诚实校准技能准入。

    输入须为语义枚举：四维 ∈ {yes, no, partial}

    规则按优先级短路返回（与 gate_prereg.json R0-R6 一致）：
      R0 任一非枚举 → flag
      R1 tried_before_promotion=no → downgrade（未经试用即晋升）
      R2 paired_counterfactual=no → downgrade（无配对反事实）
      R3 sequential_budget=no → downgrade（无共享预算序贯检验）
      R4 retire_mechanism=no → downgrade（无退役机制）
      R5 任一 partial → flag
      R6 全 yes → ok（只判机制声明自洽）
    """
    vals = (tried_before_promotion, paired_counterfactual, sequential_budget, retire_mechanism)
    if any(v not in _ENUM for v in vals):
        return SkillAdmissionVerdict(
            claim, *(str(v) for v in vals),
            "flag", "SKILL_ADMISSION.INVALID_INPUT", _A["invalid"],
        )
    if tried_before_promotion == "no":
        return SkillAdmissionVerdict(
            claim, *vals, "downgrade", "SKILL_ADMISSION.UNTRIED_PROMOTION", _A["untried"],
        )
    if paired_counterfactual == "no":
        return SkillAdmissionVerdict(
            claim, *vals, "downgrade", "SKILL_ADMISSION.NO_PAIRED_EVIDENCE", _A["no_paired"],
        )
    if sequential_budget == "no":
        return SkillAdmissionVerdict(
            claim, *vals, "downgrade", "SKILL_ADMISSION.UNCALIBRATED_TEST", _A["uncalibrated"],
        )
    if retire_mechanism == "no":
        return SkillAdmissionVerdict(
            claim, *vals, "downgrade", "SKILL_ADMISSION.NO_RETIRE", _A["no_retire"],
        )
    if any(v == "partial" for v in vals):
        return SkillAdmissionVerdict(
            claim, *vals, "flag", "SKILL_ADMISSION.PARTIAL", _A["partial"],
        )
    return SkillAdmissionVerdict(
        claim, *vals, "ok", "SKILL_ADMISSION.SELF_CONSISTENT", _A["ok"],
    )


def live_regression() -> dict:
    """7 个活体样例回归——对齐 gate_prereg.json R0-R6 预期。"""
    cases = {
        "untried_promotion": dict(tried_before_promotion="no", paired_counterfactual="yes", sequential_budget="yes", retire_mechanism="yes"),
        "no_paired": dict(tried_before_promotion="yes", paired_counterfactual="no", sequential_budget="yes", retire_mechanism="yes"),
        "uncalibrated": dict(tried_before_promotion="yes", paired_counterfactual="yes", sequential_budget="no", retire_mechanism="yes"),
        "no_retire": dict(tried_before_promotion="yes", paired_counterfactual="yes", sequential_budget="yes", retire_mechanism="no"),
        "partial_disclosure": dict(tried_before_promotion="yes", paired_counterfactual="yes", sequential_budget="partial", retire_mechanism="yes"),
        "literal_enum": dict(tried_before_promotion="yes", paired_counterfactual="maybe", sequential_budget="yes", retire_mechanism="yes"),
        "all_good": dict(tried_before_promotion="yes", paired_counterfactual="yes", sequential_budget="yes", retire_mechanism="yes"),
    }
    expects = {
        "untried_promotion": ("downgrade", "SKILL_ADMISSION.UNTRIED_PROMOTION"),
        "no_paired": ("downgrade", "SKILL_ADMISSION.NO_PAIRED_EVIDENCE"),
        "uncalibrated": ("downgrade", "SKILL_ADMISSION.UNCALIBRATED_TEST"),
        "no_retire": ("downgrade", "SKILL_ADMISSION.NO_RETIRE"),
        "partial_disclosure": ("flag", "SKILL_ADMISSION.PARTIAL"),
        "literal_enum": ("flag", "SKILL_ADMISSION.INVALID_INPUT"),
        "all_good": ("ok", "SKILL_ADMISSION.SELF_CONSISTENT"),
    }
    checks, detail = {}, {}
    for name, inp in cases.items():
        v = check_skill_admission_calibration("live:" + name, **inp)
        exp_a, exp_c = expects[name]
        detail[name] = f"{v.action}/{v.code}"
        checks[name] = (v.action == exp_a and v.code == exp_c)
    return {"checks": checks, "cases": detail, "all_passed": all(checks.values())}
