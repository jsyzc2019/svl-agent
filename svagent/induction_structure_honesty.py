"""归纳泛化结构诚实性门禁 — 把 Latent Taxonomies 的"记忆≠压缩成可归纳结构"编译成会判动作（§87）。

一手证据（见 audit_latent_taxonomies/，arXiv:2610.15836v1 HTML 全文，SHA256 81ec5da0…）：
  - Abstract：
    "taxonomically aligned induction emerges from next-token prediction alone: a property
    learned for one entity transfers more strongly within its taxonomic category than across categories"
    "clustering recovers the full taxonomic tree from entity representations"
    "induction weakens with model size when the data budget is fixed, suggesting that larger
    models memorize individual facts rather than compress them into shared structure"
  - §3.2：
    "Can the entire tree, including its branching structure, be fully reconstructed from the
    representations? Using a standard clustering technique, we find that it can."
  - §3.3：
    "At a fixed data budget, scale hurts." / "the induction advantage decreases with model size"

为什么是新牙（对比现有门禁）：
  transfer_holdout 判样本外迁移增益/过拟合（评测方法层），不判模型内部是否把事实压缩成
  可归纳共享结构；memory_provenance_honesty(§80) 判记忆证据回链/可恢复表示，非归纳泛化的
  记忆vs压缩区分与结构从表示可恢复；memory_scope(§70) 判记忆作用域。
  无一判"归纳优势证据/结构可恢复/记忆vs压缩/规模效应诚实"。尺子可迁移、会拦，KB-META01 通过。

编译纪律（gate_prereg.json SHA256 0eaa6e8a…，实现前已锁存）：
  语义枚举；字面串→flag(R0)；R1-R4 按优先级 downgrade；R5 partial→flag；R6 全 yes→ok；
  只判机制声明是否诚实自洽，不承诺结构真被恢复（存在≠有效性 KB-META01/AUDIT03）；
  self-reported 合成实验按 KB-RSI07 折1；scale 结论 scoped。

诚实边界：定位为审读外部"结构化泛化系统"的尺子，不判本仓；遵循 §58 选 A 不接 run_loop。
"""
from __future__ import annotations

from dataclasses import dataclass

_ENUM = frozenset({"yes", "no", "partial"})

_A = {
    "invalid": "四维须为 yes/no/partial 语义枚举；非法值（含字面串）→ flag，不进内容判定",
    "no_advantage": "未展示类别内优于跨类的归纳优势，泛化声明无证据（transfers more strongly within category than across）→ §Abstract，判定打折",
    "structure_opaque": "未从表示恢复内部/结构不可核查（clustering recovers the full tree 缺失）→ §3.2，判定打折",
    "memorize_as_generalize": "未区分记忆个体事实与压缩成共享结构（memorize individual facts rather than compress into shared structure）→ §3.3 scale hurts，判定打折",
    "scale_hidden": "未诚实报告规模效应，默认 bigger-is-better（induction weakens with model size at fixed budget 被隐瞒）→ §3.3，判定打折",
    "partial": "归纳泛化结构诚实性声明覆盖不全（partial）——拦截面存在但缺口未补齐，待核",
    "ok": "四维归纳结构声明自洽——只判声明诚实存在，不承诺结构真被恢复（存在≠有效性）",
}


@dataclass(frozen=True)
class InductionStructureVerdict:
    claim: str
    induction_advantage_shown: str
    structure_recoverable: str
    memorize_vs_compress_split: str
    scale_effect_honest: str
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_induction_structure_honesty(
    claim: str,
    *,
    induction_advantage_shown: str,
    structure_recoverable: str,
    memorize_vs_compress_split: str,
    scale_effect_honest: str,
) -> InductionStructureVerdict:
    """判一个声称学到可泛化结构的系统是否诚实区分记忆与压缩。

    四维均为能力语义：yes=具备。

    规则按优先级短路返回（与 gate_prereg.json R0-R6 一致）：
      R0 任一非枚举 → flag
      R1 induction_advantage_shown=no → downgrade
      R2 structure_recoverable=no → downgrade
      R3 memorize_vs_compress_split=no → downgrade
      R4 scale_effect_honest=no → downgrade
      R5 任一 partial → flag
      R6 全 yes → ok
    """
    vals = (induction_advantage_shown, structure_recoverable,
            memorize_vs_compress_split, scale_effect_honest)
    if any(v not in _ENUM for v in vals):
        return InductionStructureVerdict(
            claim, *(str(v) for v in vals),
            "flag", "INDUCTION_STRUCT.INVALID_INPUT", _A["invalid"],
        )
    if induction_advantage_shown == "no":
        return InductionStructureVerdict(
            claim, *vals, "downgrade", "INDUCTION_STRUCT.NO_ADVANTAGE", _A["no_advantage"],
        )
    if structure_recoverable == "no":
        return InductionStructureVerdict(
            claim, *vals, "downgrade", "INDUCTION_STRUCT.STRUCTURE_OPAQUE", _A["structure_opaque"],
        )
    if memorize_vs_compress_split == "no":
        return InductionStructureVerdict(
            claim, *vals, "downgrade", "INDUCTION_STRUCT.MEMORIZE_AS_GENERALIZE", _A["memorize_as_generalize"],
        )
    if scale_effect_honest == "no":
        return InductionStructureVerdict(
            claim, *vals, "downgrade", "INDUCTION_STRUCT.SCALE_HIDDEN", _A["scale_hidden"],
        )
    if any(v == "partial" for v in vals):
        return InductionStructureVerdict(
            claim, *vals, "flag", "INDUCTION_STRUCT.PARTIAL", _A["partial"],
        )
    return InductionStructureVerdict(
        claim, *vals, "ok", "INDUCTION_STRUCT.SELF_CONSISTENT", _A["ok"],
    )


def live_regression() -> dict:
    """7 个活体样例回归——对齐 gate_prereg.json R0-R6 预期。"""
    def g(**over):
        base = dict(induction_advantage_shown="yes", structure_recoverable="yes",
                    memorize_vs_compress_split="yes", scale_effect_honest="yes")
        base.update(over)
        return base
    cases = {
        "no_advantage": g(induction_advantage_shown="no"),
        "structure_opaque": g(structure_recoverable="no"),
        "memorize_as_generalize": g(memorize_vs_compress_split="no"),
        "scale_hidden": g(scale_effect_honest="no"),
        "partial_disclosure": g(structure_recoverable="partial"),
        "literal_enum": g(induction_advantage_shown="maybe"),
        "all_good": g(),
    }
    expects = {
        "no_advantage": ("downgrade", "INDUCTION_STRUCT.NO_ADVANTAGE"),
        "structure_opaque": ("downgrade", "INDUCTION_STRUCT.STRUCTURE_OPAQUE"),
        "memorize_as_generalize": ("downgrade", "INDUCTION_STRUCT.MEMORIZE_AS_GENERALIZE"),
        "scale_hidden": ("downgrade", "INDUCTION_STRUCT.SCALE_HIDDEN"),
        "partial_disclosure": ("flag", "INDUCTION_STRUCT.PARTIAL"),
        "literal_enum": ("flag", "INDUCTION_STRUCT.INVALID_INPUT"),
        "all_good": ("ok", "INDUCTION_STRUCT.SELF_CONSISTENT"),
    }
    checks, detail = {}, {}
    for name, inp in cases.items():
        v = check_induction_structure_honesty("live:" + name, **inp)
        exp_a, exp_c = expects[name]
        detail[name] = f"{v.action}/{v.code}"
        checks[name] = (v.action == exp_a and v.code == exp_c)
    return {"checks": checks, "cases": detail, "all_passed": all(checks.values())}
