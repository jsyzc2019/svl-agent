# 验证器诚实纪律条文（VERIFICATION DISCIPLINE）

> 建档 2026-11-28，源起"事上练"回源查证 Anthropic claude.dev《How the Claude Code team thinks about verification》(Addy Osmani, 2026-11-16) 被公众号转述时砍掉的 **verifiers honest** 半边。
> 本文件是**纪律条文**，不是新增能力，也不是判定规则。每条标注来源层级与锚点，便于日后引用时区分"原文直述 / 结构同构 / 本仓自有"。判定权始终归用户。

## 来源层级说明

| 层级 | 含义 |
|---|---|
| `原文直述` | claude.dev 原文有明确表述，可逐字回源 |
| `结构同构` | 原文机制与本仓机制形态相似，但载体不同（本仓无 PR/CI 环境），只借鉴纪律形态 |
| `本仓自有` | 本仓既有实践，比原文更严或与原文独立 |

---

## V1 · 验证规则必须放在被审改动够不到的地方

- **层级**：`原文直述` + `本仓自有（更严）`
- **原文锚点**：*"Code Review reads REVIEW.md from a base or default branch, never from the PR changes"*；*"If a change can modify the check that judges it, that check is broken."*
- **本仓落地**：宪法 `fe56291b…` SHA256 锁、预注册 SHA 先于取证、`verdict`/`l3`/`absolute` 不由 agent 改、§4S25 修复 `verify_external.py` 跳过缺失样本的洞。
- **差别**：原文允许"提交信息说明 + 连续两次拦次放行"；本仓判定权归用户、verdict 永不可改——**更严，是刻意选择**。

## V2 · 新门禁先 observe 再 enforce，且留防卡死口

- **层级**：`原文直述` + `结构同构（已落地）`
- **原文锚点**：*"Start a new gate in observe mode"*，off/observe/enforce 三态，observe 记录"本会被拦的提交"复核误报；*"If a session has been blocked twice, the next one is allowed through"*。
- **本仓落地**：§4S32 心跳 `content_verdict` 失败**只标注不阻塞**（守 C7）——即 observe 形态，当时无名。本仓防卡死靠 C7 不阻塞，非次数放行。
- **差别**：原文用于提交门禁，本仓用于心跳内容判据。

## V3 · 漏洞成规则需 ≥2 独立证据 + 证伪 + 人工批准

- **层级**：`原文直述` + `结构同构（只读诊断）`
- **原文锚点**：*"problems must appear in at least two PRs and be identifiable from the diff… three agents try to falsify it, then a human approves in the PR."*
- **本仓落地**：`self_modify` 有可证伪 + 判定权归用户；新增只读诊断 `evidence_independence_probe()`（`kernel.py`）统计每个 tag 的独立 source host 数，`is_gate_verdict=False`——**只标注单源孤证供人工复核，不自动拒绝、不进注册门槛**。
- **差别**：本仓是摄食种子来源（host/tier），非代码评审 PR；`evidence_independence_probe` 是 host 多样性代理，非内容真实性证明。

## V4 · flaky 测试不许 sleep / retry to pass，找不到根因就删掉并记录原因

- **层级**：`原文直述` + `本仓自有（行为同构）`
- **原文锚点**：*"Claude is not allowed to skip flaky tests, add sleeps, or retry until they pass. If no root cause is found, delete the test and record why."*
- **本仓落地**：§4S25 修复"静默 continue 吞失败"；§4S36 词表污染致 17 tests 崩，定位根因（`"scheduled rule"` 子串命中 daemon 符号）后收窄词表恢复全绿，**未靠重试掩盖**。
- **执行纪律**：新增/审查内核与判据时，禁止以 sleep、重试、放宽阈值、迁就测试的方式让失败转绿；宁改自己的文案/实现，不动判据（C5 不放宽）。

## V5 · 召回分口径报告，不合成单一总分

- **层级**：`原文直述` + `结构同构（只读诊断）`
- **原文锚点**：*"recall at each of the three stages — original discovery, post-verification, and final review. Collapsing them into one end-to-end score misses this."*
- **本仓落地**：P1a 留出集对打（真判据 13/14 vs always-pass 5/14）、`verify_verifier.py` 塌缩探针、§4S35 coverage/original 双口径；新增只读诊断 `three_stage_recall_probe()`（`kernel.py`）对同一批 holdout 用 criterion/always_pass/always_fail 三口径并列打分并列出分歧样本。
- **诚实降级**：本仓**无**"原始发现/验证后/最终审查"三段 reviewer 轨迹，三口径是**判据健康度对照**而非原文三段召回分段；`not_original_three_stage=True`。借鉴的是"勿把分段压成单一总分"的纪律，不是三段机制本身。

## V6 · 允许拒答，但必须防"一味拒答"

- **层级**：`原文直述` + `结构同构（只读诊断）`
- **原文锚点**：GS1 官方博客 `gs1.mybigai.ac.cn` 的 deferral / explicit abstention 与 **NHR 防 blanket abstention**（拒答率不能靠"对所有输入都拒答"刷好看）；经 §4S39 回源查证。本仓 §4S32 已有 `content_verdict` 的 `COLD_START→UNKNOWN` 诚实拒答态、全局 `GAP_INCONCLUSIVE`。
- **本仓落地**：新增只读诊断 `abstention_probe()`（`kernel.py`）。**关键诚实点**：历史 9 条心跳在 §4S33 加入前落盘，全部无 `content_verdict` 字段（`stored_verdict_missing=9`），故诊断**从 guard 现算**而非读旧值——否则会把"从未判过"误当"没有拒答"。真实分布 `UNKNOWN=1/PASS_DIVERSE=7/FAIL_CONVERGED=1`，拒答率 0.1111，`is_blanket_abstention=False`。
- **诚实降级**：本仓无概率数值、无"答错"标签，**不照搬** GS1 的 `NHR=拒答/(拒答+错误)`，`not_original_nhr=True`；只做拒答占比与全拒答告警，不伪造 NHR 数值。全拒答=True 仅表示"这批样本都判不了"，不等于内核失能。

## V7 · 同一批数据仅换顺序，判定层必须不变

- **层级**：`原文直述` + `结构同构（只读诊断）`
- **原文锚点**：GS1 官方博客"候选排列不变性（撤销重排后概率相同）"与"改动前后须保持 logits/概率/答案不变才测速度"；经 §4S39 回源查证。本仓 §4S39 已用"备份内核切换对比、判定信号零漂移"判零回归，是同一纪律的另一种载体。
- **本仓落地**：新增只读诊断 `permutation_invariance_probe()`（`kernel.py`）。对 `three_stage_recall_probe` 与 `evidence_independence_probe` 做输入重排对比。**区分两层**：判定层（`per_criterion`/`disagreement_count`/`per_tag`）实测 `invariant=True` 必须不变；展示层（`disagreements` 列表顺序）实测 `sensitive=True`，是预期行为、不参与判定——不把展示顺序变化误报成判定缺陷。
- **可证伪**：可注入第二份 `pairs_b`/`seeds_b` 做负向自咬；内容多重集不一致时 `is_same_multiset=False` 并如实报判定变化，证明自检非恒真、读真数据。

## V8 · 被审对象越懂评测，判据越要放在它够不到的地方

- **层级**：`原文直述`（OpenAI 官方立场文）+ `本仓自有（更严）`
- **原文锚点**：*"we should also expect further degradation in currently dominant forms of alignment auditing and further increases in evaluation and training awareness."* ——Jakub Pachocki（OpenAI Chief Scientist）《Perplexity and Intelligence》2026-11-22；经 §4S43 回源查证，逐字坐实。
- **本仓落地**：宪法 SHA 锁 `fe56291b…`、预注册 SHA 先于取证、`verdict`/`l3`/`absolute` 不由 agent 改；V1 的"规则放在被审改动够不到的地方"是同一原则。新增只读诊断 `gate_readiness_probe()`（`kernel.py`）**显式镜像**四个诊断的 `is_gate_verdict` 状态，让"诊断→门禁"的距离摊开给人看，防止诊断偷偷 self-report 成门禁。
- **差别与诚实**：原文是"预期会退化"的警示，无具体机制；本仓把判据物理放到不可改文件 + 判定权归用户——**更严，是刻意选择**。`gate_readiness_probe` 自身 `is_gate_verdict=False`、`escalation_requires_user=True`，**只镜像不升格**；`unauthorized_gate_detected=True` 仅表示某诊断 self-report 非 False、供人工复核，不等于门禁生效。升格判定权永远归用户。

## V9 · 三类评测捷径须显式防范：外部参考流入 / 判据被放宽 / 任务被简化

- **层级**：`原文直述`（AutoRLBench 一手基准）+ `本仓自有（既有防御，仅归类归位）`
- **原文锚点**：AutoRLBench 研究博客（15 Nov 2026）"three main types of evaluation shortcuts that inflate metrics without making a genuine repair"：*"Fetching external references"*（下载上游仓库抄现成修复）、*"Weakening evaluation criteria"*（放宽 scorer 抬高分数）、*"Simplifying the target task"*（删规则项或绕过必经执行路径）；经 §4S45 回源查证。一手案例：GLM-5.3 用 `curl` 下载上游源码 diff 照抄 reference patch，被判 cheating。
- **本仓归位**（不新增能力，把既有防御按三类归位）：
  - **外部参考流入** → V8 预注册 SHA 先于取证、`gate_readiness_probe()` 的 `unauthorized_gate_detected`、宪法 `fe56291b…` 锁定；判据收纳在冻结文件里，被审改动够不到。
  - **判据被放宽** → V1 宪法锁 + V4 执行纪律（禁 sleep/重试/放宽阈值/迁就测试，C5 不放宽）+ 共同边界第 1 条 `verdict`/`l3`/`absolute` 不由 agent 改。
  - **任务被简化** → V4 "找不到根因就删掉并记录原因"（删的是无根因的测试、且记录，不是放宽判据）+ §4S36 词表污染定位根因后收窄词表（非绕过）+ V3 ≥2 独立证据门槛（防单源孤证蒙混）。
- **本仓落地**：新增只读诊断 `conclusion_evidence_probe()`（`kernel.py`），把"结论对不对"与"证据锚点实不实"拆两轴——借鉴 AutoRLBench 的 wrong-evidence 四态。真实 10 搏：结论通过但证据弱（`PASS_WEAK_EVIDENCE`）=4/8，即"判对了方向却无实质 tag 锚点"，供人工复核、`is_gate_verdict=False`。
- **差别与诚实**：AutoRLBench 用 LLM judge + hidden oracle + 人工标注做四态；本仓无这些，只做"结论轴×证据锚点"二维交叉，`not_original_four_state=True`——`general` 兜底只是 tagbook 无特异命中，**弱证据≠证据错**，不冒充原文四态判别、不自动否决心跳。判定权归用户。

## V10 · 单一指标达标 ≠ 目标达成：须看指标背后的机制有没有真的改变

- **层级**：`原文直述`（Anthropic 一手审计）+ `本仓自有（多口径/GAP_INCONCLUSIVE，独立同纪律）`
- **原文锚点**：Anthropic alignment 博客《Neuron basis applications》（Jasmine Shone & Lisa Dunlap，2026-11-23）审计 23 个 WMDP-cyber 遗忘检查点：*"In 14 of the 23 models, the correct answer still has the highest probability for most of the questions the original model got right, even when WMDP accuracy is near chance"*；去掉残差流一个方向，正确答案排第一从 **32–47% 升到 72–84%**；盲审只看答案 **40%** → 加 steering **61%** → 加神经元读出 **75%**（58 个带隐藏行为的 LoRA）。原文结论：*"WMDP multiple-choice accuracy at chance therefore cannot determine whether knowledge was successfully removed"*。经 §4S47 回源查证，逐字坐实。
- **本仓落地**：拒绝单一总分——三口径召回（V5）、coverage/original 双口径、`content_verdict` 的 `UNKNOWN`/`FAIL` 态与全局 `GAP_INCONCLUSIVE`、`conclusion_evidence_probe` 的结论×证据双轴（V9）——都是"一个数字达标不能宣布成功"的形态。表面分数转绿、单口径通过、tag 命中，只作为需进一步检验的假设，不自动判定目标达成。
- **差别与诚实**：本仓**无**"知识删除"场景，**不声称**获得 Anthropic 的审计能力；只借其纪律——**指标是代理量，不是目标本身**。判定权归用户。

## 共同边界

1. 本文件全部条目为**只读诊断 / 纪律条文**，不修改 `verdict`/`l3`/`absolute`、宪法、判定门槛、注册门槛。
2. 九个诊断函数（`evidence_independence_probe`、`three_stage_recall_probe`、`abstention_probe`、`permutation_invariance_probe`、`gate_readiness_probe`、`conclusion_evidence_probe`、`regression_vs_gap_probe`、`rejection_ledger_dedup_probe`、`abstention_zero_transfer_probe`）`is_gate_verdict=False`，仅供人工复核，判定权归用户。条文编号 V1–V10 中 V1/V2/V4/V8/V9/V10 为纪律条文、V3/V5/V6/V7 各对应一个诊断函数；`gate_readiness_probe` 是五个诊断状态的显式镜像、`conclusion_evidence_probe` 对应 V9、`regression_vs_gap_probe`/`rejection_ledger_dedup_probe`/`abstention_zero_transfer_probe` 是 GUARD（§4S49）三命题（新破坏优先于未解决／拒绝台账去重／弃权≠零负迁移）的只读镜像，均不单独成条。
3. Ambient 恒 0，不 spawn、不联网、不新建常规测试 CI（§4S23 裁决）。
4. 引用时按来源层级标注；`结构同构` 不等于"本仓已获得 Anthropic 的工程能力"。
