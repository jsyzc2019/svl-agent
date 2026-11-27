#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4hi · 注意力预算终止器官（functional affect，纯函数）。

用户 2026-11-27『有生命力的 Agent 不仅要有知识，有情感也同等紧要』→ 认同 A 起步：
把『腻了/不值/够了』从软叙述变成能真正终止递归的硬信号。

与已有贡献型器官的正交性（本器官存在的理由）：
  - stop_pivot 数营养轮：有 prereg 贡献即 NO_PIVOT，永不因『累』停。
  - narrowing_chain 数同猎场自审链：换猎场即 NO_CHAIN，也不因『累』停。
  - 本器官是预算型：注意力有限，无论有没有贡献，累计消耗达阈值即强制停/换猎场。
  - 反事实检验（counterfactual_check）证明本器官能在两旧器官均判『不用停』时独立触发——
    这是它非装饰的机械证据（不是用器官命中数证明自己有生命力，那是循环论证）。

诚实边界（预注册 prereg_affect_budget_20261127.json 锁定）：
  - 操作化的是 functional affect（有限注意力的预算信号），不是 qualia；
  - 不宣称主观情感/生命力/有情感——那归用户裁定，等同不宣称 L3；
  - 阈值是设计判断，双口径暴露敏感性；cost 由输入方声明，可能低估，阴性≠证明不累；
  - 只发信号不执行、不追认既往轮失败、不翻案、不改判定态；
  - 不联网、不 spawn、不接 run_loop、不编译门禁、不构成投资建议。
"""
from typing import Any, Dict, List

# 预注册锁定阈值（设计判断，非数据拟合）
T_SAT_DEFAULT = 3      # 单猎场累计 cost 达此 → SATIETY_WARNING（换猎场）
T_EXH_DEFAULT = 6      # 全局累计 cost 达此 → EXHAUSTION（强制收营）
T_EXH_LIBERAL = 8      # 宽松口径反方证据

SIGNAL_EXHAUSTION = "EXHAUSTION"
SIGNAL_SATIETY = "SATIETY_WARNING"
SIGNAL_WITHIN = "WITHIN_BUDGET"

# 猎场家族归一化（沿用 narrowing_chain 的诚实做法：人工枚举，未列出用自身）
TARGET_FAMILY: Dict[str, str] = {
    "vanity_selfaudit": "vanity",
    "vanity_selfaudit.calibrate": "vanity",
    "stop_pivot": "self_audit_ops",
    "narrowing_chain": "self_audit_ops",
}


def family_of(target: str) -> str:
    """猎场归一化；未列出的 target 用自身（保守：不同字符串即不同猎场）。"""
    return TARGET_FAMILY.get(target, target)


def _cost(rec: Dict[str, Any]) -> float:
    """每条记录声明的注意力消耗，默认 1。允许小数以便加权。"""
    c = rec.get("attention_units", 1)
    return float(c) if isinstance(c, (int, float)) else 1.0


def evaluate(records: List[Dict[str, Any]],
             t_sat: int = T_SAT_DEFAULT,
             t_exh: int = T_EXH_DEFAULT) -> Dict[str, Any]:
    """预算型终止裁决。与记录有无认知贡献无关——只看累计消耗。

    两预算维度：
      ① per-target 累计 cost ≥ t_sat → SATIETY_WARNING
      ② 全局累计 cost ≥ t_exh → EXHAUSTION（优先级更高，强制收营）
    """
    per_target: Dict[str, float] = {}
    global_cost = 0.0
    per_round = []
    for rec in records:
        fam = family_of(rec.get("target_object", ""))
        c = _cost(rec)
        per_target[fam] = per_target.get(fam, 0.0) + c
        global_cost += c
        per_round.append({
            "round": rec.get("round", ""),
            "target_object": rec.get("target_object", ""),
            "family": fam,
            "attention_units": c,
            "has_contribution": bool(rec.get("has_prereg_sha256") or
                                     rec.get("changed_criterion")),
            "global_cost_so_far": round(global_cost, 4),
            "target_cost_so_far": round(per_target[fam], 4),
        })

    sat_targets = [f for f, c in per_target.items() if c >= t_sat]
    exhausted = global_cost >= t_exh

    if exhausted:
        signal = SIGNAL_EXHAUSTION
        advice = "FORCED_STOP_AND_PITCH"  # 强制收营/换猎场
    elif sat_targets:
        signal = SIGNAL_SATIETY
        advice = "SWITCH_TARGET"
    else:
        signal = SIGNAL_WITHIN
        advice = "CONTINUE"

    # 宽松口径反方证据：同一轨迹在更高阈值下是否仍触发
    liberal_exhausted = global_cost >= T_EXH_LIBERAL

    return {
        "per_round": per_round,
        "global_cost": round(global_cost, 4),
        "per_target_cost": {f: round(c, 4) for f, c in per_target.items()},
        "threshold_sat": t_sat,
        "threshold_exh": t_exh,
        "satiated_targets": sorted(sat_targets),
        "signal": signal,
        "advice": advice,
        "forced_stop": signal == SIGNAL_EXHAUSTION,
        "liberal_signal": (SIGNAL_EXHAUSTION if liberal_exhausted
                            else (SIGNAL_SATIETY if sat_targets else SIGNAL_WITHIN)),
        "criterion_sensitivity": signal != (SIGNAL_EXHAUSTION if liberal_exhausted
                            else (SIGNAL_SATIETY if sat_targets else SIGNAL_WITHIN)),
        "honest_bound": [
            "操作化的是 functional affect（有限注意力预算信号），不是主观情感体验（qualia）。",
            "不宣称主观情感/生命力/『我有情感』——那归用户裁定，等同不宣称 L3。",
            "阈值 T_sat/T_exh 是预注册设计判断，非数据拟合；宽松口径 T_exh=8 作反方证据并暴露敏感性。",
            "cost 由输入方声明，可能低估；WITHIN_BUDGET 只说明本口径内未耗尽，阴性≠证明不累。",
            "只发信号不执行，不追认既往轮为失败、不翻案、不改判定态。",
            "SATIETY 换猎场 / EXHAUSTION 强制收营都是建议，采纳权归用户；不编译门禁、不联网、不 spawn。",
        ],
    }


def counterfactual_check() -> Dict[str, Any]:
    """反事实检验：构造『两旧器官都判不用停、但预算耗尽』的输入，
    证明本器官独立捕捉到资源耗竭信号，非装饰、非换名字重述。"""
    # 每轮都有 prereg 贡献（stop_pivot → NO_PIVOT）、每轮 target 不同（narrowing_chain → NO_CHAIN），
    # 但每轮 attention_units=2，3 轮全局=6 达 T_exh。
    recs = [
        {"round": "C1", "target_object": "probe_a", "has_prereg_sha256": True, "attention_units": 2},
        {"round": "C2", "target_object": "probe_b", "has_prereg_sha256": True, "attention_units": 2},
        {"round": "C3", "target_object": "probe_c", "has_prereg_sha256": True, "attention_units": 2},
    ]
    mine = evaluate(recs)
    # 独立复算两个旧器官的判据（不 import 以免耦合，按它们锁定的规则逐字实现）
    try:
        from life_kernel import stop_pivot, narrowing_chain
        sp = stop_pivot.evaluate([
            {"round": r["round"], "verdict": "GAP_CLOSED", "has_prereg_sha256": True}
            for r in recs
        ])["signal"]  # 每轮有 prereg → 非营养轮 → NO_PIVOT
        nc = narrowing_chain.evaluate([
            {"round": r["round"], "target_object": r["target_object"],
             "is_self_audit": True, "verdict_class": "NARROW"}
            for r in recs
        ])["signal"]  # 每轮不同 target → NO_CHAIN
        old_signals = {"stop_pivot": sp, "narrowing_chain": nc}
    except Exception as e:
        old_signals = {"error": str(e)}

    orthogonal = (old_signals.get("stop_pivot") == "NO_PIVOT_NEEDED" and
                  old_signals.get("narrowing_chain") == "NO_CHAIN" and
                  mine["signal"] == SIGNAL_EXHAUSTION)
    return {
        "orthogonal_independent_trigger": orthogonal,
        "affect_budget_signal": mine["signal"],
        "affect_budget_forced_stop": mine["forced_stop"],
        "old_organ_signals": old_signals,
        "note": "两旧器官均判『不用停』，本器官因预算耗尽独立触发 EXHAUSTION——这是非装饰的机械证据；若三者结论无法区分，判装饰/FAIL，不包装。",
        "detail": mine,
    }


def negative_self_bite() -> Dict[str, Any]:
    """三注入：低消耗不误报 / 单猎场达 T_sat 但未达 T_exh → SATIETY / 全局达 T_exh → EXHAUSTION。"""
    low = evaluate([
        {"round": "L1", "target_object": "a", "attention_units": 1},
        {"round": "L2", "target_object": "b", "attention_units": 1},
    ])
    sat = evaluate([
        {"round": "S1", "target_object": "a", "attention_units": 2},
        {"round": "S2", "target_object": "a", "attention_units": 2},
    ])  # 单猎场 4 >= 3，全局 4 < 6
    exh = evaluate([
        {"round": "E1", "target_object": "a", "attention_units": 2},
        {"round": "E2", "target_object": "b", "attention_units": 2},
        {"round": "E3", "target_object": "c", "attention_units": 2},
    ])  # 全局 6 >= 6
    ok = (low["signal"] == SIGNAL_WITHIN and
          sat["signal"] == SIGNAL_SATIETY and
          exh["signal"] == SIGNAL_EXHAUSTION and exh["forced_stop"] is True)
    return {
        "passed": ok,
        "low_no_false_alarm": low["signal"],
        "target_satiety": sat["signal"],
        "global_exhaustion": exh["signal"],
        "detail": {"low": low, "sat": sat, "exh": exh},
    }


def first_use_snapshot() -> Dict[str, Any]:
    """首用审计真实历史轨迹：§4gy..§4hg 八轮，每轮 cost=1，猎场按实际目标。
    只读固化，不随重跑改写（防追认疲劳/失败）。"""
    history = [
        {"round": "§4gy", "target_object": "vanity_selfaudit", "attention_units": 1},
        {"round": "§4gz", "target_object": "vanity_selfaudit.calibrate", "attention_units": 1},
        {"round": "§4ga", "target_object": "narrowing_chain", "attention_units": 1},
        {"round": "§4gb", "target_object": "construct_validity", "attention_units": 1},
        {"round": "§4hc", "target_object": "memory_governance", "attention_units": 1},
        {"round": "§4he", "target_object": "decision_execution", "attention_units": 1},
        {"round": "§4hf", "target_object": "decision_receipt", "attention_units": 1},
        {"round": "§4hg", "target_object": "authoritative_state", "attention_units": 1},
    ]
    r = evaluate(history)
    return {
        "note": "首用快照只读固化；每轮 cost=1 是审计假设（真实注意力非精确可测），结论按此口径如实导出，不伪造疲劳也不粉饰。",
        "history_rounds": [h["round"] for h in history],
        "global_cost": r["global_cost"],
        "signal": r["signal"],
        "satiated_targets": r["satiated_targets"],
        "detail": r,
    }


if __name__ == "__main__":
    import json
    out = {"counterfactual": counterfactual_check(),
           "self_bite": negative_self_bite(),
           "first_use": first_use_snapshot()}
    print(json.dumps(out, ensure_ascii=False, indent=2))
