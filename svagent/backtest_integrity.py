"""回测信息污染隔离门禁 — 从 OpenAI Performance Factory 工程博客编译（§57）。

一手来源（audit_openai_perf/article.txt，2026-11-19，source.sha256 锁存）：
  §Evaluate changes to your agents 列出 8 条防 spoiler 纪律：
    - backtest against past incidents，每个 case fresh Codex investigator + original signal
    - stripped of details that might give away the answer
    - 禁 saved memories / incident writeup / results from previous runs
    - inspect its transcript afterward for information that might have spoiled the test
    - score timing 与 blame deployment 分开（"an agent can get the timing right and still blame the wrong deployment"）

本仓缺口（engine.py P4 真实核验）：evaluation_reliability.py 判 judge 独立性/复现完整性/
评估可扩展性，但不判『回测样本是否被答案泄露污染』。本模块补此缺口。

扬长避短（KB-META01）：
  - 借 8 条一手工程纪律；不借其内部自报数字当验证、不宣称复现其内部系统。
  - 语义布尔输入 + 写死规则 + 纯函数，不做字面串匹配（避开 §56 的 brittle 根因）。
  - 锚定 KB-RSI06 / KB-AUDIT04 / KB-AUDIT02 并在 support 加固指针（认知域协同）。
  - 同构打折（KB-STRUCT02）：门禁由 OpenAI 博客启发，不给本仓框架独立背书。

诚实边界：只判『隔离状态』，不判回测结论对错；隔离项状态须调用方如实声明，
是否泄露的声明本身不可自证；活体样例用于机制回归，非复现 OpenAI 内部回测。
"""
from __future__ import annotations

from dataclasses import dataclass

# 8 条隔离项（与预注册一一对应）
ISOLATION_KEYS = (
    "fresh_investigator", "original_signal", "stripped_giveaway",
    "no_saved_memories", "no_incident_writeup", "no_previous_runs",
    "inspect_transcript", "separate_timing_deployment",
)
# 关键隔离项：缺任一即 block
CRITICAL_KEYS = {"fresh_investigator", "stripped_giveaway", "no_incident_writeup"}
# 弱隔离项：缺任一 → downgrade
WEAK_KEYS = {"no_saved_memories", "no_previous_runs", "inspect_transcript", "separate_timing_deployment"}
_TRUE, _FALSE = "yes", "no"  # 状态字面；以下判定只比较集合成员，不读文本


@dataclass(frozen=True)
class BacktestVerdict:
    action: str        # ok | downgrade | flag | block
    code: str
    missing_critical: tuple
    missing_weak: tuple
    spoiler_found: bool
    undeclared: tuple
    message: str


def check_backtest_integrity(
    *,
    fresh_investigator: str,
    original_signal: str,
    stripped_giveaway: str,
    no_saved_memories: str,
    no_incident_writeup: str,
    no_previous_runs: str,
    inspect_transcript: str,
    separate_timing_deployment: str,
    spoiler_found: bool = False,
) -> BacktestVerdict:
    """按 8 条隔离项判定一次回测的信息污染风险。

    每项 ∈ {"yes","no","unknown"}（语义状态，非自由文本）：
      yes=已隔离，no=未隔离，unknown=未声明。

    规则（按优先级写死，不事后加权）：
      G3 inspect_transcript=yes 且 spoiler_found=True → block（事后确认泄露）
      G1 关键项(no) → block（回测被污染）
      G5 任一项 unknown → flag（可见信息范围未声明，不可判定）
      G2 弱隔离项(no) → downgrade（有污染风险，打折）
      G4 八项齐全且无 spoiler → ok
    """
    states = {
        "fresh_investigator": fresh_investigator,
        "original_signal": original_signal,
        "stripped_giveaway": stripped_giveaway,
        "no_saved_memories": no_saved_memories,
        "no_incident_writeup": no_incident_writeup,
        "no_previous_runs": no_previous_runs,
        "inspect_transcript": inspect_transcript,
        "separate_timing_deployment": separate_timing_deployment,
    }
    # 状态校验：非法状态一律当未声明处理（不读文本，只认集合成员）
    valid = {_TRUE, _FALSE, "unknown"}
    undeclared = tuple(k for k, v in states.items() if v not in valid or v == "unknown")
    missing = tuple(k for k, v in states.items() if v == _FALSE)
    missing_critical = tuple(k for k in missing if k in CRITICAL_KEYS)
    missing_weak = tuple(k for k in missing if k in WEAK_KEYS)
    has_transcript = inspect_transcript == _TRUE

    if has_transcript and spoiler_found:
        return BacktestVerdict("block", "BACKTEST.SPOILER_FOUND", missing_critical, missing_weak,
                               True, undeclared, "事后 transcript 审查确认答案泄露——回测无效（KB-AUDIT02）")
    if missing_critical:
        return BacktestVerdict("block", "BACKTEST.GIVEWAY", missing_critical, missing_weak,
                               spoiler_found, undeclared,
                               "关键隔离项缺失：" + ",".join(missing_critical) + "——回测被污染，结论不可信")
    if undeclared:
        return BacktestVerdict("flag", "BACKTEST.UNDECLARED", missing_critical, missing_weak,
                               spoiler_found, undeclared,
                               "可见信息范围未声明：" + ",".join(undeclared) + "——默认降级，不可判定")
    if missing_weak:
        return BacktestVerdict("downgrade", "BACKTEST.PARTIAL_ISOLATION", missing_critical, missing_weak,
                               spoiler_found, undeclared,
                               "弱隔离项缺失：" + ",".join(missing_weak) + "——有污染风险，结论打折")
    return BacktestVerdict("ok", "BACKTEST.CLEAN", (), (), False, (),
                           "八项隔离齐全且无 spoiler——回测有效（仍不替代实质证据）")


def live_regression() -> dict:
    """活体回归：正版/泄露/弱缺失/事后查获spoiler/未声明 五场景。"""
    base = dict(
        fresh_investigator="yes", original_signal="yes", stripped_giveaway="yes",
        no_saved_memories="yes", no_incident_writeup="yes", no_previous_runs="yes",
        inspect_transcript="yes", separate_timing_deployment="yes",
    )
    clean = check_backtest_integrity(**base)
    leak = check_backtest_integrity(**{**base, "no_incident_writeup": "no"})
    weak = check_backtest_integrity(**{**base, "no_saved_memories": "no"})
    spoil = check_backtest_integrity(**{**base, "spoiler_found": True})
    undec = check_backtest_integrity(**{**base, "stripped_giveaway": "unknown"})
    checks = {
        "clean_ok": clean.action == "ok" and clean.code == "BACKTEST.CLEAN",
        "leak_blocked": leak.action == "block" and leak.code == "BACKTEST.GIVEWAY",
        "weak_downgraded": weak.action == "downgrade" and weak.code == "BACKTEST.PARTIAL_ISOLATION",
        "spoiler_blocked": spoil.action == "block" and spoil.code == "BACKTEST.SPOILER_FOUND",
        "undeclared_flagged": undec.action == "flag" and undec.code == "BACKTEST.UNDECLARED",
    }
    return {
        "clean": {"action": clean.action, "code": clean.code},
        "leak": {"action": leak.action, "code": leak.code},
        "weak": {"action": weak.action, "code": weak.code},
        "spoiler": {"action": spoil.action, "code": spoil.code},
        "undeclared": {"action": undec.action, "code": undec.code},
        "checks": checks,
        "all_passed": all(checks.values()),
    }
