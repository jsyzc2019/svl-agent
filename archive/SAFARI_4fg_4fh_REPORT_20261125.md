# Safari 阶段战利品报告 · §4fg–§4fh（2026-11-25）

> 用户令："继续" → 本批聚焦「多重判据下的通过态稳定性」——发表偏倚检验分歧、多重性未校正。均 A 级一手、PubMed E-utilities 逐字核验。

## 一、本批战利品（两篇配对）

| 轮次 | 主题 | 一手来源 | 逐字锚点（摘要原文） | 镜像本仓 |
|---|---|---|---|---|
| §4fg | 发表偏倚检验分歧 | Papageorgiou et al. 2015, J Evid Based Dent Pract, PMID 25666576（一手 A 级实证，46 MA / 882 研究） | 「confirmed by Begg-Mazumdar's test in 18% and by Egger's test in 33% of the MAs」；「According to Rosenthal's criterion, 80% of the MAs were robust, while adjusted effects with unpublished studies differed from little to great」 | 同一「稳健/通过」态随检验翻转；多数未充分评估偏倚；纳入被排除项须做敏感性 |
| §4fh | 多重性未校正 | Remy et al. 2026, Fundam Clin Pharmacol, PMID 43023449（一手 A 级 meta-流行病学，93 MA） | 「the median nominal family-wise type I error probability was 40%, and only 2.2% of MAs reported alpha-risk management」；「Spin was present in 30.1% of conclusions」；关键「this estimate is a theoretical indicator and not the probability that a published conclusion is false」 | 不控多重性则「至少一个通过」几乎必然；须区分理论暴露与具体结论真假；结论措辞须与证据匹配 |

## 二、照见自身（判定红线）

1. **通过态的判据依赖性**：§4fg 同一批数据，Begg 18%、Egger 33%、Rosenthal 80% 稳健——本仓 verdict 须显式声明用哪个判据，并报多判据分歧谱，不可只报单一「通过」。
2. **程序充分性先于结论标签**：「Only a few MAs adequately assessed」——本仓「通过」态须先审判定程序是否充分执行。
3. **纳入被排除项的敏感性**：「differed from little to great」——须做「若纳入被排除项结论如何变」的敏感性分析。
4. **理论暴露 ≠ 结论为假**：§4fh 作者主动声明 40% 是理论指标、不是已发表结论为假的概率——本仓须区分「结构性假阳性暴露」与「本结论为假的证据」，不可混同；40% 为该领域特定估计，不搬来当本仓错误率。
5. **预注册方向与单一主目标**：26.9% 预注册、14% 方向性假设、5.4% 兼具——判定须预先声明，不可事后挑；30.1% 结论 spin——措辞须与证据强度匹配。

## 三、诚信现场复现

- 可选停止（data peeking）、「指标变目标」检索均零结果，如实弃用，不硬凑。
- §4fg 五检验并列、§4fh 作者主动降调，均逐字照录；数字全取一手摘要，不用二手转述。
- §4fh 的 40% 明确标注为「特定领域理论估计」，如实不搬用。

## 四、验证（全绿）

```
一致性 True | failed=[] | handoff 421 = truth 421
内核 7.5.0 | KB 421（重复 0，KB-AUDIT182 / KB-META147）| 宪法锁 fe56291b | 台账 110 末 §4fh
全量 1551 fail=0 err=0 | 内核专项 122 fail=0 err=0
verdict GAP_INCONCLUSIVE | l3=false | absolute=false | Ambient=0
```

## 五、边界

判定权归用户；内核 L0 不联网不 spawn；未编译新门禁；未动宪法/判定/十案/§100。外部一手仅作哲学镜像，不宣称本仓有同样发表偏倚/多重性结构。
