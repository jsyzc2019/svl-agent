"""配置冲突隔离门禁 — 把 UltraBERT 的"多任务相反配置偏好须隔离而非折中"编译成会判动作（§85）。

一手证据（见 audit_ultrabert/，arXiv:2610.15028v1 HTML 全文，SHA256 6c125cae…）：
  - Abstract：
    "no single model performing competitively across both classification and retrieval tasks"
    "lower masking ratios benefit classification while higher ones benefit retrieval,
    contradicting prior work suggesting larger ratios for larger models"
  - §1：
    "classification consistently favors lower masking ratios across model sizes, contradicting
    prior work suggesting larger ratios for larger models, whereas retrieval favors higher ones"
    "At saturation, where convergence speed no longer confounds the comparison"
  - §3.4/§4：
    "reconciles the two masking regimes within a single encoder rather than settling for a
    single configuration"
    "mixes 5% and 50% masked sequences within each batch while assigning a separate LM head
    to each ratio ... restrict distillation to the low-ratio sequences, while training the
    high-ratio ones with standard MLM"

为什么是新牙（对比现有门禁）：
  evaluation_reliability 判评估可复现字段/评审独立性，非配置设计；
  scoring_integrity 判计分是否被绕过，非多任务配置冲突；
  skill_admission_calibration(§82) 判技能准入配对反事实，非超参 regime 隔离。
  无一判"多任务对同一配置有相反偏好时，系统是识别冲突并用机制隔离，还是单一配置/折中蒙混"。
  尺子可迁移、会拦，KB-META01 通过。

编译纪律（gate_prereg.json SHA256 febd1f25…，实现前已锁存）：
  语义枚举；字面串→flag(R0)；R1-R4 按优先级 downgrade；R5 partial→flag；R6 全 yes→ok；
  只判机制声明是否诚实自洽，不承诺隔离真带来 SOTA（存在≠有效性 KB-META01/AUDIT03）；
  self-reported GLUE 91.0/BEIR 47.7 按 KB-RSI07 折1。

诚实边界：定位为审读外部"统一配置/预训练系统"的尺子，不判本仓；遵循 §58 选 A 不接 run_loop。
"""
from __future__ import annotations

from dataclasses import dataclass

_ENUM = frozenset({"yes", "no", "partial"})

# 中文锚点集中管理：避免 AST 自审误伤 Compare 内的中文字面量
_A = {
    "invalid": "四维须为 yes/no/partial 语义枚举；非法值（含字面串）→ flag，不进内容判定",
    "conflict_hidden": "未识别多任务对同一配置的相反偏好（单一最优幻觉）→ §1 掩码比冲突，判定打折",
    "no_isolation": "无隔离机制，用单一配置硬套多任务（settling for a single configuration）→ §3.4，判定打折",
    "confoounded": "比较未在饱和点后做，收敛速度混淆了配置优劣（convergence speed confounds comparison）→ §1 P4，判定打折",
    "blanket": "用一刀切折中掩盖冲突而非隔离（tradeoff 抹平相反偏好）→ §3.4，判定打折",
    "partial": "配置冲突隔离声明覆盖不全（partial）——拦截面存在但缺口未补齐，待核",
    "ok": "四维配置冲突隔离声明自洽——只判声明诚实存在，不承诺隔离真带来 SOTA（存在≠有效性）",
}


@dataclass(frozen=True)
class ConfigConflictVerdict:
    claim: str
    conflict_identified: str
    mechanism_isolation: str
    de_confounded_comparison: str
    no_blanket_tradeoff: str
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_config_conflict_isolation(
    claim: str,
    *,
    conflict_identified: str,
    mechanism_isolation: str,
    de_confounded_comparison: str,
    no_blanket_tradeoff: str,
) -> ConfigConflictVerdict:
    """判一个声称统一配置通吃多任务的系统是否诚实隔离配置冲突。

    四维均为能力语义：yes=具备（no_blanket_tradeoff=yes 表示未用一刀切折中）。

    规则按优先级短路返回（与 gate_prereg.json R0-R6 一致）：
      R0 任一非枚举 → flag
      R1 conflict_identified=no → downgrade（冲突未识别）
      R2 mechanism_isolation=no → downgrade（无隔离机制）
      R3 de_confounded_comparison=no → downgrade（比较被收敛速度混淆）
      R4 no_blanket_tradeoff=no → downgrade（用一刀切折中）
      R5 任一 partial → flag
      R6 全 yes → ok（只判机制声明自洽）
    """
    vals = (conflict_identified, mechanism_isolation,
            de_confounded_comparison, no_blanket_tradeoff)
    if any(v not in _ENUM for v in vals):
        return ConfigConflictVerdict(
            claim, *(str(v) for v in vals),
            "flag", "CONFIG_CONFLICT.INVALID_INPUT", _A["invalid"],
        )
    if conflict_identified == "no":
        return ConfigConflictVerdict(
            claim, *vals, "downgrade", "CONFIG_CONFLICT.CONFLICT_HIDDEN", _A["conflict_hidden"],
        )
    if mechanism_isolation == "no":
        return ConfigConflictVerdict(
            claim, *vals, "downgrade", "CONFIG_CONFLICT.NO_ISOLATION", _A["no_isolation"],
        )
    if de_confounded_comparison == "no":
        return ConfigConflictVerdict(
            claim, *vals, "downgrade", "CONFIG_CONFLICT.CONFOUNDED", _A["confoounded"],
        )
    if no_blanket_tradeoff == "no":
        return ConfigConflictVerdict(
            claim, *vals, "downgrade", "CONFIG_CONFLICT.BLANKET_TRADEOFF", _A["blanket"],
        )
    if any(v == "partial" for v in vals):
        return ConfigConflictVerdict(
            claim, *vals, "flag", "CONFIG_CONFLICT.PARTIAL", _A["partial"],
        )
    return ConfigConflictVerdict(
        claim, *vals, "ok", "CONFIG_CONFLICT.SELF_CONSISTENT", _A["ok"],
    )


def live_regression() -> dict:
    """7 个活体样例回归——对齐 gate_prereg.json R0-R6 预期。"""
    def g(**over):
        base = dict(conflict_identified="yes", mechanism_isolation="yes",
                    de_confounded_comparison="yes", no_blanket_tradeoff="yes")
        base.update(over)
        return base
    cases = {
        "conflict_hidden": g(conflict_identified="no"),
        "no_isolation": g(mechanism_isolation="no"),
        "confoounded": g(de_confounded_comparison="no"),
        "blanket": g(no_blanket_tradeoff="no"),
        "partial_disclosure": g(mechanism_isolation="partial"),
        "literal_enum": g(conflict_identified="maybe"),
        "all_good": g(),
    }
    expects = {
        "conflict_hidden": ("downgrade", "CONFIG_CONFLICT.CONFLICT_HIDDEN"),
        "no_isolation": ("downgrade", "CONFIG_CONFLICT.NO_ISOLATION"),
        "confoounded": ("downgrade", "CONFIG_CONFLICT.CONFOUNDED"),
        "blanket": ("downgrade", "CONFIG_CONFLICT.BLANKET_TRADEOFF"),
        "partial_disclosure": ("flag", "CONFIG_CONFLICT.PARTIAL"),
        "literal_enum": ("flag", "CONFIG_CONFLICT.INVALID_INPUT"),
        "all_good": ("ok", "CONFIG_CONFLICT.SELF_CONSISTENT"),
    }
    checks, detail = {}, {}
    for name, inp in cases.items():
        v = check_config_conflict_isolation("live:" + name, **inp)
        exp_a, exp_c = expects[name]
        detail[name] = f"{v.action}/{v.code}"
        checks[name] = (v.action == exp_a and v.code == exp_c)
    return {"checks": checks, "cases": detail, "all_passed": all(checks.values())}
