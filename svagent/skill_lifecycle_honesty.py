"""技能演化生命周期诚实性门禁 — 把 arXiv:2610.09832 编译成会拦的动作（自主运维第七轮 §96）。

一手证据（见 audit_skill_lifecycle_honesty/）：
  - S01 abs + S02 全文（arXiv:2610.09832v2 SkillForge，NeurIPS 2026）。
  - 核心命题：retaining every skill indiscriminately lets obsolete or harmful
    entries accumulate and mislead the agent；SkillForge 用 fitness-driven skill
    lifecycle of trial/active/stable/retired states 让技能与模型 co-evolve。

本轮认知增量（与已有的 skill_admission_calibration 区分）：
  - KB-AUDIT25 判"准入统计校准"（试用/配对反事实/共享预算/退役机制）；
  - 本门禁判"演化治理边界是否诚实披露"——论文把本仓关心的四个缺口都做了
    受控自审：credit assignment 用 leave-one-out/K=1 测 Eq(7) 近似误差；
    mutation 用 matched-teacher-budget 对照排除"多花钱"混淆 + teacher 能力消融；
    显著性用单侧 t-test；退役事件用 318 个人工标注失败类别归因。
  - 这是把"虚高指标拆穿 + self-reported 折 1"方法论迁移到技能演化领域。

编译纪律（与 gate_prereg.json 一致，实现前 SHA256 锁存 90082a02…）：
  - 语义枚举；字面串→flag(R0)；R0-R6 短路返回，不事后加权(防 Goodhart)；
  - 只判"演化治理边界声明是否诚实自洽"，不承诺 lifecycle 真实有效(KB-R07/META01)；
    self-reported 7.8% 提升/显著性按 KB-RSI07 折 1。

诚实边界：定位为审读外部 skill-library evolution 系统的尺子，不判本仓；遵循 §58 选 A 不接 run_loop。
"""
from __future__ import annotations

from dataclasses import dataclass

_ENUM = frozenset({"yes", "no", "partial"})

# 中文文案字典：Compare 内不放中文字面量（AST 自审纪律）
_A = {
    "invalid_input": (
        "SKILL_LIFE.INVALID_INPUT",
        "四维须为 yes/no/partial 语义枚举；非法值（含字面串）→ flag，不进内容判定",
    ),
    "stages_undisclosed": (
        "SKILL_LIFE.STAGES_UNDISCLOSED",
        "无 fitness 驱动 trial/active/stable/retired 四态、无 pre-retire 低适配——obsolete/harmful 技能累积 mislead agent",
    ),
    "credit_unaudited": (
        "SKILL_LIFE.CREDIT_UNAUDITED",
        "共享 reward 给 co-retrieved 技能的近似未审、无 leave-one-out 边际或 K=1 压力测——把 credit 近似当精确归因",
    ),
    "teacher_uncontrolled": (
        "SKILL_LIFE.TEACHER_UNCONTROLLED",
        "LLM 变异未做 matched-teacher-budget 对照、无 teacher 能力消融——把 teacher 增益冒充 lifecycle 增益",
    ),
    "retirement_unattributed": (
        "SKILL_LIFE.RETIREMENT_UNATTRIBUTED",
        "退役事件无失败类别归因、只报退役数不解释为何过时——过时原因不可追溯",
    ),
    "partial": (
        "SKILL_LIFE.PARTIAL",
        "演化治理边界披露覆盖不全(partial)——拦截面存在但缺口未补齐，待核",
    ),
    "ok": (
        "SKILL_LIFE.SELF_CONSISTENT",
        "四维演化治理声明自洽——只判声明诚实可审计，不承诺 lifecycle 有效；self-reported 7.8% 折 1",
    ),
}


@dataclass(frozen=True)
class SkillLifecycleVerdict:
    claim: str
    lifecycle_stages_disclosed: str
    credit_assignment_audited: str
    mutation_teacher_controlled: str
    retirement_failure_attributed: str
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_skill_lifecycle_honesty(
    claim: str,
    *,
    lifecycle_stages_disclosed: str,
    credit_assignment_audited: str,
    mutation_teacher_controlled: str,
    retirement_failure_attributed: str,
) -> SkillLifecycleVerdict:
    """判一个技能库自演化研究是否诚实披露四演化治理边界（不承诺 lifecycle 有效）。

    输入须为语义枚举：四维 ∈ {yes, no, partial}

    规则按优先级短路返回（与 gate_prereg.json R0-R6 一致）：
      R0 任一非枚举 → flag
      R1 lifecycle_stages_disclosed=no → downgrade（无四态/无 pre-retire）
      R2 credit_assignment_audited=no → downgrade（信用分配近似未审）
      R3 mutation_teacher_controlled=no → flag（teacher 混淆未控）
      R4 retirement_failure_attributed=no → flag（退役原因不可追溯）
      R5 任一 partial → flag（覆盖不全，待核）
      R6 全 yes → ok（只判声明自洽，self-reported 折 1）
    """
    vals = (lifecycle_stages_disclosed, credit_assignment_audited,
            mutation_teacher_controlled, retirement_failure_attributed)
    if any(v not in _ENUM for v in vals):
        code, msg = _A["invalid_input"]
        return SkillLifecycleVerdict(claim, *(str(v) for v in vals), "flag", code, msg)
    if lifecycle_stages_disclosed == "no":
        code, msg = _A["stages_undisclosed"]
        return SkillLifecycleVerdict(claim, *vals, "downgrade", code, msg)
    if credit_assignment_audited == "no":
        code, msg = _A["credit_unaudited"]
        return SkillLifecycleVerdict(claim, *vals, "downgrade", code, msg)
    if mutation_teacher_controlled == "no":
        code, msg = _A["teacher_uncontrolled"]
        return SkillLifecycleVerdict(claim, *vals, "flag", code, msg)
    if retirement_failure_attributed == "no":
        code, msg = _A["retirement_unattributed"]
        return SkillLifecycleVerdict(claim, *vals, "flag", code, msg)
    if any(v == "partial" for v in vals):
        code, msg = _A["partial"]
        return SkillLifecycleVerdict(claim, *vals, "flag", code, msg)
    code, msg = _A["ok"]
    return SkillLifecycleVerdict(claim, *vals, "ok", code, msg)


def live_regression() -> dict:
    """7 个活体样例回归——对齐 gate_prereg.json 的 R0-R6 预期。"""
    cases = {
        "stages_undisclosed": dict(lifecycle_stages_disclosed="no", credit_assignment_audited="yes", mutation_teacher_controlled="yes", retirement_failure_attributed="yes"),
        "credit_unaudited": dict(lifecycle_stages_disclosed="yes", credit_assignment_audited="no", mutation_teacher_controlled="yes", retirement_failure_attributed="yes"),
        "teacher_uncontrolled": dict(lifecycle_stages_disclosed="yes", credit_assignment_audited="yes", mutation_teacher_controlled="no", retirement_failure_attributed="yes"),
        "retirement_unattributed": dict(lifecycle_stages_disclosed="yes", credit_assignment_audited="yes", mutation_teacher_controlled="yes", retirement_failure_attributed="no"),
        "partial_disclosure": dict(lifecycle_stages_disclosed="yes", credit_assignment_audited="yes", mutation_teacher_controlled="partial", retirement_failure_attributed="yes"),
        "literal_enum": dict(lifecycle_stages_disclosed="maybe", credit_assignment_audited="yes", mutation_teacher_controlled="yes", retirement_failure_attributed="yes"),
        "all_good": dict(lifecycle_stages_disclosed="yes", credit_assignment_audited="yes", mutation_teacher_controlled="yes", retirement_failure_attributed="yes"),
    }
    expects = {
        "stages_undisclosed": ("downgrade", "SKILL_LIFE.STAGES_UNDISCLOSED"),
        "credit_unaudited": ("downgrade", "SKILL_LIFE.CREDIT_UNAUDITED"),
        "teacher_uncontrolled": ("flag", "SKILL_LIFE.TEACHER_UNCONTROLLED"),
        "retirement_unattributed": ("flag", "SKILL_LIFE.RETIREMENT_UNATTRIBUTED"),
        "partial_disclosure": ("flag", "SKILL_LIFE.PARTIAL"),
        "literal_enum": ("flag", "SKILL_LIFE.INVALID_INPUT"),
        "all_good": ("ok", "SKILL_LIFE.SELF_CONSISTENT"),
    }
    checks, detail = {}, {}
    for name, inp in cases.items():
        v = check_skill_lifecycle_honesty("live:" + name, **inp)
        exp_a, exp_c = expects[name]
        detail[name] = f"{v.action}/{v.code}"
        checks[name] = (v.action == exp_a and v.code == exp_c)
    return {"checks": checks, "cases": detail, "all_passed": all(checks.values())}
