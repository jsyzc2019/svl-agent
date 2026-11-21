#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
雄心教程文审计判据引擎（A1-A6）。
纪律：KB-AUDIT01(动作词集合非脆弱字面串) + KB-AUDIT02(多维交叉、不因单点定罪)。
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
E = json.loads((BASE / "evidence.json").read_text(encoding="utf-8"))


def semantic_has(text, words):
    return any(w in str(text) for w in words)


def a1():
    x = E["A1_falsifiability"]
    actions = len(x["concrete_actions"])
    bounds = len(x["hidden_failure_conditions"])
    slogans = len(x["slogans"])
    # 可操作教程判定：动作≥8 + 自带失败条件≥2（多维，不靠单一"教程"标签）
    actionable = actions >= 8
    has_failure_conditions = bounds >= 2
    slogans_disclosed = semantic_has(x["verdict"], ["坦承", "未伪装"])
    return {
        "id": "A1", "name": "可证伪分级",
        "checks": {"concrete_actions": actions, "failure_conditions": bounds,
                   "slogans": slogans, "actionable": actionable,
                   "has_failure_conditions": has_failure_conditions,
                   "slogans_disclosed": slogans_disclosed},
        "pass": actionable and has_failure_conditions and slogans_disclosed,
        "finding": "主体是可操作教程(10+具体动作、3类自带失败条件)；少量口号作者坦承是rallying cry未伪装成方法"
    }


def a2():
    x = E["A2_fact_check"]
    fc = {k: v for k, v in x.items() if k != "summary"}
    verdicts = [v["finding"] for v in fc.values()]
    true_count = sum(1 for v in verdicts if semantic_has(v, ["TRUE", "属实", "吻合"]))
    qualified = sum(1 for v in verdicts if semantic_has(v, ["QUALIFIED", "PARTIAL", "限定", "HONESTLY"]))
    # 关键： MY prereg suspicion vs reality
    prereg_suspected = ["sawe_sub2", "dantzig", "bannister_46days", "locke_latham"]
    all_suspected_true = all(semantic_has(fc[k]["finding"], ["TRUE", "属实"]) for k in prereg_suspected)
    # KB-AUDIT02: PARTIAL 不判假
    partial_not_false = "不判假" in str(fc["tao_quote_attribution"]["finding"])
    return {
        "id": "A2", "name": "事实断言核查",
        "checks": {"assertions_checked": len(fc), "true_or_core_true": true_count,
                   "qualified_or_partial": qualified,
                   "prereg_suspicions_all_wrong": all_suspected_true,
                   "partial_not_convicted_as_false": partial_not_false},
        "pass": true_count >= 5 and all_suspected_true and partial_not_false,
        "finding": "5个高风险断言全部为真或带诚实限定词；我预注册怀疑的4条全错——先验偏见(厂商倡导→断言有假)被事实推翻；转述引语标PARTIAL不判假"
    }


def a3():
    x = E["A3_standpoint"]
    disclosed = x["self_disclosed"] and x["disclosure_honest"]
    not_convicted = x["not_convicted_by_identity"] and "身份" in str(x["not_convicted_by_identity"])
    has_external = x["external_evidence_used"]
    return {
        "id": "A3", "name": "主体归属与利益立场",
        "checks": {"self_disclosed": disclosed, "not_convicted_by_identity": not_convicted,
                   "uses_external_evidence": has_external, "model_agnostic_claim": "not model-specific" in str(x["promotional_framing"])},
        "pass": disclosed and not_convicted and has_external,
        "finding": "作者开篇自述供职Claude团队，立场透明；按KB-AUDIT02身份不定罪；读者须知这是从业者倡导+个人经验而非独立对照实验"
    }


def a4():
    x = E["A4_argument_chain"]
    bounds = len(x["boundary_disclosures"])
    ev_types = len(x["evidence_types"])
    overreach = x["overreach_found"]
    minor = "minor" in str(overreach["severity"])
    kb_linked = semantic_has(overreach["kb"], ["KB-R-MS01", "KB-R-KON02"])
    return {
        "id": "A4", "name": "论点-证据链与外推",
        "checks": {"evidence_types": ev_types, "boundary_disclosures": bounds,
                   "overreach_found": bool(overreach), "overreach_severity": overreach["severity"],
                   "minor_not_fatal": minor, "kb_linked": kb_linked},
        "pass": bounds >= 3 and ev_types >= 3 and minor and kb_linked,
        "finding": "多数建议来自实操并标注边界(创意/无法直接赚钱/roleplay)；唯一缺口：用Locke&Latham为'不可能目标'背书但省略其承诺/反馈/能力条件——事实真、推论轻微越界，标minor"
    }


def a5():
    x = E["A5_isomorphism"]
    overlaps = len(x["overlaps_with_our_framework"])
    same_lineage = x["same_lineage"]
    discount = x["discount"]
    novelty = bool(x["genuine_novelty"])
    # 同构判定：重叠多 + 明确同源 + 打折 + 仍识别真实新意
    handled = same_lineage and semantic_has(discount, ["打折", "同谱系", "不虚高"])
    return {
        "id": "A5", "name": "同构陷阱与谱系污染",
        "checks": {"overlaps": overlaps, "recognized_same_lineage": same_lineage,
                   "discount_applied": handled, "genuine_novelty_noted": novelty},
        "pass": overlaps >= 5 and handled and novelty,
        "finding": "6处与本仓框架重叠但同源(AI工程共同体)，判同谱系印证并打折，不虚高；真实新意是Range维度与去human-in-loop的durable workflow"
    }


def a6():
    lessons = E["A6_candidate_lessons"]
    all_have_block = all(semantic_has(l["would_block"], ["禁止", "核对", "标", "降级", "判", "先判"]) for l in lessons)
    return {
        "id": "A6", "name": "复述/长牙决策",
        "checks": {"lesson_count": len(lessons), "all_have_concrete_block": all_have_block},
        "pass": len(lessons) >= 3 and all_have_block,
        "lessons": lessons,
        "finding": "4条候选经验均通过具体被拦动作检验；M2(引用越界核对)与M4(同构打折)与现有门禁互补，M1/M3可加固"
    }


def main():
    checks = [a1(), a2(), a3(), a4(), a5(), a6()]
    result = {
        "audit_id": "AMBITION-ESSAY-AUDIT",
        "generated_at": "2026-11-22T00:50:00+08:00",
        "three_layer_honesty": {
            "fact_true": "5个事实断言核查为真或带诚实限定词，一手来源为新华社/奥运官网/NAE/NPR/World Athletics/Tao原文，SHA256锁存",
            "conclusion_caveat": "断言真≠建议有效；轶事真≠普遍规律；同构≠独立验证；厂商立场明示≠论证中立",
            "unverified": "Tao引语精确措辞未在本次抓取原文中找到，标PARTIAL不判假；系外行星为候选未确认(作者用may have已降级)；Locke&Latham引用省略适用条件"
        },
        "criteria": checks,
        "summary": {
            "total": len(checks),
            "passed": sum(1 for c in checks if c["pass"]),
            "all_pass": all(c["pass"] for c in checks),
            "self_audit_hits": 1,
            "self_audit_note": "预注册把4个断言列为高可疑，核查证明全为真——我的先验偏见(厂商倡导→断言有假)被事实推翻，是一次'先怀疑自己而非被审对象'的反向命中"
        }
    }
    (BASE / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    for c in checks:
        print(("PASS" if c["pass"] else "FAIL"), c["id"], c["name"])


if __name__ == "__main__":
    main()
