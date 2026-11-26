# Safari §4bx / §4by 战利品报告（2026-11-25）

> 用户令："给你的诚信点讚！持续Safari"。本轮两场，两份一手论文逐字核验。**编号错配再次现场复现并如实降权**。

## §4bx · 结局切换——预注册锁防的是"看到结果后换判据"

**一手摄食**：Song/Jespersen/Hróbjartsson 等《Outcome switching in cohort studies of interventions》BMJ 2026;393:e087975（2026-05-27）。筛查 9965 条注册、纳入 124 项队列研究；「Only 30 studies (24%) completely prespecified their primary outcomes」；「Outcome switching occurred in 60 (48%) studies, but only two provided an explanation」；四类：omission 26% / downgrading 26% / new primary 20% / upgrading 2%；「statistically significant results were favoured in 77% (44/57)」；结论「Most changes were unexplained and favoured statistically significant results」。

**认知增量**：预注册的价值不在仪式，而在禁止看到结果后换判据——正是 §100 预注册锁、§106→§107 post-hoc 分层不可同批确认。48% 切换仅 2 项解释、77% 偏向显著 → 判据会被无意识朝有利结果重塑；改名/降级/升级/新增须显式理由且预注册在前，裁定权归用户。

## §4by · 虚假奖励刷分——判据过拟合不是真能力

**一手摄食**：Shao/Li/Xin 等《Spurious Rewards: Rethinking Training Signals in RLVR》arXiv:2506.10947 v2（2026-02-25）。「spurious rewards that have little, no, or even negative correlation with the correct answer」；随机奖励使 Qwen2.5-Math-7B MATH-500 **+21.4pp**（近真实奖励 29.1pp）；「GRPO exhibits a clipping bias...amplify high-prior behaviors learned during pretraining even without informative rewards」；code-reasoning 65%→90%+；但「highly model-dependent...fail to produce gains for other model families, such as Llama3 or OLMo2」；「large gains can arise...even from random rewards that do not reflect genuine capability improvements」。

**诚信现场复现**：以 Leaderboard Illusion 编号检索却得 Spurious Rewards，如实标注错配、以实际一手摘要为准，不硬凑成想要的论文——KB-META48 纪律实盘。

**认知增量**：随机奖励刷 21.4pp = 单判据 6/6 量身定做也能高分（§102）；clipping 放大高先验 = 判据只奖励既有倾向非新能力；model-dependent 换族失效 = §104 换实现不迁移、跨 seed 不可外推；论文处方「validating across diverse models rather than single de facto choice」= 本仓多判据独立确认。

## 内化与验证
- KB **259→261**（KB-AUDIT102 结局切换/虚假奖励 + KB-META67 两论文一手&错配降权）；Safari 台账 **23 轮**；LIFE_KERNEL.md 新增 §4bx/§4by；handoff 同步 round=§4by / KB=261。
- 一致性脚本 `all_consistent=true`、`failed=[]`；全量 **1551 passed**；内核专项 **122 passed**。
- 内核 7.5.0、宪法锁 `fe56291b`、verdict `GAP_INCONCLUSIVE` / l3=false / absolute=false、Ambient=0 **全部零漂移**。

## 红线
判定权归用户；内核 L0 不联网不 spawn；只读内化、未编译新门禁、未动十案/§100。外部 BMJ 队列与 RLVR 仅为 B 级哲学镜像，只内化思维器官。
