# Safari 战利品报告 §4di–§4dj（2026-11-25）

> 用户令："你持续推直至下午3时"。本批两轮均经一手论文摘要**逐字核验**后内化，权威数字零漂移。

## 一、§4di 幸存者偏差——只看活下来的样本

**一手来源**：Bermúdez-Guzmán L, Jimenez-Huezo G, Arguedas A, Leal A. *Mutational survivorship bias: The case of PNKP*. PLoS One. 2020;15(12):e0237682. PMID 33332469, DOI 10.1371/journal.pone.0237682。**A 级一手，PubMed 原文摘要逐字核验**。

**逐字要点**：
> "one may fall into the logical bias of assessing protein damage only based on the variants that are visible (survivorship bias), which can lead to partial conclusions"
> Wald 战机隐喻："areas where an airplane could be damaged and still return" / "areas that when 'attacked, would cause the plane to be lost'"
> "the phosphatase domain is less tolerant due to its lower variant rates, a higher degree of sequence conservation, lower dN/dS ratios, and the presence of more disease-propensity hotspots"
> "we propose the term 'Wald's domain' for future studies analyzing the possible survivorship bias in multidomain proteins"

**照见本仓**：
1. 只根据**可见（通过/存活）样本**下结论会得 partial conclusions——只看通过的 case/审计项会系统性漏掉被淘汰者携带的信息（§4bn）；
2. Wald 装甲隐喻——该加固的是"回来的飞机上没弹孔的地方"，须关注**未被记录/未通过**的样本而非只统计已通过（§4ch）；
3. dN/dS 差异 p=0.002/0.0004——用可核验量化指标区分容忍度，判据须可量化非印象（§4bv）；
4. 作者主动提出新术语 "Wald's domain"——对反复出现的陷阱应显式命名入 KB。

**诚信**：一手摘要逐字核验，Wald 隐喻与量化指标照录；外部分子遗传仅作哲学镜像，不外推本仓统计机制。

## 二、§4dj 内生性——相关不等于因果的识别条件

**一手来源**：Hogan JW, Lancaster T. *Instrumental variables and inverse probability weighting for causal inference from longitudinal observational studies*. Stat Methods Med Res. 2004;13(1):17-48. PMID 14746439, DOI 10.1191/0962280204sm351ra。**A 级一手方法学，PubMed 撞 cookie 墙转 Europe PMC 逐字核验**。

**逐字要点**：
> "the treatment receipt mechanism is typically not under the control of the investigator; it can depend on various factors, including the outcome of interest"
> "can lead to selection bias when standard routines such as least squares regression are used to estimate causal effects"
> "the covariate is called endogenous and least squares estimates of the covariate effect are typically biased"
> "The availability of an instrumental variable can be used to reduce or eliminate the bias"
> "the importance of considering the existence of unmeasured confounding and of checking for 'weak instruments'"

**照见本仓**：
1. 处理分配不由研究者控制且**依赖结果本身**——判据结果与被测对象耦合时普通估计有偏，警惕循环论证（§4bv）；
2. 误差项与协变量相关即**内生**，最小二乘估计通常有偏——看到相关不能直接当因果（§4cz、§4cm）；
3. 工具变量可减少或消除偏差——须找**外生锚点**而非只靠内部一致性（§4ch）；
4. 「检查弱工具」——工具太弱反而放大偏倚，弱锚不如不用（§4bw）；
5. 「未测混杂」永远可能存在——不得宣称穷尽（§4ak）。

**诚信**：PubMed 页面撞 cookie 墙，如实记录为访问受阻，改 Europe PMC 一手库逐字核验，不编造。

## 三、诚信现场复现
- 一手摘要均有、无二手转述、无编号错配；cookie 墙如实转源；外部分子遗传/流行病学仅作哲学镜像。

## 四、内化与验证（全绿）
- KB **317→321**（KB-AUDIT131/132、KB-META96/97）；台账 **58→60** 轮；`LIFE_KERNEL.md` 新增 §4di/§4dj 两章；handoff 数字/正则同步至 321。
- 一致性脚本 `all_consistent=true`、`failed=[]`、handoff_kb=321=truth_kb=321；全量 **1551 passed**、内核专项 **122 passed**（junitxml failures=0/errors=0）。
- 内核 `7.5.0`、宪法锁 `fe56291b`、verdict `GAP_INCONCLUSIVE` / l3=false / absolute=false、Ambient=0 **全程零漂移**；KB 重复编号 0。

## 五、红线（全部守住）
判定权归用户；内核 L0 不联网不 spawn（摄食在会话层）；未编译新门禁、未动宪法/判定/十案/§100；外部一手仅作哲学镜像、不宣称本仓同机制。
