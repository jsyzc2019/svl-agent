# Safari 战利品报告 · §4ew–§4ex（2026-11-25）

## 本批主题

| 轮次 | 猎场 | 一手锚点 | 层级 | 核心增量 |
|---|---|---|---|---|
| §4ew | Type S / Type M 错误 | Gelman & Carlin, *Perspect Psychol Sci* 2014;9(6):641-651, PMID 26186114 | A 级一手（方法论经典） | 窄化强调统计显著有缺陷；噪声小样本中显著常误导；显著≠方向对、≠幅度对 |
| §4ex | 前瞻/回溯设计分析 | Altoè et al., *Front Psychol* 2020;10:2893, PMID 31993004 | A 级一手方法论文 | 推断非孤立程序；不只聚焦显著与 I/II 错误，还须推理合理效应量；规划期与回溯期都有用 |

## 一手逐字核验（PubMed E-utilities 原文摘要）

**§4ew（Gelman & Carlin 2014）**：
> "power analysis is flawed in that a narrow emphasis on statistical significance is placed as the primary focus of study design… In noisy, small-sample settings, statistically significant results can often be misleading… we recommend design calculations in which (a) the probability of an estimate being in the wrong direction (Type S [sign] error) and (b) the factor by which the magnitude of an effect might be overestimated (Type M [magnitude] error or exaggeration ratio) are estimated… the largest challenge in a design calculation: coming up with reasonable estimates of plausible effect sizes based on external information."

**§4ex（Altoè et al. 2020）**：
> "statistical inference is too often viewed as an isolated procedure limited to the analysis of data that have already been collected. Instead, statistical reasoning is necessary both at the planning stage and when interpreting the results… Rather than focusing only on the statistical significance of a result and on the classical control of type I and type II errors, a comprehensive design analysis involves reasoning about what can be considered a plausible effect size… the exaggeration ratio or Type M error (i.e., the predictable average overestimation of an effect that emerges as statistically significant) and the sign error or Type S error (i.e., the risk that a statistically significant effect is estimated in the wrong direction)… it can be usefully carried out both in the planning phase of a study and for the evaluation of studies that have already been conducted."

## 诚信现场复现

- 本批 Europe PMC REST API 返回 **HTTP 503（服务临时不可用）**，如实记录并改用 **NCBI E-utilities** 端点复核，两篇一手摘要均逐字核验，不虚构来源、不用二手转述顶替。
- 上次停点的两个检索（锚定 Furnham/Boochsler 拼写错配、`order effects` primacy/recency 元分析）均为零结果，按纪律弃用；锚定主题已在 §4ay/KB-AUDIT121 覆盖，不重复摄食。
- 本批「winner's curse」检索零结果，如实弃用，不硬凑。
- 内核专项测试曾误用 `audit_l3_gap_targeted/` 目录得 36，经查证正确范围为 `life_kernel/tests/`，实测 **122**，如实纠正，不硬凑数字。

## 照见本仓（哲学镜像，非宣称同机制）

| 一手结论 | 本仓镜像 |
|---|---|
| 窄化强调统计显著作为设计焦点有缺陷 | verdict 不能只看单阈值通过/不通过（§4ev、§4eu） |
| 噪声小样本中统计显著常误导 | 显著结论在弱证据下更可能错，须显式标注证据强度与不确定性（§4bv、§4dx） |
| Type S 方向错误 | 即使「通过」，方向可能反了（§4dp、§4ed） |
| Type M 幅度夸大 | 显著效应被系统性高估，「通过」不等于效应量/质量达标（§4br） |
| 合理效应量须外部信息锚定 | 先验/合理量须外部锚定且诚实，交还用户裁定（§4ch、§4dj） |
| 推断非孤立程序，规划期+解释期都须推理 | 判定不只在结果端，判据设计期就要想清（§4ch、§4cq） |
| 规划期与已做研究评估期都有用 | 每轮一致性+全量测试即回溯设计分析（§4co、§4dz） |

## 内化与验证（现场实测）

```
一致性: all_consistent=True | failed=[] | handoff_kb=401 | truth_kb=401
权威数字: 内核7.5.0 | KB401 | 宪法锁fe56291b | 台账100 | 末§4ex
判定: GAP_INCONCLUSIVE | l3=false | absolute=false | Ambient=0
KB实物: 401 | 重复: 0 | KB-AUDIT max=172 | KB-META max=137
全量: 1551 fail=0 err=0
内核专项(life_kernel/tests): 122 fail=0 err=0
```

## 红线（全部守住）

判定权归用户；内核 L0 不联网不 spawn（摄食在会话层）；Ambient 恒 0；**未编译新门禁、未动宪法/判定/十案/§100**。两篇外部统计方法论仅作 A 级一手哲学镜像，只内化思维器官，不宣称本仓有同样统计机制。
