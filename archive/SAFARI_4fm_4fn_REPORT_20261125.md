# Safari 阶段战利品报告 · §4fm–§4fn（2026-11-25）

> 用户令："继续，但不要急，超点可接受" → 本批从容推进，聚焦「二分判据的语境边界」——连续变量二分化 vs 小试验问题，构成张力对。均 A 级一手、PubMed E-utilities 逐字核验。

## 一、本批战利品（张力对，并列不 selection）

| 轮次 | 主题 | 一手来源 | 逐字锚点（摘要原文） | 镜像本仓 |
|---|---|---|---|---|
| §4fm | 二分化连续变量 | Royston, Altman & Sauerbrei 2006, Stat Med, PMID 16217841（A 级一手方法学，PBC 试验案例） | 「The simplicity achieved is gained at a cost…considerable loss of power and residual confounding」；「a data-derived 'optimal' cutpoint leads to serious bias」；「should not be applied to explanatory variables in regression models」 | 把连续证据压成布尔通过态会丢信息、数据驱动阈值引入偏差、简化须记账 |
| §4fn | 二分禁令的边界 | Raymond et al. 2023, Trials, PMID 37349843（A 级一手方法学 + 五个 Cochrane 试验） | 「the admonition not to dichotomize…may not apply to…number of patients required」；「not a mean effect at the population level but…efficacy at the patient level」；「proportions of patients reaching a certain threshold is a more meaningful method」 | 判据形式须看语境不教条；群体均值≠逐患者有效；判据须对应决策单元 |

**张力对说明**：同为「是否该把连续量二分」——§4fm 在「回归解释变量」语境下说不该，§4fn 在「小试验样本量规划」语境下说阈值比例比较更有意义。两篇均在各自语境成立，如实并列，由用户按场景裁定，不 selection。

## 二、照见自身（判定红线）

1. **布尔化丢信息**：§4fm「loss of power and residual confounding」——把多维连续符合度压成单一布尔通过态会丢区分信息、留残余混淆（§4eq、§4dl、§4dp）。
2. **阈值不可事后优化**：「data-derived 'optimal' cutpoint leads to serious bias」——判据阈值不可从判定数据本身挑最优（§4ca、§4fh）。
3. **简化须记账**：「simplicity achieved is gained at a cost」——判据简化不是免费午餐，须显式记简化换来什么、丢什么（§4bl、§4er）。
4. **语境决定形式**：§4fn 判据形式（连续评分 vs 布尔通过）须按用途选、不教条；群体平均达标≠逐患者有效（§4fi、§4dp、§4dl）。
5. **省事判据低估证据**：五个试验中四个用连续均差规划出「implausibly small trials」——省事判据可能低估所需证据规模（§4fh、§4bl）。
6. **判据对应决策单元**：先定「裁定单案还是总体」再定判据粒度，裁定权归用户（§4ch、§4fi）。

## 三、诚信现场复现

- MacCallum 二分化经典检索零结果，如实弃用，不硬凑。
- 两篇同为二分主题但结论相反，如实并列为张力对、不 selection；数字全取一手摘要逐字。
- 用户放宽时间后仍坚持逐字核验与时点留痕，未因赶时间牺牲任何一步。

## 四、验证（全绿）

```
一致性 True | failed=[] | handoff 433 = truth 433
内核 7.5.0 | KB 433（重复 0，KB-AUDIT188 / KB-META153）| 宪法锁 fe56291b | 台账 116 末 §4fn
全量 1551 fail=0 err=0 | 内核专项 122 fail=0 err=0
verdict GAP_INCONCLUSIVE | l3=false | absolute=false | Ambient=0
```

## 五、边界

判定权归用户；内核 L0 不联网不 spawn；未编译新门禁；未动宪法/判定/十案/§100。外部一手仅作哲学镜像，不宣称本仓有同样回归、二分或样本量结构。MNAR 缺失机制一手（PMID 35098576）留作下批线索。
