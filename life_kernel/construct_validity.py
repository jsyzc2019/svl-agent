#!/usr/bin/env python3
"""构念效度检查项（§4gb，按 prereg_finance_construct_validity_20261127.json 预注册）。

纯函数：给定二分类评估的代理标签/独立信号/判据预测/样本基础率，
输出『代理标签能否当构念真值用』的方法论判定。

硬边界（预注册 hard_limit）：
- 绝不输出任何个股是否造假/是否值得投资的判断；
- population_base_rate_hint 缺省则 UNKNOWN，不外推；
- 不改判定态、不联网、不 spawn。

数据可以来自财务盲测，但本模块只看『标签 vs 信号 vs 预测』的结构关系，
不读任何公司名做真假判断。
"""
from __future__ import annotations

import math
from typing import Optional


def wilson_interval(successes: int, trials: int, z: float = 1.96):
    """Wilson score 95% 置信区间。trials<=0 返回 (None, None)。"""
    if trials <= 0:
        return (None, None)
    p = successes / trials
    den = 1 + z * z / trials
    center = (p + z * z / (2 * trials)) / den
    half = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / den
    return (center - half, center + half)


def proxy_construct_gap(proxy_labels, signals, predictions):
    """统计代理标签与独立信号背离的样本数。

    proxy_labels[i]: 代理标签 0/1（如审计意见是否非标）
    signals[i]:      独立会计信号是否异常 0/1（如 alarm）
    predictions[i]:  判据预测 0/1
    返回背离样本：信号异常(1) 但代理标签阴性(0) 的条数，及其索引。
    注意：只判『标签与信号背离』这一结构事实，不判孰真孰假。
    """
    if not (len(proxy_labels) == len(signals) == len(predictions)):
        raise ValueError("length mismatch")
    divergent = [i for i, (p, s) in enumerate(zip(proxy_labels, signals)) if s == 1 and p == 0]
    return {"count": len(divergent), "indices": divergent, "n": len(proxy_labels)}


def base_rate_sensitivity(configs):
    """configs: [{name, precision, alarm_positive_rate}, ...]
    返回 precision 的极差与是否敏感（极差>0.15 视为敏感）。"""
    if not configs:
        return {"span": None, "sensitive": False, "n": 0}
    precisions = [c["precision"] for c in configs]
    span = max(precisions) - min(precisions)
    return {"span": round(span, 4), "sensitive": span > 0.15, "n": len(configs),
            "min": min(precisions), "max": max(precisions)}


def evaluate(proxy_labels, signals, predictions, tp, fp, configs,
             population_base_rate_hint: Optional[float] = None):
    """主入口：合成三条证伪检验，给方法论 verdict。

    tp/fp: 混淆矩阵里的真阳/假阳（算 precision 点估计 + Wilson CI）
    configs: 阈值敏感性配置列表（算 base_rate_sensitivity）
    """
    gap = proxy_construct_gap(proxy_labels, signals, predictions)
    ci_lo, ci_hi = wilson_interval(tp, tp + fp)
    n_pos = tp + fp
    precision = tp / n_pos if n_pos else None

    cv1 = gap["count"] > 0
    cv2 = (ci_lo is not None and ci_lo < 0.5 and (ci_hi - ci_lo) > 0.5)
    br = base_rate_sensitivity(configs)
    cv3 = br["sensitive"]

    hits = sum([cv1, cv2, cv3])
    if hits == 3:
        verdict = "PROXY_GAP_CONFIRMED"
    elif hits >= 1:
        verdict = "PARTIAL"
    else:
        verdict = "REFUTED"

    return {
        "verdict": verdict,
        "cv1_proxy_gap": {
            "passed": cv1, "count": gap["count"], "n": gap["n"],
            "indices": gap["indices"],
            "note": "信号异常但代理标签阴性=代理与构念非同一；只判背离事实不判真假。",
        },
        "cv2_precision_ci": {
            "passed": cv2, "tp": tp, "fp": fp, "n": n_pos,
            "precision": round(precision, 4) if precision is not None else None,
            "wilson_ci": [round(ci_lo, 4) if ci_lo is not None else None,
                          round(ci_hi, 4) if ci_hi is not None else None],
            "ci_width": round(ci_hi - ci_lo, 4) if ci_lo is not None else None,
        },
        "cv3_base_rate_sensitivity": {
            "passed": cv3, **br,
            "population_base_rate_hint": population_base_rate_hint if population_base_rate_hint is not None else "UNKNOWN",
            "note": "hint 缺省为 UNKNOWN，不外推真实世界基础率。",
        },
        "hard_limit": "方法论判定：代理标签与构念是否可混用。绝不判个股真假/投资价值，不构成投资建议。",
    }


def negative_self_bite():
    """三条负向注入：防器官永远喊『有 gap / CI 宽 / 敏感』。"""
    # 1) 代理与信号完全一致 → 应无背离
    r1 = proxy_construct_gap([0, 1, 0, 1], [0, 1, 0, 1], [0, 1, 0, 1])
    # 2) CI 窄样本 → 不得报 CI 宽
    lo2, hi2 = wilson_interval(90, 100)
    cv2_narrow = not (lo2 < 0.5 and (hi2 - lo2) > 0.5)
    # 3) 阈值不敏感 → 不得报敏感
    r3 = base_rate_sensitivity([
        {"name": "a", "precision": 0.75}, {"name": "b", "precision": 0.75},
    ])
    passed = (r1["count"] == 0) and cv2_narrow and (not r3["sensitive"])
    return {
        "passed": passed,
        "detail": {
            "identical_labels_no_gap": r1["count"] == 0,
            "narrow_ci_not_flagged": cv2_narrow,
            "insensitive_not_flagged": not r3["sensitive"],
        },
    }


if __name__ == "__main__":
    import json
    print(json.dumps(negative_self_bite(), ensure_ascii=False, indent=2))
