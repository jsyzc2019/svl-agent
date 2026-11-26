# §4fs · 证伪性摄食首跑报告（2026-11-26）

> 用户令："时时总结很重要，第三方综述就是替大家普照一下，当然这不等于说全面或正确，自己做的也是这样，建议你把这个机制落到运行代码级，注意总结的方法。Safari 吧，别停留，一次干是。"
> 本轮性质：**P0 证伪性摄食首跑**——不找支持本仓红线的证据，找能推翻它的证据。

---

## 一、预注册（先于取证锁存）

`prereg_falsify_20261126.json`，sha256 `99ebfeac8d0c8b4d37a589bf46d15f070bd90c858581b47b2985b10304fad472`

- **靶信条**：本仓证据阶梯"一手(A级)优于二手(B/C级)；一手逐字核验是可靠性金标准"。
- **可证伪预测**：若二手合成在稳定性/准确性上系统性优于一手，或一手逐字核验仍系统性误读，则阶梯被削弱。
- **决策树**：FOUND_A→`EVIDENCE_LADDER_WEAKENED` / FOUND_B_ONLY→提示性线索不翻案 / NOT_FOUND→如实记"搜了没找到"，**不宣称证实原信条**。

## 二、一手摄食（A级，逐字核验）

| 来源 | 关键读数（逐字/数值） | 对靶信条的方向 |
|---|---|---|
| Tam WW et al. *PLoS One* 2014;9(12):e113994 PMID25474198 | 647 meta 分析；首个试验显著→84.1%（95%CI 79.4–88.8）对应 meta 同向显著；不显著→57.9% 对应 meta 不显著。"The conclusion of the first trial…is mostly likely correct." | 支持显著一手可靠 |
| Glasziou P et al. *BMC Med Res Methodol* 2010;10:23 PMID20298582 | 200 Cochrane 综述；最精确单试占 51% 权重，秩相关 0.90，一致率 81%；101 个不显著单试中 31 个被 meta 翻案。"negative results were less reliable" | 削弱"一手天然可靠"（阴性场景） |
| Lewis M et al. *R Soc Open Sci* 2022;9:211499 PMC8864345 | 15 现象，meta 估计约为 MLR 的 **3 倍**；但"both…informative, discrepancy…still largely unexplained" | 削弱"二手绝对权威"，也不证实"二手无用" |

核验通道：PubMed E-utilities efetch（前两篇）+ EuropePMC REST core（第三篇）。三篇跨独立期刊，非同源谱系（KB-STRUCT02 通过）。

## 三、裁决

**`EVIDENCE_LADDER_REFINED_NOT_OVERTHROWN`**——靶信条未被推翻，但被精确化。

1. 显著单篇一手 ↔ 合成二手：高度一致（84.1% / 81% / 秩相关 0.90）→ 一手可靠；
2. 阴性单篇一手：31/101 被 meta 翻案 → 一手不可靠是场景性的，非层级性的；
3. 合成二手：系统性偏大 3 倍且差异**未被解释** → 二手不是裁决器。

结论是**场景依赖**，不是层级翻转。按预注册决策树如实写"未找到推翻性证据"——**不制造证伪战利品**。这是自审 P0 的对内诚信兑现：找了、没找到、就写没找到。

## 四、机制落地（运行代码级）

`life_kernel/evidence_honesty.py`，两个纯函数器官：

- `guard_negative()`——"没查到≠没有"编译成可调用判据。今晨事故：目录枚举查自动化任务得"无"，而调度器里 ACTIVE 任务一直在（KB-META158）。
- `scope_summary()`——"综述=普照非全知；自作总结同律无豁免"编译成强制作用域标注；盲区为空即 flag（"没有盲区"本身是未被证伪的断言）。
- 7 活体回归全绿；过程中自咬一次：把"有1个ACTIVE任务"（非负面断言）误写成合规样例，被守卫判 `NOT_NEGATIVE`，**改样例不改判据**。
- 不接 run_loop、不编译门禁、不碰判定层。

## 五、照见自身

用户："第三方综述替大家普照一下，不等于全面或正确，自己做的也是这样。"

本仓 KB 总报告、收营终检、乃至**本报告**，都是普照工具，不是真理裁决器。`scope_summary(self_applied=True)` 把这条反向钉死在自己身上。Lewis 那句"差异仍 largely unexplained"是最诚实的落点：**不知道谁对，就写不知道，不替证据签字。**

## 六、边界与终检

- 三篇为期刊一手摘要/全文，跨独立期刊非同源谱系；Glasziou 81% 是统计结论一致非效应量相等；Lewis 3 倍限于 Kvarven2020 的 15 现象特定领域，均不外推。
- 判定层零变动：verdict `GAP_INCONCLUSIVE` / l3=false / absolute=false / 内核 7.5.0 / 宪法锁 fe56291b；不翻十案、不编译新门禁；内核 L0 不联网不 spawn，联网仅外层摄食工具；判定权归用户。
- KB 441→**444**（KB-META158 / KB-AUDIT193 / KB-META159）；台账 120→**121**（末 §4fs）；LIFE_KERNEL 章节 +1。
- 全量测试 **1551 passed**（新模块未破坏既有）。
