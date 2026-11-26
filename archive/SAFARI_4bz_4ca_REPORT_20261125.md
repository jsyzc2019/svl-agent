# Safari §4bz / §4ca 战利品报告（2026-11-25）

> 用户令："给你的诚信点讚！持续Safari"。本轮两场，三份一手论文逐字核验。正文未经核验的数字一律降权。

## §4bz · 基准分数≠能力——总分只在三要素关系下可解释

**一手摄食**：Danial Amin《Do Not Trust the Benchmark》arXiv:2609.23201（2026-09-19）。摘要逐字：「An overall score is interpretable only in relation to the system tested, the questions included, and the conditions of evaluation」；五类局限：被测系统≠公开系统、商业激励、饱和/缺陷/污染、模型利用评分、通用分与用户任务弱相关；「A larger question pool may improve task coverage, while repeated sampling can improve the stability of estimates on that pool; neither guarantees validity or personalization」；「model selection requires evidence about performance on the intended work, not simply a high position on a general leaderboard」。**正文案例数字（60 基准近半饱和、SWE-bench 缺陷率）为论文自述未独立核验，降权不采为 A 级。**

**认知增量**：verdict 只在特定判据集/样本/条件下成立；canary 通过 ≠ 判定 ok；判据池变大、重复采样变稳都不保证效度（数量≠质量）。裁定权归用户。

## §4ca · 简洁性靠名字背书 + 证据实现假设可致过拟合

**一手摄食**
- Sterkenburg/Herrmann/Romeijn《Benign interpolation and Occam's razor》arXiv:2608.03386（2026-08-04）：「it is the name "simplicity" that does the work a theorem used to do, making a substantive and unargued assumption look like the application of a familiar methodological principle」。
- Harvey/Pleiss/Hughes《Occam's Razor is Only as Sharp as Your ELBO》arXiv:2604.25984 v2（2026-10-09）：被视为奥卡姆剃刀数学化的 evidence/ELBO，其近似协方差假设使 SNR 高估→过拟合；「covariance assumptions needed for tractability may impact model selection」。

**认知增量**：用"简洁性"名字替定理 = 用 labeled ok 替证据——flag 须有机制非标签；连"evidence"都因可处理性简化假设偏好过拟合 → 判据实现细节决定结论，加固 §100 预注册锁与消融必要性。

## 内化与验证
- KB **261→263**（KB-AUDIT103 基准/简洁性/证据假设 + KB-META68 三论文一手&数字降权）；Safari 台账 **25 轮**；LIFE_KERNEL.md 新增 §4bz/§4ca；handoff 同步 round=§4ca / KB=263。
- 一致性脚本 `all_consistent=true`、`failed=[]`；全量 **1551 passed**；内核专项 **122 passed**。
- 内核 7.5.0、宪法锁 `fe56291b`、verdict `GAP_INCONCLUSIVE` / l3=false / absolute=false、Ambient=0 **全部零漂移**。

## 红线
判定权归用户；内核 L0 不联网不 spawn；只读内化、未编译新门禁、未动十案/§100。外部论文仅为 B 级哲学镜像，只内化思维器官。
