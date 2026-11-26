# Safari §4cs 战利品报告 · 开放评审与视角分歧（2026-11-25）

> 用户令："你持续推直至下午3时"（§4bc 续）。授权至 15:00，连续推进、不逐轮等待。

## 一、一手摄食（A 级 · 一手 RCT 摘要逐字核验）
一手：van Rooyen S, Godlee F, Evans S, Black N, Smith R. *Effect of open peer review on quality of reviews and on reviewers' recommendations: a randomised trial*. **BMJ** 1999;318(7175):23-7，PMID 9872878，DOI 10.1136/bmj.318.7175.23。随机对照试验，编辑与作者均对干预盲。

**逐字数字**（原文摘要）：
- 署名组比匿名组更可能拒审："12% (95% confidence interval 0.2% to 24%) more likely to decline to review (35% v 23%)"
- 评审质量无显著差异："anonymous (3.06 (SD 0.72)) and identified (3.09 (0.68)) (P=0.68, 95% CI -0.19 to 0.12)"
- 编辑给分显著高于作者："editors' quality score (3.05 (SD 0.70)) significantly higher than that of authors (2.90 (0.87)) (P<0.005, 95% CI -0.26 to -0.03)"
- 结论："no important effect on the quality of the review...but it significantly increased the likelihood of reviewers declining to review"

## 二、照见本仓（认知增量）
| 外部一手事实 | 本仓同构器官 | 增量 |
|---|---|---|
| 署名使拒审率 23%→35% | 制度设计 | 透明有真实成本，不可只看好处不算代价 |
| 质量 P=0.68 无差异 | — | "看起来更透明"≠"质量更好"，须实测 |
| 编辑 3.05 vs 作者 2.90，P<0.005 | flag 分层 / 裁定权归用户 | 同一份评审，裁判视角与被评视角系统性分歧，评分依立场漂移，不能假设"分数客观" |
| 随机 + 双盲才敢下结论 | 独立确认集 / 盲评（§109、§114） | 无盲评不得下"无差异"结论 |
| 摘要列三篇一手 RCT 互证 | 证据阶梯 | 非单点，多一手互证 |

## 三、诚信现场复现（编号错配，如实降权）
凭记忆猜 PMID 10530451 去抓，实为**肺炎球菌论文**（Clin Infect Dis 1999），与同行评审无关——编号错配，如实降权、未采；改用精确标题检索定位到正确的一手 PMID 9872878，逐字核验。这是本会话又一次"记忆编号不可靠"的活样本，不硬凑。

## 四、内化与验证
- KB 新增 `KB-AUDIT115` / `KB-META80`（285→287）；台账 42→43 轮（末 §4cs）；`LIFE_KERNEL.md` 新增 §4cs 章；handoff 数字/正则同步（287）。
- 一致性脚本 `all_consistent=true`、`failed=[]`（handoff=truth=287）；实物复核 KB 287、两编号各 1、无重复。
- 全量 **1551 passed**、内核专项 **122 passed**（junitxml failures=0, errors=0）。
- 内核 `7.5.0`、宪法锁 `fe56291b`、verdict `GAP_INCONCLUSIVE` / l3=false / absolute=false、Ambient=0 **全部零漂移**。

## 五、红线
判定权归用户；内核 L0 不联网不 spawn；Ambient 恒 0；**未编译新门禁、未动宪法/判定/十案/§100**。外部出版流程仅作 A 级一手 RCT 哲学镜像。
