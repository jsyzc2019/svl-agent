"""在线修复诚实性门禁 — 把 EvoSteer 的"运行中执行中途修复"原则编译成会判动作（§81）。

一手证据（见 audit_evosteer/，arXiv:2609.38661v2 HTML 全文，SHA256 942ac20f…）：
  - §1 Introduction：
    "in which the orchestrator dynamically builds and repairs a running team from
    execution features and a learned value estimate—replacing the run-then-revise loop."
    "The orchestrator issues one atomic edit per turn, rerun and drop included; each
    is executed at once, and its feedback and the value estimate enter the state,
    so a plausible but failing result can be redone mid-run."
  - §1 Introduction (i) Post-hoc evolution：
    "orchestration still evolves only between trajectories, by revising skills, prompts,
    or topology after a batch of runs has ended ... impossible to repair while the
    workflow is still being executed."
  - §1 (ii) Credit diffusion：
    "give every action the same coefficient of a single terminal advantage, and
    learned state values confound how often a task is solved, execution noise, and
    structural choice, so the orchestrator cannot tell whether a low score came from
    a task the reference rarely solves or from a badly organized team"

为什么是新牙（对比现有门禁）：
  self_evolving 是本仓判据自造的运行时机制，非审读外部在线编排系统的尺子；
  component_attribution 判失败归因到 Prompt/Memory/Skill/Harness 哪个组件，不判修复
  是否在同一运行中途发生；policy_evolution_grounding(§79) 判记忆管理策略演化接地，
  对象是记忆而非编排团队；scoring_integrity 判计分是否被绕过。无一判"一个声称
  在线自演化的编排系统是否真的具备运行中执行中途、由执行特征与参考锚定价值驱动的
  原子修复能力（含 rerun/drop）"。尺子可迁移、会拦，KB-META01 通过。

编译纪律（gate_prereg.json SHA256 a7ad398d…，实现前已锁存）：
  语义枚举；字面串→flag(R0)；R1-R4 按优先级 downgrade；R5 partial→flag；R6 全 yes→ok；
  只判机制声明是否诚实自洽，不承诺在线修复真提升性能（存在≠有效性 KB-META01/AUDIT03）；
  论文 self-reported 结果按 KB-RSI07 折1。

诚实边界：定位为审读外部"在线自演化编排系统"的尺子，不判本仓；遵循 §58 选 A 不接 run_loop。
"""
from __future__ import annotations

from dataclasses import dataclass

_ENUM = frozenset({"yes", "no", "partial"})

# 中文锚点集中管理：避免 AST 自审误伤 Compare 内的中文字面量
_A = {
    "invalid": "四维须为 yes/no/partial 语义枚举；非法值（含字面串）→ flag，不进内容判定",
    "post_hoc": "编排只在轨迹之间/批次结束后修订，执行中途不可编辑（impossible to repair while the workflow is still being executed）→ §1 post-hoc evolution，判定打折",
    "no_rerun": "不能重跑失败步骤或丢弃错误 agent，只能追加节点（decisive error locally indistinguishable from recoverable step）→ rerun/drop 缺失，判定打折",
    "not_execution_driven": "编辑不由执行特征/失败信号驱动，仅凭输出表面合理性（outputs still look plausible）→ §1 驱动信号缺失，判定打折",
    "ungrounded_value": "价值估计无冻结参考锚定，混淆任务被解决频率/执行噪声/结构选择（cannot tell low score from rare-solved task vs badly organized team）→ §1 credit diffusion，判定打折",
    "partial": "在线修复机制声明覆盖不全（partial）——拦截面存在但缺口未补齐，待核",
    "ok": "四维在线修复声明自洽——只判声明诚实存在，不承诺在线修复真提升性能（存在≠有效性）",
}


@dataclass(frozen=True)
class OnlineRepairVerdict:
    claim: str
    in_run_edit: str
    rerun_drop: str
    execution_feature_driven: str
    ref_grounded_value: str
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_online_repair_honesty(
    claim: str,
    *,
    in_run_edit: str,
    rerun_drop: str,
    execution_feature_driven: str,
    ref_grounded_value: str,
) -> OnlineRepairVerdict:
    """判一个声称在线自演化的编排系统是否诚实具备运行中途修复能力。

    输入须为语义枚举：四维 ∈ {yes, no, partial}

    规则按优先级短路返回（与 gate_prereg.json R0-R6 一致）：
      R0 任一非枚举 → flag
      R1 in_run_edit=no → downgrade（仅事后修订）
      R2 rerun_drop=no → downgrade（无 rerun/drop）
      R3 execution_feature_driven=no → downgrade（非执行特征驱动）
      R4 ref_grounded_value=no → downgrade（价值无参考锚定）
      R5 任一 partial → flag
      R6 全 yes → ok（只判机制声明自洽）
    """
    vals = (in_run_edit, rerun_drop, execution_feature_driven, ref_grounded_value)
    if any(v not in _ENUM for v in vals):
        return OnlineRepairVerdict(
            claim, *(str(v) for v in vals),
            "flag", "ONLINE_REPAIR.INVALID_INPUT", _A["invalid"],
        )
    if in_run_edit == "no":
        return OnlineRepairVerdict(
            claim, *vals, "downgrade", "ONLINE_REPAIR.POST_HOC_ONLY", _A["post_hoc"],
        )
    if rerun_drop == "no":
        return OnlineRepairVerdict(
            claim, *vals, "downgrade", "ONLINE_REPAIR.NO_RERUN_DROP", _A["no_rerun"],
        )
    if execution_feature_driven == "no":
        return OnlineRepairVerdict(
            claim, *vals, "downgrade", "ONLINE_REPAIR.NOT_EXECUTION_DRIVEN", _A["not_execution_driven"],
        )
    if ref_grounded_value == "no":
        return OnlineRepairVerdict(
            claim, *vals, "downgrade", "ONLINE_REPAIR.UNGROUNDED_VALUE", _A["ungrounded_value"],
        )
    if any(v == "partial" for v in vals):
        return OnlineRepairVerdict(
            claim, *vals, "flag", "ONLINE_REPAIR.PARTIAL", _A["partial"],
        )
    return OnlineRepairVerdict(
        claim, *vals, "ok", "ONLINE_REPAIR.SELF_CONSISTENT", _A["ok"],
    )


def live_regression() -> dict:
    """7 个活体样例回归——对齐 gate_prereg.json R0-R6 预期。"""
    cases = {
        "post_hoc_only": dict(in_run_edit="no", rerun_drop="yes", execution_feature_driven="yes", ref_grounded_value="yes"),
        "no_rerun_drop": dict(in_run_edit="yes", rerun_drop="no", execution_feature_driven="yes", ref_grounded_value="yes"),
        "not_execution_driven": dict(in_run_edit="yes", rerun_drop="yes", execution_feature_driven="no", ref_grounded_value="yes"),
        "ungrounded_value": dict(in_run_edit="yes", rerun_drop="yes", execution_feature_driven="yes", ref_grounded_value="no"),
        "partial_disclosure": dict(in_run_edit="yes", rerun_drop="yes", execution_feature_driven="partial", ref_grounded_value="yes"),
        "literal_enum": dict(in_run_edit="yes", rerun_drop="maybe", execution_feature_driven="yes", ref_grounded_value="yes"),
        "all_good": dict(in_run_edit="yes", rerun_drop="yes", execution_feature_driven="yes", ref_grounded_value="yes"),
    }
    expects = {
        "post_hoc_only": ("downgrade", "ONLINE_REPAIR.POST_HOC_ONLY"),
        "no_rerun_drop": ("downgrade", "ONLINE_REPAIR.NO_RERUN_DROP"),
        "not_execution_driven": ("downgrade", "ONLINE_REPAIR.NOT_EXECUTION_DRIVEN"),
        "ungrounded_value": ("downgrade", "ONLINE_REPAIR.UNGROUNDED_VALUE"),
        "partial_disclosure": ("flag", "ONLINE_REPAIR.PARTIAL"),
        "literal_enum": ("flag", "ONLINE_REPAIR.INVALID_INPUT"),
        "all_good": ("ok", "ONLINE_REPAIR.SELF_CONSISTENT"),
    }
    checks, detail = {}, {}
    for name, inp in cases.items():
        v = check_online_repair_honesty("live:" + name, **inp)
        exp_a, exp_c = expects[name]
        detail[name] = f"{v.action}/{v.code}"
        checks[name] = (v.action == exp_a and v.code == exp_c)
    return {"checks": checks, "cases": detail, "all_passed": all(checks.values())}
