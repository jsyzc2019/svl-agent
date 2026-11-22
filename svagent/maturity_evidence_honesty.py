"""成熟度证据诚实性门禁 — 把 arXiv:2610.38266 的 L0-L3 rubric 编译成会拦的动作（§97）。

一手证据（见 audit_l3_evidence_rubric/）：
  - S01 abs + S02 全文（arXiv:2610.38266v1，Physical AI RSI survey）+ S03 TRUST abs（2611.10787）。
  - 核心 rubric：task-local adaptation(L0) / persistent capability gain(L1) /
    inherited process revision(L2) / verified improver gain(L3)。
    L3 requires greater subsequent gains from shared learner starts under
    matched resource budgets and independent tests.

本轮由来（用户"期待L3"）：
  - 不宣布达标，而把 L3 门槛编译成尺子并首次对准本仓自审。
  - 回溯 KB-SIM03：Task→Retained→Improver gain，无受控实验不认 L3。
  - §91 rsi_claim_audit_honesty 已审"外部 RSI 声称四评估边界"——本门禁不重复，
    而是审"任一系统（含本仓）宣称的成熟度等级 Lx 是否诚实披露四证据边界"。

编译纪律（与 gate_prereg.json 一致，实现前 SHA256 锁存 d0e24033…）：
  - 语义枚举；字面串→flag(R0)；R0-R6 短路返回，不事后加权(防 Goodhart)；
  - 只判"成熟度声明是否诚实可追溯"，不承诺等级真实(KB-R07/META01)；
    self-reported 折 1；预承诺：若受控验证不达标则诚实判未达 L3。

诚实边界：本门禁可审任意系统（含本仓）的等级声明；遵循 §58 选 A 不接 run_loop。
"""
from __future__ import annotations

from dataclasses import dataclass

_ENUM = frozenset({"yes", "no", "partial"})

# 中文文案字典：Compare 内不放中文字面量（AST 自审纪律）
_A = {
    "invalid_input": (
        "MATURITY.INVALID_INPUT",
        "四维须为 yes/no/partial 语义枚举；非法值（含字面串）→ flag，不进内容判定",
    ),
    "level_untraced": (
        "MATURITY.LEVEL_UNTRACED",
        "声称 Lx 无绑定 L0-L3 可追溯等级定义（task-local/persistent/inherited process/verified improver）——自封等级",
    ),
    "process_product_conflation": (
        "MATURITY.PROCESS_PRODUCT_CONFLATION",
        "把产品能力(product capability)变好当改进过程(process revision)变强——声明层级混淆",
    ),
    "shared_start_uncontrolled": (
        "MATURITY.SHARED_START_UNCONTROLLED",
        "L3 声称无 shared learner starts + matched resource budgets 受控验证——拿更强初始/更多预算冒充 improver gain",
    ),
    "tests_not_independent": (
        "MATURITY.TESTS_NOT_INDEPENDENT",
        "仅单一评估器自证、无 common-data / independent tests——等级证据不可复现",
    ),
    "partial": (
        "MATURITY.PARTIAL",
        "成熟度证据边界披露覆盖不全(partial)——拦截面存在但缺口未补齐，待核",
    ),
    "ok": (
        "MATURITY.SELF_CONSISTENT",
        "四维成熟度声明自洽——只判声明诚实可追溯，不承诺等级真实；self-reported 折 1",
    ),
}


@dataclass(frozen=True)
class MaturityEvidenceVerdict:
    claim: str
    level_definition_traced: str
    process_product_split: str
    shared_start_controlled: str
    independent_tests: str
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_maturity_evidence_honesty(
    claim: str,
    *,
    level_definition_traced: str,
    process_product_split: str,
    shared_start_controlled: str,
    independent_tests: str,
) -> MaturityEvidenceVerdict:
    """判一个系统的成熟度等级声明是否诚实披露四证据边界（不承诺等级真实）。

    输入须为语义枚举：四维 ∈ {yes, no, partial}

    规则按优先级短路返回（与 gate_prereg.json R0-R6 一致）：
      R0 任一非枚举 → flag
      R1 level_definition_traced=no → downgrade（等级无定义/自封）
      R2 process_product_split=no → downgrade（product 当 process）
      R3 shared_start_controlled=no → flag（L3 无相同起点受控验证）
      R4 independent_tests=no → flag（无独立测试）
      R5 任一 partial → flag（覆盖不全，待核）
      R6 全 yes → ok（只判声明自洽，self-reported 折 1）
    """
    vals = (level_definition_traced, process_product_split,
            shared_start_controlled, independent_tests)
    if any(v not in _ENUM for v in vals):
        code, msg = _A["invalid_input"]
        return MaturityEvidenceVerdict(claim, *(str(v) for v in vals), "flag", code, msg)
    if level_definition_traced == "no":
        code, msg = _A["level_untraced"]
        return MaturityEvidenceVerdict(claim, *vals, "downgrade", code, msg)
    if process_product_split == "no":
        code, msg = _A["process_product_conflation"]
        return MaturityEvidenceVerdict(claim, *vals, "downgrade", code, msg)
    if shared_start_controlled == "no":
        code, msg = _A["shared_start_uncontrolled"]
        return MaturityEvidenceVerdict(claim, *vals, "flag", code, msg)
    if independent_tests == "no":
        code, msg = _A["tests_not_independent"]
        return MaturityEvidenceVerdict(claim, *vals, "flag", code, msg)
    if any(v == "partial" for v in vals):
        code, msg = _A["partial"]
        return MaturityEvidenceVerdict(claim, *vals, "flag", code, msg)
    code, msg = _A["ok"]
    return MaturityEvidenceVerdict(claim, *vals, "ok", code, msg)


def live_regression() -> dict:
    """7 个活体样例回归——对齐 gate_prereg.json 的 R0-R6 预期。"""
    cases = {
        "level_untraced": dict(level_definition_traced="no", process_product_split="yes", shared_start_controlled="yes", independent_tests="yes"),
        "process_product_conflation": dict(level_definition_traced="yes", process_product_split="no", shared_start_controlled="yes", independent_tests="yes"),
        "shared_start_uncontrolled": dict(level_definition_traced="yes", process_product_split="yes", shared_start_controlled="no", independent_tests="yes"),
        "tests_not_independent": dict(level_definition_traced="yes", process_product_split="yes", shared_start_controlled="yes", independent_tests="no"),
        "partial_disclosure": dict(level_definition_traced="yes", process_product_split="yes", shared_start_controlled="partial", independent_tests="yes"),
        "literal_enum": dict(level_definition_traced="maybe", process_product_split="yes", shared_start_controlled="yes", independent_tests="yes"),
        "all_good": dict(level_definition_traced="yes", process_product_split="yes", shared_start_controlled="yes", independent_tests="yes"),
    }
    expects = {
        "level_untraced": ("downgrade", "MATURITY.LEVEL_UNTRACED"),
        "process_product_conflation": ("downgrade", "MATURITY.PROCESS_PRODUCT_CONFLATION"),
        "shared_start_uncontrolled": ("flag", "MATURITY.SHARED_START_UNCONTROLLED"),
        "tests_not_independent": ("flag", "MATURITY.TESTS_NOT_INDEPENDENT"),
        "partial_disclosure": ("flag", "MATURITY.PARTIAL"),
        "literal_enum": ("flag", "MATURITY.INVALID_INPUT"),
        "all_good": ("ok", "MATURITY.SELF_CONSISTENT"),
    }
    checks, detail = {}, {}
    for name, inp in cases.items():
        v = check_maturity_evidence_honesty("live:" + name, **inp)
        exp_a, exp_c = expects[name]
        detail[name] = f"{v.action}/{v.code}"
        checks[name] = (v.action == exp_a and v.code == exp_c)
    return {"checks": checks, "cases": detail, "all_passed": all(checks.values())}
