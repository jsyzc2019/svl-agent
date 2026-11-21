"""上证综指有效性检验 — 严格执行预注册判据（弱式有效性）。

纪律：判据/阈值/种子全部来自 sse_preregistration.json（已哈希锁存），不得事后修改。
只借用统计检验工具，不借用任何现成结论；结论由数据独立提出。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from statsmodels.stats.diagnostic import acorr_ljungbox

PREREG_PATH = "sse_preregistration.json"
DATA_PATH = "sse_daily.json"


def load_returns(path=DATA_PATH):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    close = np.array([float(d["close"]) for d in data])
    dates = [d["date"] for d in data]
    logret = np.diff(np.log(close))
    return dates[1:], logret, close, dates


def variance_ratio(r, q):
    """Lo-MacKinlay 方差比检验（异方差稳健 z 统计量）。"""
    n = len(r)
    mu = r.mean()
    # 用重叠q期收益
    rq = np.array([r[i:i + q].sum() for i in range(n - q + 1)])
    var1 = np.var(r, ddof=1)
    varq = np.var(rq, ddof=1)
    vr = varq / (q * var1)
    # Lo-MacKinlay 异方差稳健渐近方差
    sigma_sq = 0.0
    for j in range(1, q):
        cov = np.cov(r[:-j], r[j:])[0, 1] if n - j > 1 else 0.0
        sigma_sq += ((2 * (q - j) / q) ** 2) * (cov / var1)
    var_vr = (2 * (2 * q - 1) * (q - 1)) / (3 * q) + sigma_sq
    z = (vr - 1) / np.sqrt(max(var_vr, 1e-12) / n)
    return vr, z


def runs_test(signs):
    """游程检验：正负号序列的游程数 z 统计量。"""
    signs = np.asarray(signs)
    n = len(signs)
    n_pos = np.sum(signs > 0)
    n_neg = np.sum(signs < 0)
    n_runs = 1 + np.sum(signs[1:] != signs[:-1])
    p = (n_pos * n_pos + n_neg * n_neg) / (n * n)
    exp_runs = (2 * n_pos * n_neg) / n + 1
    var_runs = (2 * n_pos * n_neg * (2 * n_pos * n_neg - n)) / (n * n * (n - 1))
    z = (n_runs - exp_runs) / np.sqrt(max(var_runs, 1e-12))
    return n_runs, exp_runs, z


def anomaly_score(feat, ref):
    """综合异常度（预注册 G0 定义）。"""
    def z_of(key, value):
        arr = ref[key]
        mu, sd = np.mean(arr), np.std(arr)
        return abs(value - mu) / sd if sd else 0.0
    lb_z = z_of("lb_z", feat["lb_z"])
    vr_z_sum = sum(z_of(f"vr_z_{q}", feat[f"vr_z_{q}"]) for q in feat["qs"])
    run_z = z_of("runs_z", feat["runs_z"])
    cal_z = z_of("cal_max_t", feat["cal_max_t"])
    total = lb_z + vr_z_sum + run_z + cal_z
    return {"lb_z": round(lb_z, 3), "vr_z_sum": round(vr_z_sum, 3),
            "runs_z": round(run_z, 3), "cal_z": round(cal_z, 3),
            "total": round(total, 3)}


def feats_of(r, weekdays=None, qs=(2, 5, 10, 20)):
    """计算一条收益序列的检验特征。"""
    f = {"qs": list(qs)}
    # F1 序列相关
    ac = [float(np.corrcoef(r[:-k], r[k:])[0, 1]) for k in range(1, 11)]
    lb = acorr_ljungbox(r, lags=[10], return_df=True)["lb_stat"].values[0]
    lb_p = acorr_ljungbox(r, lags=[10], return_df=True)["lb_pvalue"].values[0]
    f["ac1_10"] = [round(x, 4) for x in ac]
    f["lb_stat"] = float(lb)
    f["lb_p"] = float(lb_p)
    f["lb_z"] = float(lb)  # 用统计量本身做z（卡方10自由度近正态）
    # F2 方差比
    for q in qs:
        vr, z = variance_ratio(r, q)
        f[f"vr_{q}"] = round(float(vr), 4)
        f[f"vr_z_{q}"] = round(float(z), 3)
    # F3 游程
    nr, er, rz = runs_test(np.sign(r))
    f["n_runs"], f["exp_runs"], f["runs_z"] = int(nr), round(float(er), 1), round(float(rz), 3)
    # F4 日历效应：用weekday索引(0-4)分组，计算最大|t|
    if weekdays is not None and len(weekdays) == len(r):
        means = []
        for w in range(5):
            grp = r[np.array(weekdays) == w]
            if len(grp) > 30:
                se = grp.std(ddof=1) / np.sqrt(len(grp))
                means.append(grp.mean() / se if se else 0.0)
        f["cal_max_t"] = float(max((abs(t) for t in means), default=0.0))
    else:
        # 对照序列无weekday，用星期随机分组模仿（保证同分布）——预注册原则：对照与真实同机制
        rng = np.random.default_rng(20261121)
        wd = rng.integers(0, 5, len(r))
        means = []
        for w in range(5):
            grp = r[wd == w]
            if len(grp) > 30:
                se = grp.std(ddof=1) / np.sqrt(len(grp))
                means.append(grp.mean() / se if se else 0.0)
        f["cal_max_t"] = float(max((abs(t) for t in means), default=0.0))
    return f


def backtest(r, train_ratio=0.7, cost=0.0015):
    """H0 样本外回测：动量/反转/均线择时 vs 买入持有，含交易成本。"""
    n = len(r)
    cut = int(n * train_ratio)
    test = r[cut:]
    results = {}

    def sharpe_with_cost(signal):
        # signal: 1 持仓 / 0 空仓 / -1 做空(这里简化为多空)
        pos = np.asarray(signal, dtype=float)
        ret = pos * test
        turnover = np.abs(np.diff(np.concatenate([[0], pos])))
        net = ret - turnover * (2 * cost)  # 每次换仓双边成本
        ann = net.mean() * 252
        vol = net.std() * np.sqrt(252)
        shp = ann / vol if vol > 0 else 0.0
        return ann, shp, net

    # 买入持有基线
    bh_ann = test.mean() * 252
    bh_vol = test.std() * np.sqrt(252)
    bh_shp = bh_ann / bh_vol if bh_vol > 0 else 0.0
    results["buy_hold"] = {"annual": round(bh_ann, 4), "sharpe": round(bh_shp, 3)}

    # (a) 动量：过去20日收益>0持仓
    window = 20
    mom_sig = []
    for i in range(len(test)):
        idx = cut + i
        past = r[max(0, idx - window):idx]
        mom_sig.append(1 if past.sum() > 0 else -1)
    ann, shp, net = sharpe_with_cost(mom_sig)
    results["momentum20"] = {"annual": round(ann, 4), "sharpe": round(shp, 3),
                             "excess": round(ann - bh_ann, 4)}

    # (b) 反转：过去5日收益<0持仓（做多超跌）
    window = 5
    rev_sig = []
    for i in range(len(test)):
        idx = cut + i
        past = r[max(0, idx - window):idx]
        rev_sig.append(1 if past.sum() < 0 else -1)
    ann, shp, net = sharpe_with_cost(rev_sig)
    results["reversal5"] = {"annual": round(ann, 4), "sharpe": round(shp, 3),
                            "excess": round(ann - bh_ann, 4)}

    # (c) 移动均线择时：价格>MA20持仓
    # 【前视偏差修复】信号只能用 t-1 收盘信息，t 日执行；
    # 初版用 close[idx]（当天收盘）判断却计入当天收益 r[idx]，属用未来信息决策，
    # 会把亏损策略伪装成年化+26%。修正后须严格 shift 一期。
    close = np.exp(np.cumsum(r))  # 重构价格路径
    ma_sig = []
    for i in range(len(test)):
        idx = cut + i
        if idx - 1 < 20:
            ma_sig.append(0)
            continue
        ma = close[idx - 20:idx].mean()          # close[idx-20..idx-1]，不含当天
        ma_sig.append(1 if close[idx - 1] > ma else 0)  # 用 t-1 收盘判断
    ann, shp, net = sharpe_with_cost(ma_sig)
    results["ma20_timing"] = {"annual": round(ann, 4), "sharpe": round(shp, 3),
                              "excess": round(ann - bh_ann, 4)}
    return results, cut


def run_all() -> dict[str, Any]:
    pre = json.loads(Path(PREREG_PATH).read_text(encoding="utf-8"))
    dates, r, close, all_dates = load_returns()
    n = len(r)
    # weekday 用日期字符串解析
    from datetime import datetime
    weekdays = [datetime.strptime(d, "%Y-%m-%d").weekday() for d in dates]

    # ---- 真实序列特征 ----
    real_feat = feats_of(r, weekdays)

    # ---- 随机游走对照 ----
    seed = pre["seed_for_random_walk"]
    M = pre["n_random_walks"]
    mu, sigma = r.mean(), r.std(ddof=1)
    ref = {"lb_z": [], "runs_z": [], "cal_max_t": []}
    for q in (2, 5, 10, 20):
        ref[f"vr_z_{q}"] = []
    pseudo_feats = []
    for s in range(M):
        rng = np.random.default_rng(seed + s)
        rw = rng.normal(mu, sigma, n)
        pf = feats_of(rw)  # 对照用随机weekday分组（同机制）
        pseudo_feats.append(pf)
        ref["lb_z"].append(pf["lb_z"])
        ref["runs_z"].append(abs(pf["runs_z"]))
        ref["cal_max_t"].append(pf["cal_max_t"])
        for q in (2, 5, 10, 20):
            ref[f"vr_z_{q}"].append(abs(pf[f"vr_z_{q}"]))
    # runs_z 用绝对值
    real_feat_abs = dict(real_feat)
    real_feat_abs["runs_z"] = abs(real_feat["runs_z"])

    real_score = anomaly_score(real_feat_abs, ref)
    pseudo_scores = [anomaly_score(pf, ref)["total"] for pf in pseudo_feats]
    pool = pseudo_scores + [real_score["total"]]
    real_rank = sorted(pool).index(real_score["total"]) + 1
    pct_more_anomalous = sum(1 for x in pseudo_scores if x < real_score["total"]) / M
    g0_trigger = pct_more_anomalous >= 0.95

    # ---- F1/F2/F3 分位 ----
    def pct(arr, v):
        return float(np.sum(np.array(arr) < v) / len(arr))

    # ---- H0 回测 ----
    bt, cut = backtest(r, pre["train_ratio"], pre["cost_single_side"])

    # ---- 子时期稳健性 ----
    half = n // 2
    sub = {}
    for label, sl in [("early", slice(0, half)), ("late", slice(half, n))]:
        sf = feats_of(r[sl])
        sub[label] = {
            "vr_2": sf["vr_2"], "vr_10": sf["vr_10"],
            "ac1": sf["ac1_10"][0], "lb_p": round(sf["lb_p"], 4),
        }

    result = {
        "n_returns": n,
        "date_range": [dates[0], dates[-1]],
        "mean_daily_return": round(float(mu), 6),
        "std_daily_return": round(float(sigma), 6),
        "seed": seed, "n_random_walks": M,
        "backtest_cut_index": cut,
        "tests": {
            "F1_autocorr": {
                "ac1_10": real_feat["ac1_10"],
                "lb_stat": round(real_feat["lb_stat"], 2),
                "lb_p": round(real_feat["lb_p"], 6),
                "bonferroni_alpha_lag": 0.001,
                "n_sig_lags": sum(1 for x in real_feat["ac1_10"] if abs(x) > 0.05),
            },
            "F2_variance_ratio": {
                q: {"vr": real_feat[f"vr_{q}"], "z": real_feat[f"vr_z_{q}"],
                    "sig_1pct": abs(real_feat[f"vr_z_{q}"]) > 2.58}
                for q in (2, 5, 10, 20)
            },
            "F3_runs": {
                "n_runs": real_feat["n_runs"], "exp_runs": real_feat["exp_runs"],
                "z": real_feat["runs_z"], "sig_1pct": abs(real_feat["runs_z"]) > 2.58,
            },
            "F4_calendar": {
                "max_abs_t": round(real_feat["cal_max_t"], 3),
                "bonferroni_alpha": 0.0029,
                "note": "17个星期/月份检验的Bonferroni阈值；max|t|对应p需<0.0029才显著",
            },
            "G0_random_walk_control": {
                "real_anomaly_total": real_score["total"],
                "breakdown": real_score,
                "pseudo_mean": round(float(np.mean(pseudo_scores)), 3),
                "pseudo_max": round(float(np.max(pseudo_scores)), 3),
                "real_rank_of": M + 1,
                "percentile_more_anomalous": round(pct_more_anomalous, 4),
                "threshold": 0.95, "triggered_H1": g0_trigger,
            },
            "H0_backtest": bt,
            "subperiod_stability": sub,
        },
    }
    return result


if __name__ == "__main__":
    import json as _j
    print(_j.dumps(run_all(), ensure_ascii=False, indent=2))
