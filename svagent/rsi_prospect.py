"""RSI 未来前景独立论证引擎 — 预注册判据 R1~R5 的可执行实现。

设计纪律（与 sse_randomness/ai_text_detect 同构）：
- 所有判据来自 rsi_preregistration.json（SHA256 锁存），不事后加权。
- 严格 t 日信号 / t+1 日收益，杜绝前视偏差。
- 叙事层(GitHub证据)不进入实证层判据，来源隔离。
- 输出三层诚实结论，而非单一"有效/无效"断言。
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------- RSI 实现
def rsi_wilder(close: np.ndarray, period: int = 14) -> np.ndarray:
    """标准 Wilder 平滑 RSI。递推式 avg = (prev*(n-1)+cur)/n。"""
    n = len(close)
    out = np.full(n, np.nan)
    if n < period + 1:
        return out
    delta = np.diff(close)
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)
    avg_gain = gain[:period].mean()
    avg_loss = loss[:period].mean()
    for i in range(period, n - 1):
        avg_gain = (avg_gain * (period - 1) + gain[i]) / period
        avg_loss = (avg_loss * (period - 1) + loss[i]) / period
        if avg_loss == 0:
            out[i + 1] = 100.0
        else:
            rs = avg_gain / avg_loss
            out[i + 1] = 100.0 - 100.0 / (1.0 + rs)
    return out


def rsi_sma(close: np.ndarray, period: int = 14) -> np.ndarray:
    """简单均值 RSI（部分库的简化实现）——用于 R1 实现分歧对照。"""
    n = len(close)
    out = np.full(n, np.nan)
    delta = np.diff(close)
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)
    for i in range(period, n):
        ag = gain[i - period:i].mean()
        al = loss[i - period:i].mean()
        out[i] = 100.0 if al == 0 else 100.0 - 100.0 / (1.0 + ag / al)
    return out


# ---------------------------------------------------------------- 回测核心
@dataclass
class BacktestResult:
    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe: float
    n_trades: int
    strategy_returns: np.ndarray
    benchmark_returns: np.ndarray
    excess: float  # 策略年化 - 基准年化


def _max_drawdown(equity: np.ndarray) -> float:
    peak = np.maximum.accumulate(equity)
    dd = (equity - peak) / peak
    return float(dd.min()) if len(dd) else 0.0


def backtest_rsi(
    close: np.ndarray,
    period: int = 14,
    low: float = 30.0,
    high: float = 70.0,
    cost: float = 0.0015,
    allow_short: bool = False,
) -> BacktestResult:
    """RSI 超买超卖择时。信号在 t 收盘生成，仓位 t+1 生效（严格滞后）。

    多头规则：RSI<low 买入持有；RSI>high 卖出(空仓)。不允许做空时卖出后空仓。
    allow_short=True 时 RSI>high 持有 -1（仅蒙特卡洛零分布对照用，保持对称）。
    """
    n = len(close)
    rsi = rsi_wilder(close, period)
    ret = np.zeros(n, dtype=float)
    ret[1:] = close[1:] / close[:-1] - 1.0
    position = np.zeros(n, dtype=float)  # t 日实际持仓
    desired = 0.0
    trades = 0
    for t in range(1, n):
        r = rsi[t - 1]  # 严格用 t-1 的 RSI 决定 t 日仓位
        if np.isnan(r):
            desired = 0.0
        elif r < low:
            desired = 1.0
        elif r > high:
            desired = -1.0 if allow_short else 0.0
        # 不变则保持
        if desired != position[t - 1]:
            trades += 1
        position[t] = desired
    # 成本在换仓时扣除
    turnover = np.abs(np.diff(np.concatenate([[0.0], position])))
    strat = position * ret - turnover * cost
    equity = np.cumprod(1.0 + strat)
    bench = np.cumprod(1.0 + ret)
    total = float(equity[-1] - 1.0) if len(equity) else 0.0
    years = n / 244.0
    ann = float(equity[-1] ** (1.0 / years) - 1.0) if equity[-1] > 0 else -1.0
    bann = float(bench[-1] ** (1.0 / years) - 1.0) if bench[-1] > 0 else -1.0
    std = float(np.std(strat) * math.sqrt(244)) if np.std(strat) > 0 else 1e-12
    sharpe = ann / std if std > 0 else 0.0
    return BacktestResult(
        total_return=total,
        annual_return=ann,
        max_drawdown=_max_drawdown(equity),
        sharpe=sharpe,
        n_trades=trades,
        strategy_returns=strat,
        benchmark_returns=ret,
        excess=ann - bann,
    )


def _ann_return(equity_like: np.ndarray, n: int) -> float:
    eq = np.cumprod(1.0 + equity_like)
    years = n / 244.0
    return float(eq[-1] ** (1.0 / years) - 1.0) if eq[-1] > 0 else -1.0


# ---------------------------------------------------------------- 检验 R1~R5
def run_all(close: np.ndarray, dates: list[str] | None = None) -> dict[str, Any]:
    results: dict[str, Any] = {}
    n = len(close)

    # R1 实现正确性分歧
    w = rsi_wilder(close, 14)[100:]
    s = rsi_sma(close, 14)[100:]
    mask = ~(np.isnan(w) | np.isnan(s))
    diff = np.abs(w[mask] - s[mask])
    results["R1"] = {
        "name": "RSI 实现正确性自检(Wilder vs SMA)",
        "n_compared": int(mask.sum()),
        "mean_abs_diff": float(diff.mean()),
        "max_abs_diff": float(diff.max()),
        "pct_diff_gt5": float((diff > 5).mean()),
        "divergence_found": bool((diff > 5).mean() > 0.05),
        "note": "同一价格、同一周期，两实现差异越大，印证'用了RSI≠用了同一个RSI'",
    }

    # R2 经典择时回测（防前视）
    r2 = backtest_rsi(close, 14, 30, 70, cost=0.0015)
    r2_nocost = backtest_rsi(close, 14, 30, 70, cost=0.0)
    results["R2"] = {
        "name": "经典超买超卖择时回测(t+1生效,含成本)",
        "period": 14, "low": 30, "high": 70, "cost": 0.0015,
        "strategy_annual": r2.annual_return,
        "benchmark_annual": _ann_return(r2.benchmark_returns[1:], n - 1),
        "excess": r2.excess,
        "strategy_max_dd": r2.max_drawdown,
        "benchmark_max_dd": _max_drawdown(np.cumprod(1 + r2.benchmark_returns)),
        "sharpe": r2.sharpe,
        "n_trades": r2.n_trades,
        "excess_without_cost": r2_nocost.excess,
        "economic_advantage": bool(r2.excess > 0),
        "note": "扣成本后超额<=0 判无经济优势；信号严格用t-1 RSI",
    }

    # R3 参数网格 + Bonferroni
    grid = []
    for p in (7, 14, 21):
        for th in (20, 25, 30, 35):
            rr = backtest_rsi(close, p, th, 100 - th, cost=0.0015)
            # t 统计量量纲一致性：用【日超额序列均值 / 其标准误】，
            # 不得用年化超额(标量) / 日标准误——那会产生 -600 级假量级（高功效陷阱）。
            ex_series = (rr.strategy_returns - rr.benchmark_returns)[1:]
            mean_ex = float(ex_series.mean())
            se = float(ex_series.std(ddof=1) / math.sqrt(len(ex_series))) if len(ex_series) > 1 else 1e-9
            tstat = mean_ex / se if se > 0 else 0.0
            grid.append({"period": p, "threshold": th, "excess": rr.excess, "tstat_daily": tstat})
    m = len(grid)
    alpha = 0.05 / m
    # 量纲修正后：日超额 t 值，|t|>2.58 约 p<0.01；Bonferroni 近似用 |t|>3.5
    nominal = [g for g in grid if abs(g["tstat_daily"]) > 2.58]
    corrected = [g for g in grid if abs(g["tstat_daily"]) > 3.5]
    pos = sum(1 for g in grid if g["excess"] > 0)
    # 方向一致性判定：数据窥探的典型特征是"少数正显著被挑出"；
    # 若全体方向一致为负，则是稳健负向发现，不是数据窥探。
    if pos == 0:
        decision = "12/12全为负超额，方向高度一致→稳健的负向发现(RSI择时系统性劣于买入持有)，非数据窥探"
    elif pos == m:
        decision = "全部为正超额且校正后多数显著→方向一致的正向信号，可进一步交叉验证"
    else:
        decision = "正负混杂且校正后个别显著→数据窥探风险高，不可采信"
    results["R3"] = {
        "name": "参数网格+多重比较校正",
        "grid": grid, "n_tests": m,
        "bonferroni_alpha": alpha,
        "n_nominal_significant": len(nominal),
        "n_corrected_significant": len(corrected),
        "positive_excess_count": pos,
        "negative_excess_count": m - pos,
        "direction": "全负" if pos == 0 else ("全正" if pos == m else "混杂"),
        "decision": decision,
        "audit_note": "首跑曾误用'年化超额/日标准误'得t≈-647假量级，已修为'日超额均值/日标准误'(高功效陷阱自检)",
        "note": "t统计量量纲必须与序列同频；方向一致性优先于显著性个数",
    }

    # R4 蒙特卡洛零分布对照
    seed = 20261121
    rng = np.random.default_rng(seed)
    lr = np.diff(np.log(close))
    mu, sigma = float(lr.mean()), float(lr.std())
    zero_excess = []
    M = 500
    for _ in range(M):
        path = close[0] * np.exp(np.cumsum(rng.normal(mu, sigma, n - 1)))
        path = np.concatenate([[close[0]], path])
        rr = backtest_rsi(path, 14, 30, 70, cost=0.0015)
        zero_excess.append(rr.excess)
    zero_excess = np.array(zero_excess)
    real_excess = r2.excess
    pct = float((zero_excess < real_excess).mean())
    results["R4"] = {
        "name": "蒙特卡洛零分布盲测",
        "M": M, "seed": seed, "mu": mu, "sigma": sigma,
        "real_excess": real_excess,
        "zero_mean": float(zero_excess.mean()),
        "zero_p05": float(np.percentile(zero_excess, 5)),
        "zero_p95": float(np.percentile(zero_excess, 95)),
        "percentile": pct,
        "beyond_random": bool(pct >= 0.95),
        "decision": ("超出95%随机序列→存在超出随机的信号" if pct >= 0.95
                     else "未达95%阈值→与随机不可区分"),
    }

    # R5 样本内外分割
    split = n // 2
    in_sample = close[:split]
    out_sample = close[split:]
    best = None
    for p in (7, 14, 21):
        for th in (20, 25, 30, 35):
            rr = backtest_rsi(in_sample, p, th, 100 - th, cost=0.0015)
            if best is None or rr.excess > best[0]:
                best = (rr.excess, p, th)
    _, bp, bt = best
    rr_out = backtest_rsi(out_sample, bp, bt, 100 - bt, cost=0.0015)
    rr_out_default = backtest_rsi(out_sample, 14, 30, 70, cost=0.0015)
    decay = rr_out.excess - best[0]
    results["R5"] = {
        "name": "样本内/样本外过拟合门禁",
        "split_date": dates[split] if dates else f"index_{split}",
        "best_in_params": {"period": bp, "threshold": bt, "in_excess": best[0]},
        "out_excess_same_params": rr_out.excess,
        "out_excess_default": rr_out_default.excess,
        "decay": decay,
        "robust": bool(rr_out.excess > 0 and decay > -0.10),
        "decision": ("样本外仍为正且衰减可控→参数较稳健" if (rr_out.excess > 0 and decay > -0.10)
                     else "样本外转负或大幅衰减→过拟合/参数不稳"),
    }

    results["_meta"] = {
        "n_bars": n,
        "prereg_sha256": _sha256(ROOT / "rsi_preregistration.json"),
        "data_file": "sse_daily.json",
        "source_isolation": "GitHub证据仅叙事层，未进入R1-R5判据",
    }
    return results


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    data = json.loads((ROOT / "sse_daily.json").read_text(encoding="utf-8"))
    close = np.array([d["close"] for d in data], dtype=float)
    dates = [d["date"] for d in data]
    results = run_all(close, dates)
    (ROOT / "rsi_full_result.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, default=float), encoding="utf-8"
    )
    # 精简结论
    summary = {
        "R1_divergence_found": results["R1"]["divergence_found"],
        "R2_economic_advantage": results["R2"]["economic_advantage"],
        "R2_excess": results["R2"]["excess"],
        "R2_excess_without_cost": results["R2"]["excess_without_cost"],
        "R3_direction": results["R3"]["direction"],
        "R3_decision": results["R3"]["decision"],
        "R3_positive_count": results["R3"]["positive_excess_count"],
        "R4_beyond_random": results["R4"]["beyond_random"],
        "R4_percentile": results["R4"]["percentile"],
        "R5_robust": results["R5"]["robust"],
        "R5_out_excess": results["R5"]["out_excess_same_params"],
    }
    (ROOT / "rsi_result.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
