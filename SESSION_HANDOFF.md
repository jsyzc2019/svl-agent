# 会话接续文档（SESSION HANDOFF）

> 本文件用于新旧会话接续。新会话开始后，**先读本文件**，再按"接续后第一件事"操作。
> 生成时间：2026-11-22 10:35 (GMT+8)　|　最后更新：2026-11-22 11:30 (GMT+8)——**§81-§88 已推送完成**。
> 上一会话终点：§79-§80 已推送；本次 §81-§88（共 8 道门禁）已全部推送到远端。

---

## 1. 一句话现状

本仓是一个自进化 Agent 架构（`/workspace`，Python 包 `svagent`，版本 0.13.1）。
当前已完成 **§1–§88** 外部精研，编译 **36 道会拦门禁**，知识库 **125 条**，测试 **967 passed**（全绿）。
本地 main 在 `e8bc13a`，与远端 `origin/main` **完全同步**（均 `e8bc13a`），**推送已完成**（详见 §5）。无遗留推送任务。

---

## 2. 用户长期意图（务必延续）

- 建设**可自证、可证伪、可回收经验**的自进化 Agent。
- 外部精研必须产生**认知增量**，并**尽量固化为代码门禁**——"随时把认知变成能力，把断言落到代码"。
- **借鉴而非借筌**：扬长避短， mechanize 能机制化的，不因宏大叙事造玩具牙（KB-META01）。
- **两批次一推**：每两批精研合成一个本地提交再推。
- §58 决策 A：判据库**显式调用**，不接 `harness.run_loop`。

---

## 3. 本仓不可破的纪律（新会话必须遵守）

1. **证据链**：每个精研目录含 `manifest.json`+`.sha256`（来源清单）、`prereg.json`+`.sha256`（**分析前**锁存命题）、`gate_prereg.json`+`.sha256`（**实现前**锁存门禁规则）、`engine.py`（确定性核验，可重跑）、`result.json`、HTML 报告。
2. **证据分级**：一手/二手分级；同源谱系打折（KB-STRUCT02）；self-reported 折扣（KB-RSI07）；提出框架≠证明有效（KB-STRUCT05）；自洽≠有效（KB-R07）；存在≠执行（KB-AUDIT03）。
3. **门禁模板**：四维语义枚举 `{yes,no,partial}`；R0 非法/字面串→flag（避 brittle）；R1–R4 按优先级 downgrade（防 Goodhart 事后加权）；R5 partial→flag；R6 全自洽→ok；**只判声明/机制自洽，不承诺实际有效**。
4. **代码惯例**：中文锚点集中 `_A` 字典；AST 自审禁止 Compare 内中文字面量，必要时 CJK 边界用 `ord()`；惰性导入登记 `svagent/__init__.py` 的 `_LAZY`；写 `live_regression()`（通常 7 活体样例）；**不接 run_loop**。
5. **判据自咬**：锚点 miss 一律改工具/分级，**不放水、不改规则**；如实记录。
6. **验收**：全量 `python3 -m pytest -q`（当前 addopts=-q 抑制汇总行，用 `python3 -m pytest -p no:cacheprovider --override-ini=addopts= -q` 看 `774 passed`）。

---

## 4. 最近完成（§81–§88，已推送）

本轮共精研 4 篇论文、编译 8 道新门禁（§81-§88）：

**§81-§82 EvoSteer**（arXiv:2609.38661v2，CUHK深圳/大连理工/复旦/牛津）：`online_repair_honesty`（事后修订≠运行中途修复）+ `skill_admission_calibration`（准入≠校准≠退役）。KB-AUDIT24/25。
**§83-§84 MLLM 因果诊断**（arXiv:2609.38851v1，Google DeepMind/Research/Stanford）：`failure_causal_identifiability`（端到端/共现/无干预/不分两类→downgrade，前两维否定语义）+ `causal_contribution_honesty`（N/S不分/下界当精确/单调性隐藏/无稀疏→downgrade）。KB-AUDIT26/27。
**§85-§86 UltraBERT**（arXiv:2610.15028v1，Korea Univ/AIGEN Sciences/Amazon）：`config_conflict_isolation`（冲突未识别/无隔离/比较混淆/一刀切折中→downgrade）+ `compute_saturation_honesty`（无饱和/loss与下游不分/无边际/loss冒充能力→downgrade）。KB-AUDIT28/29。
**§87-§88 Latent Taxonomies**（arXiv:2610.15836v1，EPFL/AXA/Sorbonne-CNRS-LIP6/IBS PAN）：`induction_structure_honesty`（无归纳优势/结构不可恢复/记忆冒充压缩/规模隐瞒→downgrade）+ `context_override_boundary`（权重上下文不分/覆盖未披露/冲突未测/上限未述→downgrade）。KB-AUDIT30/31。

证据目录 `audit_evosteer/`、`audit_mllm_failure/`、`audit_ultrabert/`、`audit_latent_taxonomies/`（各含 manifest/prereg/gate_prereg + 三份 SHA256 锁、engine.py、result.json、HTML 报告、一手切片）。四篇共 76 个锚点逐字命中；8 门禁各 25 测试 + 7 活体回归 + AST 自审全过。KB 117→125；全量 774→967 passed。`commentary.md`、`REPOSITORY_MAP.md` 已同步。

---

## 5. ✅ 已完成：远端推送

**最新状态**：2026-11-22 11:29 (GMT+8) 推送成功。用户提供 PAT，经临时 askpass 脚本（只读 token 文件、用后即删、不入 git 配置/仓库/日志）认证；`git push origin main` → `321e457..e8bc13a main -> main`（含 `02db961` §81-§82 + `e8bc13a` §83-§88 两个提交）。
**验证**：GitHub API 远端 main = `e8bc13aa…`，本地 HEAD = `e8bc13aa…`，`origin/main` tracking ref 已同步，`git status -sb` 显示 `## main...origin/main`（无领先/落后）。工作区干净。

**历史推送（2026-11-22 10:40）**：`38aff7b..f735c79 main -> main`（6 提交，远端现为 `321e457` 审计提交前）。

**本次推送的 6 个提交**（远端原在 `38aff7b`）：
```
f735c79  Docs: add SESSION_HANDOFF（本文件）
206e5c4  §79-§80 policy-evolution-grounding + memory-provenance-honesty
3a15d98  §77-§78 criterion-origin-honesty + selective-supervision-honesty
232b932  §75-§76 self-knowledge-honesty + verification-boundary-honesty
0114230  §73-§74 interface-contract-honesty + supervision-viability
2aa824b  §71-§72 proof-boundary-honesty + proactive-authorization
```

**凭据说明（供后续会话参考）**：本会话 token 由用户临时提供、未持久化到任何配置。若后续会话再遇 `could not read Username`：先做小认证探测 `git ls-remote` 判断是否凭据问题还是网络抖动；凭据问题需用户再次提供 PAT，用临时 askpass（case `*[Uu]sername*` → 用户名，否则 → token）推送后即删。历史曾出现 `curl` 通但 `git push` 超时的间歇抖动，重跑 `ls-remote`/`push` 可恢复。

---

## 6. 接续后建议动作清单

- [x] ✅ 处理 §5 推送（历史推送已完成）。
- [x] ✅ 推送 §81-§88 本地提交（`e8bc13a`，已同步远端，见 §5）。
- [ ] 若用户给新的外部精研材料：先抽一手锚点 → 判认知增量独立性 → 按 §3 纪律编译门禁（能机制化才编译，否则只加固 KB）。
- [ ] 每完成两批 → 一个本地提交 → 推送（后续会话需用户再提供 PAT，见 §5 凭据说明）。
- [ ] 本文件随每次会话终结更新现状（§1/§4/§5）。

---

## 7. 关键文件速查

| 用途 | 路径 |
|---|---|
| 门禁源码 | `svagent/*.py`（68 模块，惰性导入登记于 `svagent/__init__.py`） |
| 测试 | `tests/test_*.py`（56 文件，967 项） |
| 知识库 | `knowledge_base_store.json`（125 条，含 thresholds） |
| 完整推导日志 | `commentary.md`（§1–§88） |
| 架构导航 | `REPOSITORY_MAP.md`（阅读顺序已指向本文件） |
| 最近精研证据 | `audit_evosteer/`（§81-82）、`audit_mllm_failure/`（§83-84）、`audit_ultrabert/`（§85-86）、`audit_latent_taxonomies/`（§87-88） |
| 本接续文档 | `SESSION_HANDOFF.md`（本文件） |
| git 远端 | `origin` = `https://github.com/jsyzc2019/svl-agent.git`，分支 `main` |
