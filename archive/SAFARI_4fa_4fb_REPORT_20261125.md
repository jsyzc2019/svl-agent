# Safari 战利品报告 · §4fa–§4fb（2026-11-25）

## 本批主题

| 轮次 | 猎场 | 一手锚点 | 层级 | 核心增量 |
|---|---|---|---|---|
| §4fa | 判定者期望效应自审 | Rosenthal, *Res Synth Methods* 2015;6(3):240-245, PMID 26355797 | 一手访谈体（非实证/非综述，层级如实标注） | 期望污染须先证存在再量化、须可复制；「是否存在本身曾有争议」；期望由判定者/权威持有 |
| §4fb | 判据构造偏差使结论翻转 | Kim, Yon, Lee, et al.（Ioannidis senior）, *J R Soc Med* 2025;118(9):293-303, PMID 40842270 | A 级一手（meta-流行病学，PROSPERO CRD42022356073） | 永恒时间偏差使 44% 研究受影响、23.8% 结论显著性翻转、ES 比 0.71 |

## 一手逐字核验（PubMed E-utilities 原文摘要）

**§4fa（Rosenthal 2015，访谈体）**：
> "we discuss my early uses of meta-analytic procedures, first to combine p-values and then to combine effect sizes as well… My interest in quantifying the magnitude and the statistical significance of the effect of interpersonal expectations probably grew out of the following: (1) a long-held interest in the concept of replication and (2) a series of controversies over the very existence of any effect of interpersonal expectations held, for example, by psychological experimenters, classroom teachers, and leaders of various organizations."

**§4fb（Kim / Ioannidis et al. 2025）**：
> "Immortal time bias (ITB) occurs when a period during which, by design, participants cannot experience the outcome (like death) is incorrectly included in the treatment group's follow-up, artificially making the treatment look better than it truly is… Across 25 topics (including 182 studies), 44.0% of the eligible studies (80 studies) were affected by ITB… 57.1% (12/21) demonstrated statistically significant results only in studies with ITB or only in studies without ITB… In 23.8% (5/21), the overall summary results changed from statistically significant to non-statistically significant or vice versa after excluding studies with ITB… The ratio of ES…was 0.71 (95% CI, 0.66-0.78)."

## 诚信现场复现

- **层级如实标注**：§4fa 是访谈体一手，非实证、非系统综述，**如实标注层级，不夸大为 A 级实证结论**。
- **零结果/错配弃用**：demand characteristics、期望效应实证、皮格马利翁、盲法偏倚、预测区间方法学、生存偏差配对等多组检索零结果或错配，均如实弃用，不硬凑；只在 Rosenthal 访谈与 Ioannidis meta-流行病学两处扎实命中。
- **数字取一手**：§4fb 的 44%、57.1%、23.8%、0.71 全部取自一手摘要逐字，不用二手转述。

## 照见本仓（哲学镜像，非宣称同机制）

| 一手结论 | 本仓镜像 |
|---|---|
| 期望效应须先证存在、再量化、须可复制 | 判定是否被期望/框架污染须可证伪，不预设（§4co、§4eu） |
| 「是否存在本身曾有争议」 | 对污染是否存在保持可证伪立场，不当不证自明（§4em、§4ee） |
| 期望由判定者/权威持有 | 判据设计者/裁判须自审期望渗入，形式中立≠实质中立（§4ch、§4r） |
| 先合并 p 值再合并效应量 | 判据从「是否显著」走向「效应多大」（§4bv、§4ev） |
| 构造偏差把不可能发生的时期计入支持面 | 审计数口径/分母是否把不可能情形算进支持面（§4bv、§4bl） |
| 44% 研究受影响、23.8% 结论翻转 | verdict 对口径/纳入方式须做敏感性分析（§4dj、§4er、§4ev） |
| ES 比 0.71 一致夸大、审查 PROSPERO 注册 | 警惕「通过态」被系统性抬高；审查本身须预注册可审计（§4ew、§4ch） |

## 内化与验证（现场实测）

```
一致性: all_consistent=True | failed=[] | handoff_kb=409 | truth_kb=409
权威数字: 内核7.5.0 | KB409 | 宪法锁fe56291b | 台账104 | 末§4fb
判定: GAP_INCONCLUSIVE | l3=false | absolute=false | Ambient=0
KB实物: 409 | 重复: 0 | KB-AUDIT max=176 | KB-META max=141
全量: 1551 fail=0 err=0
内核专项(life_kernel/tests): 122 fail=0 err=0
```

## 红线（全部守住）

判定权归用户；内核 L0 不联网不 spawn（摄食在会话层）；Ambient 恒 0；**未编译新门禁、未动宪法/判定/十案/§100**。两篇外部研究仅作一手哲学镜像（§4fa 访谈体层级如实标注），只内化思维器官，不宣称本仓有同样心理/生存分析机制。
