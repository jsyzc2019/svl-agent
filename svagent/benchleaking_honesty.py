"""Benchmark 污染诚实性门禁 — 把 arXiv:2611.21315 编译成会拦的动作（自主运维第五轮 §94）。

一手证据（见 audit_benchleaking_honesty/）：
  - S01 abs + S02 全文（arXiv:2611.21315v1，Benchleaking Is Accelerating）。
  - 核心定义：benchleaking = a benchmark's own test examples enter training data,
    so that a score reflects recall rather than capability；与 benchmaxxing（optimizes
    toward a benchmark without seeing its test set）不同。
  - 两种升级：post-training 中 agent 23% attempts 说出未给的隐藏测试要求、任务改后
    仍遵循；pre-training 中 few-shot continuation on 20 benchmarks across four public
    base models，部分模型写出 appear nowhere in their input 的完整测试样例（ERNIE-5.5-
    Flash-Base 96% HumanEval / 85% OpenBookQA 泄漏，对照 DeepSeek 9%/none）。
  - 校正：Anti-Hack score = benchmark score recomputed with every leaked example marked
    wrong and the number of examples unchanged；量化 a reported score owes to such examples
    （5.0 / 16.6 分等）。结论 call for decontamination reports and contamination-adjusted
    scores to become standard practice。

为什么是新牙（对比已有门禁）：
  KB-T03 只讲"基准须与生成过程隔离"、KB-RSI06 只讲"样本外复验"、KB-AUDIT09 是检索
  注入层——都不判"一个 benchmark 分数声称是否诚实披露污染边界"：
    ①是否区分 benchleaking（recall）与 benchmaxxing（capability 优化）；
    ②是否有实证泄漏探针（few-shot continuation）而非泛泛声称 clean；
    ③是否有 Anti-Hack 式泄漏校正（泄漏样本计错、数量不变重算）；
    ④声称范围是否收窄（倡导 decontamination 报告，不外推为成员身份/流行率）。
  尺子对象是"任何 leaderboard/模型发布的 benchmark 分数声称"——可迁移、会拦，KB-META01 会拦才入。

编译纪律（与 gate_prereg.json 一致，实现前 SHA256 锁存 f96fc498…）：
  - 语义枚举；字面串→flag(R0)；R0-R6 短路返回，不事后加权(防 Goodhart)；
  - 只判"边界声明是否诚实自洽"，不承诺模型真实无污染(KB-R07/META01)；
    self-reported 泄漏率(96%/85%)按 KB-RSI07 折 1。

诚实边界：定位为审读外部 benchmark 分数声称的尺子，不判本仓；遵循 §58 选 A 不接 run_loop。
"""
from __future__ import annotations

from dataclasses import dataclass

_ENUM = frozenset({"yes", "no", "partial"})

# 中文文案字典：Compare 内不放中文字面量（AST 自审纪律）
_A = {
    "invalid_input": (
        "BENCHLEAK.INVALID_INPUT",
        "四维须为 yes/no/partial 语义枚举；非法值（含字面串）→ flag，不进内容判定",
    ),
    "recall_as_capability": (
        "BENCHLEAK.RECALL_AS_CAPABILITY",
        "把测试集泄漏的 recall 冒充 capability、不区分 benchleaking 与 benchmaxxing——分数反映记忆而非能力",
    ),
    "probe_undisclosed": (
        "BENCHLEAK.PROBE_UNDISCLOSED",
        "无 few-shot continuation 等实证泄漏探针、泛泛声称 clean 或只报有利数字——污染声称无证据支撑",
    ),
    "score_unadjusted": (
        "BENCHLEAK.SCORE_UNADJUSTED",
        "无 Anti-Hack 式泄漏校正（泄漏样本不计错、数量不重算）——报告分数仍含泄漏增益",
    ),
    "scope_overclaimed": (
        "BENCHLEAK.SCOPE_OVERCLAIMED",
        "把探针结果外推为训练数据成员身份/污染流行率/分数膨胀，或不倡导 decontamination 报告——过度宣称",
    ),
    "partial": (
        "BENCHLEAK.PARTIAL",
        "Benchmark 污染边界披露覆盖不全(partial)——拦截面存在但缺口未补齐，待核",
    ),
    "ok": (
        "BENCHLEAK.SELF_CONSISTENT",
        "四维污染边界声明自洽——只判声明诚实存在，不承诺模型真实无污染(泄漏率 self-reported 折 1)",
    ),
}


@dataclass(frozen=True)
class BenchleakingVerdict:
    claim: str
    benchleaking_vs_maxxing: str
    leakage_probe_disclosed: str
    score_adjusted_for_leak: str
    scope_bounded: str
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_benchleaking_honesty(
    claim: str,
    *,
    benchleaking_vs_maxxing: str,
    leakage_probe_disclosed: str,
    score_adjusted_for_leak: str,
    scope_bounded: str,
) -> BenchleakingVerdict:
    """判一个 benchmark 分数声称是否诚实披露四污染边界（不承诺模型真实无污染）。

    输入须为语义枚举：四维 ∈ {yes, no, partial}

    规则按优先级短路返回（与 gate_prereg.json R0-R6 一致）：
      R0 任一非枚举 → flag
      R1 benchleaking_vs_maxxing=no → downgrade（recall 冒充 capability/不区分两类声称）
      R2 leakage_probe_disclosed=no → downgrade（无实证泄漏探针/泛泛声称 clean）
      R3 score_adjusted_for_leak=no → flag（无泄漏校正/分数仍含增益）
      R4 scope_bounded=no → flag（外推成员身份/不倡导 decontamination）
      R5 任一 partial → flag（覆盖不全，待核）
      R6 全 yes → ok（只判声明自洽，泄漏率折 1）
    """
    vals = (benchleaking_vs_maxxing, leakage_probe_disclosed,
            score_adjusted_for_leak, scope_bounded)
    if any(v not in _ENUM for v in vals):
        code, msg = _A["invalid_input"]
        return BenchleakingVerdict(claim, *(str(v) for v in vals), "flag", code, msg)
    if benchleaking_vs_maxxing == "no":
        code, msg = _A["recall_as_capability"]
        return BenchleakingVerdict(claim, *vals, "downgrade", code, msg)
    if leakage_probe_disclosed == "no":
        code, msg = _A["probe_undisclosed"]
        return BenchleakingVerdict(claim, *vals, "downgrade", code, msg)
    if score_adjusted_for_leak == "no":
        code, msg = _A["score_unadjusted"]
        return BenchleakingVerdict(claim, *vals, "flag", code, msg)
    if scope_bounded == "no":
        code, msg = _A["scope_overclaimed"]
        return BenchleakingVerdict(claim, *vals, "flag", code, msg)
    if any(v == "partial" for v in vals):
        code, msg = _A["partial"]
        return BenchleakingVerdict(claim, *vals, "flag", code, msg)
    code, msg = _A["ok"]
    return BenchleakingVerdict(claim, *vals, "ok", code, msg)


def live_regression() -> dict:
    """7 个活体样例回归——对齐 gate_prereg.json 的 R0-R6 预期。"""
    cases = {
        "recall_as_capability": dict(benchleaking_vs_maxxing="no", leakage_probe_disclosed="yes", score_adjusted_for_leak="yes", scope_bounded="yes"),
        "probe_undisclosed": dict(benchleaking_vs_maxxing="yes", leakage_probe_disclosed="no", score_adjusted_for_leak="yes", scope_bounded="yes"),
        "score_unadjusted": dict(benchleaking_vs_maxxing="yes", leakage_probe_disclosed="yes", score_adjusted_for_leak="no", scope_bounded="yes"),
        "scope_overclaimed": dict(benchleaking_vs_maxxing="yes", leakage_probe_disclosed="yes", score_adjusted_for_leak="yes", scope_bounded="no"),
        "partial_disclosure": dict(benchleaking_vs_maxxing="yes", leakage_probe_disclosed="yes", score_adjusted_for_leak="partial", scope_bounded="yes"),
        "literal_enum": dict(benchleaking_vs_maxxing="maybe", leakage_probe_disclosed="yes", score_adjusted_for_leak="yes", scope_bounded="yes"),
        "all_good": dict(benchleaking_vs_maxxing="yes", leakage_probe_disclosed="yes", score_adjusted_for_leak="yes", scope_bounded="yes"),
    }
    expects = {
        "recall_as_capability": ("downgrade", "BENCHLEAK.RECALL_AS_CAPABILITY"),
        "probe_undisclosed": ("downgrade", "BENCHLEAK.PROBE_UNDISCLOSED"),
        "score_unadjusted": ("flag", "BENCHLEAK.SCORE_UNADJUSTED"),
        "scope_overclaimed": ("flag", "BENCHLEAK.SCOPE_OVERCLAIMED"),
        "partial_disclosure": ("flag", "BENCHLEAK.PARTIAL"),
        "literal_enum": ("flag", "BENCHLEAK.INVALID_INPUT"),
        "all_good": ("ok", "BENCHLEAK.SELF_CONSISTENT"),
    }
    checks, detail = {}, {}
    for name, inp in cases.items():
        v = check_benchleaking_honesty("live:" + name, **inp)
        exp_a, exp_c = expects[name]
        detail[name] = f"{v.action}/{v.code}"
        checks[name] = (v.action == exp_a and v.code == exp_c)
    return {"checks": checks, "cases": detail, "all_passed": all(checks.values())}
