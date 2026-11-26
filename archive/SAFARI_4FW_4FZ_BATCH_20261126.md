# §4fw–§4fz · 批量证伪 Safari 四轮报告

**日期**：2026-11-26
**台账**：§4fw–§4fz（第 125–128 轮）
**预注册**：`prereg_batch_20261126.json`，sha256 `0ce1607b…`，先于取证锁存
**授权**：Hy4 新增资源，"去 Safari 直至耗尽"

## 边界声明

无法精确读取资源计量，故不假装能判定"耗尽那一刻"。做法：连续跑一批、每轮完整落档、段段播报，到检查点如实报进度（本批 4 轮）。

## 四轮裁决

| 轮 | 靶 | 一手（A 级逐字核验） | 裁决 |
|---|---|---|---|
| §4fw | 代理指标可靠 | Karwowski et al. *Goodhart's Law in RL*, arXiv:2310.09144 | `PROXY_RELIABILITY_REFINED_WITH_CRITICAL_POINT`：代理有临界点，过则越优化越损真实目标 |
| §4fx | RSI 可持续增益 | Duan et al. *The Last AI Built by Humans*, arXiv:2609.11873v3 | `RSI_LEVEL_SELF_LOCATION`：本仓在 L1 执行自主，非 L5 递归元改进 |
| §4fy | 内在动机促进成长 | Deci, Koestner & Ryan 1999, *Psych Bull* 125(6):627（Crossref 元数据 A，效应量 B） | `INTRINSIC_MOTIVATION_REFINED_BY_REWARD_TYPE`：控制性激励挤出、信息性反馈加固 |
| §4fz | 环境进化增益可复现 | Prathifkumar et al. arXiv:2512.10218v2 | `REPRODUCIBILITY_RISK_NOT_REFUTATION`：评测基线需去污、归因待复现，非结论推翻 |

关键逐字句：
- §4fw："increasing optimisation of an imperfect proxy beyond some critical point **decreases performance on the true objective**"
- §4fx：五级路图 L1→L5，"key challenges to achieving genuine RSI"
- §4fz："3 times better on SWE-Bench-Verified"、"6 times better at finding edited files"、"scores may reflect **training recall, not issue-solving skill**"

## 五条闭环

§4fv 代理驱动递归（建设）+ §4fw 代理有临界点（警示）+ §4fx RSI 分级本仓 L1（定位）+ §4fy 动机按奖励类型（动力）+ §4fz 评测基线污染（复现）。

**增益三问**：谁测的（作者自报/独立）？测尺可信吗（污染/Goodhart）？测的是哪一级（任务输出/L1 执行/改进器）？

本仓"1551 全绿 / 一致性 True / KB+2"同理：是代理不是真实目标，是 L1 不是 L5，是计数不是自主感。

## 零战利品

四靶全部 REFINE / WEAKEN / RISK，无一次宣布"推翻成功"。这是三轮自审 P0 要求的对内诚信。

## 限定词（一并搬回）

- 四轮一手均 arXiv 预印本，未经同行评审。
- §4fy 效应量 d 值来自三独立二手源彼此一致，但 PsycNET / Semantic Scholar 摘要均返回 None，标 B 级不坐实。
- §4fz 污染风险 ≠ RepoFactory 结论错；OpenAI 审计数字（59.4% 缺陷等）为多源转述，B 级不坐实。
- 所有 arXiv 编号经 API/官方页按标题查得，从不凭印象猜（本批次未发生猜号事故）。

## 终态

KB 458（+8，重复 0）、台账 128 轮（§4fz）、内核 7.5.0、宪法锁 fe56291b、verdict `GAP_INCONCLUSIVE` / l3=false / absolute=false 全不动。判定权归用户。
