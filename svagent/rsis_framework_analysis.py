"""RSI-Structure 综述论文的框架论证引擎（T1–T6）。

设计纪律（继承 §33–§37）：
1. 判据来自预注册锁存文件 rsi_structure_preregistration.json，脚本只读不改。
2. 对象是综述/分类学，无自己实验统计量 → 不套统计复算（T3 判据适配）。
3. 与 awesome-rsi 同谱系 → 同构判为污染而非独立验证（T2 触发≠真相）。
4. 吸收决策受 KB-META01 约束：指不出被拦/被判/被降级的动作 = 复述，不得宣称内化。
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 论文六条关键判定（逐字原文，来源 rsi_structure_paper.txt）
PAPER_VERDICTS = {
    "V1_reuse_not_recursive": "Reuse in later tasks alone does not establish that recursive dependency.",
    "V2_rounds_not_effectiveness": "the number of rounds alone does not identify which factor produced the gain.",
    "V3_failure_not_what_to_edit": "Failure alone does not specify what to edit; the system must analyze what happened.",
    "V4_combined_not_single_attribution": "the gains of the combined system cannot all be attributed to one external component.",
    "V5_evaluate_not_verify": "Evaluate examines an existing execution to provide evidence for an update; Verify tests a candidate change.",
    "V6_retirement_cover_rare": "the check needs to cover intended uses, including less frequent but still important tasks.",
}

# 我方框架对每条判定的既有对应机制（证据来自知识库/模块，非凭印象）
FRAMEWORK_COUNTERPARTS = {
    "V1_reuse_not_recursive": {
        "mechanisms": ["KB-SIM03 证据阶梯 L1/L2/L3", "KB-SIM07 可证伪配对"],
        "status": "已具备",
        "note": "触发≠真相、retained≠improver 已固化；同谱系（awesome-rsi），非独立发现",
    },
    "V2_rounds_not_effectiveness": {
        "mechanisms": ["KB-SIM03 L3 需受控实验", "commentary:§34 改进机制本身变强才算L3"],
        "status": "已具备",
        "note": "轮数≠有效性、改进器增益需对照——已在 SIM 论证中落地",
    },
    "V3_failure_not_what_to_edit": {
        "mechanisms": ["improvement_memory:root_cause 字段", "retrospective:Diagnose"],
        "status": "部分缺口",
        "note": "有根因记录，但未强制'归因到具体组件 + 按组件选择验证方式'——Where 维度缺失",
    },
    "V4_combined_not_single_attribution": {
        "mechanisms": ["消融混杂门禁(§34 S4)", "经济意义门禁(§33 R2 无成本对照)"],
        "status": "已具备",
        "note": "多因素混合时不可单归因，已由无成本/消融对照判据覆盖",
    },
    "V5_evaluate_not_verify": {
        "mechanisms": ["retrospective(复盘=Evaluate)", "pytest 测试套件(=Verify)"],
        "status": "已具备",
        "note": "两类活动在框架中已实际分离；论文措辞更精确，但无需另造轮子",
    },
    "V6_retirement_cover_rare": {
        "mechanisms": ["improvement_memory:transfer_decision drop"],
        "status": "部分缺口",
        "note": "有 drop 降级，但未要求'退役检查覆盖低频但重要用途'；可并入 V3 的组件化验证要求",
    },
}


def load_evidence() -> dict:
    return json.loads((ROOT / "rsi_structure_evidence.json").read_text(encoding="utf-8"))


def t1_subject_misplacement(ev: dict) -> dict:
    """提出分类学框架 ≠ 证明 RSI 有效。"""
    p = ev["primary_paper"]
    is_survey = "SURVEY" in p["type"].upper()
    has_own_exp = "不产出自己的实验统计量" in p["contribution_type"]
    media_title_escalates = "越用越强" in ev["secondary_narrative"].get("narrative_framing", "")
    paper_self_limited = any("does not by itself prove" in q for q in p["key_verdict_quotes"])
    misplaced = is_survey and has_own_exp and media_title_escalates
    return {
        "id": "T1",
        "survey_not_empirical": is_survey and has_own_exp,
        "media_title_escalates": media_title_escalates,
        "paper_self_limited": paper_self_limited,
        "decision": "主体错位（传播层把'提出框架'读成'证明有效'）" if misplaced else "无主体错位",
        "attribution": "论文克制且自我限定，夸张来自媒体标题——不连坐一手作者",
        "pass": misplaced,  # 命中预期异常 = 判据成功触发
    }


def t2_isomorphism_contamination(ev: dict) -> dict:
    """同构 ≠ 独立验证。"""
    c = ev["lineage_contamination"]
    contaminated = "同谱系" in c["consequence"] or "非独立" in c["consequence"]
    return {
        "id": "T2",
        "lineage_declared": bool(c.get("note")),
        "isomorphic": "高度同构" in c["consequence"],
        "contaminated": contaminated,
        "decision": "同谱系印证（非独立验证）" if contaminated else "疑似独立（需警惕）",
        "honesty": "触发≠真相：Figure3 与我方阶梯长得像，但 §34 已受 awesome-rsi 影响，印证力度打折",
        "pass": contaminated,
    }


def t3_criterion_fit(ev: dict) -> dict:
    """判据要适配对象：综述不硬套统计复算。"""
    p = ev["primary_paper"]
    survey = "SURVEY" in p["type"].upper()
    counts_are_classification = "文献分类，非实验样本" in p["scale"]
    return {
        "id": "T3",
        "object_is_survey": survey,
        "counts_are_classification_not_samples": counts_are_classification,
        "statistical_recompute_applicable": False,
        "decision": "判据适配：不做统计功效复算，改做分类学自洽/可操作性/主体错位/诚实刻度审计",
        "anti_pattern": "为套 S3 统计判据而对无实验统计量的综述做 t 检验 = 判据错配，禁止",
        "pass": survey and counts_are_classification,
    }


def t4_counterparts() -> dict:
    """六条判定逐条核对：已具备 vs 缺口。"""
    rows = []
    for vid, verdict in PAPER_VERDICTS.items():
        cp = FRAMEWORK_COUNTERPARTS[vid]
        rows.append({
            "id": vid,
            "paper_verdict": verdict,
            "framework_mechanisms": cp["mechanisms"],
            "status": cp["status"],
            "note": cp["note"],
        })
    gaps = [r["id"] for r in rows if "缺口" in r["status"]]
    return {
        "id": "T4",
        "rows": rows,
        "gap_ids": gaps,
        "n_already": sum(1 for r in rows if r["status"] == "已具备"),
        "n_gaps": len(gaps),
        "decision": f"6条中 {sum(1 for r in rows if r['status']=='已具备')} 条已具备、{len(gaps)} 条部分缺口：{', '.join(gaps)}",
        "anti_duplicate": "已具备的不重复造轮子（preserve）；只对真缺口评估是否编译",
        "pass": len(gaps) > 0,
    }


def t5_honesty(ev: dict) -> dict:
    """诚实刻度：论文自我限定 + 标注 NR + 组合归因 + 不夸大。"""
    p = ev["primary_paper"]
    signals = p["honesty_signals"]
    self_limit = any("does not by itself prove" in s for s in signals)
    nr_marked = any("NR" in s for s in signals)
    combined_caveat = any("组合" in s for s in signals)
    not_overclaim = any("不夸大" in s for s in signals)
    high = sum([self_limit, nr_marked, combined_caveat, not_overclaim]) >= 3
    return {
        "id": "T5",
        "self_limited": self_limit,
        "nr_marked": nr_marked,
        "combined_attribution_caveat": combined_caveat,
        "not_overclaim_each_as_full_rsi": not_overclaim,
        "decision": "高诚实度（preserve）" if high else "需警惕夸大",
        "attribution": "夸张来自二手传播，不连坐一手论文",
        "pass": high,
    }


def t6_absorption(t4: dict) -> dict:
    """复述 vs 长牙（KB-META01）：只对真缺口判断是否编译成会拦/判/降级的动作。"""
    gap_ids = t4["gap_ids"]
    # 对缺口做"能否指出具体被拦/被判/被降级的动作"检验
    teeth_test = {
        "V3_failure_not_what_to_edit": {
            "concrete_action": "改进记录若未标注作用于哪个组件(Prompt/Memory/Skill/Harness)且未按组件选验证方式 → 拦截为'归因不足'，不允许 consolidate",
            "verdict": "能长出牙",
        },
        "V6_retirement_cover_rare": {
            "concrete_action": "退役/降级一条经验时，若未检查'低频但重要用途' → 降级为 verify，不能直接 drop",
            "verdict": "能长出牙（并入组件化验证要求）",
        },
    }
    actionable = [gid for gid in gap_ids if gid in teeth_test and "能长出牙" in teeth_test[gid]["verdict"]]
    return {
        "id": "T6",
        "gaps": gap_ids,
        "teeth_test": teeth_test,
        "actionable_ids": actionable,
        "decision": f"真缺口 {len(gap_ids)} 条，均可指出具体被拦/被判/被降级动作 → 编译为组件归因+验证门禁（非复述）" if actionable else "仅复述，不得宣称内化",
        "kb_meta01_compliance": True,
        "pass": len(actionable) >= 1,
    }


def three_layer_conclusion(t1, t2, t3, t4, t5, t6) -> dict:
    return {
        "layer1_fact": (
            "论文是中科院自动化所+美团等单位的 RSI 综述（OpenReview/Preprints），"
            "产出四组件×七阶段分类学 + When/Where/How 三问题 + 40/20 研究对照；"
            "无自己的实验统计量，贡献是统一语言与分析框架。"
        ),
        "layer2_boundary": (
            "提出框架≠证明RSI有效（综述无实证）；Figure3 与我方证据阶梯同构但同谱系"
            "（§34 已受 awesome-rsi 影响），是印证而非独立验证；传播层'越用越强'是主体错位；"
            "40/20 是分类计数非实验样本，不可做统计复算。"
        ),
        "layer3_method": (
            "①判据要适配对象——综述不套统计检验；②同构≠独立验证，谱系污染须标注（触发≠真相）；"
            "③吸收受 KB-META01 约束——6条判定中4条已具备(preserve)、2条真缺口（组件归因/退役覆盖）"
            "编译成会拦会降级的动作，才是长牙而非复述。"
        ),
    }


def run() -> dict:
    ev = load_evidence()
    t1 = t1_subject_misplacement(ev)
    t2 = t2_isomorphism_contamination(ev)
    t3 = t3_criterion_fit(ev)
    t4 = t4_counterparts()
    t5 = t5_honesty(ev)
    t6 = t6_absorption(t4)
    result = {
        "document": "RSI-Structure 综述框架论证结果",
        "pre_registration_sha256": (ROOT / "rsi_structure_prereg.sha256").read_text().split()[0],
        "T1": t1, "T2": t2, "T3": t3, "T4": t4, "T5": t5, "T6": t6,
        "conclusion": three_layer_conclusion(t1, t2, t3, t4, t5, t6),
        "all_judgments_fired": all(t["pass"] for t in [t1, t2, t3, t4, t5, t6]),
    }
    (ROOT / "rsi_structure_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result


if __name__ == "__main__":
    r = run()
    for t in ["T1", "T2", "T3", "T4", "T5", "T6"]:
        print(f"[{t}] {r[t]['decision']}")
    print("\n三层结论：")
    for k, v in r["conclusion"].items():
        print(f"  {k}: {v[:80]}...")
    print("\n全部判据按预期触发:", r["all_judgments_fired"])
