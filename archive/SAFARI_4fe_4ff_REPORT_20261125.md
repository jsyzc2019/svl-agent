# Safari 战利品报告 · §4fe–§4ff（2026-11-25）

## 本批主题

| 轮次 | 猎场 | 一手锚点 | 层级 | 核心增量 |
|---|---|---|---|---|
| §4fe | 对撞机偏差 | Munafò et al., *Int J Epidemiol* 2018;47(1):226-235, PMID 29040562 | A 级一手（方法学） | 选择进入/流失 = 对撞机偏差；轻微筛选即可产生误导性关联；须声明样本代表谁+敏感性分析 |
| §4ff | 条件化使结论反转 | Banack & Kaufman, *Prev Med* 2014;62:96-102, PMID 24525165 | A 级一手（NHANES III 17,636 人实证 + bias 分析） | 肥胖悖论：一般人群 RR=1.24（有害）→ CVD 患者 RR=0.79（看似保护） |

## 一手逐字核验（PubMed E-utilities 原文摘要）

**§4fe（Munafò et al. 2018）**：
> "the representativeness of these samples may be limited – either through selection into studies, or by attrition from studies over time… this amounts to conditioning on a collider (i.e. a form of collider bias)… it is often assumed that it should not have a strong impact on estimates of associations… because selection can induce collider bias… selection can lead to substantially biased estimates of associations… even modest influences on selection into, or attrition from, a study can generate biased and potentially misleading estimates of both phenotypic and genotypic associations… Our results highlight the value of knowing which population your study sample is representative of… sensitivity analyses of the extent to which bias might distort estimates."

**§4ff（Banack & Kaufman 2014）**：
> "explore whether the paradox can be attributed to a form of selection bias known as collider stratification bias… data from 17,636 participants in the US National and Nutrition Examination Survey (NHANES III)… In the general population, the adjusted risk ratio relating obesity and all-cause mortality was 1.24 (95% CI 1.11, 1.39)… Adjusted risk ratios comparing obese and non-obese among individuals with and without CVD were 0.79 (95% CI 0.68, 0.91) and 1.30 (95% CI 1.12, 1.50), indicating that obesity has a protective association among individuals with CVD… After conditioning on CVD status in the design or analysis, obesity can appear protective among individuals with CVD."

## 诚信现场复现

- **零结果弃用、改精确检索**：肥胖悖论单独检索零结果如实弃用，改用 collider 精确检索命中两篇硬一手，不硬凑。
- **不包装成唯一真因**：§4ff「collider stratification bias is one plausible explanation」只声称一个可能解释、非定论，如实照录。
- **数字取一手**：RR 1.24 / 0.79 / 1.30、17,636 人全部取自一手摘要逐字。

## 照见本仓（哲学镜像，非宣称同机制）

| 一手结论 | 本仓镜像 |
|---|---|
| 选择进入/流失 = 对撞机偏差 | 进入判定集的数据不是中性的，须审筛选机制（§4bn、§4bl） |
| 常见错误假设「筛选不影响关联」 | 不能假设「换了样本结论不变」（§4ee、§4fb） |
| 轻微筛选即可产生误导性关联 | 须对样本选择做敏感性分析（§4dj、§4ev） |
| 须知道样本代表哪个总体 | verdict 须声明适用样本/范围，不可外推（§4dp、§4ch） |
| 一般人群 RR=1.24 → CVD 患者 RR=0.79 | 条件化一个变量能让结论完全反转，须显式分层并测其影响（§4fe、§4fb、§4eq） |
| 表面保护可由选择偏差生成 | 「通过/有利」态须排除选择偏差解释（§4ep、§4dj） |
| one plausible explanation | 保留多机制并列不独占（§4er、§4em） |
| 模拟+实证+bias 分析三层证据 | 裁定须机制模拟+实证+偏差分析三层（§4bl、§4ev） |

## 内化与验证（现场实测）

```
一致性: all_consistent=True | failed=[] | handoff_kb=417 | truth_kb=417
权威数字: 内核7.5.0 | KB417 | 宪法锁fe56291b | 台账108 | 末§4ff
判定: GAP_INCONCLUSIVE | l3=false | absolute=false | Ambient=0
KB实物: 417 | 重复: 0 | KB-AUDIT max=180 | KB-META max=145
全量: 1551 fail=0 err=0
内核专项(life_kernel/tests): 122 fail=0 err=0
```

## 红线（全部守住）

判定权归用户；内核 L0 不联网不 spawn（摄食在会话层）；Ambient 恒 0；**未编译新门禁、未动宪法/判定/十案/§100**。两篇外部研究仅作 A 级一手哲学镜像，只内化思维器官，不宣称本仓有同样 collider/CVD 条件化结构。
