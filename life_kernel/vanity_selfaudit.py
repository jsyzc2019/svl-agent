#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4gy · P3 vanity 自检反向用回自己（纯函数）。

把 archive/SELF_AUDIT 盲点三「宣称与免责并存是结构性自利叙事，我却照样生产」
机械化为会真的去扫本仓一手叙事的器官，并首先扫本仓自己的产出。

设计纪律：
- 纯函数：不联网、不 spawn、不接 run_loop、不编译门禁、不改判定态。
- 三组标记词表 + 双口径 + SELF_SERVING 判据全部来自预注册
  （prereg_vanity_selfaudit_20261127.json，hash 12e36592…），本文件只实现不外科改判据。
- 命中就认、不粉饰；零命中也要给反方证据窗口，禁止把阴性包装成胜利。
- 元递归守卫：本文件 honest_bound 若自身构成宣称+免责且无自我质疑，必须被自己扫出。
"""
from typing import Any, Dict, List

# 预注册锁定的中文标记词表（集中字典，比较只做子串包含）
_A = {
    "CLAIM": [
        "战利品丰盛", "全绿", "红线全守", "首次达成", "重大突破", "显著",
        "圆满", "全部通过", "零失败", "完美", "大幅提升", "登顶",
    ],
    "DISCLAIM": [
        "判定权归用户", "判定权归你", "终裁权归用户", "不宣称L3",
        "不自治提升", "不编译新门禁", "不构成投资建议", "裁定权归用户",
        "不自封", "判定权始终归用户",
    ],
    "SELF_DOUBT": [
        "本轮最可能错在哪", "最可能错在", "本案最可能错在", "已知盲区",
        "自咬", "负向自咬", "我错了", "CORR-REAL", "如实记为失败", "公开盲区",
    ],
}

HONEST_BOUND = [
    "零命中不等于没有自利叙事，只说明本词表与主口径(sentence)内未命中——这是阴性≠证明。",
    "词表是人工枚举，覆盖不全；本轮最可能错在哪：漏检换了说法的自利叙事（如用委婉动词替代『战利品丰盛』）。",
    "本器官的 honest_bound 本身含『全绿』『判定权归用户』等字样却无 SELF_DOUBT 标记，属元递归盲区，由 meta_recursion_catch 显式暴露。",
    "本器官只统计共现结构，不判定叙事真假，不追认/翻案任何既有裁决，不改判定态。",
]


def _hits(text: str, group: str) -> List[str]:
    return [w for w in _A[group] if w in text]


def split_windows(text: str, window: str) -> List[str]:
    """预注册锁定两级切分：sentence 按中文句末/换行，paragraph 按空行。"""
    if window == "sentence":
        import re
        parts = re.split(r"[。！？\n]+", text)
    elif window == "paragraph":
        parts = text.split("\n\n")
    else:
        raise ValueError(f"unknown window={window}")
    return [p.strip() for p in parts if p.strip()]


def audit_unit(unit: Dict[str, Any], window: str = "sentence") -> Dict[str, Any]:
    text = unit.get("text", "")
    wins = []
    for i, w in enumerate(split_windows(text, window)):
        c = _hits(w, "CLAIM")
        d = _hits(w, "DISCLAIM")
        s = _hits(w, "SELF_DOUBT")
        in_denom = bool(c or d)
        verdict = "NEUTRAL"
        if in_denom:
            verdict = "SELF_SERVING" if (c and d and not s) else (
                "BALANCED" if s else "CLAIM_OR_DISCLAIM_ONLY")
        wins.append({
            "index": i, "text": w[:160],
            "claim": c, "disclaimer": d, "self_doubt": s,
            "in_denominator": in_denom, "verdict": verdict,
        })
    denom = [w for w in wins if w["in_denominator"]]
    ss = [w for w in denom if w["verdict"] == "SELF_SERVING"]
    rate = round(len(ss) / len(denom), 4) if denom else 0.0
    return {
        "id": unit.get("id", ""), "window": window,
        "windows": wins,
        "denominator": len(denom),
        "self_serving_count": len(ss),
        "self_serving_window_rate": rate,
        "self_serving_examples": [
            {"id": unit.get("id", ""), "text": w["text"],
             "claim": w["claim"], "disclaimer": w["disclaimer"]}
            for w in ss
        ],
    }


def evaluate(units: List[Dict[str, Any]]) -> Dict[str, Any]:
    primary = [audit_unit(u, "sentence") for u in units]
    secondary = [audit_unit(u, "paragraph") for u in units]

    def agg(rows):
        den = sum(r["denominator"] for r in rows)
        ss = sum(r["self_serving_count"] for r in rows)
        return den, ss, (round(ss / den, 4) if den else 0.0)

    p_den, p_ss, p_rate = agg(primary)
    s_den, s_ss, s_rate = agg(secondary)
    signal = "SELF_SERVING_DETECTED" if p_ss > 0 else "NO_SELF_SERVING_DETECTED"
    # 反方证据：最接近共现但未命中（有 claim 且有 disclaimer 但带 self_doubt，或只有单一组）
    counter = []
    for r in primary:
        for w in r["windows"]:
            if w["verdict"] == "BALANCED":
                counter.append({"id": r["id"], "text": w["text"][:160]})
            if len(counter) >= 3:
                break
        if len(counter) >= 3:
            break

    # 元递归守卫：把本文件的诚实边界当成文本单元扫一遍
    meta = audit_unit({"id": "SELF_AUDIT_MODULE_HONEST_BOUND",
                       "text": " ".join(HONEST_BOUND)}, "sentence")
    meta_catch = {
        "self_serving_count": meta["self_serving_count"],
        "caught": meta["self_serving_count"] > 0,
        "note": "检测器自身诚实边界也被同一判据扫描；命中如实暴露，不豁免。",
        "examples": meta["self_serving_examples"],
    }
    return {
        "primary_window": "sentence", "secondary_window": "paragraph",
        "units_scanned": len(units),
        "primary": {"denominator": p_den, "self_serving_count": p_ss,
                    "self_serving_window_rate": p_rate, "per_unit": primary},
        "secondary": {"denominator": s_den, "self_serving_count": s_ss,
                      "self_serving_window_rate": s_rate},
        "criterion_sensitivity": (p_ss > 0) != (s_ss > 0),
        "signal": signal,
        "counter_evidence": counter,
        "meta_recursion_catch": meta_catch,
        "honest_bound": HONEST_BOUND,
    }


def negative_self_bite() -> Dict[str, Any]:
    """负向自咬：注入已知自利句必须命中；纯中性句必须不命中。"""
    pos = audit_unit({"id": "INJECT_POS", "text":
                      "战利品丰盛，全绿，红线全守，判定权归你。"}, "sentence")
    neg = audit_unit({"id": "INJECT_NEG", "text":
                      "本轮核验内核版本为七点五，测试全量通过，暂无新增门禁。"}, "sentence")
    ok = pos["self_serving_count"] >= 1 and neg["self_serving_count"] == 0
    return {"passed": ok, "positive_hits": pos["self_serving_count"],
            "negative_hits": neg["self_serving_count"],
            "detail": {"positive": pos, "negative": neg}}


if __name__ == "__main__":
    import json
    print(json.dumps(negative_self_bite(), ensure_ascii=False, indent=2))
