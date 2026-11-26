# Safari §4cq + §4cr 战利品报告（2026-11-25）

> 用户令："你持续推直至下午3时"（§4bc 续）。授权至 15:00，连续推进、不逐轮等待。

## §4cq · 公平判据不可兼容（A 级一手）
一手：Kleinberg, Mullainathan & Raghavan, *Inherent Trade-Offs in the Fair Determination of Risk Scores*, ITCS 2017, arXiv:1609.05807。摘要逐字："we prove that except in highly constrained special cases, there is no method that can satisfy these three conditions simultaneously"；"even satisfying all three conditions approximately requires that the data lie in an approximate version of one of the constrained special cases"。

照见本仓：多判据不可全拉满；只有强约束特例才兼容、不可把特例当通例；近似满足也须落在特例近似版、不能靠调权重假修；判据冲突须显式暴露、交裁定权归用户排序（不编译新门禁假装兼容）。

**诚信**：三公平条件的名称只在正文、摘要未逐字列出，故不凭记忆补条件名。

## §4cr · HARKing 事后假设（A 级一手）
一手：Kerr NL, *HARKing: hypothesizing after the results are known*, Perspectives on Psychological Science Review, 1998, PMID 15647155。摘要逐字："presenting a post hoc hypothesis (i.e., one based on or informed by one's results) in one's research report as if it were, in fact, an a priori hypotheses"；"at least some forms of HARKing are widely practiced and widely seen as inappropriate"；"suggestions for deterring HARKing"。

照见本仓：post-hoc 分层不得翻案、须预注册锁（§4bx）；普遍且公认不当≠可接受；成本收益争议留公开辩论、不假装定论；制度性抑制（预注册/canary/裁定权）而非靠自觉。

## 诚信现场复现：一次被当场抓住的 wrong-evidence
§4cr 内化脚本用占位法给两条目递增编号，导致第二条（KB-AUDIT114/META79）**未真正写入 KB**，但台账与 handoff 已按 285 条记录——这正是"声称≠实物"的 wrong-evidence 病，恰是 §4cr 自己的镜像。复核时发现 KB 实为 283 条，立即补写落账，修复后 KB=285=handoff=台账声称，一致性脚本全绿。如实记录，不掩盖。

## 内化与验证
- KB 新增 `KB-AUDIT113/114`、`KB-META78/79`（281→285）；台账 40→42 轮（末 §4cr）；`LIFE_KERNEL.md` 新增 2 章；handoff 数字/正则同步（285）。
- 一致性脚本 `all_consistent=true`、`failed=[]`（handoff=truth=285）。
- 全量 **1551 passed**、内核专项 **122 passed**（junitxml failures=0, errors=0）。
- 内核 `7.5.0`、宪法锁 `fe56291b`、verdict `GAP_INCONCLUSIVE` / l3=false / absolute=false、Ambient=0 **全部零漂移**。

## 红线
判定权归用户；内核 L0 不联网不 spawn；Ambient 恒 0；**未编译新门禁、未动宪法/判定/十案/§100**。外部一手仅作哲学镜像。
