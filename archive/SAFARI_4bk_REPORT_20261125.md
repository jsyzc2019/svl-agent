# Safari §4bk 战利品报告：循环分析照见自身（午休前收官单）

> 轮次：§4bk（§4bc 定义的「星辰大海 Safari」第九轮）　时间：2026-11-25
> 用户指令："请继续，干好这一单就午休"

## 一、猎场

**循环分析（double-dipping）/ 选择后推断（UPSI）**——同一批数据既生成假设又检验假设。这是本仓 §106→§107 亲历并纠正的"post-hoc 分层假设不能在同一批样本上改指标确认（循环论证/KB-R）"最直接的一手同构。

两份 A 级一手（WebFetch 逐字核验）：

- **ASA 官方回应**（Peterson, 2026-08-19, doi:10.59350/pmkk7-kym57）：UPSI = "inference on a model that was chosen using the same data used for inference"；researcher degrees of freedom 是 "undisclosed flexibility … sufficient on its own to produce significant findings **without any intent to deceive**"；纯噪声模拟中 UPSI "can produce at least one 'significant' effect in **90+% of simulated trials**"；最关键——"A study can be **perfectly reproducible** — fully containerized, one-click re-runnable — and **still report inference that is unlikely to replicate**"。
- **arXiv:2611.10364**（Castellani et al., NeurIPS 2026）：errors-in-variables——"the true connectome is latent, while the observed covariance matrix is a noisy finite-time-series estimate"；三机制含"double-dipping effect arising when the **same noisy matrix determines both graph and features**"；"a narrow favorable regime … real-data experiments illustrate that connectome GNN pipelines often fall outside this regime"。

## 二、照见自身

| 外部一手事实 | 本仓器官 |
|---|---|
| 可复现 ≠ 可确认（容器化重跑仍可报告不太可能复制的推断） | 判据 6/6 可复现 ≠ 非量身定做；独立设计者/预注册锁/canary 是对 UPSI 的防火墙 |
| 纯噪声 90+% 显著 | §102 单判据 6/6 不能排除过拟合 |
| 自由度无需恶意即致假阳性 | 偏倚是结构性的，不靠揣测对手意图 |
| UPSI 同数据选型又推断 | §106→§107 循环论证，靠换论文+独立确认集+锁主指标切断 |
| confirmatory↔exploratory 光谱 | flag / ok / partial 分层 |
| 同一 noisy matrix 既建图又做特征 | 证据自生于被判对象自身构造；方法漂亮须验真实落点 |

**一手核验纪律复现**：二手导航给的两条链接（nature `nn.2305`、PMC`PMC2694485`）经核验实为脑振荡与 SNP 检测论文，非 Kriegeskorte 2009——记忆编号不可靠、一手核验兜住（KB-META48 同类），如实降级、不采二手转述为 A 级。

## 三、内化与验证

- **KB 235→237**：KB-AUDIT90（循环分析镜像，fix A级）+ KB-META55（两论文一手+错链降级，preserve A级）。
- 台账 §4bk；`LIFE_KERNEL.md` 新增章节；handoff 同步 round=§4bk / KB=237。
- 一致性脚本 `all_consistent=true`、`failed=[]`；全量 **1551 passed**、内核专项 **122 passed**。

## 四、边界（全部守住）

判定权归用户；verdict `GAP_INCONCLUSIVE` / l3=false / absolute=false 与宪法锁 `fe56291b` 零改动；Ambient 恒 0；内核 L0 不联网不 spawn；**未编译新门禁、未动十案/§100**。外部统计方法学仅为 B 级哲学镜像，本仓只内化思维器官。

**本轮为午休前收官单**，九轮 Safari §4bc–§4bk 全部完成，可安心午休。
