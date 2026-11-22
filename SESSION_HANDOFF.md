# 会话接续文档（SESSION HANDOFF）

> 本文件用于新旧会话接续。新会话开始后，**先读本文件**，再按"接续后第一件事"操作。
> 生成时间：2026-11-22 10:35 (GMT+8)　|　上一会话终点：§79-§80 完成并本地提交。

---

## 1. 一句话现状

本仓是一个自进化 Agent 架构（`/workspace`，Python 包 `svagent`，版本 0.13.1）。
当前已完成 **§1–§80** 外部精研，编译 **28 道会拦门禁**，知识库 **117 条**，测试 **774 passed**（全绿）。
本地 main 领先远端 **8 个提交**；**推送因无 GitHub 凭据受阻**，尚未完成（详见 §5）。

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

## 4. 最近完成（§79–§80，提交 206e5c4）

精研 arXiv:2610.19366v1《Seeing, Maintaining, and Learning: The Evolution of Multimodal Agent Memory》综述。
- **PDF 36.5MB 三次超时失败** → 降级用 arXiv 官方 HTML 全文作一手证据（已如实记录）；项目主页统计口径与论文不同，分标不混用。
- 编译两道新门禁（**第 27、28 道**）：
  - `svagent/policy_evolution_grounding.py:check_policy_evolution_grounding`（§79）——"正确率↑≠接地保持"：策略不可寻址/反馈未归因策略级/证据路径被削弱/修订未经验证 → downgrade。
  - `svagent/memory_provenance_honesty.py:check_memory_provenance_honesty`（§80）——"召回量≠可恢复溯源+时间有效性"：溯源是可选元数据/证据不可恢复/时间有效性缺失/不可逆 → downgrade。
- 证据目录 `audit_multimodal_memory/`；报告 `audit_multimodal_memory/multimodal_memory_report.html`。
- KB 新增 `KB-AUDIT22/23`（115→117）；新增测试 `tests/test_policy_evolution_grounding.py`、`tests/test_memory_provenance_honesty.py`（各 25 项）。
- 一手锚点 39/39 命中；三处跨行断字锚点修工具不放水；双文件 AST 自审干净；`__init__.py` 已登记惰性导入。
- 文档已更新：`commentary.md`（§79-§80）、`REPOSITORY_MAP.md`（门禁表/测试列表/头部统计/推导链）。

---

## 5. ⚠️ 未完成：远端推送（接续后第一件事）

**状态**：本地 main = `206e5c4`，领先 `origin/main`（`2fa339e`）**8 个提交**：

```
206e5c4  §79-§80 policy-evolution-grounding + memory-provenance-honesty
3a15d98  §77-§78 criterion-origin-honesty + selective-supervision-honesty
232b932  §75-§76 self-knowledge-honesty + verification-boundary-honesty
0114230  §73-§74 interface-contract-honesty + supervision-viability
2aa824b  §71-§72 proof-boundary-honesty + proactive-authorization
38aff7b  §69-§70 async-delegation-lifecycle + memory-scope
863e0f0  §67-§68 memory_curation
f07b6db  §61-§66 serving-signal/retrieval-grounding/session-continuity 等
```

**失败原因**：`git push origin main` → `fatal: could not read Username for 'https://github.com': No such device or address`。
已排查：`gh auth status` 未登录；无 `GH_TOKEN`/`GITHUB_TOKEN` 环境变量；无 `~/.git-credentials`；无可用 GitHub MCP 连接器（当前仅 scheduler-assistant / spaceengine 两个未连接 connector）。**非网络抖动，是凭据缺失**，历史多次同因失败。

**新会话接续后按此顺序处理**：
1. 先确认用户是否已提供凭据（PAT / gh 登录 / SSH key）。**若仍无凭据，不要反复重试 push**，直接如实告知用户"推送受阻于凭据，需用户配置"。
2. 凭据就绪后任选其一：
   - `gh auth login`（浏览器或 token），再 `git push origin main`；
   - 或 `git remote set-url origin https://<TOKEN>@github.com/jsyzc2019/svl-agent.git` 后 push（注意 token 不入日志/不入库）；
   - 或配置 SSH key 改用 `git@github.com:...`。
3. push 成功后在 `commentary.md` 追加一行推送记录（含时间、提交数、目标分支）。

---

## 6. 接续后建议动作清单

- [ ] 处理 §5 推送（第一优先级；无凭据则如实报告，不硬试）。
- [ ] 若用户给新的外部精研材料：先抽一手锚点 → 判认知增量独立性 → 按 §3 纪律编译门禁（能机制化才编译，否则只加固 KB）。
- [ ] 每完成两批 → 一个本地提交 → 尝试推送（凭据就绪时）。
- [ ] 本文件随每次会话终结更新现状（§1/§4/§5）。

---

## 7. 关键文件速查

| 用途 | 路径 |
|---|---|
| 门禁源码 | `svagent/*.py`（59 模块，惰性导入登记于 `svagent/__init__.py`） |
| 测试 | `tests/test_*.py`（48 文件，774 项） |
| 知识库 | `knowledge_base_store.json`（117 条，含 thresholds） |
| 完整推导日志 | `commentary.md`（§1–§80） |
| 架构导航 | `REPOSITORY_MAP.md`（阅读顺序已指向本文件） |
| 最近精研证据 | `audit_multimodal_memory/`（§79-§80） |
| 本接续文档 | `SESSION_HANDOFF.md`（本文件） |
| git 远端 | `origin` = `https://github.com/jsyzc2019/svl-agent.git`，分支 `main` |
