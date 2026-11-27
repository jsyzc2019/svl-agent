#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4ga · 连续收窄链判据（补 M6 stop_pivot 的已知盲区，纯函数）。

SESSION_HANDOFF §4gt 首用时诚实记录盲区：『连续收窄链本身不被本判据捕捉』。
stop_pivot 的营养轮三贡献位只看 ①改判据②新增可证伪命题③推翻旧判断；
只要每轮有 prereg（贡献位②真）即非营养轮，于是『同猎场建工具→校准工具→
再校准校准器』层层自指的收窄链每轮都不算营养轮，M6 永不触发。

本器官补这一个盲区：连续 N 轮同一猎场 + 自审 + 无实质突破 → 预警收敛/换猎场。

纪律：纯函数、不联网、不 spawn、不接 run_loop、不编译门禁、不改判定态。
判据与阈值全部来自预注册 prereg_narrowing_chain_20261127.json（9b1b71cc…）。
"""
from typing import Any, Dict, List

# 预注册锁猎场家族归一化：同一工具家族的不同轮次算同一猎场。
TARGET_FAMILY: Dict[str, str] = {
    "vanity_selfaudit": "vanity",
    "vanity_selfaudit.calibrate": "vanity",
}

# 预注册锁：这些类算『实质突破/新证据』，出现即断链
BREAKTHROUGH_CLASSES = {"BREAKTHROUGH", "CONFIRM"}

DEFAULT_N = 2


def family_of(target: str) -> str:
    """猎场归一化；未列出的 target 用自身（保守：不同字符串即不同猎场）。"""
    return TARGET_FAMILY.get(target, target)


def _is_chain_link(rec: Dict[str, Any]) -> bool:
    """收窄链一环 = 自审 且 无实质突破（同猎场由调用方按相邻比较）。"""
    if rec.get("is_self_audit") is not True:
        return False
    if rec.get("verdict_class") in BREAKTHROUGH_CLASSES:
        return False
    return True


def longest_same_target_streak(records: List[Dict[str, Any]]) -> int:
    """同猎场+自审+无突破的最长连续轮数。"""
    best = cur = 0
    prev_family = None
    for rec in records:
        fam = family_of(rec.get("target_object", ""))
        link = _is_chain_link(rec)
        if link and fam == prev_family:
            cur += 1
        elif link:
            cur = 1
        else:
            cur = 0
        best = max(best, cur)
        prev_family = fam if link else None
    return best


def evaluate(records: List[Dict[str, Any]], n: int = DEFAULT_N) -> Dict[str, Any]:
    primary = longest_same_target_streak(records)
    signal = "CONSECUTIVE_NARROWING" if primary >= n else "NO_CHAIN"
    # 宽口径 N=3 反方证据
    lib_signal = "CONSECUTIVE_NARROWING" if primary >= 3 else "NO_CHAIN"
    per_round = []
    prev_family = None
    for rec in records:
        fam = family_of(rec.get("target_object", ""))
        link = _is_chain_link(rec)
        same = link and fam == prev_family
        per_round.append({
            "round": rec.get("round", ""),
            "target_object": rec.get("target_object", ""),
            "family": fam,
            "verdict_class": rec.get("verdict_class", ""),
            "is_self_audit": rec.get("is_self_audit", False),
            "chain_link": link,
            "same_as_prev": same,
        })
        prev_family = fam if link else None
    # 自指捕获：本器官的靶场也是 vanity 家族，若输入里有本轮就记下来
    self_ref = [p for p in per_round if p["family"] == "vanity" and
                str(p["round"]).startswith("§4ga")]
    return {
        "per_round": per_round,
        "longest_same_target_streak": primary,
        "threshold_n": n,
        "signal": signal,
        "liberal_signal_n3": lib_signal,
        "criterion_sensitivity": signal != lib_signal,
        "self_reference_catch": {
            "caught": bool(self_ref),
            "rounds": [p["round"] for p in self_ref],
            "note": "若本轮 §4ga 也在 vanity 猎场家族，判据把它算进链——如实暴露，不假装站在链外。",
        },
        "honest_bound": [
            "阈值 N=2 是预注册设计判断（M6 原 N=3 对收窄链太钝），非数据拟合；N=3 作反方证据两口径都落档。",
            "猎场归一化 TARGET_FAMILY 是人工枚举，未列出的 target 按不同字符串算不同猎场——可能漏判换了名字的同猎场，这是已知盲区。",
            "本器官只数同猎场自审链并发预警，不追认任何既往轮为失败、不翻案、不改判定态。",
            "NO_CHAIN 只说明本口径内未检出，阴性≠证明。",
        ],
    }


def negative_self_bite() -> Dict[str, Any]:
    """三注入：不同猎场→NO_CHAIN；含突破→断链；同猎场自审→CONSECUTIVE_NARROWING。"""
    base = {"verdict_class": "NARROW", "is_self_audit": True, "has_prereg_sha256": True}
    diff = evaluate([
        {**base, "round": "A", "target_object": "vanity_selfaudit"},
        {**base, "round": "B", "target_object": "stop_pivot"},
    ])
    breakout = evaluate([
        {**base, "round": "A", "target_object": "vanity_selfaudit"},
        {**base, "round": "B", "target_object": "vanity_selfaudit", "verdict_class": "BREAKTHROUGH"},
    ])
    chain = evaluate([
        {**base, "round": "A", "target_object": "vanity_selfaudit"},
        {**base, "round": "B", "target_object": "vanity_selfaudit.calibrate"},
    ])
    ok = (diff["signal"] == "NO_CHAIN" and breakout["signal"] == "NO_CHAIN" and
          chain["signal"] == "CONSECUTIVE_NARROWING")
    return {
        "passed": ok,
        "diff_target": diff["signal"], "with_breakthrough": breakout["signal"],
        "same_target_self_audit": chain["signal"],
        "detail": {"diff": diff, "breakout": breakout, "chain": chain},
    }


if __name__ == "__main__":
    import json
    print(json.dumps(negative_self_bite(), ensure_ascii=False, indent=2))
