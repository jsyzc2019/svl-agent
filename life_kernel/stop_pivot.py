#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4gt · M6 内生 stop/pivot 判据器官（纯函数）。

把 §4gs 元命题 M6「连续3营养轮须主动标记收敛并建议换猎场」从纸面命题
机械化为会真的数营养轮、真的输出信号的器官。

设计纪律：
- 纯函数：不联网、不 spawn、不接 run_loop、不编译门禁、不改判定态。
- 贡献三态与 verdict 分类全部来自预注册锁定的规则（prereg_stop_pivot_20261126.json）。
- 双口径诚实：NARROW 类是否算「推翻旧判断」存在真实分歧，两种口径都算并都落档，
  主裁决取保守口径，宽口径作为反方证据 —— 禁止事后挑口径。
- 表演性自我批评守卫：若输入不变而翻转口径就改变信号，必须暴露这一敏感性。
"""
from typing import Any, Dict, List

# 预注册锁定的 verdict 分类字典（集中管理，比较只查 ASCII 键）
VERDICT_CLASS: Dict[str, str] = {
    "GAP_CLOSED": "BREAKTHROUGH",
    "STRATIFIED_CONFIRMED": "CONFIRM",
    "INTERPRETER_CONFIRMED": "CONFIRM",
    "EXECUTOR_INDEPENDENCE_CONFIRMED": "CONFIRM",
    "CROSS_VENDOR2_PARTIAL": "NARROW",
    "SET_VENDOR2_INCONCLUSIVE": "GAP",
    "DESIGN_SENSITIVE_BUT_DISCRIMINATIVE": "NARROW",
    "SPECIALIZED_SYNTAX": "NARROW",
    "ISOMORPHIC_CONFIRMED": "NARROW",
    "GAP_INCONCLUSIVE": "GAP",
    "CROSS_DOMAIN_INCONCLUSIVE": "GAP",
    "PURPOSE_INCONCLUSIVE": "GAP",
    "INTERPRETER_CROSS_INCONCLUSIVE": "GAP",
    "FULLCHAIN_PARTIAL": "NARROW",
}

# 保守口径下，视为「推翻/实质修正旧判断」的类
OVERTURN_CLASSES_CONSERVATIVE = {"BREAKTHROUGH", "CONFIRM"}
# 宽口径额外纳入 NARROW（收窄认识也算推进）
OVERTURN_CLASSES_LIBERAL = {"BREAKTHROUGH", "CONFIRM", "NARROW"}

DEFAULT_THRESHOLD = 3


def classify(verdict: str) -> str:
    """verdict 字符串 → 预注册锁定的贡献类；未知 verdict 落 GAP（保守）。"""
    return VERDICT_CLASS.get(verdict, "GAP")


def _is_nutritive(rec: Dict[str, Any], liberal: bool) -> bool:
    """营养轮 = ①改判据 ②新增可证伪命题 ③推翻旧判断 三者全 false。"""
    if rec.get("changed_criterion") is True:
        return False
    if rec.get("has_prereg_sha256") is True:
        return False
    cls = classify(rec.get("verdict", ""))
    overturn_set = OVERTURN_CLASSES_LIBERAL if liberal else OVERTURN_CLASSES_CONSERVATIVE
    if cls in overturn_set:
        return False
    return True


def longest_nutritive_streak(records: List[Dict[str, Any]], liberal: bool = False) -> int:
    best = cur = 0
    for rec in records:
        if _is_nutritive(rec, liberal):
            cur += 1
            best = max(best, cur)
        else:
            cur = 0
    return best


def evaluate(records: List[Dict[str, Any]],
             threshold: int = DEFAULT_THRESHOLD) -> Dict[str, Any]:
    """主裁决：保守口径定信号，宽口径作反方证据，暴露口径敏感性。"""
    cons = longest_nutritive_streak(records, liberal=False)
    lib = longest_nutritive_streak(records, liberal=True)
    signal = "PIVOT_ADVISED" if cons >= threshold else "NO_PIVOT_NEEDED"
    lib_signal = "PIVOT_ADVISED" if lib >= threshold else "NO_PIVOT_NEEDED"
    per_round = []
    for rec in records:
        cls = classify(rec.get("verdict", ""))
        per_round.append({
            "round": rec.get("round", ""),
            "verdict": rec.get("verdict", ""),
            "class": cls,
            "nutritive_conservative": _is_nutritive(rec, liberal=False),
            "nutritive_liberal": _is_nutritive(rec, liberal=True),
        })
    return {
        "per_round": per_round,
        "longest_nutritive_streak_conservative": cons,
        "longest_nutritive_streak_liberal": lib,
        "threshold": threshold,
        "signal": signal,
        "liberal_counter_signal": lib_signal,
        "criterion_sensitivity": cons != lib or signal != lib_signal,
        "honest_bound": [
            "保守口径把 NARROW 类（收窄认识）不算推翻旧判断；宽口径算。两者都基于预注册锁定规则，非事后挑口径。",
            "主裁决取保守口径，是为避免'用收窄包装成突破'；若两种口径信号不同，已通过 criterion_sensitivity 显式暴露。",
            "本器官只数营养轮并发信号，不追认任何既往轮为失败、不翻任何既有裁决、不改判定态。",
            "verdict 未知时保守归 GAP，可能高估营养轮——这是已知的工具盲区，不宣称精确。",
        ],
    }


def self_bite_check() -> Dict[str, Any]:
    """负向自咬：人工构造全营养轮序列，两种口径下都必须触发 PIVOT_ADVISED。"""
    all_nutritive = [
        {"round": f"X{i}", "verdict": "NO_SUCH_CLASS",
         "has_prereg_sha256": False, "changed_criterion": False}
        for i in range(3)
    ]
    r = evaluate(all_nutritive)
    ok = (r["signal"] == "PIVOT_ADVISED" and
          r["liberal_counter_signal"] == "PIVOT_ADVISED")
    return {"passed": ok, "conservative": r["signal"],
            "liberal": r["liberal_counter_signal"], "detail": r}


if __name__ == "__main__":
    import json
    print(json.dumps(self_bite_check(), ensure_ascii=False, indent=2))
