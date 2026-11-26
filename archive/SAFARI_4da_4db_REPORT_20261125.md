# Safari §4da + §4db 战利品报告（2026-11-25）

> 用户令："你持续推直至下午3时"（§4bc 续）。授权至 15:00，连续推进、不逐轮等待。

## §4da · 计划谬误（A 级一手实证）
一手：Katt et al., *The Planning Fallacy in the Orthopedic Operating Room*, Cureus 2021;13(1):e12433，PMID 33552753。9 位骨科医生、759 例：总手术室时间低估 **17.3%**（p=0.034）但手术时间未低估（p=0.590）；反馈后估计误差从 **13.6→10.9 分钟**（p=0.031）；场地系统性差异（医院低估 vs 门诊中心高估，p<0.001）。

照见本仓：预测系统性乐观须打折（§4cl）；有反馈就能校准、偏误非不可逆（§4cf，每轮验证即反馈回路）；偏误选择性存在须逐维测不可一刀切；环境结构影响估计须分层（§4cm）。

**诚信**：planning fallacy 首轮长查询零结果如实记录、简化后命中。

## §4db · 教师内隐态度（A 级一手元分析）
一手：Pit-Ten Cate & Glock, *Teachers' Implicit Attitudes Toward Students From Different Social Groups: A Meta-Analysis*, Front Psychol 2019;10:2832，PMID 31920865。43 篇→22 篇 34 研究；内隐态度平均效应 **0.56** 偏向非边缘群体；高异质性；**内隐与外显态度低或不显著相关**。

照见本仓：内隐自动激活引导行为，偏见无需恶意（§4cd）；内隐外显低相关——声明的公正不证明实际无偏，须测行为（§4cc）；效应有方向但不跨情境一致须分层（§4cm）；时间压力下偏见更强、不赶工留核验时间（§4cp）。

**诚信**：本篇主题是教师内隐态度，与经典皮格马利翁"期望→成绩"因果相邻但不同，如实标注、不冒充。

## 内化与验证
- KB 新增 `KB-AUDIT123/124`、`KB-META88/89`（301→305）；台账 50→52 轮（末 §4db）；`LIFE_KERNEL.md` 新增 2 章；handoff 正则同步（305）。
- 一致性脚本 `all_consistent=true`、`failed=[]`（handoff=truth=305）；KB 305、四编号各 1、无重复。
- 全量 **1551 passed**、内核专项 **122 passed**（junitxml failures=0, errors=0）。
- 内核 `7.5.0`、宪法锁 `fe56291b`、verdict `GAP_INCONCLUSIVE` / l3=false / absolute=false、Ambient=0 **全部零漂移**。

## 红线
判定权归用户；内核 L0 不联网不 spawn；Ambient 恒 0；**未编译新门禁、未动宪法/判定/十案/§100**。外部一手仅作 A 级哲学镜像，主题边界如实标注。
