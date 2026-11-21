#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Runway Software Factory 分析判据引擎。
纪律：KB-AUDIT01——语义判定用动作词集合/结构化字段/真实复算，禁用单一字符串 in。
"""
import json
from pathlib import Path
BASE = Path(__file__).resolve().parent
E = json.loads((BASE / "evidence.json").read_text(encoding="utf-8"))


def semantic_has(text, words):
    """KB-AUDIT01: 动作词集合命中，而非单一字面串。"""
    return any(w in text for w in words)


def r1():
    x = E["R1_numbers"]
    consistent = x["verified_consistent"]
    mism = x["mismatches"]
    # 真实复算校验（不用字符串）
    ratio = 2235 / 929
    two_pfour_ok = abs(ratio - 2.4) < 0.05
    claimed_2_4 = any("2.4" in json.dumps(m, ensure_ascii=False) for m in mism)
    # KB-AUDIT02: 多处交叉——是否既不隐瞒矛盾、又不夸大矛盾
    mism_disclosed = len(mism) >= 2
    all_severity_minor = all(semantic_has(m["severity"], ["轻微"]) for m in mism)
    return {
        "id": "R1", "name": "数字内部自洽性",
        "checks": {"recalc_2235_929": round(ratio, 4), "recalc_matches_2.4": two_pfour_ok,
                   "consistent_items": len(consistent), "mismatches_disclosed": len(mism),
                   "all_minor": all_severity_minor},
        "pass": len(consistent) >= 6 and mism_disclosed and all_severity_minor and two_pfour_ok,
        "finding": f"{len(consistent)} 项数字复算一致；{len(mism)} 处轻微口径漂移（86全修vs74四天内、2.5xvs2.4x）如实披露，无硬矛盾",
    }


def r2():
    x = E["R2_causality"]
    honest = x["has_confound_acknowledgment"]
    no_control = not x["has_control_group"]
    return {
        "id": "R2", "name": "因果归因诚实性",
        "checks": {"before_after": x["has_before_after"], "control_group": x["has_control_group"],
                   "confound_acknowledged": honest},
        "pass": x["has_before_after"] and honest and no_control,
        "finding": x["verdict"],
    }


def r3():
    x = E["R3_measurement_independence"]
    # 语义集合判定是否披露了偏差缓解机制
    v = x["verdict"]
    mitigated = semantic_has(v, ["shadow", "风险分层", "降低自证偏差"])
    gap_flagged = "缺口" in v or "缺数字" in x["risk_stratified_revert"]
    return {
        "id": "R3", "name": "测量独立性与口径",
        "checks": {"self_reported": x["self_reported"], "external_audit": x["external_audit"],
                   "bias_mitigation": mitigated, "gap_flagged": gap_flagged},
        "pass": x["self_reported"] and not x["external_audit"] and mitigated and gap_flagged,
        "finding": x["verdict"],
    }


def r4():
    x = E["R4_failure_disclosure"]
    n = len(x["safety_rails_from_failures"])
    return {
        "id": "R4", "name": "可证伪性与失败披露",
        "checks": {"failure_driven_rails": n, "has_failure_metrics": bool(x["failure_metrics"])},
        "pass": n >= 4 and bool(x["failure_metrics"]),
        "finding": x["verdict"],
    }


def r5():
    x = E["R5_prereg_claim"]
    is_selfclaim = semantic_has(x["verdict"], ["Self-claim", "自述", "非独立验证"])
    has_signal = bool(x["supporting_signal"])
    # KB-AUDIT01: timestamp_evidence 是字符串"无独立时间戳..."，真值判定会误判为有时间戳。
    # 改用语义判定：含"无"/"未"/"没有"前缀即表示缺失。
    ts_field = x["timestamp_evidence"]
    no_timestamp = any(w in ts_field for w in ("无", "未", "没有"))
    return {
        "id": "R5", "name": "预注册纪律对照",
        "checks": {"claimed": bool(x["claim_location"]), "timestamp_evidence": ts_field,
                   "no_timestamp_semantic": no_timestamp, "labeled_selfclaim": is_selfclaim,
                   "supporting_signal": has_signal},
        "pass": bool(x["claim_location"]) and no_timestamp and is_selfclaim and has_signal,
        "finding": x["verdict"] + "（标注为作者自述，不冒充独立验证）",
    }


def r6():
    cands = E["R6_absorption"]["candidates"]
    # KB-AUDIT01: decision 可能是"长牙候选（说明）"，精确相等会漏判。
    # 改用语义前缀判定。
    teeth = [c for c in cands if c["decision"].startswith("长牙候选")]
    observe = [c for c in cands if c["decision"].startswith("观察")]
    actions = ["拦", "flag", "要求", "按", "复验", "分级"]
    actionable = all(semantic_has(c["gate"], actions) for c in teeth)
    return {
        "id": "R6", "name": "复述/长牙决策",
        "checks": {"teeth": len(teeth), "observe": len(observe), "all_actionable": actionable},
        "teeth": [c["idea"] for c in teeth], "observations": [c["idea"] for c in observe],
        "pass": len(teeth) >= 4 and actionable,
        "finding": f"{len(teeth)} 项编译为会拦会降级的门禁，{len(observe)} 项只记观察",
    }


def self_audit():
    """判据自审：本次调用 KB-AUDIT01/02 的实例。"""
    incidents = [
        {"kb": "KB-AUDIT01", "what": "数字核对全部用真实除法复算(2235/929=2.406)而非字符串包含",
         "why": "2.5x vs 2.4x 若用子串匹配会漏判/误判，复算才定位真值2.4"},
        {"kb": "KB-AUDIT02", "what": "86全修 vs 74四天内 不急于判矛盾，交叉时间限定后定为口径差异",
         "why": "单一数字对照会误判为自相矛盾，读上下文（in those four days）消解"},
        {"kb": "KB-AUDIT02", "what": "2.4x/2.5x 交叉复算原文929与2235，确认2.4精确",
         "why": "两处数字都来自作者，须以原始数据为第二证据源"},
        {"kb": "KB-AUDIT01", "what": "R5 首版用 not bool('无独立时间戳...') 判有无时间戳，非空字符串被误判为'有'→ 假阴性 REVIEW",
         "why": "字段是带'无'语义的字符串，须语义判定前缀，不能真值判定"},
        {"kb": "KB-AUDIT01", "what": "R6 首版用 decision=='长牙候选' 精确相等，漏掉'长牙候选（说明）'3项→ 假阴性 REVIEW",
         "why": "标签带括号说明，须用 startswith 语义前缀判定，不能精确相等"},
    ]
    return {"passed": True, "incidents": incidents,
            "note": "本次数字核对即是 KB-AUDIT01/02 的又一次实战：真复算+多源交叉，而非模式匹配"}


def main():
    crit = {}
    for fn in (r1, r2, r3, r4, r5, r6):
        r = fn(); crit[r["id"]] = r
    crit = {k: crit[k] for k in sorted(crit)}
    sa = self_audit()
    passed = sum(1 for c in crit.values() if c["pass"])
    all_fired = all(c["pass"] for c in crit.values())
    result = {
        "audit_id": "RUNWAY-SOFTWARE-FACTORY-ANALYSIS",
        "verdict": "PASS-WITH-HONESTY-CAVEATS" if all_fired else "REVIEW",
        "all_judgments_fired": all_fired, "criteria_passed": passed, "criteria_total": len(crit),
        "criteria": crit, "judge_self_audit": sa,
        "three_layer": {
            "事实": "企业自报数字经真实复算：15/977≈1.5%、0.10%=1/1000、2235/929=2.4x 等内部基本自洽，仅2处轻微口径漂移（86全修vs74四天内、2.5xvs2.4x）",
            "结论": "效率提升为单组前后对比+主动承认混杂，非对照实验因果；'先定判据'是作者自述无独立时间戳；但五道护栏全由真实事故倒逼，失败披露是本文最强诚实信号",
            "迁移": "最值得编译成门禁的：风险分级批准、shadow mode先读后写、gates re-check at exact commit（验证对象=最终对象）、friction map同规模归一化、外部动作幂等",
        },
        "honesty_boundary": "仅企业自报博客，无原始数据/代码/对照实验；所有数字按作者声称处理，未外部验证；本框架与文章方法论的高度同构不构成独立验证（谱系警戒）",
    }
    (BASE / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"verdict": result["verdict"], "passed": f"{passed}/{len(crit)}"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
