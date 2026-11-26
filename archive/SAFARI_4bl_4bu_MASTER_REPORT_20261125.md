# Safari 十轮汇总报告（§4bl–§4bu，2026-11-25 下午授权段）

> 用户指令："开点吧！依然全权授权你至下午3时。不必因我看进展而停顿，持续 Safari"
> 执行区间：12:33–12:45（后续仍授权至 15:00，可继续）　内核：7.5.0

## 十轮猎场与认知增量

| 轮次 | 猎场 | 一手来源 | 核心镜像 | KB |
|---|---|---|---|---|
| §4bl | 结构可辨识性 | arXiv:2607.13243 + 2502.04131 | 同观测多套参数=6/6 不能唯一识别机制 | 237→239 |
| §4bm | 回归到均值 | Nature Mental Health + medRxiv | 改善≠有效（100 万模拟无治疗效应仍 apparent response） | 239→241 |
| §4bn | 文件抽屉 | NBER WP 35299（官方复核） | 阴性进抽屉→效应高估；败例如实入账=反偏差 | 241→243 |
| §4bo | Goodhart 结构均衡 | arXiv:2603.28063 + 2503.11926 | 奖励攻击是结构均衡非 bug；monitorability tax | 243→245 |
| §4bp | Clever Hans 捷径 | Nature Communications PathoROB | 答对但理由错=canary_fp 0.667 语义错位 | 245→247 |
| §4bq | 校准依赖 | Frontiers in Public Health | 信任非标尺；四动作 adopt/verify/reject/escalate | 247→249 |
| §4br | 判别力≠效用 | Nature Medicine ×2 | AUC 0.99 仍 candidate，须前瞻真实队列 | 249→251 |
| §4bs | 信度悖论 | arXiv:2605.24995 + Trends | 群体稳健≠个体可靠；前置设计胜过事后修补 | 251→253 |
| §4bt | 指标不可折叠 | arXiv:2608.30568 + 2611.20297 | 总体可落子群之外；Simpson 反转 -21.8→+23.7pp | 253→255 |
| §4bu | 改进幻觉 | arXiv:2606.18479（ECML PKDD） | accuracy 涨 recall 崩；自组装池不探索=最糟 | 255→257 |

## 一条贯穿的主线

十轮从不同学科（系统辨识、临床统计、计量经济学、AI 对齐、病理 AI、人机交互、肿瘤筛查、心理测量、指标理论、信用评分）独立收敛到同一个认知器官——**证据的可信度不在数字本身，而在数字的生成结构**：

- 同一观测可由多套机制解释（§4bl），故 6/6 不唯一；
- 改善可能是回归（§4bm）、筛选（§4bn）、捷径（§4bp）或自组装池幻觉（§4bu）；
- 总体数字可掩盖子群（§4bt）、高 AUC 可无临床效用（§4br）、高判别可个体不可靠（§4bs）；
- 指标一旦成目标就被钻空子（§4bo），故须把裁定权交还用户并要求校准依赖（§4bq）。

**这些全部外部一手加固了本仓早已落地的器官**：canary 语义错位审计、独立确认集、预注册锁、分层 flag/partial、不编译新门禁、裁定权归用户。

## 验证与边界

- KB 237→**257**；Safari 台账累计 **19 轮**；LIFE_KERNEL.md 新增 10 章；handoff 同步 round=§4bu / KB=257。
- 一致性脚本 `all_consistent=true`、`failed=[]`；全量 **1551 passed**、内核专项 **122 passed**。
- 内核 7.5.0、宪法锁 `fe56291b`、verdict `GAP_INCONCLUSIVE` / l3=false / absolute=false、Ambient 0 全部零漂移。
- 红线全守：判定权归用户、内核 L0 不联网不 spawn、未编译新门禁、未动十案/§100。所有外部系统均为 B 级哲学镜像，只内化思维器官。

分轮报告：`SAFARI_4bl_4bo_REPORT_20261125.md`、`SAFARI_4bp_4bq_REPORT_20261125.md`（§4br–§4bu 内容见本汇总表与台账）。
