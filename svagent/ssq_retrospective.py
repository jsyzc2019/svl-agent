"""第25节双色球推演的 L3 框架自我反省（scope=framework）。

只审逻辑方法，不审双色球结论。事前锚点是可追溯的真实时间戳：
ssq_preregistration.json 在 2026-11-21T12:55:01 CST 锁存（SHA256 acf5ab5d…），
早于揭盲与诊断。每条方法决策带显式三分标记，避免事后主观改写分类。
"""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from .retrospective import (
    DecisionPoint, ReasoningTrace, Retrospective, RetrospectiveStore,
    report_framework_reflection,
)


def ssq_framework_trace() -> ReasoningTrace:
    return ReasoningTrace(
        trace_id="ssq-validation-2026",
        scope="framework",
        question="这套方法论在双色球随机性检验推演中，逻辑方法上有何经验与教训？",
        # 事前锚点：预注册文件里锁存的方法信念（有时间戳+哈希，早于揭盲）
        prior_belief=(
            "我在预注册里锁存了判据/阈值/种子，预期 D0 盲测能给出可靠二选一判定；"
            "事前倾向认为红球频率分位若极端(0.995)就支持人为调节方向"
        ),
        prior_confidence=0.7,  # 保留谦逊：预注册写了诚实边界，未锁死结论
        prior_ts="2026-11-21T12:55:01",   # 预注册 SHA256 锁存时刻
        outcome_ts="2026-11-21T13:12:00",  # 诊断+E0 完成、准备复盘时刻（晚于先验）
        situation_tags=[
            "framework", "self_reflection", "validation", "statistical_test",
            "anti_bias", "blind_test", "hindsight_risk", "large_sample",
        ],
        expected_outcome="预注册判据机械执行 → 得到可靠的随机/非随机判定",
        actual_outcome=(
            "D0 把真实序列排到 201/201 触发 H1，但诊断证伪了它："
            "卡方未归一 bug 把统计量虚高到 88257；修正后红球 p=0.052、蓝球 p=0.88；"
            "分位极端却效应量微小(0.89个百分点)——大样本高功效陷阱；"
            "零分布套教科书 χ² 但数据是无放回抽样；三区/奇偶 p<0.05 是多重比较假象；"
            "E0 可预测性终检 p=0.50/0.66 无任何预测力。机械执行判据 ≠ 得到真相。"
        ),
        cognitive_corrections=[
            "把'判据触发H1'当成了结论——触发只是调查起点，不是终点",
            "卡方期望概率用未归一6/33，实现bug差点直接支撑结论——判据缺少实现自检",
            "高功效陷阱：n=3530下0.89个百分点偏离也能判分位0.99，统计显著≠实际显著",
            "零分布用教科书χ²但数据无放回抽样——零分布必须匹配抽样机制",
            "代理变量混淆：分布不均匀≠人为调节，物理偏差/随机漂移都能造成",
            "三区p=0.023、奇偶p=0.033是多重比较假象——做了几十个检验，裸p必然<0.05",
        ],
        anti_bias_measures=[
            "预注册判据+SHA256哈希锁存", "真随机对照盲测(D0)",
            "时间序列留出集(E0)", "诊断性消融(非新检验)", "效应量报告",
        ],
        decisions=[
            DecisionPoint(
                "检验开始前锁定判据/阈值/种子并哈希存证",
                "先写判据再揭盲，拒绝事后调阈值",
                "preserve：这是防后知先觉的脊梁，守住了才能声称结论独立；事后改判据是绝对禁区",
                "看完数据再定判据，反正结果更漂亮",
            ),
            DecisionPoint(
                "如何区分'随机正常涨落'与'真实偏离'",
                "生成200条同机制伪随机，把真实序列放进分布看是否离群",
                "preserve：对照盲测是防聚类错觉/赌徒谬误的核心设计，被证明有效，守住",
                "直接看频率直观看是否均匀",
            ),
            DecisionPoint(
                "A1红球卡方统计量虚高到88257",
                "诊断出期望概率用了未归一6/33，修正为标准卡方",
                "fix：可被客观证伪的实现bug。改机制——增加'判据实现自检'：期望概率必须归一、量级须sanity check",
                "把异常量级当成'强烈偏离证据'写进结论",
            ),
            DecisionPoint(
                "D0分位0.995极端，但效应量仅0.89个百分点",
                "引入效应量硬闸门：分位显著但效应量微小不得宣称实质偏离",
                "fix：判据只有p值/分位、缺效应量闸门，大样本下必然误报——这是判定机制的结构缺陷",
                "照搬'分位0.995=强证据'的叙事",
            ),
            DecisionPoint(
                "伪随机卡方均值26.8 ≠ 教科书χ²(32)",
                "改用同机制蒙特卡洛零分布，不套教科书分布",
                "fix：拟合优度零分布必须与抽样机制(无放回)一致，这是方法硬伤，改机制",
                "继续用教科书χ²查表",
            ),
            DecisionPoint(
                "三区p=0.023、奇偶p=0.033看似显著",
                "识别为多重比较假象，按预注册Bonferroni意识不采信裸p",
                "fix：几十个检验下裸p<0.05必然出现；预注册写了校正但执行时差点忘——把多重比较校正固化为默认闸门",
                "挑显著的p值写进结论",
            ),
            DecisionPoint(
                "D0排名201/201，机械触发H1，'发现猫腻的漂亮结论'很诱人",
                "拒绝直接宣布H1，坚持做诊断性拆解(查bug/看效应量/验时间稳定性)",
                "vanity：'判据触发+极端排名'是诱人的进步叙事，直接当结论就是拿机械输出冒充真相——识破它",
                "把201/201当惊人发现汇报",
            ),
            DecisionPoint(
                "如何判别'人为操纵'这种不可直接观测的机制",
                "用留出集预测回测E0：任何牟利操纵必留序列痕迹",
                "preserve：可预测性是操纵的最强可观测证据，方法有效，守住",
                "凭'号码看着不均匀'下判断",
            ),
            DecisionPoint(
                "判据输出与真相冲突时怎么办",
                "坚持'触发只是调查起点'，触发后必须诊断再定性",
                "preserve：这是'区分自洽与有效'的脊梁，不能被'机械执行判据'的自动化冲动吞掉",
                "判据说啥就是啥，自动化到底",
            ),
            DecisionPoint(
                "如何陈述最终结论的边界",
                "分'能说的/不能说的/方法反身'三层，明确'无法证明绝对随机'",
                "preserve：承认检验力边界、把'不知道'当一等公民，是框架脊梁，守住",
                "为了确定性宣称'已证明随机'",
            ),
        ],
    )


def main() -> None:
    trace = ssq_framework_trace()
    store = RetrospectiveStore()
    rev = Retrospective(store)
    outcome = rev.review(trace)
    if not outcome.admitted:
        print("门禁拒绝:", outcome.rejected_reason)
        return
    store.reviews.append(outcome)
    store.log_trace(trace)
    report_framework_reflection(outcome)

    # 把复盘产物落地
    payload = {
        "trace": asdict(trace),
        "outcome": asdict(outcome),
        "worked": outcome.worked,
        "failed": outcome.failed,
        "root_cause": outcome.root_cause,
        "improvement_audit": outcome.improvement_audit,
    }
    Path("ssq_retrospective_result.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    store.save("ssq_retrospective_store.json")
    print("\n\n== 经验(worked) ==")
    for w in outcome.worked:
        print("  +", w)
    print("\n== 教训(failed/根因) ==")
    for f in outcome.failed:
        print("  -", f)
    print("\n  根因:", outcome.root_cause)
    print("\n已保存 ssq_retrospective_result.json / ssq_retrospective_store.json")


if __name__ == "__main__":
    main()
