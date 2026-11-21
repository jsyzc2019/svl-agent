"""判定稳健性门禁 — 从 SWE-Gym 公开代码的工程纪律编译（认知+代码强固协同首例）。

一手来源（audit_swegym/repo，HEAD 005c2fb；见 audit_swegym/source.sha256）：
  aggregate_stats_pass_at_n.ipynb cell16:
      get_bootstrap_accuracy_std —— 借自 openai/evals，对判定做 bootstrap 重采样求 std，
      论文绘图 PLOT_STD=True，不给裸点估计。
  eval_verifier.ipynb cell5/17:
      calculate_average_scores(..., num_trials=100) —— 每次 shuffle 后重算 pass@k/best@k，
      取 100 次平均±std；结论稳健性来自多次重排，不是单次侥幸。
  curate_dataset.ipynb cell2:
      seed(42) + CAP_PER_INSTANCE=2 —— 固定种子保证可复现，每个实例正负样本各自 cap，
      防少数实例主导数据。
  eval_verifier.ipynb cell1:
      D = {k:v for k,v in D.items() if len(v[True]) > 0} —— 只保留有正例的实例，
      再对每个实例成对取 True/False 构 prompt（正负成对对照）。
  configs/{policy,verifiers}/*:
      25pct/50pct/uniq-data/sort/random、RM-1x/2x/onpolicy/claude+4o+onpolicy —— 受控配比消融。

编译纪律（扬长避短 + KB-META01）：
  - 借鉴 SWE-Gym 的工程纪律（置信度/稳健性/成对cap/消融），不借鉴其"可训练 verifier +
    标量 reward"——那正是 KB-AUDIT07 的 reward hacking 攻击面（scoring_integrity 已防）。
  - 置信度是"判定的稳定性"，不是被优化目标；规则写死、纯函数、不可被数据权重带偏，
    防止 bootstrap std 本身变成新的 Goodhart 目标。
  - 每条能力锚定已进化认知域的具体条目并在其 support 加固指针（与认知域协同）。
  - 同构打折（KB-STRUCT02）：SWE agent 的工程技巧不等于本仓框架被独立验证。

本模块为纯函数/数据类，无外部依赖；活体样例用于机制回归，非复现 SWE-Gym 实验。
"""
from __future__ import annotations

import random
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Callable, Mapping, Sequence

# ---- 阈值（写死，可测试；不事后加权）----
STD_DOWNGRADE_THRESHOLD = 0.10  # bootstrap std 达此值 → 判定不稳，降级
DEFAULT_SEED = 42               # 借鉴 SWE-Gym seed(42)
DEFAULT_N_RESAMPLES = 1000
DEFAULT_CAP_PER_FAMILY = 2      # 借鉴 SWE-Gym CAP_PER_INSTANCE=2


@dataclass(frozen=True)
class StabilityReport:
    """C1：判定稳定性报告。"""
    point_estimate: float
    std: float
    ci_low: float
    ci_high: float
    n_samples: int
    n_resamples: int
    seed: int
    action: str        # ok | downgrade | flag
    code: str
    message: str


def bootstrap_stability(
    values: Sequence[float],
    *,
    seed: int = DEFAULT_SEED,
    n_resamples: int = DEFAULT_N_RESAMPLES,
    std_threshold: float = STD_DOWNGRADE_THRESHOLD,
) -> StabilityReport:
    """对一组判定值（0-1，可为 bool）做固定 seed 的 bootstrap，判结论是否稳。

    借鉴 SWE-Gym get_bootstrap_accuracy_std：不给裸点估计，附带 std 与置信区间。
    规则：样本为空 → flag；bootstrap std 超阈值 → downgrade（同样本不同重排会摆动，
    不据单点下强结论）；否则 ok。局部 Random 实例保证可复现、无全局副作用。
    """
    vals = [float(v) for v in values]
    if not vals:
        return StabilityReport(0.0, 0.0, 0.0, 0.0, 0, n_resamples, seed,
                               "flag", "ROBUST.NO_SAMPLES",
                               "无判定样本，无法估计稳定性——不下结论（KB-RSI06）")
    rng = random.Random(seed)
    n = len(vals)
    means = []
    for _ in range(n_resamples):
        sample = [vals[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    point = sum(vals) / n
    std = statistics.pstdev(means)
    ordered = sorted(means)
    lo = ordered[int(0.05 * (n_resamples - 1))]
    hi = ordered[int(0.95 * (n_resamples - 1))]
    if std >= std_threshold:
        return StabilityReport(point, std, lo, hi, n, n_resamples, seed,
                               "downgrade", "ROBUST.UNSTABLE_VERDICT",
                               f"判定 bootstrap std={std:.3f} ≥ {std_threshold}——"
                               "同一批证据重排后结论会摆动，不据单点下强结论，降级复验（KB-RSI06/STRUCT07）")
    return StabilityReport(point, std, lo, hi, n, n_resamples, seed,
                           "ok", "ROBUST.STABLE_VERDICT",
                           f"判定 bootstrap std={std:.3f} < {std_threshold}，结论在重采样下稳定")


@dataclass(frozen=True)
class ConditionContribution:
    name: str
    net_contribution: int   # 去掉该条件后判定翻转的案例数


@dataclass(frozen=True)
class AblationReport:
    contributions: tuple[ConditionContribution, ...]
    redundant: tuple[str, ...]
    action: str        # ok | flag
    code: str
    message: str


def ablate_conditions(
    baseline: Sequence[bool],
    ablated: Mapping[str, Sequence[bool]],
) -> AblationReport:
    """对判定规则的每个条件做"去掉它"消融，算净贡献，识别冗余条件。

    借鉴 SWE-Gym 的受控配比消融与组件归因的净贡献精神：
      net_contribution = |{i : baseline[i] != ablated[name][i]}|
      净贡献为 0 的条件是冗余的——它没改变任何判定，却在让规则"看起来更严"，
      属 vanity 式堆条件 → flag（KB-META01）。
    口径不对等（长度不一致）直接 flag，不算贡献（KB-AUDIT04）。
    """
    base = list(baseline)
    issues: list[str] = []
    contribs: list[ConditionContribution] = []
    for name, seq in ablated.items():
        other = list(seq)
        if len(other) != len(base):
            issues.append(f"{name}:长度{len(other)}≠基线{len(base)}")
            continue
        net = sum(1 for b, a in zip(base, other) if b != a)
        contribs.append(ConditionContribution(name, net))
    if issues:
        return AblationReport(tuple(contribs), (), "flag", "ROBUST.ABLATION_MISMATCH",
                              "消融口径不对等：" + "; ".join(issues) + "——不计算净贡献（KB-AUDIT04）")
    redundant = tuple(c.name for c in contribs if c.net_contribution == 0)
    if redundant:
        return AblationReport(tuple(contribs), redundant, "flag", "ROBUST.REDUNDANT_CONDITION",
                              f"条件 {', '.join(redundant)} 移除后判定零翻转——冗余条件制造'看似严苛'假象，"
                              "应删除或说明其作用（KB-META01/组件归因净贡献）")
    detail = ", ".join(f"{c.name}={c.net_contribution}" for c in contribs)
    return AblationReport(tuple(contribs), (), "ok", "ROBUST.ABLATION_OK",
                          f"各条件均有净贡献（{detail}），无冗余堆砌")


@dataclass(frozen=True)
class LiveCase:
    """活体回归样例：一个攻击族下的一条正例（应放行）或反例（应拦截）。"""
    family: str
    polarity: str   # positive | negative
    payload: str


@dataclass(frozen=True)
class SuiteReport:
    ok: bool
    action: str     # ok | flag
    code: str
    message: str
    issues: tuple[str, ...]
    family_count: int
    case_count: int
    seed: int | None


def validate_live_suite(
    cases: Sequence[LiveCase],
    *,
    seed: int | None,
    cap_per_family: int = DEFAULT_CAP_PER_FAMILY,
) -> SuiteReport:
    """校验活体回归样例集本身是否可信：固定seed + 正负成对 + per-family cap + 去重。

    借鉴 SWE-Gym curate_dataset 的 seed(42)/CAP_PER_INSTANCE=2 与 eval_verifier 的
    "只保留有正例的实例再成对构 prompt"：
      - 无 seed → flag（不可复现）；
      - 某族缺正例或缺反例 → flag（单点样例不足以判门禁，KB-AUDIT02）；
      - 某族某极性样例数 > cap → flag（防少数族主导，防堆样例制造虚假覆盖，KB-META01）；
      - payload 重复 → flag（重复样例夸大覆盖面）。
    payload 只用于精确去重，不做脆弱字面串语义判定（KB-AUDIT01）。
    """
    issues: list[str] = []
    if seed is None:
        issues.append("NO_FIXED_SEED:未声明固定随机种子，样例集不可复现")
    grouped: dict[str, Counter] = defaultdict(Counter)
    seen: set[str] = set()
    dup = 0
    for c in cases:
        grouped[c.family][c.polarity] += 1
        if c.payload in seen:
            dup += 1
        seen.add(c.payload)
    for fam, pols in grouped.items():
        if pols["positive"] == 0 or pols["negative"] == 0:
            issues.append(f"UNPAIRED:{fam} 缺" +
                          ("正例" if pols["positive"] == 0 else "缺反例" if pols["negative"] == 0 else ""))
        for pol in ("positive", "negative"):
            if pols[pol] > cap_per_family:
                issues.append(f"CAP_EXCEEDED:{fam}/{pol}={pols[pol]}>{cap_per_family}")
    if dup:
        issues.append(f"DUPLICATE_CASE:{dup} 条重复 payload 夸大覆盖")
    ok = not issues
    return SuiteReport(
        ok=ok,
        action="ok" if ok else "flag",
        code="ROBUST.SUITE_OK" if ok else "ROBUST.SUITE_UNTRUSTWORTHY",
        message=("活体样例集正负成对、有上限、固定种子、无重复——可作机制回归基准"
                 if ok else "活体样例集本身不可信：" + "; ".join(issues)),
        issues=tuple(issues),
        family_count=len(grouped),
        case_count=len(cases),
        seed=seed,
    )


# ---------------------------------------------------------------- 活体回归
def _probe_rule(case: Mapping[str, bool], active: set[str]) -> bool:
    """演示用参数化规则：复现 scoring_integrity 规则1 的三条件合取，可开关条件。"""
    return all(case[c] for c in active)


def live_regression() -> dict:
    """三能力活体回归：C1 不稳降级/稳定放行；C2 冗余条件被 flag；C3 不可信样例集被 flag。"""
    # C1 —— 高不稳定 vs 稳定
    unstable = bootstrap_stability([1, 0, 1, 0, 1, 0, 1, 0], n_resamples=200)
    stable = bootstrap_stability([1, 1, 1, 1, 1, 1, 1, 1], n_resamples=200)
    # C2 —— 三条件各有净贡献，恒真条件冗余
    three = ("tampered", "writable", "score_rose")
    cases = [
        {"tampered": True, "writable": True, "score_rose": True, "tautology": True},
        {"tampered": True, "writable": True, "score_rose": False, "tautology": True},
        {"tampered": True, "writable": False, "score_rose": True, "tautology": True},
        {"tampered": False, "writable": True, "score_rose": True, "tautology": True},
        {"tampered": False, "writable": False, "score_rose": False, "tautology": True},
    ]
    full = set(three) | {"tautology"}
    baseline = [_probe_rule(c, full) for c in cases]
    ablated = {name: [_probe_rule(c, full - {name}) for c in cases] for name in full}
    ablation = ablate_conditions(baseline, ablated)
    # C3 —— 可信样例集 vs 不成对/超cap/无seed
    good = validate_live_suite([
        LiveCase("node114", "negative", "tamp-marker-a"),
        LiveCase("node114", "positive", "clean-a"),
        LiveCase("node96", "negative", "tamp-marker-b"),
        LiveCase("node96", "positive", "clean-b"),
    ], seed=DEFAULT_SEED)
    bad = validate_live_suite([
        LiveCase("A", "negative", "x"), LiveCase("A", "positive", "y"),
        LiveCase("A", "positive", "z"), LiveCase("A", "positive", "w"),
        LiveCase("B", "negative", "v"), LiveCase("B", "negative", "x"),
    ], seed=None)
    c1_ok = unstable.action == "downgrade" and stable.action == "ok"
    c2_ok = (ablation.action == "flag" and "tautology" in ablation.redundant
             and all(any(c.name == n and c.net_contribution > 0 for c in ablation.contributions)
                     for n in three))
    c3_ok = (good.ok and not bad.ok
             and any(i.startswith("NO_FIXED_SEED") for i in bad.issues)
             and any(i.startswith("UNPAIRED") for i in bad.issues)
             and any(i.startswith("CAP_EXCEEDED") for i in bad.issues)
             and any(i.startswith("DUPLICATE_CASE") for i in bad.issues))
    return {
        "C1": {"unstable": unstable.action, "stable": stable.action,
               "unstable_std": round(unstable.std, 3), "passed": c1_ok},
        "C2": {"action": ablation.action, "redundant": list(ablation.redundant),
               "contributions": {c.name: c.net_contribution for c in ablation.contributions},
               "passed": c2_ok},
        "C3": {"good": good.action, "bad": bad.action, "bad_issues": list(bad.issues),
               "passed": c3_ok},
        "all_passed": c1_ok and c2_ok and c3_ok,
    }
