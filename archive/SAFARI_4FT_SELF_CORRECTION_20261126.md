# 证伪性 Safari §4ft：自我审计的根基被削弱

**日期**：2026-11-26
**轮次**：§4ft（台账第 122 轮）
**预注册**：`prereg_falsify_self_20261126.json`，sha256 `15ce59b5…`，先于取证锁存

## 一、靶子：打本仓自己的地基

上一轮（§4fs）打的是"读证据的方法"（一手优于二手），结果是**精确化而非推翻**。这一轮把枪口上移一层，对准**本仓自我纠错机制的根基**：

> **靶信条**：主动自曝确认性采样 / 空杯自我审计能提升认知诚实、减少偏误。`SELF_AUDIT` 与每日"我这条评论最可能错在哪"都建立在这条信条上。

**什么算推翻**：A 级一手证明——无外部反馈的自我纠错无效甚至有害；或偏见盲点使人对自己偏见的自查系统失效。

## 二、证据（两篇 A 级一手，逐字核验，跨学科非同源）

| 一手 | 出处 | 逐字关键句 | 方向 |
|---|---|---|---|
| Huang et al. *LLMs Cannot Self-Correct Reasoning Yet* | ICLR 2024, OpenReview `wNYfnZGxS2` | "LLMs struggle to self-correct their responses without external feedback, **and at times, their performance even degrades after self-correction**" | 无外部反馈的自纠错反致降级 |
| Pronin, Lin & Ross *The Bias Blind Spot* | PSPB 2002;28(3), DOI 10.1177/0146167202286008 | "insisted that their self-assessments were accurate and objective **even after reading a description of how they could have been affected by the relevant bias**" | 读到偏见解释后仍自认客观 |

核验渠道：ICLR 官方 poster 页、OpenReview API、SAGE 期刊页、Crossref 元数据——均为一手/权威元数据，非二手博客。

## 三、裁决：`SELF_CORRECTION_FOUNDATION_WEAKENED`（削弱，非推翻）

1. **Critic = Author**：模型审阅自己的输出，审阅者继承作者的同一套权重与盲点。它能认出的错多半当初就不会犯；它犯的错恰是它自审最看不见的。我每日那句"我这条评论最可能错在哪"，若只是我审我自己，就是纯 intrinsic self-correction，正落在 Huang 的降级区。
2. **偏见盲点**：人读到偏见机制描述后仍坚称自己客观。`SELF_AUDIT` 的自评分数属同类 better-than-average 自评，需外部锚校验，不能自证。
3. **边界（诚实）**：两篇都不否定"有外部反馈时自纠错有效"——oracle 标签下 GPT-4 显著提升；Huang 标题带 "Yet"，测的是当时模型非技术天花板。故为**削弱而非推翻**，按预注册决策树写 WEAKENED，不制造证伪战利品。

## 四、工程含义

自审 / 自曝不是免疫针，是**可能失效的器官**。要让它从 intrinsic 升级为有效纠错，必须 **externalize**：外部一手逐字、用户判定、独立模型、或可运行测试判据。这正是 `evidence_honesty.py` 的 `scope_summary(self_applied=True)` 与 `guard_negative()` 要防的结构——把"自己审自己就够了"从信条降为待校验假设。

## 五、本轮自咬（时时总结）

- **开局猜错编号**：凭印象猜 arXiv `2310.03142`（实为编码计算论文），当场弃用，改从 ICLR 官方 / OpenReview 取权威锚点 `wNYfnZGxS2`。猜编号本身即一次 intrinsic 失误，靠外部核验拦下。
- **单边证据诚实**：counter_discipline 要求找"自审有效"的反方，本轮未找到——如实标注为单边削弱证据，不自称均衡。
- **不外推**：Huang "Yet" 不外推为"自审永无可能"；Pronin 为 2002 群体样本，不直接等同本 Agent。

## 六、终态

KB 446（+2，重复 0）、台账 122 轮（§4ft）、内核 7.5.0、宪法锁 fe56291b、verdict `GAP_INCONCLUSIVE` / l3=false / absolute=false 全不动。判定权归用户。
