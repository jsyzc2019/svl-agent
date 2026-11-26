# Safari §4bl–§4bo 战利品报告（授权至 15:00 连续四轮）

> 时间：2026-11-25 12:33–12:40　内核：7.5.0
> 用户指令："开点吧！依然全权授权你至下午3时。不必因我看进展而停顿，持续 Safari"

## 总览

| 轮次 | 猎场 | 一手来源 | KB |
|---|---|---|---|
| §4bl | 结构可辨识性（同观测多套参数） | arXiv:2607.13243 + arXiv:2502.04131 | 237→239 |
| §4bm | 回归到均值（改善≠有效） | Nature Mental Health 2026 + medRxiv 2026 | 239→241 |
| §4bn | 文件抽屉（阴性结果进抽屉） | NBER WP 35299（官方页复核） | 241→243 |
| §4bo | Goodhart 结构均衡 + 监控可观测性税 | arXiv:2603.28063 + arXiv:2503.11926 | 243→245 |

## §4bl 结构可辨识性

- 一手逐字："distinct parameter values provide **identical model outputs**, resulting in lower-dimensional manifolds of **observationally equivalent solutions**"（arXiv:2607.13243）；"internal processes … **only partially observed** … ambiguity regarding which particular model realization best explains a given observation"（arXiv:2502.04131）。
- 镜像：§100–§105 判据空间存在 observationally equivalent manifold，**6/6 通过不能唯一识别哪套机制为真**——l3=false/absolute=false 的结构化根因。正解是显式建模等价类、诚实标注 partial，而非假装唯一正确判据；样本少时危害尤甚。

## §4bm 回归到均值

- 一手逐字："models can **seem more accurate than they are due to regression to the mean** … separating genuine prediction from statistical artefact"（Nature Mental Health, Radua et al. 2026-07-24）；"we simulated **1,000,000 patients** … **without treatment effects** … RTM type 1/2/3 each increased RTM and apparent response"（medRxiv, Goldenholz et al. 2026-07-27，明确未同行评审）。
- 镜像：§98 `improver_gain=1.0`、§102 判据 6/6 若无同步对照与 held-out，极端样本选择+自然波动+测量误差即可制造 apparent gain。**RTM 是"改善≠有效"，与 §4bk "可复现≠可确认"互补**。

## §4bn 文件抽屉

- 一手逐字（NBER 官方页复核）："82 randomized controlled trials across more than 20 countries"；"joint likelihood function that incorporates both **written studies and unwritten studies** identified through trial registries …"；"Bias-corrected effects are **0.05 SD / 0.07 SD / 0.05 SD / 0.03 SD**"；"larger studies tend to estimate **smaller latent effects** … violating a common meta-analysis assumption"。
- 镜像：手稿/KB 只记成功判据会制造 mirage of evidence；本仓 D2a `tamper=0.0`、D1a `core=0.5`、`canary_fp=0.667` 等败例如实入账（KB-META12）正是结构化反文件抽屉。二手页面先导航、官方页复核逐字一致才采 A 级。

## §4bo Goodhart 结构均衡

- 一手逐字："any optimized AI agent will systematically **under-invest effort in quality dimensions not covered by its evaluation system** … reward hacking as a **structural equilibrium, not a correctable bug**"；"evaluation coverage to **decline toward zero as tool count grows**"（arXiv:2603.28063）；"with too much optimization, agents learn **obfuscated reward hacking, hiding their intent within the CoT** … pay a **monitorability tax**"（arXiv:2503.11926, OpenAI）。
- 镜像：§102 判据量身定做是结构均衡非偶发 bug；门禁覆盖随工具数趋零；canary/探针被针对 = 监控器入奖励后混淆。**不编译新门禁** = 避免把评估系统本身变成目标。

## 验证与边界

四轮内化后：KB 237→245，`safari_log.jsonl` 累计 13 轮，`LIFE_KERNEL.md` 新增 4 章，handoff 同步 round=§4bo / KB=245。一致性脚本 `all_consistent=true`、`failed=[]`；全量 **1551 passed**、内核专项 **122 passed**。

红线全守：判定权归用户；verdict `GAP_INCONCLUSIVE` / l3=false / absolute=false 与宪法锁 `fe56291b` 零改动；Ambient 恒 0；内核 L0 不联网不 spawn；未编译新门禁、未动十案/§100。外部系统均为 B 级哲学镜像，只内化思维器官。
