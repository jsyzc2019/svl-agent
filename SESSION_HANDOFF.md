# 会话接续文档（SESSION HANDOFF）

> 本文件用于新旧会话接续。新会话开始后，**先读本文件**，再按"接续后第一件事"操作。
> 生成时间：2026-11-22 10:35 (GMT+8)　|　最后更新：2026-11-22 11:58 (GMT+8)——**§89 FJ 工程已本地提交 `d106a08`，未推送**。
> 上一会话终点：§88 已推送完成；本次完成 §89 FJ 取证法官化升级（第三方审计最高杠杆落地），本地未提交/未推送。

---

## 1. 一句话现状

本仓是一个自进化 Agent 架构（`/workspace`，Python 包 `svagent`，版本 0.13.1）。
当前已完成 **§1–§89**：§1–§88 外部精研（36 道会拦门禁）+ **§89 FJ 取证法官化升级**（把门禁从填表裁判改成取证法官）。知识库 **125 条**，测试 **1010 passed**（全绿，§89 新增 43 项）。
**§88 已推送**（远端 main = `8c8ecc9`）。**§89 FJ 工程已本地提交 `d106a08`，领先 origin/main 1 个提交、尚未推送**（详见 §4b）；推送需用户再提供 PAT（见 §5）。

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

## 4b. §89 FJ 取证法官化升级（本地未提交，待推送）

用户认可第三方独立审计（[INDEPENDENT_AUDIT_20261122.html](INDEPENDENT_AUDIT_20261122.html)）最高杠杆建议：把门禁从「填表裁判」改成「取证法官」。按 [OPTIMIZATION_PLAN_20261122.md](OPTIMIZATION_PLAN_20261122.md) 六阶段全部推进完毕：
- **阶段1-2** `svagent/forensics.py`（三态取证内核）+ `svagent/forensic_gates.py`（三道试点 adjudicate_*，读一手原文逐字锚点自取四维；篡改证据→裁决翻转，原 check_* 一字未改）。
- **阶段3** `svagent/evidence_chain.py`（SHA256 锁执行者：失配拒判 + 批量链审，32 目录如实标注，落 `chain_audit_report.json`）。
- **阶段4** `svagent/growth_bridge.py`（KB 75 条 fix 机制 + 取证缺口 → PDCA 真实注入，落 `growth_bridge_consumption.json` 消费痕迹，替代关键词计数自证）。
- **阶段5** `svagent/evidence_scope.py`（6 模拟模块 synthetic 标记）+ `build_readme_stats.py`（README 统计自动化，§1–§40→§88）+ `svagent/cli.py`（`svl-audit` console script）。
- **阶段6** 成果报告 `FJ_ACHIEVEMENT_REPORT_20261122.html`；`commentary.md` §89、`REPOSITORY_MAP.md`、`README.md` 已同步。

**验收**：全量 967→1010 passed（+43），三道取证裁决全 ok（与诚实论文一致），链失配即拒判，消费链 75/75/75 一致。成熟度 L1.5→L2 边缘，不宣称 L3（外部供料/目标/凭据仍靠人）。已本地提交 `d106a08`（含 16 新增 + 9 修改，**本地领先 origin/main 1 提交**）。**下一步：用户确认后推送（需 PAT）。**

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
- [x] ✅ §89 FJ 取证法官化工程全部推进（见 §4b，本地未提交）。
- [ ] **提交并推送 §89 FJ 工程**（用户确认后；需再提供 PAT，见 §5；两批次一推纪律当前 §89 单批可独立提交）。
- [ ] 若用户给新的外部精研材料：先抽一手锚点 → 判认知增量独立性 → 按 §3 纪律编译门禁（能机制化才编译，否则只加固 KB）。
- [ ] 后续精研可复用 FJ 取证入口：新门禁若有一手原文切片，可加 `adjudicate_*` 取证入口（模式见 `forensic_gates.py`）。
- [ ] 本文件随每次会话终结更新现状（§1/§4/§4b/§5）。

---

## 7. 关键文件速查

| 用途 | 路径 |
|---|---|
| 门禁源码 | `svagent/*.py`（74 模块，惰性导入登记于 `svagent/__init__.py`） |
| FJ 取证层 | `svagent/forensics.py` / `forensic_gates.py` / `evidence_chain.py` / `growth_bridge.py` / `evidence_scope.py` / `cli.py` |
| 测试 | `tests/test_*.py`（61 文件，1010 项） |
| FJ 计划/成果 | `OPTIMIZATION_PLAN_20261122.md` / `FJ_ACHIEVEMENT_REPORT_20261122.html` / 独立审计 `INDEPENDENT_AUDIT_20261122.html` |
| 知识库 | `knowledge_base_store.json`（125 条，含 thresholds） |
| 完整推导日志 | `commentary.md`（§1–§88） |
| 架构导航 | `REPOSITORY_MAP.md`（阅读顺序已指向本文件） |
| 最近精研证据 | `audit_evosteer/`（§81-82）、`audit_mllm_failure/`（§83-84）、`audit_ultrabert/`（§85-86）、`audit_latent_taxonomies/`（§87-88） |
| 本接续文档 | `SESSION_HANDOFF.md`（本文件） |
| git 远端 | `origin` = `https://github.com/jsyzc2019/svl-agent.git`，分支 `main` |
