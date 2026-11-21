# 仓库地图（Repository Map）

> 本仓约 120 个根目录文件并非杂乱堆放，而是 **N 条彼此独立的实验/研究线** 的产物。
> 每条线遵循同一纪律：**预注册（preregistration）→ SHA256 锁存 → 证据 → 结果 → 报告**。
> 本文件按主题归位，帮助读者快速定位；文件路径刻意保持平铺，因为脚本内与锁存文件内
> 记录了这些精确路径，移动文件会破坏可复现性。

---

## 0. 阅读顺序（建议）

| 顺序 | 文件 | 作用 |
|---|---|---|
| 1 | `README.md` | 核心命题、三层递归、关键实测结果、设计原则 |
| 2 | `commentary.md` | 完整推导日志，§1–§68 逐节记录机制如何长出来 |
| 3 | `REPOSITORY_MAP.md`（本文件） | 文件按主题归位 |
| 4 | `svagent/` | 可执行代码（50 个模块，惰性导入） |
| 5 | `tests/` | 回归测试（446 项，`python3 -m pytest -q`） |

---

## 1. 核心代码与工程

| 位置 | 说明 |
|---|---|
| `svagent/` | 主包。核心闭环、自组织、判据自举、PDCA、认知/目的论/价值/机制/估参、知识库与各道门禁 |
| `tests/` | 全部回归测试，`test_<模块>.py` 与 `svagent/<模块>.py` 一一对应 |
| `examples/quickstart.py` | 最小上手示例 |
| `.github/workflows/ci.yml` | 三版本 Python 矩阵 + 12 个 smoke demo |
| `pyproject.toml` | 包元数据、依赖、pytest 配置 |
| `CONTRIBUTING.md` / `LICENSE` | 贡献规范 / MIT 许可 |

代码分层（由底到高）：

```
core → verifiers → harness → handoff          L0 产物层：生成→判据→返工→交接
      → experiment / evolution / self_evolving L1 判据层：自举 + 对抗红队 + 复利
      → autopoiesis / pdca                      L2 元层：开放自组织 + PDCA 驱动
      → insight / telos / axiology / mechanism / estimation   认知升级→目的论→价值→机制→估参
      → knowledge_base + 各 *gate/*analysis                   知识库与把外部经验编译成的门禁
```

---

## 2. 实验/研究线索引

每条线的文件命名前缀即主题。带 `*_prereg.sha256` 的线遵循预注册锁存纪律。

### A. 叙事核对主线（项目起点）
- 代码：`svagent/core.py` `verifiers.py` `harness.py` `handoff.py` `demo.py`
- 构建：`build_blind_report.py` `build_audit_report.py` `build_reflection_report.py`
- 产物：`finance_blind_test_report.html` `finance_blind_test_result.json` `independent_audit_report.html` `framework_reflection_report.html`

### B. 真实财报真实性检验
- 代码：`svagent/finance_fetch.py` `finance_audit.py`
- 数据：`financials.json`（5 家真实公司 2021–2025 + 造假对照）、`real_financials_cache.json`、`sse_daily.json`、`china_monthly_raw.json` `china_ppi_monthly.json` `china_invsales_ratio.json`
- 预注册：`sse_preregistration.json` + `sse_prereg.sha256`
- 构建/产物：`build_sse_report.py` `build_finance...`；`sse_report.html` `sse_result.json` `sse_full_result.json`

### C. 彩票/随机性诊断（双色球）
- 代码：`svagent/ssq_randomness.py` `ssq_diagnose.py` `ssq_retrospective.py`
- 数据：`ssq_history.json`
- 预注册：`ssq_preregistration.json` + `ssq_prereg.sha256`
- 产物：`ssq_report.html` `ssq_result.json` `ssq_full_result.json` `ssq_retrospective_report.html` `ssq_retrospective_result.json` `ssq_retrospective_store.json`
- 构建：`build_ssq_report.py` `build_retro_ssq_report.py`

### D. AI 生成文本检测（网文）
- 代码：`svagent/ai_text_detect.py`、`ai_samples_raw.py`、`build_samples.py`
- 数据：`webnovel_samples.json`、`doupo_train.txt`、`doupo_raw.txt`
- 锁存：`samples.sha256`
- 预注册：`ai_detect_preregistration.json` + `ai_detect_prereg.sha256`
- 构建/产物：`build_aidetect_report.py`；`ai_detect_report.html` `ai_detect_result.json` `ai_detect_full_result.json`

### E. 仓储/宏观主题（上下文研究）
- `svagent/inventory_cycle.py` + `build_inventory_report.py` + `inventory_cycle_report.html`
- `kondratieff_data.py` `kondratieff_factcheck.json` `kondratieff_input.txt` + `build_kondratieff_report.py` + `kondratieff_report.html`

### F. 回溯审计与整改
- 代码：`svagent/retro_audit.py` `retrospective.py`
- 构建：`build_retro_audit_report.py` `build_retrospective_report.py` `build_remediation_report.py`
- 产物：`retro_audit_report.html` `retro_audit_result.json` `retrospective_report.html` `retrospective_store.json` `remediation_report.html`

### G. 文章事实核查（外部文本核查练习）
- `article_input.txt` `article_factcheck.json` + `build_factcheck_report.py` + `factcheck_report.html`
- `ms_article_input.txt` `ms_article_factcheck.json` `ms_factcheck_data.py` + `build_ms_report.py` + `ms_article_report.html`
- `hcnh_300627_report.html` + `build_hcnh_report.py`

### H. 证券 RSI（相对强弱指标）线 —— 注意与 I 区分
- 代码：`svagent/rsi_prospect.py`
- 预注册：`rsi_preregistration.json` + `rsi_prereg.sha256`；证据 `rsi_github_evidence.json`
- 构建/产物：`build_rsi_report.py`；`rsi_report.html` `rsi_result.json` `rsi_full_result.json`

### I. RSI = Recursive Self-Improvement（递归自改进）线
> 曾因术语歧义误判为 H 线证券指标，故立 `disambiguation_gate` 门禁（见 §3）。
- 论文原文：`rsi_sim_paper.pdf` / `.txt`
- 预注册：`sim_preregistration.json` + `sim_prereg.sha256`；证据 `rsi_sim_evidence.json`
- 产物：`sim_report.html` `sim_framework_result.json` + `build_sim_report.py`
- 四要素记忆模块：`svagent/improvement_memory.py` + `sim_memory_report.html` + `build_sim_memory_report.py`

### J. RSI-Structure 综述线（经验如何变结构）
- 原文：`rsi_structure_full.txt`（用户上传的官方 PDF 全文提取）、`rsi_structure_paper.pdf/.txt`、`rsi_structure_raw.txt`、`rsi_structure_page.html`、`or_note.json` `or_v1.json` `s2.json`（OpenReview 抓取留痕）
- 预注册：`rsi_structure_preregistration.json` + `rsi_structure_prereg.sha256`
- 修正记录：`rsi_structure_amendment.json` + `rsi_structure_amendment.sha256`（全文到手后的后验增量，不伪装预注册）
- 证据/结果：`rsi_structure_evidence.json` `rsi_structure_result.json`
- 构建/产物：`build_rsis_report.py` + `rsi_structure_report.html`
- 分析/门禁代码：`svagent/rsis_framework_analysis.py` `component_attribution.py` `evaluation_reliability.py`

### K. DeepMind《What comes after AGI?》观点文线
- 原文：`agi_essay_raw.txt`（19971 字符正文）、`agi_essay.html`（原始页面）
- 预注册：`agi_essay_preregistration.json` + `agi_essay_prereg.sha256`
- 证据/结果：`agi_essay_evidence.json` `agi_essay_result.json`
- 构建/产物：`build_agi_essay_report.py` + `agi_essay_report.html`
- 分析代码：`svagent/agi_essay_analysis.py`（含 `verify_extrapolation_arithmetic()` 真实复算）

### L. 知识库本体
- `knowledge_base_store.json`（105 条知识，就绪）、`knowledge_base_report.html`
- 代码：`svagent/knowledge_base.py`

### M. DGM 论文研读 + 架构对比线（§49–§50）
- 研读：`audit_dgm/`（预注册/五重 SHA256/8 判据/报告 `dgm_report.html`，结果 `result.json`）
- 架构对比：`build_dgm_svl_compare.py` → `dgm_svl_compare.html` + `dgm_svl_compare_result.json`
  （8 维逐项对照 / 16 一手锚点 / 16 条双向借鉴；同构打折、不新增 KB）
- 推导：`commentary.md` §49（判据审计）/ §50（扬长避短·相互借鉴）/ §51（代码落地：两道门禁 + 判据自咬修正）/ §53（SWE-Gym 代码强固 + 审读三段式工作流规范）/ §54（元学习闭环泛化：所有任务双源复盘 + 判据自咬实录）/ §55（SIM 再审：旧论文×新框架，3 补刀 + 循环论证警觉）/ §56（谱系打折门禁：警觉长牙 + 自审工具假阳性）/ §57（OpenAI Performance Factory 精研：回测信息污染隔离门禁 + P1判据自咬）/ §58（架构定位决策：用户选 A 保持判据库显式调用，把 KB-AUDIT03 量回本仓、判定粒度细化）/ §59（把断言落到代码：§58 认知增量编译成调用点完整性门禁，判据自审一次过）/ §60（精研 Claude Code 验证一文：审查者评估漏斗保真门禁 + 一次咬两处的判据自咬）/ §61（旧论文×新框架再审 ReVeal：N1-N5 用 §56-§60 新牙重咬，咬出"区分力信号算了没接线"=KB-AUDIT03 活体；判据自审连咬自己两口；加固 4 条不新增）/ §62（精研 HiGR v5：从工业推荐论文编译"训练-服务信号可得性"新门禁 serving_signal_gate，新增 KB-AUDIT08）/ §63（精研 How to Train a Swarm：村-城落差对照验证 §62 门禁区分力——GR主动披露→flag vs HiGR未披露→downgrade；加固不新增）/ §64（精研 LangChain Context Engineering：claim-vs-code 7/7 命中 + 从检索文本污染编译 retrieval_grounding 门禁，新增 KB-AUDIT09）/ §65（精研 Anthropic Building always-on agents：五原语运行时指南，结构化能力矩阵核验咬出跨会话状态连续性缺口→编译 session_continuity 门禁，新增 KB-AUDIT10；V3 无代码判 UNVERIFIABLE、V6 与 V5 同维收敛防多牙）/ §66（精研 TCSExam 三来源评测基准：数字全独立复算 ρ=0.9286→0.93/26-28/1838实例、claim-vs-code 12项全落地、V4选择偏差因披露+held-out降为设计选择→加固不新增；判据两次自咬修工具）/ §67（精研三来源思想谱系 Bitter Lesson→Alberta Plan→机器人幼儿园：同源三粒度按KB-STRUCT02打折、纲领≠成果、落地兑现度scoped，加固不新增；AST自审误伤锚点→中文锚点集中字典重构）/ §68（精研22来源记忆生命周期谱系 海马体SPW-R→Claude Dreams：五子主题同源打折、记忆内容治理缺口→编译第16道门禁 memory_curation，新增KB-AUDIT11；主体错位/self-reported守界、两次自咬修工具）
- 架构定位决策（§58）：`architecture_decision_A.json`（三层核查：代码已落盘 / 未接 run_loop / 如实声明工具库定位；A vs B；双源复盘；诚实边界）→ 加固 KB-AUDIT03 一条 support（调用点分在线主循环 vs 离线审计脚本、定位声明诚实性决定是否死代码）。**本轮不动代码、不加测试、不接编排器**；101 条不新增；全量 357 passed。
- 调用点完整性门禁（§59）：`call_site_prereg.json` + `call_site_prereg.sha256`（实现前锁存）→ `svagent/call_site_integrity.py`（audit_call_site：R0 字面串 flag / R1 无断言 block / R2 死代码声称自动 block / R3 幽灵接线 block / R4 离线冒充在线 downgrade / R5 诚实未接线 downgrade / R6 诚实工具库 preserve / R7 在线咬合 ok / R8 定位未声明 flag）→ `tests/test_call_site_integrity.py`（14 项）→ `build_call_site_result.py` + `call_site_result.json` + `call_site_report.html`（后验）。把 §58「调用点分在线/离线、定位声明算不算数」的认知断言编译成代码（用户叮嘱"把断言落到代码"）；AST 源码自审判定分支无中文字面串比较（前置应用 §56 教训）；遵循 §58 选 A 不接 run_loop；101 条不新增，加固 KB-AUDIT03 一条；全量 371 passed。
- Claude Code 验证一文精研（§60）：`audit_claude_verify/`（一手 HTML 106KB+正文 164 行二重锁存 → `prereg.json` V1–V10 分析前锁存 → `engine.py` 判据+三层诚实结论+V10源码缺口核验 → `result.json`）→ `reviewer_eval_prereg.json`+锁存（实现前）→ `svagent/reviewer_evaluation.py`（check_review_evaluation：三阶段压一分数 block / 无对照·tuning泄漏·无answer key downgrade / 漏斗倒挂·越界 flag / 全自洽 ok）→ `tests/test_reviewer_evaluation.py`（14 项）→ `build_report.py` + `final_result.json` + `claude_verify_report.html`（后验）。把文章 line 122-123『审查者也要被分阶段评估』编译成代码；活体回归首跑 4/8 失败咬出两处漏写 return，信规则改代码后 8/8 过；101 条不新增，加固 3 条（AUDIT04/STRUCT07/AUDIT02）；遵循 §58 选 A 不接 run_loop；全量 385 passed。
- 旧论文×新框架再审 ReVeal（§61）：`audit_reveal/review_prereg.json`+锁存（分析前 `41ae1052…`）+ `review_engine.py`（N1-N5 调用 scoring_integrity/call_site_integrity/backtest_integrity/reviewer_evaluation/lineage_guard 五把已锁存新牙）+ `review_result.json` + `build_review_report.py` → `reveal_review_report.html`（后验）。咬出：区分力信号 `success_output_passrate` 算了只进观测未进 reward（KB-AUDIT03 活体）、消融无单独 verification reward（N4 block）、TAPO turn 隔离同构打折（N5 downgrade）。判据自审连咬自己两口（中文串 brittle + 检测器自指），信规则改代码后 5/5 过。不新增、不编译新门禁（旧条款新实例），加固 4 条（AUDIT03/AUDIT07/RSI06/STRUCT02）；101 条不变。
- HiGR v5 精研（§62）：`audit_higr/`（PDF 1.08MB/8页 EOF 校验 + 正文 690 行 + abs 三重锁存 → `prereg.json` V1–V6 分析前锁存 `1cfb6686…` → `engine.py` 判据+三层诚实结论 → `result.json` + `higr_report.html`）→ `serving_gate_prereg.json`+锁存（实现前 `fddecbea…`）→ `svagent/serving_signal_gate.py`（训练-服务信号可得性：不可得+未声明+无桥接 downgrade / 声明无桥接·代理未声明·字面串 flag / 声明且桥接·口径对等 ok）→ `tests/test_serving_signal_gate.py`（17 项）。从工业推荐论文正样本 y+ 依赖 true feedback、服务时无此信号的落差编译本仓第四道独立维度门禁（评测/回测/泛化/调用点之外的 train-serving 维度）；6 活体回归+17 测试+源码自审全过；新增 KB-AUDIT08（102 条）+ 加固 KB-AUDIT04；遵循 §58 选 A 不接 run_loop；全量 402 passed。
- How to Train a Swarm 精研（§63）：`audit_swarm/`（博客 HTML 430KB+正文 379 行 + Avalon-M1 技术报告 81页PDF/5071行，四重 SHA256 锁存 → `prereg.json` V1–V7 分析前锁存 `d723fd28…` → `engine.py` V1–V6 判据调用真实门禁+三层诚实结论 → `result.json` + `build_report.py` → `swarm_report.html`）。用 gem-seeker 做 claim-vs-code：无公开代码判 unverified 不判造假。V4 村-城落差（训练9/部署1000s）调用 `check_serving_signal` 得 `SERVING.DISCLOSED_NO_BRIDGE`=flag，对照 HiGR(§62)未披露=downgrade——验证 §62 门禁区分力；V2 抓出博客"2.4h"无一手支撑（报告 1.7h）、"4x"vs"3.9×"倒数一致；V5 insularity flag（agent 规避人类报告）。判据自审 S4 口径自咬（V1无结论层/V4用message），精确化后 6/6 过。**加固不新增**：加固 KB-AUDIT08/AUDIT04 两条 support，102 条不变、不编译新门禁（老条款对照验证，防 vanity）；全量 402 passed 不变。
- 22来源记忆生命周期谱系精研（§68）：`audit_memory/`（22来源并行抓取：14一手 HTML/PDF/WebFetch摘要/官方中文镜像 + 6二手区域锁WebSearch聚合标S3 + 2未取；35份来源文件语料SHA256锁存 → `prereg.json` V1–V9 分析前锁存 `e8006152…` → `gate_prereg.json` 实现前锁存 `213ed6e2…` → `engine.py` → `result.json` + `build_report.py` → `memory_report.html`）。五子主题同源谱系：T1选择(S02 CLS/S03 SPW-R only-small-fraction/S11 tagging)→T2整合(S04重放/S05系统巩固)→T3 AI巩固(S06 sleep-time/S08 Google SLEEP两阶段/S07 Dreams/S21 cookbook)→T4工具(S01/S12 memory tool六操作/S19 MEMORY.md 200line25KB/S10 compaction)→T5范式(S17 Karpathy wiki/S13 CL-Bench/S18 Harvey/S22)。按KB-STRUCT02同源打折，22篇≠22独立验证。V4能力矩阵差集：本仓15道门禁(session_continuity判状态续接/improvement_memory判可证伪/四要素记忆判要素存在)无一判记忆内容质量治理→编译第16道 `memory_curation.py`（无选择/无整理downgrade、破坏性/部分/字面串flag、自洽ok；7活体+15测试+双AST自审全过，遵循§58选A不接run_loop）。V6守主体错位(Google官方sleep/dreaming terms borrow from neuroscience、Dreaming deliberate reference to hippocampal consolidation→生物机制不证成AI设计,KB-STRUCT05)+self-reported数字不采信(KB-RSI07)。V7 Karpathy wiki≈本仓KB/commentary/REPO_MAP同构打折。新增KB-AUDIT11(105条)+加固STRUCT02/STRUCT05/RSI07；两次自咬(S03首字母大写/S17中文摘要无英文maintenance)改一手锚点不放水；全量446 passed。
- 三来源思想谱系精研（§67）：`audit_bitter_lesson/`（一手：bitterlesson.org HTML 54KB + arXiv 2208.11173 PDF 14页/正文699行 + 北京市政府机器人幼儿园 HTML 46KB，七份 SHA256 锁存 → `prereg.json` V1–V8 分析前锁存 `b0fd51e0…` → `engine.py` → `result.json` + `build_report.py` → `bitter_lesson_report.html`）。对象为同源思想谱系三粒度（哲学随笔/研究纲领/self-reported工程落地），按KB-STRUCT01逐篇适配判据。核心洞察 V2：Bitter Lesson(Sutton2019)→Alberta Plan(Sutton组2022自承heed bitter lesson)→机器人幼儿园(他山×图灵奖得主萨顿团队Openmind共建)是同一思想的三个粒度，按KB-STRUCT02打折不计为三独立验证。V4 Alberta自述5-10年长期计划/不关心即时应用/研究计划可疑临时→纲领非成果(KB-AUDIT03延伸)。V5 目标函数(摔倒负反馈/小红花奖励)+从人类采集转自主经验+三区递进=机制叙事对应纲领，但自承大多还在小班+学习效率成本持续运行挑战→scoped，不升华为Bitter Lesson被验证。V3 无代码无统计量判UNVERIFIABLE。V6 全部已被现有KB覆盖且硬编译会成无法会拦的叙事尺子→加固不新增(STRUCT02/AUDIT03/STRUCT09各加support，104条保持)。AST自审误伤合法中文锚点→辨析§56 brittle根因是中文串做判定结论比较→中文锚点集中字典用键引用、verdict英文枚举、ord数值边界避免自指；V2中文名"萨顿"/V4 PDF断行两处自咬均修工具不放水；V1–V8零漂移。全量431 passed。
- TCSExam 精研（§66）：`audit_tcsexam/`（三来源：arXiv 2611.07962v1 PDF 52页/正文3305行 + 项目交互主页 HTML 165KB + 开源评测代码 7282文件 @ f0518c35；五重 SHA256 锁存 → `prereg.json` V1–V9 分析前锁存 `ea91b47d…` → `engine.py` 独立复算+claim-vs-code+三层诚实结论 → `result.json` + `build_report.py` → `tcsexam_report.html`）。对象为评测基准论文，判据适配统计复算+claim-vs-code+披露分级。V2 从 Table2/3 独立复算 Spearman ρ=0.9286→0.93、26/28同序2倒挂(点名DS1017)、reference 1838实例、sigma floor 0.02/1e-9、Index 30/30/30/10 全命中。V3 claim-vs-code 12项全落地(scoring.py/reference JSON/suites)，额外发现"缺失≠0"(null index/unscored separate)诚实设计。V4 用被测6-agent反馈选Lite子集再证排名一致=选择偏差风险面，但作者全文披露+两agent held-out+点名倒挂→降为设计选择非漏洞(§63先例)，加固 KB-AUDIT04/07 不新增不编译(硬编译会成无法会拦的玩具)。V5/V8 scoped、V6 同构打折、V7 8项披露正面信号。判据两次自咬(PDF跨行断言+检测器自指)均修工具不放水。104条不变、全量 431 passed。
- Anthropic Building always-on agents 精研（§65）：`audit_always_on/`（一手 HTML 563950B+正文 154行/14023字符，四重 SHA256 锁存 `467e47d7…`/`26a0c4b8…`/预注册 `0020f5fd…`/门禁预注册 `42b10e90…` → `prereg.json` V1–V7 分析前锁存 → `engine.py` V1–V7 判据+能力矩阵差集+三层诚实结论 → `result.json` + `build_report.py` → `always_on_report.html`）。对象为工程指南（无代码无A/B），V2 数字 self-reported 判 scoped、V3 claim-vs-code 判 UNVERIFIABLE、V4 四处同构按 KB-STRUCT02 打折。V5 结构化核验本仓 14 道门禁能力矩阵→9 项跨会话状态/事件能力无一覆盖→编译 `session_continuity.py`（无持久状态 block / 不可续跑·无真相源·多消费者 downgrade / 等待阻塞·部分·字面串 flag / 自洽 ok，只判机制声明自洽不承诺真永续）。8 活体回归+16 测试+门禁&引擎双 AST 自审全过；遵循 §58 选 A 不接 run_loop；新增 KB-AUDIT10（104 条）+ 加固 AUDIT03/STRUCT02；全量 431 passed。V6 与 V5 同维收敛为一牙防多牙。
- LangChain Context Engineering 精研（§64）：`audit_langchain_ctx/`（博客 HTML 188KB+正文 247行/14686字符 + Deep Agents 开源源码 filesystem.py 176KB/skills.py/_blob_offload.py 一手抓取 → `prereg.json` V1–V7 分析前锁存 `f1eaf338…` → `engine.py` → `result.json` + `build_report.py` → `ctx_report.html`）。V3 claim-vs-code 7/7 全命中（glob/grep内置、100行分页、20000token offload `tool_token_limit_before_evict=20000`、progressive disclosure 均在源码落地），判 verified 但只证机制存在不证效果最优。V2 数字全为 harness 参数非实验结论→scoped。V4 咬出检索文本污染（retrieved text 是 data 非 instructions、no strategy fully prevents injection）与 `core.py:98 GT.SOURCE_UNTRUSTED`（审计输入层源身份）场景/对象/动作三者不同→真新牙：`gate_prereg.json`+锁存（实现前 `33c4f789…`）→ `svagent/retrieval_grounding.py`（未标记data block / 无溯源·断言不匹配·无关未隔离 downgrade / 无时效检查·字面串 flag / 全自洽 ok，只判验证动作存在不承诺防住注入）→ `tests/test_retrieval_grounding.py`（13 项）。8 活体回归+13 测试+源码自审全过；判据自审 6/6 一次过（前三轮坑已固化为口径，教训复利）；V5/V6 同构打折（惰性导入/pointer/SHA-256 锁存）。新增 KB-AUDIT09（103 条，会拦才入）+ 加固 KB-AUDIT04；遵循 §58 选 A 不接 run_loop；全量 415 passed。
- OpenAI 性能工厂精研（§57）：`audit_openai_perf/`（一手 HTML+正文三重锁存 → `prereg.json` P1–P7 分析前锁存 → `engine.py` 判据+数字复算+P4缺口核验 → `result.json`）→ `svagent/backtest_integrity.py`（回测信息污染隔离：关键项缺失 block / 弱项 downgrade / spoiler block / 未声明 flag）→ `tests/test_backtest_integrity.py`（14 项）→ `hardening_prereg.json`+锁存（实现前）→ `build_report.py` + `perf_factory_result.json` + `perf_factory_report.html`（后验）。本仓第一道回测污染门禁；101 条不新增，加固 3 条（RSI06/AUDIT04/AUDIT02）；P1 判据过严自咬修正；全量 357 passed。
- 谱系打折门禁（§56）：`lineage_guard_prereg.json` + `lineage_guard_prereg.sha256`（实现前锁存）→ `svagent/lineage_guard.py`（discount_claim：R1 循环 block / R2 同构 downgrade / R3 部分 flag / R4 诚实 preserve / R5 独立 ok / R6 字面串 flag）→ `tests/test_lineage_guard.py`（13 项）→ `build_lineage_result.py` + `lineage_guard_result.json` + `lineage_guard_report.html`（后验）。把 §55 循环论证警觉从文字编译成通用门禁，替代 t2 brittle 匹配；自审工具口径错位（注释当代码）假阳性→修工具不修代码；101 条不新增，加固 3 条（STRUCT02/META01/AUDIT04）；全量 343 passed。
- 优化落地：`optimize_preregistration.json` + `optimize_prereg.sha256`（预注册锁存）→ `svagent/scoring_integrity.py` + `svagent/transfer_holdout.py`（两道门禁）→ `tests/test_scoring_integrity.py` + `tests/test_transfer_holdout.py`（14 项）→ `build_optimize_result.py` + `optimize_result.json`（后验结果）。100 条不新增，仅加固 3 条 support；全量 301 passed。
- 代码强固（§53）：`robustness_prereg.json` + `robustness_prereg.sha256`（实现前锁存）→ `svagent/judgment_robustness.py`（C1 bootstrap 稳定性 / C2 条件消融 / C3 活体样例校验）→ `tests/test_judgment_robustness.py`（15 项）→ `build_robustness_result.py` + `robustness_result.json` + `robustness_report.html`（后验）。借自 SWE-Gym 五类工程纪律，避其可训练 verifier 攻击面；加固 5 条 KB support（RSI06/STRUCT07/STRUCT03/AUDIT02/META01）；100 条不新增，全量 316 passed。
- 元学习闭环（§54）：`meta_loop_prereg.json` + `meta_loop_prereg.sha256`（实现前锁存）→ `svagent/task_retrospective.py`（双源复盘：task_content+process，G1-G5 规则）→ `tests/test_task_retrospective.py`（14 项）→ `build_meta_loop_result.py` + `meta_loop_result.json` + `meta_loop_report.html`（后验）。新增 1 条 KB-META02（触发泛化），加固 4 条（META01/R06/R08/SIM05）；活体样例写错被 G1 判据自咬并修正；全量 330 passed。
- SIM 再审（§55）：`sim_review_prereg.json` + `sim_review_prereg.sha256`（实现前锁存）→ `sim_review_engine.py`（六道新门禁咬向原论文：N1 分域 judge / N2 相对基线迁移 / N3 bootstrap / N4 消融 / N5 计分完整性 / N6 双源复盘）→ `sim_review_result.json` + `build_sim_review_report.py` + `sim_review_report.html`（后验）。3 处补刀（N1/N3/N5）+ 循环论证警觉；101 条不新增，加固 4 条（SIM02/SIM05/STRUCT07/AUDIT07）；330 passed。

### N. SWE-Gym 论文精研线（§52）
- `audit_swegym/`：预注册 `prereg.json` + 四重 `source.sha256` → `paper.pdf`/`paper.txt`/`arxiv_abs.html` → `engine.py`（8 判据 + 10 项数字复算）→ `result.json` → `build_report.py` + `swegym_report.html`；代码仓 `repo/`（clone，已在 .gitignore 排除大原件）。
- 结论：verifier 是 trajectory 级 ORM、可被 reward hacking（本仓 KB-AUDIT07 攻击面的一手实证）；摘要 19% gains vs 表内 13.6% 口径差；同构打折不新增条目，加固 4 条 support。推导见 commentary §52。

---

## 3. 从外部经验编译出的门禁（本仓的"牙齿"）

这些不是复述论文，而是按 `KB-META01`（复述 vs 长牙）编译成**会拦、会判、会降级**的可执行模块：

| 门禁 | 来源线 | 能力 |
|---|---|---|
| `svagent/disambiguation_gate.py` | I 线术语歧义事故 | 命中歧义词强制用户确认，agent 自猜不算 |
| `svagent/improvement_memory.py` | I 线 SIM 四要素 | predicted↔observed 配对、命中率、回归检测、可否迁移判定 |
| `svagent/component_attribution.py` | J 线综述 Where 维度 | 组件归因需给证据/去留/稀有用法核查，按组件类型定验证方式 |
| `svagent/evaluation_reliability.py` | J 全文 + K 线 | judge 独立性、复现完整性/双编码、评估可扩展性降级 |
| `svagent/scoring_integrity.py` | DGM 附录 H（§51） | 计分完整性：检测字段被篡改/绕过 → 分数作废或降级；node114 活体回归 |
| `svagent/transfer_holdout.py` | DGM 跨基准 + KB-RSI06/SIM09（§51） | 跨领域迁移：按相对基线增益判过拟合 vs 可迁移；上下文漂移 revise |
| `svagent/judgment_robustness.py` | SWE-Gym 代码工程纪律（§53） | 判定稳健性：bootstrap 置信度降级 / 条件消融揪冗余 / 活体样例成对+cap+seed 校验 |
| `svagent/task_retrospective.py` | 用户元学习想法（§54） | 任务复盘：双源（任务+过程）+ 可证伪 + 目的约束 + 非复述；复述拦截/单源降级/失败未记降级 |
| `svagent/lineage_guard.py` | SIM 再审循环论证警觉（§56） | 谱系打折：判据来源与被审对象同源却声称独立 → block；高同构 → downgrade；诚实标注 → preserve；字面串输入 flag |
| `svagent/backtest_integrity.py` | OpenAI Performance Factory 8条防spoiler纪律（§57） | 回测信息污染隔离：关键隔离项缺失→block / 弱项缺失→downgrade / 事后查获spoiler→block / 状态未声明→flag |
| `svagent/call_site_integrity.py` | §58 自审的认知增量 + 用户叮嘱（§59） | 调用点完整性：死代码/幽灵接线/无断言→block；离线冒充在线/诚实未接线→downgrade；诚实工具库/在线咬合→ok；定位未声明/字面串→flag |
| `svagent/reviewer_evaluation.py` | Claude Code 验证一文 line 122-123（§60） | 审查者评估漏斗保真：三阶段压成一分数→block；无对照/tuning泄漏/无answer key→downgrade；漏斗倒挂/越界→flag；分阶段+对照+分离+计分→ok |
| `svagent/serving_signal_gate.py` | HiGR v5 line 366-380/425-428（§62） | 训练-服务信号可得性：不可得+未声明+无桥接→downgrade；声明但无桥接/代理未声明/字面串→flag；声明且桥接/口径对等→ok |
| `svagent/retrieval_grounding.py` | LangChain Context Engineering line 191-194（§64） | 检索文本溯源：未标记data→block；无引用核对/断言不匹配/无关未隔离→downgrade；无时效检查/字面串→flag；全自洽→ok（只判验证动作存在，不承诺防住注入） |
| `svagent/session_continuity.py` | Anthropic Building always-on agents line 27/48/91/105-110（§65） | 跨会话状态连续性：无持久状态→block；会话不可续跑/无真相源/多消费者→downgrade；等待阻塞/部分持久化/字面串→flag；全自洽→ok（只判机制声明自洽，不承诺系统真永续；判外部 always-on 声称，不判本仓） |
| `svagent/memory_curation.py` | 22来源记忆生命周期谱系 S02/S03/S07/S17（§68） | 记忆内容质量治理：无选择(全量写入)/无整理(去重·矛盾·过时)→downgrade；无选择downgrade；破坏性覆盖/部分治理/字面串→flag；全自洽→ok（只判机制声明自洽，不承诺记忆真的有用；判外部长期记忆声称，不判本仓） |

每道门禁都有对应测试：`tests/test_disambiguation_gate.py` `test_improvement_memory.py` `test_component_attribution.py` `test_evaluation_reliability.py` `test_scoring_integrity.py` `test_transfer_holdout.py` `test_judgment_robustness.py` `test_task_retrospective.py` `test_lineage_guard.py` `test_backtest_integrity.py` `test_call_site_integrity.py` `test_reviewer_evaluation.py` `test_serving_signal_gate.py` `test_retrieval_grounding.py` `test_session_continuity.py` `test_memory_curation.py`。

---

## 4. 复现纪律（为什么要保持文件平铺）

1. **路径被记录**：`build_*.py` 内硬编码了如 `open("/workspace/...")` 与相对文件名；预注册 JSON 记录了证据文件名。移动/改名会让脚本失效。
2. **哈希被锁存**：9 个 `*.sha256` 文件锁定了预注册与样本内容；已逐一验证一致（见整理记录）。改动内容会破坏锁存。
3. **后验不伪装**：`rsi_structure_amendment.json` 明确标注为全文到手后的增量，与 `rsi_structure_preregistration.json` 的哈希严格区分。

因此本仓采用 **"保路径 + 强导航"** 的整理策略：结构清晰靠本文档，不靠移动文件。
