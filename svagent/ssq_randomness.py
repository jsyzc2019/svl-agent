"""双色球开奖随机性检验 — 严格执行预注册判据。

纪律：
  - 判据、阈值、种子全部来自 ssq_preregistration.json（已哈希锁存），本模块不得事后修改。
  - 结论独立提出：只借用统计学检验工具，不借用任何现成的随机/非随机结论。
  - 核心是 D0 盲测：把真实序列放进 200 条伪随机序列的分布里看它是否离群，
    这是防「聚类错觉 / 赌徒谬误 / 代理变量陷阱」的关键。
"""
from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scipy import stats as sps

PREREG_PATH = "ssq_preregistration.json"
DATA_PATH = "ssq_history.json"


# ---------------------------------------------------------------- 工具函数
def chi2_gof(observed: list[int], expected_prob: list[float]) -> float:
    """卡方拟合优度统计量。"""
    n = sum(observed)
    return sum((o - n * p) ** 2 / (n * p) for o, p in zip(observed, expected_prob))


def draw_sequence(rng: random.Random, n: int):
    """按双色球规则生成一个序列：红球 33 选 6 不放回，蓝球 16 选 1。"""
    reds, blues = [], []
    population = list(range(1, 34))
    for _ in range(n):
        reds.append(sorted(rng.sample(population, 6)))
        blues.append(rng.randint(1, 16))
    return reds, blues


def feature_vector(reds: list[list[int]], blues: list[int]) -> dict[str, Any]:
    """计算一条序列的结构性特征与频率计数（预注册 B1/A1/A2/C1 所需）。"""
    n = len(reds)
    red_count = [0] * 34
    blue_count = [0] * 17
    sum_vals, odd_ratios, big_ratios = [], [], []
    consecutive_counts, repeat_counts = [], []
    zone_counts = [[0, 0, 0] for _ in range(3)]  # 占位，实际下面用总量
    z1 = z2 = z3 = 0
    ac_values = []

    prev = None
    for r, b in zip(reds, blues):
        for x in r:
            red_count[x] += 1
        blue_count[b] += 1
        sum_vals.append(sum(r))
        odd_ratios.append(sum(1 for x in r if x % 2 == 1) / 6)
        big_ratios.append(sum(1 for x in r if x >= 17) / 6)
        # 连号对数
        consec = sum(1 for i in range(5) if r[i + 1] - r[i] == 1)
        consecutive_counts.append(consec)
        # 与上期重号数
        if prev is not None:
            repeat_counts.append(len(set(r) & set(prev)))
        prev = r
        # 三区分布
        z1 += sum(1 for x in r if 1 <= x <= 11)
        z2 += sum(1 for x in r if 12 <= x <= 22)
        z3 += sum(1 for x in r if 23 <= x <= 33)
        # AC 值：所有两两差值的不同个数 - (号码个数-1)
        diffs = {abs(r[i] - r[j]) for i in range(6) for j in range(i + 1, 6)}
        ac_values.append(len(diffs) - 5)

    # lag-1 自相关：对重号数序列
    ac1_repeat = 0.0
    if len(repeat_counts) > 2:
        ac1_repeat = _lag1_autocorr([float(x) for x in repeat_counts])

    return {
        "n": n,
        "red_count": red_count[1:34],
        "blue_count": blue_count[1:17],
        "chi2_red": chi2_gof(red_count[1:34], [6 / 33] * 33),
        "chi2_blue": chi2_gof(blue_count[1:17], [1 / 16] * 16),
        "sum_vals": sum_vals,
        "odd_ratios": odd_ratios,
        "big_ratios": big_ratios,
        "consecutive_counts": consecutive_counts,
        "repeat_counts": repeat_counts,
        "zone_totals": [z1, z2, z3],
        "ac_values": ac_values,
        "ac1_repeat": ac1_repeat,
    }


def _lag1_autocorr(xs: list[float]) -> float:
    n = len(xs)
    m = sum(xs) / n
    num = sum((xs[i] - m) * (xs[i - 1] - m) for i in range(1, n))
    den = sum((x - m) ** 2 for x in xs)
    return num / den if den else 0.0


import numpy as np

def ks_distance(a, b) -> float:
    """两个经验分布之间的 KS 距离（排序后双指针，O(n log n)）。

    对两个已排序样本，在所有样本点处比较经验 CDF，取最大差。
    """
    a = np.sort(np.asarray(a, dtype=float))
    b = np.sort(np.asarray(b, dtype=float))
    na, nb = len(a), len(b)
    # 合并去重后的候选点
    grid = np.union1d(a, b)
    # 用 searchsorted 向量化求每个点的 ECDF
    ea = np.searchsorted(a, grid, side="right") / na
    eb = np.searchsorted(b, grid, side="right") / nb
    return float(np.max(np.abs(ea - eb)))


def anomaly_score(feat: dict[str, Any], ref: dict[str, dict[str, list[float]]]) -> dict[str, float]:
    """综合异常度分数（预注册 D0 定义），返回各分量与总分。

    ref: 伪随机对照在每个指标上的分布（list of values across sequences）。
    z 分 = (真实值 - 对照均值) / 对照标准差；用绝对值衡量偏离。
    """
    def z_of(key, value):
        arr = ref[key]
        mu = sum(arr) / len(arr)
        sd = (sum((x - mu) ** 2 for x in arr) / len(arr)) ** 0.5
        return abs(value - mu) / sd if sd else 0.0

    z_red = z_of("chi2_red", feat["chi2_red"])
    z_blue = z_of("chi2_blue", feat["chi2_blue"])
    # B1 各特征的 KS 距离：真实分布 vs 对照的" pooled 分布"
    ks_terms = {}
    for fname in ["sum_vals", "odd_ratios", "big_ratios", "consecutive_counts", "repeat_counts", "ac_values"]:
        ks_terms[fname] = ks_distance(feat[fname], ref["pooled_" + fname])
    # 标准化每个 KS 距离
    ks_z = {}
    for fname, d in ks_terms.items():
        ks_z[fname] = z_of("ks_" + fname, d)
    # 三区分布卡方
    zone_expected = [feat["n"] * 6 / 3] * 3  # 每区理论红球数 = n*6/3
    z_zone = z_of("chi2_zone", chi2_gof(feat["zone_totals"], [1 / 3] * 3))
    ac1_z = z_of("ac1_repeat", abs(feat["ac1_repeat"]))

    total = z_red + z_blue + z_zone + ac1_z + sum(ks_z.values())
    return {
        "z_red": round(z_red, 3), "z_blue": round(z_blue, 3),
        "z_zone": round(z_zone, 3), "ac1_z": round(ac1_z, 3),
        **{f"ks_{k}": round(v, 3) for k, v in ks_z.items()},
        "total": round(total, 3),
    }


# ---------------------------------------------------------------- 主检验
def run_all(data_path=DATA_PATH, prereg_path=PREREG_PATH) -> dict[str, Any]:
    pre = json.loads(Path(prereg_path).read_text(encoding="utf-8"))
    data = json.loads(Path(data_path).read_text(encoding="utf-8"))
    n = len(data)
    reds = [d["red"] for d in data]
    blues = [d["blue"] for d in data]

    seed = pre["seed_for_pseudo_random"]
    M = pre["n_pseudo_sequences"]

    # ---- 生成伪随机对照池 ----
    pseudo = []
    for s in range(M):
        rng = random.Random(seed + s)
        pr, pb = draw_sequence(rng, n)
        pseudo.append(feature_vector(pr, pb))

    # ---- 构造对照分布 ref ----
    ref: dict[str, list[float]] = {}
    ref["chi2_red"] = [p["chi2_red"] for p in pseudo]
    ref["chi2_blue"] = [p["chi2_blue"] for p in pseudo]
    ref["chi2_zone"] = [chi2_gof(p["zone_totals"], [1 / 3] * 3) for p in pseudo]
    ref["ac1_repeat"] = [p["ac1_repeat"] for p in pseudo]
    for fname in ["sum_vals", "odd_ratios", "big_ratios", "consecutive_counts", "repeat_counts", "ac_values"]:
        # pooled 分布：所有伪随机序列该特征的合并样本
        ref["pooled_" + fname] = [v for p in pseudo for v in p[fname]]
        # 每条伪随机序列与该 pooled 的 KS 距离，作为 KS 距离的对照分布
        ref["ks_" + fname] = [ks_distance(p[fname], ref["pooled_" + fname]) for p in pseudo]

    # ---- 真实序列特征与异常度 ----
    real_feat = feature_vector(reds, blues)
    real_score = anomaly_score(real_feat, ref)

    # ---- 每条伪随机序列的异常度（同法，用自己的特征） ----
    pseudo_scores = [anomaly_score(p, ref)["total"] for p in pseudo]

    # ---- D0 盲测排名 ----
    pool = pseudo_scores + [real_score["total"]]
    pool_sorted = sorted(pool)
    real_rank = pool_sorted.index(real_score["total"]) + 1  # 1=最不异常
    percentile_more_anomalous = sum(1 for x in pseudo_scores if x < real_score["total"]) / M
    # 预注册：真实序列比>=95%伪随机更异常 -> H1方向
    triggered_H1 = percentile_more_anomalous >= 0.95

    # ---- A1/A2 卡方在对照分布中的分位 ----
    def pct(arr, v):
        return sum(1 for x in arr if x < v) / len(arr)

    chi2_red_pct = pct(ref["chi2_red"], real_feat["chi2_red"])
    chi2_blue_pct = pct(ref["chi2_blue"], real_feat["chi2_blue"])

    # ---- B1 各特征 KS 距离在对照中的分位 ----
    ks_pct = {}
    for fname in ["sum_vals", "odd_ratios", "big_ratios", "consecutive_counts", "repeat_counts", "ac_values"]:
        d = ks_distance(real_feat[fname], ref["pooled_" + fname])
        ks_pct[fname] = round(pct(ref["ks_" + fname], d), 3)
    n_extreme_ks = sum(1 for v in ks_pct.values() if v >= 0.95)

    # ---- 子时期稳定性（稳健性补充）----
    half = n // 2
    sub = {}
    for label, sl in [("early", slice(0, half)), ("late", slice(half, n))]:
        fr = feature_vector(reds[sl], blues[sl])
        sub[label] = {
            "chi2_red_pct": round(pct(ref["chi2_red"], fr["chi2_red"]), 3),
            "chi2_blue_pct": round(pct(ref["chi2_blue"], fr["chi2_blue"]), 3),
        }

    result = {
        "prereg_sha256": pre.get("alpha"),  # 占位，报告层填真实哈希
        "n_draws": n,
        "date_range": [data[0]["date"], data[-1]["date"]],
        "seed": seed,
        "n_pseudo": M,
        "tests": {
            "A1_chi2_red": {
                "statistic": round(real_feat["chi2_red"], 2),
                "pct_in_random": round(chi2_red_pct, 3),
                "exceeds_97_5": chi2_red_pct >= 0.975,
            },
            "A2_chi2_blue": {
                "statistic": round(real_feat["chi2_blue"], 2),
                "pct_in_random": round(chi2_blue_pct, 3),
                "exceeds_97_5": chi2_blue_pct >= 0.975,
            },
            "B1_structure_ks": {
                "pct_in_random": ks_pct,
                "n_features_exceed_95": n_extreme_ks,
                "threshold_ge_2": pre["tests"][1]["decision_rule"],
            },
            "C1_autocorr": {
                "ac1_repeat_real": round(real_feat["ac1_repeat"], 4),
                "pct_in_random": round(pct(ref["ac1_repeat"], abs(real_feat["ac1_repeat"])), 3),
            },
            "D0_blind_comparison": {
                "real_anomaly_total": real_score["total"],
                "real_score_breakdown": real_score,
                "pseudo_mean": round(sum(pseudo_scores) / M, 3),
                "pseudo_max": round(max(pseudo_scores), 3),
                "real_rank_of": M + 1,
                "percentile_more_anomalous_than_pseudo": round(percentile_more_anomalous, 4),
                "threshold": 0.95,
                "triggered_H1": triggered_H1,
            },
            "subperiod_stability": sub,
        },
    }
    return result


if __name__ == "__main__":
    import json as _j
    print(_j.dumps(run_all(), ensure_ascii=False, indent=2))
