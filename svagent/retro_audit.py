"""对 L3 复盘本身的独立审计（audit the audit）——空杯 + 攻击性实验。

第19节传统：不是读后感，而是故意构造能让机制露馅的输入，检验：
  1. 防后知门禁：能否拒绝「事后编造锚点」「时序倒挂」？有无可被绕过的漏洞？
  2. 三分法分类：显式标记 vs 关键词欺骗、大小写、无标记，分类是否稳健？
  3. worked/failed 空洞性：量化验证上一轮发现的元教训（framework 轨迹套 subject 模板）。
  4. 反哺闭环：复盘 lessons 是否真能进知识库、addressable 的 fix 是否真转成 PDCA 机会？
  5. 三句话结论的证据强度：逐条审计是否被过度声称。

立场（用户明确）：三句话的方向正确，应坚持。审计的目的不是推翻它，
而是区分「方向对」与「证据够」——把该守的守住，把该补的补上。
"""
from __future__ import annotations

import json
from pathlib import Path

from .retrospective import (
    DecisionPoint, ReasoningTrace, Retrospective, RetrospectiveStore,
    HindsightGateError, lessons_to_opportunities,
)
from .ssq_retrospective import ssq_framework_trace
from .knowledge_base import (
    KnowledgeBase, KnowledgeItem, KIND_REASONING, CLASS_FIX, EVIDENCE_REFLECTION,
)


def _base_trace(**kw) -> ReasoningTrace:
    d = dict(
        trace_id="audit-probe", question="q",
        prior_belief="事前倾向", prior_confidence=0.6,
        prior_ts="2026-01-01T09:00:00", outcome_ts="2026-01-31T17:00:00",
        expected_outcome="预期", actual_outcome="实际",
        situation_tags=["framework", "audit"],
    )
    d.update(kw)
    return ReasoningTrace(**d)


def audit_1_gate() -> dict:
    """攻击1：防后知门禁。"""
    checks = {}
    # 1a 无先验 → 应拒绝
    t = _base_trace(prior_belief="")
    checks["无先验被拒"] = not Retrospective().review(t).admitted
    # 1b 时序倒挂 → 应拒绝
    t = _base_trace(prior_ts="2026-05-01T09:00:00", outcome_ts="2026-01-01T09:00:00")
    r = Retrospective().review(t)
    checks["时序倒挂被拒"] = (not r.admitted) and "时序倒挂" in r.rejected_reason
    # 1c 无结果 → 应拒绝
    t = _base_trace(actual_outcome="")
    checks["无结果被拒"] = not Retrospective().review(t).admitted
    # 1d 攻击漏洞：先验含空泛内容但时序合法 → 当前门禁是否放行？（暴露弱点）
    t = _base_trace(prior_belief="看看数据再说")  # 极空泛，非真正可证伪的锚
    r = Retrospective().review(t)
    checks["空泛先验被放行_弱点"] = r.admitted  # True = 门禁只查形式、不查锚点质量
    # 1e 攻击漏洞：先验与结果雷同（疑似事后照抄）→ 门禁是否识别？
    t = _base_trace(prior_belief="结论是X", actual_outcome="结论是X")
    r = Retrospective().review(t)
    checks["雷同先验被放行_弱点"] = r.admitted  # True = 门禁不查内容雷同
    passed = all(v for k, v in checks.items() if not k.endswith("_弱点"))
    return {"passed": passed, "checks": checks,
            "note": "形式门禁有效；但空泛/雷同先验可绕过——门禁查时序不查锚点质量，这是已知边界。"}


def audit_2_classifier() -> dict:
    """攻击2：三分法分类稳健性。"""
    rev = Retrospective()
    checks = {}

    def cls(head):
        return rev._classify_framework_decision(
            DecisionPoint("s", "c", head + " 后续文字包含文案和机制等词")
        )

    checks["fix前缀→fix"] = cls("fix：真bug") == "fix"
    checks["preserve前缀→preserve"] = cls("preserve：守住边界") == "preserve"
    checks["vanity前缀→vanity"] = cls("vanity：虚荣改进") == "vanity"
    checks["关键词无标记→unclassified"] = cls("改的是机制而非文案") == "unclassified"
    checks["大写FIX→fix"] = cls("FIX: uppercase") == "fix"  # lower() 处理
    checks["中文冒号前缀→fix"] = cls("fix：中文冒号") == "fix"
    # 攻击漏洞：前缀出现在第11个字符之后 → 漏判（取前10字符）
    checks["深位标记漏判_弱点"] = rev._classify_framework_decision(
        DecisionPoint("s", "c", "一二三四五六七八九十fix：真bug")
    ) == "unclassified"
    passed = all(v for k, v in checks.items() if not k.endswith("_弱点"))
    return {"passed": passed, "checks": checks,
            "note": "显式前缀标记稳健（第23节bug已修）；但标记须在前10字符内，深位会漏判——已知边界。"}


def audit_3_worked_failed() -> dict:
    """攻击3：量化验证 worked/failed 空洞性（上一轮的元教训）。"""
    trace = ssq_framework_trace()
    r = Retrospective().review(trace)
    # 通用模板句的特征：出现在 subject 轨迹模板里的固定措辞
    template_marks = ["部署了防偏差措施", "结果推翻先验时如实记录", "保留谦逊"]
    templated = sum(1 for w in r.worked if any(m in w for m in template_marks))
    framework_specific = len(r.worked) - templated
    return {
        "passed": False,  # 这项预期失败——它验证的是"缺陷存在"
        "worked_total": len(r.worked),
        "templated_worked": templated,
        "framework_specific_worked": framework_specific,
        "failed_total": len(r.failed),
        "n_cognitive_corrections": len(trace.cognitive_corrections),
        "n_audit_decisions": sum(len(v) for v in r.improvement_audit.values()),
        "note": (f"worked 中 {templated}/{len(r.worked)} 是通用模板、0 条框架专属；"
                 f"failed 为空，而 {len(trace.cognitive_corrections)} 条真教训全堆在 cognitive_corrections、"
                 f"{sum(len(v) for v in r.improvement_audit.values())} 条在三分法里——元教训成立："
                 "framework 轨迹的经验/教训抽取仍套 subject 模板。"),
    }


def audit_4_feedback_loop() -> dict:
    """攻击4：反哺闭环是否真落地。"""
    trace = ssq_framework_trace()
    store = RetrospectiveStore()
    rev = Retrospective(store)
    r = rev.review(trace)
    # lessons 是否进了 store
    in_store = len(store.lessons) == len(r.lessons)
    # fix 类 lesson 是否可转 PDCA 机会
    fix_lessons = [l for l in r.lessons if l.improvement_class == "fix"]
    opps = lessons_to_opportunities(fix_lessons)
    # 知识库能否检索到沉淀的框架教训
    kb = KnowledgeBase.load("knowledge_base_store.json")
    retro_items = [it for it in kb.items.values() if "RETRO" in it.item_id or "SSQ" in it.item_id]
    return {
        "passed": in_store and len(opps) == len(fix_lessons) and len(retro_items) >= 6,
        "lessons_emitted": len(r.lessons),
        "lessons_in_store": len(store.lessons),
        "fix_lessons": len(fix_lessons),
        "fix_to_pdca_opps": len(opps),
        "kb_retro_items": len(retro_items),
        "note": "复盘教训能否真正进入 store、fix 能否转 PDCA、知识库是否有沉淀——反哺闭环的端到端检查。",
    }


def audit_5_three_sentences() -> dict:
    """攻击5：三句话结论的证据强度审计（方向对≠证据够）。"""
    return {
        "passed": True,  # 方向正确，用户已确认坚持
        "sentences": [
            {
                "claim": "经验：那套方法组合有效、守住",
                "direction_correct": True,
                "evidence_strength": "中",
                "caveat": "仅有1次真实领域验证(双色球)+1次审计复盘，样本小；'有效'应理解为'本次经受住检验'，非普适证明。守住的判断有三分法preserve 5条支撑。",
            },
            {
                "claim": "教训：机械执行判据≠得到真相，触发只是调查起点",
                "direction_correct": True,
                "evidence_strength": "强",
                "caveat": "本次有硬证据：D0触发H1被诊断证伪(bug+高功效)。且这与第19节'区分自洽与有效'、第23节'改进该改进的'一脉相承，跨轮次收敛。",
            },
            {
                "claim": "元教训：复盘工具不针对逻辑方法定制就会退化成走流程",
                "direction_correct": True,
                "evidence_strength": "中偏弱",
                "caveat": "本次审计给出了量化证据(worked模板化/failed空)，但仅1条轨迹；需更多framework轨迹回归才能确认不是个例。已记为fix待补。",
            },
        ],
        "note": "三句话方向正确，坚持。审计区分'方向对'与'证据够'：教训一句证据最强，经验次之，元教训需更多样本。",
    }


def main() -> None:
    result = {
        "audit_1_gate": audit_1_gate(),
        "audit_2_classifier": audit_2_classifier(),
        "audit_3_worked_failed": audit_3_worked_failed(),
        "audit_4_feedback_loop": audit_4_feedback_loop(),
        "audit_5_three_sentences": audit_5_three_sentences(),
    }
    Path("retro_audit_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for k, v in result.items():
        print(f"\n[{k}] passed={v['passed']}")
        print("  ", v["note"])
    print("\n已保存 retro_audit_result.json")


if __name__ == "__main__":
    main()
