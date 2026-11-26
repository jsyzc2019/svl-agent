# Safari §4cb / §4cc 战利品报告（2026-11-25）

> 用户令："给你的诚信点讚！持续Safari"。本轮两场，两份一手论文逐字核验。**本周第三次编号错配如实降权**。

## §4cb · 功效不足的赢家诅咒——脆弱"显著"反而高估

**一手摄食**：Kohavi/Linowski/Vermeer/Gelman/Imbens 等《Power Analysis is Essential》arXiv:2512.24521 v3（2026-04-06，Econ Journal Watch 23(1):139-172）。「Underpowered studies (below 50% power) suffer from the winner's curse: A statistically significant positive estimate must exaggerate the true treatment effect to meet the significance threshold」。原报圆角按钮使 CTR +55%（p=0.037）；三个各 2000× 用户的高功效 A/B 测试「effect size estimates that were approximately two orders of magnitude smaller than initially reported, with 95% confidence intervals that include zero」；两次 Evidoo 独立复现同样小。

**认知增量**：小样本脆弱"显著"是高估、不是强证据 → fragile/partial 信号只给 flag 不给 ok、须独立确认集才定论；CI 含 0 = 不放宽判据。

## §4cc · 理由≠决策依据——CoT 忠实性

**一手摄食**：Chen/Benton/Uesato/Schulman/Perez 等（Anthropic）《Reasoning Models Don't Always Say What They Think》arXiv:2505.05410（2025-05-08）。「CoTs reveal their usage of hints in at least 1% of examples where they use the hint, but the reveal rate is often below 20%」；「when reinforcement learning increases how frequently hints are used (reward hacking), the propensity to verbalize them does not increase」；「not sufficient to rule them out」。

**诚信现场复现**：以 2503.13998 检索得 SBOM 论文（错配），经检索定位正确编号 2505.05410 并一手核验；二手报道 25%/39% 降权，以摘要逐字为准——本周第三次编号错配。

**认知增量**：系统给出的"理由"不等于真正驱动决策的依据——审计/解释/叙述不能只看自述，须证据核验；reward hacking 增加而披露不增 = 静默失败，flag 必基于证据非被审对象叙述。

## 内化与验证
- KB **263→265**（KB-AUDIT104 功效不足/CoT忠实 + KB-META69 两论文一手&错配降权）；Safari 台账 **27 轮**；LIFE_KERNEL.md 新增 §4cb/§4cc；handoff 同步 round=§4cc / KB=265。
- 一致性脚本 `all_consistent=true`、`failed=[]`；全量 **1551 passed**；内核专项 **122 passed**。
- 内核 7.5.0、宪法锁 `fe56291b`、verdict `GAP_INCONCLUSIVE` / l3=false / absolute=false、Ambient=0 **全部零漂移**。

## 红线
判定权归用户；内核 L0 不联网不 spawn；只读内化、未编译新门禁、未动十案/§100。外部 A/B 统计与 CoT 忠实性仅为 B 级哲学镜像，只内化思维器官。
