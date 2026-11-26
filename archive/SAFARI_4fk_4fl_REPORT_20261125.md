# Safari 阶段战利品报告 · §4fk–§4fl（2026-11-25）

> 用户令："继续" → 本批聚焦「分析口径冲突」与「测量噪声低估」——Lord 悖论、回归稀释偏倚。均 A 级一手、PubMed E-utilities 逐字核验。

## 一、本批战利品（两篇配对）

| 轮次 | 主题 | 一手来源 | 逐字锚点（摘要原文） | 镜像本仓 |
|---|---|---|---|---|
| §4fk | Lord 悖论 | Tu & Hodges 2026, Res Synth Methods, PMID 41626894（A 级一手方法学） | 「the t-test and analysis of covariance (ANCOVA) yield conflicting conclusions」；「the t-test compares the observed weight change, whereas ANCOVA compares an adjusted weight change」；「When these two models produce substantially different results, it may indicate a violation of the transitivity assumption」；「we should be cautious in interpreting the results from either model」 | 同一数据两种合理分析冲突；分歧本身是假设违背信号；两模型都不可独断 |
| §4fl | 回归稀释偏倚 | Masudi et al. 2015, J Res Health Sci, PMID 26175288（A 级一手实证，TLGS 队列 1167 男/1786 女） | 「Use of single measurement…distort their estimated effects, due to random error」；「26% and 25% underestimation in HR of SBP and 23% and 33% in HR of DBP」；「Using baseline measurements…underestimate its real association」 | 测量噪声系统低估效应；「未检出」未必真无；重复测量估噪校正；偏差跨层稳定 |

## 二、照见自身（判定红线）

1. **观察态 vs 调整态**：§4fk t-test（观察变化）vs ANCOVA（调整变化）对同一数据给出冲突结论——verdict 须显式声明用哪个判据，不可混用（§4eq、§4fc/fd、§4ff）。
2. **分歧即警报**：两模型结果显著不同「may indicate a violation of transitivity」——多判据冲突时不应选一个报，应回查假设（§4fg、§4fh）。
3. **两模型都谨慎**：「cautious in interpreting results from either model」——须并列呈现+声明各自假设，裁定权归用户（§4ch、§4er）。
4. **流行≠正确**：CBM 最流行但 BM 少用——不可因默认判据常用就免审（§4fh、§4fa）。
5. **系统低估**：§4fl 测量噪声使 SBP HR 低估 26%/25%、DBP 23%/33%、BMI 约 8%——「未检出/效应小」须怀疑是否被噪声压低（§4fj、§4fg、§4bn）。
6. **重复测量校正**：用三年间隔重复测量算 RDR 校正——须引入独立测量估计噪声幅度，不只报单次观测（§4fe、§4fh）。

## 三、诚信现场复现

- 信号检测论、Berkson 悖论检索零结果，如实弃用，不硬凑。
- §4fl RDR 具体数值为该队列特定，明确不搬到本仓当错误率；数字全取一手摘要逐字。

## 四、验证（全绿）

```
一致性 True | failed=[] | handoff 429 = truth 429
内核 7.5.0 | KB 429（重复 0，KB-AUDIT186 / KB-META151）| 宪法锁 fe56291b | 台账 114 末 §4fl
全量 1551 fail=0 err=0 | 内核专项 122 fail=0 err=0
verdict GAP_INCONCLUSIVE | l3=false | absolute=false | Ambient=0
```

## 五、边界

判定权归用户；内核 L0 不联网不 spawn；未编译新门禁；未动宪法/判定/十案/§100。外部一手仅作哲学镜像，不宣称本仓有同样 NMA 或测量误差结构。
