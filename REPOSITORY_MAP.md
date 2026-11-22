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
| 1.5 | `SESSION_HANDOFF.md` | **新旧会话接续**：现状、用户意图、纪律、未完成推送任务（换会话先读此） |
| 2 | `commentary.md` | 完整推导日志，§1–§80 逐节记录机制如何长出来 |
| 3 | `REPOSITORY_MAP.md`（本文件） | 文件按主题归位 |
| 4 | `svagent/` | 可执行代码（59 个模块，惰性导入） |
| 5 | `tests/` | 回归测试（774 项，`python3 -m pytest -q`） |

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
- `knowledge_base_store.json`（111 条知识，就绪）、`knowledge_base_report.html`
- 代码：`svagent/knowledge_base.py`

### M. DGM 论文研读 + 架构对比线（§49–§50）
- 研读：`audit_dgm/`（预注册/五重 SHA256/8 判据/报告 `dgm_report.html`，结果 `result.json`）
- 架构对比：`build_dgm_svl_compare.py` → `dgm_svl_compare.html` + `dgm_svl_compare_result.json`
  （8 维逐项对照 / 16 一手锚点 / 16 条双向借鉴；同构打折、不新增 KB）
- 推导：`commentary.md` §49（判据审计）/ §50（扬长避短·相互借鉴）/ §51（代码落地：两道门禁 + 判据自咬修正）/ §53（SWE-Gym 代码强固 + 审读三段式工作流规范）/ §54（元学习闭环泛化：所有任务双源复盘 + 判据自咬实录）/ §55（SIM 再审：旧论文×新框架，3 补刀 + 循环论证警觉）/ §56（谱系打折门禁：警觉长牙 + 自审工具假阳性）/ §57（OpenAI Performance Factory 精研：回测信息污染隔离门禁 + P1判据自咬）/ §58（架构定位决策：用户选 A 保持判据库显式调用，把 KB-AUDIT03 量回本仓、判定粒度细化）/ §59（把断言落到代码：§58 认知增量编译成调用点完整性门禁，判据自审一次过）/ §60（精研 Claude Code 验证一文：审查者评估漏斗保真门禁 + 一次咬两处的判据自咬）/ §61（旧论文×新框架再审 ReVeal：N1-N5 用 §56-§60 新牙重咬，咬出"区分力信号算了没接线"=KB-AUDIT03 活体；判据自审连咬自己两口；加固 4 条不新增）/ §62（精研 HiGR v5：从工业推荐论文编译"训练-服务信号可得性"新门禁 serving_signal_gate，新增 KB-AUDIT08）/ §63（精研 How to Train a Swarm：村-城落差对照验证 §62 门禁区分力——GR主动披露→flag vs HiGR未披露→downgrade；加固不新增）/ §64（精研 LangChain Context Engineering：claim-vs-code 7/7 命中 + 从检索文本污染编译 retrieval_grounding 门禁，新增 KB-AUDIT09）/ §65（精研 Anthropic Building always-on agents：五原语运行时指南，结构化能力矩阵核验咬出跨会话状态连续性缺口→编译 session_continuity 门禁，新增 KB-AUDIT10；V3 无代码判 UNVERIFIABLE、V6 与 V5 同维收敛防多牙）/ §66（精研 TCSExam 三来源评测基准：数字全独立复算 ρ=0.9286→0.93/26-28/1838实例、claim-vs-code 12项全落地、V4选择偏差因披露+held-out降为设计选择→加固不新增；判据两次自咬修工具）/ §67（精研三来源思想谱系 Bitter Lesson→Alberta Plan→机器人幼儿园：同源三粒度按KB-STRUCT02打折、纲领≠成果、落地兑现度scoped，加固不新增；AST自审误伤锚点→中文锚点集中字典重构）/ §68（精研22来源记忆生命周期谱系 海马体SPW-R→Claude Dreams：五子主题同源打折、记忆内容治理缺口→编译第16道门禁 memory_curation，新增KB-AUDIT11；主体错位/self-reported守界、两次自咬修工具）/ §69（精研11来源异步子Agent谱系 LangChain六源+Claude Code+DeepSeek Super-agent+OpenAI dots：四家主体谱系按KB-STRUCT02打折、后台委派生命周期缺口→编译第17道门禁 async_delegation_lifecycle，新增KB-AUDIT12；通用词resume过宽误伤→收窄专属术语修工具不放水）/ §70（精研记忆三来源 components+Dreams+Memory Trap：前两源与§68同源打折、Memory Trap作用域风险是新对象→编译第18道门禁 memory_scope，新增KB-AUDIT13；PDF跨行断锚点+中文串brittle两次自咬修工具）/ §71（精研FlashProve公众号文章+附录48链接按必须必要仅取6个一手载体：同源打折1主体、编译第19道门禁 proof_boundary_honesty 证明边界诚实性，新增KB-AUDIT14；manifest缺字段·跨行锚点·翻译漏项·中文串brittle四次自咬修工具）/ §72（精研 Proactive AI 综述三来源：论文PDF一手11658行+项目主页同主体、Google Research页抓取失败标unavailable、四载体同源折为1；主动介入的授权正当性缺口→编译第20道门禁 proactive_authorization，新增KB-AUDIT15；capability≠authority≠calibration、提出框架≠证明有效；跨行锚点·误用主页句·HTML断串三处自咬修工具不放水）/ §73（精研 DeepSeek 全家桶 API 五来源 公告+Chatbot指南+在线Demo+chat-demo仓库+定价：五来源同主体折1、能力self-reported折扣、提出能力≠真能控制；接口契约边界缺口→编译第21道门禁 interface_contract_honesty，新增KB-AUDIT16；传入≠生效/别名≠路由/基础风控≠合规/工具免费≠零成本四层错位；中文Compare+CJK边界字面量两处自咬修工具不放水）/ §74（精研认知投降谱系18来源[去重22链接,门首篇X]：DNS劫持6+来源不可达标unavailable、Osmani作者家族折1、一手实验数字vs博客无数据vs preprint未评审vs survey自陈分级；监督可行性缺口→编译第22道门禁 supervision_viability，新增KB-AUDIT17；独立观点/能力未侵蚀/监督未自我消解/表面≠系统正确四层前提；中文折扣Compare+锚点大小写两处自咬修工具不放水）/ §75（精研公众号AINLP《当Agent接手工作如何保持批判性思考》[用户确认出处,经同源52nlp站下载,含原稿截图+参考链接]：X/unwire/BI网络不可达标unavailable；S02繁体综述明标个人实务观察/六问未被证有效/132人自报→只证现象不证六问有效；主体认知边界诚实觉察缺口→编译第23道门禁 self_knowledge_honesty，新增KB-AUDIT18；假设先行/局限自陈/可证伪自问/技能退化披露四维；用户点明此文是洞见本体(自知)基础、与insight/retrospective/estimation一脉；C5/C6/C7锚点措辞+繁简交叉三处自咬修工具不放水）/ §76（系统机制化自见自知本体：用户定位'Agent洞悉本体即自见自知,能机制化尽量机制化'→建self_insight_ontology.json将全文6簇自问系统化为本体[自见K2验证边界/K3决定透明,自知K1认知边界/K4意图完整/K5反方论证/K6责任编排;已编译2·候选2·并入1·仅声明1];验证边界簇≠proof_boundary_honesty形式化证明→编译第24道门禁verification_boundary_honesty，新增KB-AUDIT19；绿灯只证明一件事/标准事前/证据先于总结/自我质疑四维;不为宏大叙事造玩具牙KB-META01/§67;全量650 passed）/ §77（精研HarnessPro三来源[arXiv:2610.26770v2 preprint未评审+GitHub@6fd2d4d+evaluation.md]：PDF转文本2836行通读；label-free用LLM合成测试评估自生成改进,Fig2自曝LLM judge失败召回41.7%→自生成测试83.3%仍漏16.7%、混淆矩阵横轴靠Official outcome外部锚、指令'No separate reviewer is part of this run'；S03诚实披露GLM-5.2 snapshots缺失/错配不复现[复现边界诚实加分但结果不可核]；判据来源缺口≠proof_boundary形式化证明/≠verification_boundary通过声明→编译第25道门禁criterion_origin_honesty,新增KB-AUDIT20；断字锚点三处修工具不放水;全量687 passed）/ §78（精研PaperAgent公众号文+清华源论文[arXiv:2610.39497v1 Perspective未评审]：predict-gate-execute-update条件交互;核心=§7.2'门控审查自身训练数据'——p_train∝p_cand·e≠p_cand→标签MNAR、被压制者结果永不观测分数永不修正、blind spots而非平均误差主导、审计率须独立于分数、'独立审计与探索是保险丝';Perspective折1·公众号'20%→5倍'为编辑添加论文无此数字诚实记录;选择性监督结构性机制≠§77声明诚实→编译第26道门禁selective_supervision_honesty,新增KB-AUDIT21;三处锚点/分级自咬留痕;全量724 passed）/ §79-§80（精研多模态 Agent 记忆综述 arXiv:2610.19366v1[PDF36.5MB三次超时降级用官方HTML;主页口径299系统/68.2%与论文297架构/68.7%分别标注不混用]：两轴框架Axis I表示+Axis II管理[T2占68.7%/T3仅5.7%且全显式];认知增量两处——①§8.3.3'策略演化可提升短期正确率却少依赖最初接地模态'(缓存摘要替代视觉证据,正确率↑≠接地↑)②§8.3'核心不是召回量而是可恢复溯源+时间有效性';survey二手折1。两拦截面≠self_evolving运行时/memory_scope单条边界/criterion_origin判据来源/selective_supervision筛选数据→编译第27道policy_evolution_grounding[策略不可寻址·反馈未归因策略级·证据路径削弱·修订未验证→downgrade]+第28道memory_provenance_honesty[溯源可选·证据不可恢复·时间有效性缺失·不可逆→downgrade],新增KB-AUDIT22/23;三处跨行断字锚点修工具不放水;全量774 passed）
- 架构定位决策（§58）：`architecture_decision_A.json`（三层核查：代码已落盘 / 未接 run_loop / 如实声明工具库定位；A vs B；双源复盘；诚实边界）→ 加固 KB-AUDIT03 一条 support（调用点分在线主循环 vs 离线审计脚本、定位声明诚实性决定是否死代码）。**本轮不动代码、不加测试、不接编排器**；101 条不新增；全量 357 passed。
- 调用点完整性门禁（§59）：`call_site_prereg.json` + `call_site_prereg.sha256`（实现前锁存）→ `svagent/call_site_integrity.py`（audit_call_site：R0 字面串 flag / R1 无断言 block / R2 死代码声称自动 block / R3 幽灵接线 block / R4 离线冒充在线 downgrade / R5 诚实未接线 downgrade / R6 诚实工具库 preserve / R7 在线咬合 ok / R8 定位未声明 flag）→ `tests/test_call_site_integrity.py`（14 项）→ `build_call_site_result.py` + `call_site_result.json` + `call_site_report.html`（后验）。把 §58「调用点分在线/离线、定位声明算不算数」的认知断言编译成代码（用户叮嘱"把断言落到代码"）；AST 源码自审判定分支无中文字面串比较（前置应用 §56 教训）；遵循 §58 选 A 不接 run_loop；101 条不新增，加固 KB-AUDIT03 一条；全量 371 passed。
- Claude Code 验证一文精研（§60）：`audit_claude_verify/`（一手 HTML 106KB+正文 164 行二重锁存 → `prereg.json` V1–V10 分析前锁存 → `engine.py` 判据+三层诚实结论+V10源码缺口核验 → `result.json`）→ `reviewer_eval_prereg.json`+锁存（实现前）→ `svagent/reviewer_evaluation.py`（check_review_evaluation：三阶段压一分数 block / 无对照·tuning泄漏·无answer key downgrade / 漏斗倒挂·越界 flag / 全自洽 ok）→ `tests/test_reviewer_evaluation.py`（14 项）→ `build_report.py` + `final_result.json` + `claude_verify_report.html`（后验）。把文章 line 122-123『审查者也要被分阶段评估』编译成代码；活体回归首跑 4/8 失败咬出两处漏写 return，信规则改代码后 8/8 过；101 条不新增，加固 3 条（AUDIT04/STRUCT07/AUDIT02）；遵循 §58 选 A 不接 run_loop；全量 385 passed。
- 旧论文×新框架再审 ReVeal（§61）：`audit_reveal/review_prereg.json`+锁存（分析前 `41ae1052…`）+ `review_engine.py`（N1-N5 调用 scoring_integrity/call_site_integrity/backtest_integrity/reviewer_evaluation/lineage_guard 五把已锁存新牙）+ `review_result.json` + `build_review_report.py` → `reveal_review_report.html`（后验）。咬出：区分力信号 `success_output_passrate` 算了只进观测未进 reward（KB-AUDIT03 活体）、消融无单独 verification reward（N4 block）、TAPO turn 隔离同构打折（N5 downgrade）。判据自审连咬自己两口（中文串 brittle + 检测器自指），信规则改代码后 5/5 过。不新增、不编译新门禁（旧条款新实例），加固 4 条（AUDIT03/AUDIT07/RSI06/STRUCT02）；101 条不变。
- HiGR v5 精研（§62）：`audit_higr/`（PDF 1.08MB/8页 EOF 校验 + 正文 690 行 + abs 三重锁存 → `prereg.json` V1–V6 分析前锁存 `1cfb6686…` → `engine.py` 判据+三层诚实结论 → `result.json` + `higr_report.html`）→ `serving_gate_prereg.json`+锁存（实现前 `fddecbea…`）→ `svagent/serving_signal_gate.py`（训练-服务信号可得性：不可得+未声明+无桥接 downgrade / 声明无桥接·代理未声明·字面串 flag / 声明且桥接·口径对等 ok）→ `tests/test_serving_signal_gate.py`（17 项）。从工业推荐论文正样本 y+ 依赖 true feedback、服务时无此信号的落差编译本仓第四道独立维度门禁（评测/回测/泛化/调用点之外的 train-serving 维度）；6 活体回归+17 测试+源码自审全过；新增 KB-AUDIT08（102 条）+ 加固 KB-AUDIT04；遵循 §58 选 A 不接 run_loop；全量 402 passed。
- How to Train a Swarm 精研（§63）：`audit_swarm/`（博客 HTML 430KB+正文 379 行 + Avalon-M1 技术报告 81页PDF/5071行，四重 SHA256 锁存 → `prereg.json` V1–V7 分析前锁存 `d723fd28…` → `engine.py` V1–V6 判据调用真实门禁+三层诚实结论 → `result.json` + `build_report.py` → `swarm_report.html`）。用 gem-seeker 做 claim-vs-code：无公开代码判 unverified 不判造假。V4 村-城落差（训练9/部署1000s）调用 `check_serving_signal` 得 `SERVING.DISCLOSED_NO_BRIDGE`=flag，对照 HiGR(§62)未披露=downgrade——验证 §62 门禁区分力；V2 抓出博客"2.4h"无一手支撑（报告 1.7h）、"4x"vs"3.9×"倒数一致；V5 insularity flag（agent 规避人类报告）。判据自审 S4 口径自咬（V1无结论层/V4用message），精确化后 6/6 过。**加固不新增**：加固 KB-AUDIT08/AUDIT04 两条 support，102 条不变、不编译新门禁（老条款对照验证，防 vanity）；全量 402 passed 不变。
- 22来源记忆生命周期谱系精研（§68）：`audit_memory/`（22来源并行抓取：14一手 HTML/PDF/WebFetch摘要/官方中文镜像 + 6二手区域锁WebSearch聚合标S3 + 2未取；35份来源文件语料SHA256锁存 → `prereg.json` V1–V9 分析前锁存 `e8006152…` → `gate_prereg.json` 实现前锁存 `213ed6e2…` → `engine.py` → `result.json` + `build_report.py` → `memory_report.html`）。五子主题同源谱系：T1选择(S02 CLS/S03 SPW-R only-small-fraction/S11 tagging)→T2整合(S04重放/S05系统巩固)→T3 AI巩固(S06 sleep-time/S08 Google SLEEP两阶段/S07 Dreams/S21 cookbook)→T4工具(S01/S12 memory tool六操作/S19 MEMORY.md 200line25KB/S10 compaction)→T5范式(S17 Karpathy wiki/S13 CL-Bench/S18 Harvey/S22)。按KB-STRUCT02同源打折，22篇≠22独立验证。V4能力矩阵差集：本仓15道门禁(session_continuity判状态续接/improvement_memory判可证伪/四要素记忆判要素存在)无一判记忆内容质量治理→编译第16道 `memory_curation.py`（无选择/无整理downgrade、破坏性/部分/字面串flag、自洽ok；7活体+15测试+双AST自审全过，遵循§58选A不接run_loop）。V6守主体错位(Google官方sleep/dreaming terms borrow from neuroscience、Dreaming deliberate reference to hippocampal consolidation→生物机制不证成AI设计,KB-STRUCT05)+self-reported数字不采信(KB-RSI07)。V7 Karpathy wiki≈本仓KB/commentary/REPO_MAP同构打折。新增KB-AUDIT11(105条)+加固STRUCT02/STRUCT05/RSI07；两次自咬(S03首字母大写/S17中文摘要无英文maintenance)改一手锚点不放水；全量446 passed。
- FlashProve 公众号文章+附录精研（§71）：`audit_flashprove/`（微信NLPer号二手S2翻译Anthropic官方博客《Progress on provable inference》+ 附录48链接按必须必要原则仅下6个一手载体[官方研究页248KB/技术报告PDF3.18MB/GitHub README+THIRD_PARTY+paper.pdf]+1辅助工具超时不补,取舍见appendix_triage.md；SHA256锁存 → `prereg.json` V1–V8 分析前锁存 `5306c3f8…`[笔误修正重锁] → `gate_prereg.json` 实现前锁存 `bf208433…` → `engine.py` → `result.json` + `build_report.py`(内联) → `flashprove_report.html`）。6载体全是Anthropic同一主体按KB-STRUCT02打折为1;性能110tok/s/19MB/70-95x全self-reported不采信。核心缺口:10门禁无一判可证明声明的边界诚实性(证明执行来源≠事实正确/信任根须可信渠道/形式化协议≠全栈代码/未覆盖项披露)→编译第19道 `proof_boundary_honesty.py`（来源冒充事实·信任根自定·形式化无边界→downgrade,未覆盖隐藏/部分/字面串→flag,全自洽→ok;7活体+25测试+双AST自审,§58选A不接run_loop）。四次自咬:V2 manifest缺subject字段、V3 README跨markdown链接断锚点、V6翻译漏项+锚点错、V7引擎中文串进Compare,全修工具不放水零漂移。新增KB-AUDIT14(108条)+加固T05/AUDIT03/STRUCT02。全量513 passed。\n- Proactive AI for Superintelligent Agents 综述精研（§72）：`audit_proactive_ai/`（论文PDF一手9.1MB/8页+正文11658行、作者项目主页HTML34KB同主体、Google Research页抓取失败标unavailable；SHA256锁存 → `prereg.json` V1–V8 分析前锁存 `52f80aad…` → `gate_prereg.json` 实现前锁存 `028504e5…` → `engine.py` → `result.json`）。四载体同一综述同一作者主体按KB-STRUCT02折为1;1410 cited/80/13域是综述规模非独立证据;提出6A框架≠证明主动行为有效(KB-STRUCT05),capability≠authority≠calibration。核心缺口:19门禁无一判主动介入的授权正当性(目标值得做≠被授权做/仲裁四关/形式控制≠真实控制/沉默与风险分级同意)→编译第20道 `proactive_authorization.py`（目标冒充授权·无仲裁·形式冒充实控→downgrade,沉默隐藏/部分/字面串→flag,全自洽→ok;7活体+27测试+双AST自审,§58选A不接run_loop）。三处自咬:high_impact_confirm跨行断裂/intelligence_alignment误用主页句/六能力串HTML标签分隔,全修工具不放水零漂移。新增KB-AUDIT15(109条)+加固STRUCT02/STRUCT05/AUDIT03。全量540 passed。\n- DeepSeek 全家桶 API 五来源精研（§73）：`audit_deepseek/`（在线Demo 436字节SPA壳+JS bundle477KB+CSS、全家桶发布公告HTML27KB、Chatbot指南HTML52KB→纯文本txt、chat-demo仓库commit8ad7b56 v0.1.3、定价页HTML29KB→纯文本txt；SHA256锁存 → `prereg.json` V1–V8 分析前锁存 `c0dd563d…` → `manifest.json` → `gate_prereg.json` 实现前锁存 `8f8dbf15…` → `engine.py` → `result.json`）。五来源全DeepSeek官方同一产品deepseek-flash按KB-STRUCT02折为1;能力效果self-reported不采信(KB-RSI07);提出能力≠真能控制(KB-STRUCT05)。核心缺口:20门禁无一判客户端声称的控制vs服务端裁决(传入≠生效/别名≠路由/基础风控≠合规/工具免费≠零成本)→编译第21道 `interface_contract_honesty.py`（参数忽略·别名改路由·风控冒合规→downgrade,免费冒零成本/部分/字面串→flag,全自洽→ok;8活体+25测试+双AST自审,§58选A不接run_loop）。两处自咬:中文Compare移_A字典/has_cjk改ord()边界,全修工具不放水零漂移。新增KB-AUDIT16(110条)+加固STRUCT02/STRUCT05/AUDIT03。全量565 passed。\n- 认知投降谱系18来源精研（§74）：`audit_cognitive_surrender/`（门首篇X@addyosmani不可达[DNS劫持到Meta IP];7一手[认知投降/Storey认知债/理解债务/ClaudeCode评审/意图债务/编排税/Anthropic内部研究]+PubMed Clark用NCBI E-utils补救[Nature Comms2025];SSRN研究abstract经Zotero/managementcraft二手镜像、Substack agentic-verification经thekb.eu二手摘要;6+来源[X/5Substack/SSRNdirect/claude.com]DNS劫持不可达标unavailable;SHA256锁存28文件 → `prereg.json` V1–V8锁存`dc52aa6c…` → `manifest.json` → `gate_prereg.json`锁存`791f5407…` → `engine.py` → `result.json`）。Osmani作者家族8+来源折1;一手实验数字(Shaw-Nave N1372/+25-15pp/h0.81、Anthropic RCT52人17%lower、ClaudeCode2500→30000changes/day revert降40%)vs博客无数据vs preprint未评审vs survey自陈分级;术语cognitive debt区分提出vs转述。核心缺口:20门禁无一判评审者独立判断能力前提(独立观点/能力未侵蚀/监督未自我消解/表面≠系统正确,paradox of supervision原话)→编译第22道 `supervision_viability.py`（无独立观点/能力侵蚀/监督悖论自我消解→downgrade,表面冒系统/部分/字面串→flag,全自洽→ok;8活体+25测试+双AST自审,§58选A不接run_loop,与§60评审漏斗保真对象层级不同）。两处自咬:中文折扣Compare移_A字典/锚点大小写按原文,全修工具不放水零漂移14/14锚点。新增KB-AUDIT17(111条)+加固STRUCT02/STRUCT05/AUDIT03。全量590 passed。\n- 公众号AINLP批判性思考精研（§75）：`audit_addy_critical_thinking/`（用户确认出处公众号AINLP，本机公众号付费通道未开通→经同源站52nlp下载全文26483d35…，文末『关注微信公众号AINLP』证实同源；S01中文全文含原作者英文原稿检测截图+完整参考链接；S02 TechMoon繁体综述独立交叉；X原文/unwire/BI网络不可达标unavailable；SHA256锁存 → `prereg.json` V1–V8分析前锁存`80e6af27…` → `manifest.json`[用户确认补强重锁9038e9df…] → `gate_prereg.json`实现前锁存`7ca4020e…` → result.json → self_knowledge_report.html）。用户点明此文是洞见本体(自知)基础；精髓『你只需要知道，自己缺少哪些理解』——自知=标记盲区而非拥有完整模型，与insight/retrospective/estimation一脉。S02繁体交叉5/5明标个人实务观察/无量化对照/六问未被证有效/132人单公司自报→证据只证现象不证六问有效；Addy概念家族与§74同源折1;self-reported折扣。八个命题26/26锚点命中。核心缺口:22门禁无一判主体对自己认知边界的诚实觉察(比§74评审者能力前提更内一层元认知自知)→编译第23道 `self_knowledge_honesty.py`（无假设/假装完整/不可证伪/隐瞒技能退化→downgrade,部分/字面串→flag,全自洽→ok;8活体+30测试+AST自审,§58选A不接run_loop,只判声明诚实不承诺真防投降）。三处自咬:C5意图债务措辞/C6『就』字C7『恰恰是』/繁简交叉,全修工具不放水零漂移26/26锚点。新增KB-AUDIT18(112条)+加固STRUCT02/STRUCT05/RSI07/AUDIT03。全量620 passed。\n- 自见自知本体系统机制化（§76）：`audit_addy_critical_thinking/`扩展（用户定位'Agent洞悉本体即自见自知,能机制化尽量机制化'→`ext_prereg.json`实现前锁存`86d3a7f8…`→核验原文6簇自问锚点全命中→`self_insight_ontology.json`[1a8bfa3a…]把全文系统化为本体:自见=看见产出真相[K2验证边界/K3决定透明]、自知=知道自身状态[K1认知边界/K4意图完整/K5反方论证/K6责任编排],机制化状态已编译2·候选2·并入1·仅声明1）。K2验证边界簇独立(绿灯≠全覆盖/测试可与功能同错/标准事前/证据先于总结/自我质疑),与proof_boundary_honesty形式化证明对象不同→编译第24道`verification_boundary_honesty.py`（绿灯冒充全覆盖/标准事后合理化/总结盖证据/无自我质疑→downgrade,部分/字面串→flag,全自洽→ok;8活体+30测试+AST自审,§58选A不接run_loop,只判声明诚实不承诺验证真有效）。K3决定透明/K4意图完整识别为候选未硬编译(对象层级须辨析)、K5并入K1可证伪、K6与§72部分重叠仅声明——能机制化尽量机制化但只机制化会拦且独立拦截面,不为宏大叙事造玩具牙(KB-META01/§67)。S02繁体明标六问未被证有效。新增KB-AUDIT19(113条)+加固STRUCT02/STRUCT05/RSI07/AUDIT17。全量650 passed。\n- HarnessPro 三来源精研（§77）：`audit_harnesspro/`（用户给 arXiv:2610.26770v2 + GitHub pzs19/HarnessPro@6fd2d4d + evaluation.md；PDF+abs+仓库页+README[API补取]+评估说明全抓取，SHA256锁存 → 清单07d46012…/分析前69850798…/门实现前ecf7d724… → PDF转文本2836行通读 → result.json 28/28锚点+交叉5/5。核心：label-free自生成判据评估自生成改进,Fig2自曝LLM judge失败召回41.7%→自生成测试83.3%仍漏16.7%、横轴靠Official outcome外部锚、指令'No separate reviewer is part of this run'；S03诚实披露release不含数据/权重、GLM-5.2 snapshots缺失、错配不复现[加分但结果不可核]；preprint未评审+自报实验折1）。判据来源缺口≠proof_boundary形式化证明/≠verification_boundary通过声明→编译第25道`criterion_origin_honesty.py`（自生成冒充外部锚/召回边界隐藏/无外部锚定/自审冒充独立评审→downgrade,部分/字面串→flag,全自洽→ok;37项测试+7活体+AST自审,§58选A不接run_loop,只判声明诚实不承诺判据可靠）。断字锚点三处（answer key/cost 26.1%/checked by authors）按真实单行修工具不放水。新增KB-AUDIT20(114条)+加固STRUCT02/STRUCT05/RSI07/AUDIT17。全量687 passed。\n- PaperAgent 清华AGI新范式精研（§78）：`audit_system1_system2/`（用户指定PaperAgent公众号文+源论文arXiv:2610.39497v1清华季向阳团队Perspective;PDF+abs+公众号原文全抓取,GAIR验证墙/头条空正文unavailable,英文BestHub交叉 → 清单dfc6d66a…/分析前0dc64f44…/门实现前7976b4e1… → 论文29/29锚点+公众号7/7+交叉5/5。核心:§7.2'门控审查自身训练数据'——p_train∝p_cand·e≠p_cand→MNAR、被压制者结果永不观测分数永不修正、Theorem19盲点非平均误差主导、审计率须independent of predictor scores、保险丝;Perspective非实证/qualified yes/hypothesis折1;公众号'20%→5倍'编辑添加论文无此数字诚实记录）。选择性监督结构性机制≠§77声明诚实→编译第26道`selective_supervision_honesty.py`（压制区零概率/审计自审污染/盲点隐藏/反事实损失不承认→downgrade,部分/字面串→flag,全自洽→ok;37项测试+7活体+AST自审,§58选A不接run_loop,只判机制声明诚实不承诺筛选真有效）。三处锚点/分级自咬留痕。新增KB-AUDIT21(115条)+加固STRUCT02/STRUCT05/RSI07/AUDIT17。全量724 passed。\n- 记忆三来源精研（§70）：`audit_memory_trap/`（S01 components-of-agent-memory 一手HTML25KB[anthropic 2026-11-06] + S02 Dreams 区域锁二手复用§68 S07标S3 + S03 Memory Trap 一手HTML482KB+PDF798KB正文2761行[Princeton+Anthropic,6模型对照,有code]；SHA256锁存 → `prereg.json` V1–V8 分析前锁存 `b61ed731…` → `gate_prereg.json` 实现前锁存 `a34e50c0…` → `engine.py` → `result.json` + `build_report.py` → `memory_scope_report.html`）。谱系：S01 components(hippocampus→neocortex巩固+dreaming)与§68同源、S02 Dreams=§68 S07同源二手,均按KB-STRUCT02打折;S03 Memory Trap是新对象(作用域风险)独立。核心:良性交互(benign interactions)自写记忆在超出原作用域时致unsafe行为——write-time(写时broaden,skip confirmation→never confirm)+read-time(读时overgeneralize),"no adversary"恶意过滤器抓不到;6模型实验:高风险任务跳过确认/sycophancy/削弱正确测试/ImpossibleBench作弊。V4缺口:本仓memory_curation(内容质量)/retrieval_grounding(检索污染)/improvement_memory(可证伪)无一判记忆作用域保持→编译第18道 `memory_scope.py`（写broaden·读不核情境·无适用边界→downgrade,良性漂移/部分/字面串→flag,全自洽→ok;7活体+21测试+双AST自审,§58选A不接run_loop）。两次自咬:V3 'with and without memory'跨PDF行断裂→单行锚点,V7引擎自身'内容质量'中文字面串进Compare→移_A字典键引用,修工具不放水零漂移。新增KB-AUDIT13(107条)+加固AUDIT11(内容质量vs作用域)/STRUCT02。全量488 passed。
- 11来源异步子Agent谱系精研（§69）：`audit_async_subagents/`（11来源：9一手直连[LangChain博客/Claude Code子Agent文档/DeepSeek Harness长文fxtwitter API全文143blocks/Deep Agents产品页/Python+JS异步子Agent文档/Managed文档/async-deep-agents仓库raw README/issues页] + 2二手区域锁[OpenAI dots与async-tool-calling，developers.openai.com全Forbidden→WebSearch聚合官方原文逐字转录标S3]；11份正文SHA256锁存 → `prereg.json` V1–V8 分析前锁存 `5f343965…` → `gate_prereg.json` 实现前锁存 `0b78ad89…` → `engine.py` → `result.json` + `build_report.py` → `async_delegation_report.html`）。四家主体谱系：LangChain系6源(S01/S05/S06/S07/S09/S10)同源打折为1条 + Anthropic Claude Code(S02) + DeepSeek Super-agent(S04) + OpenAI dots/async-tools(S03/S08)=4独立主体，非11项独立验证。V4缺口：本仓门禁(session_continuity判跨run续接/memory_curation判记忆治理)无一判单会话内后台委派生命周期(提交收集解耦/可引导可取消/句柄穿越compaction/完成主动通知)→编译第17道 `async_delegation_lifecycle.py`（无解耦·不可引导·句柄随压缩丢失→downgrade，无完成通知·部分·字面串→flag，全自洽→ok；7活体+21测试+双AST自审全过，§58选A不接run_loop）。判据自咬一次：V4首跑resume/cancel通用词过宽，resume误伤KB-AUDIT10跨会话resume(假阳性)→收窄为7个专属术语全0命中，修工具不放水零漂移。V6守主体错位(DeepSeek架构主张非效果、self-reported不采信)、V8同构打折(Router/Worker≈本仓always-on)。新增KB-AUDIT12(106条)+加固AUDIT10(区分续接vs委派)/STRUCT02。全量467 passed。
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
| `svagent/async_delegation_lifecycle.py` | 11来源异步子Agent谱系 S10/S06/S02/S04/S03/S08（§69） | 后台委派生命周期：无解耦(同步阻塞)/不可引导(不可取消)/句柄随压缩丢失→downgrade；无完成通知(fire-and-forget)/部分/字面串→flag；全自洽→ok（只判机制声明自洽，不承诺委派真高效/完成真被通知；判外部异步系统声称，不判本仓） |
| `svagent/memory_scope.py` | Memory Trap 论文 arXiv 2611.07554（§70） | 记忆作用域保持：写时broaden/读时不核情境/无适用边界→downgrade；良性漂移已发生/部分/字面串→flag；全自洽→ok（只判机制声明自洽，不承诺记忆真不过度泛化；判外部记忆系统声称，不判本仓） |
| `svagent/proof_boundary_honesty.py` | FlashProve 公众号文章+6一手载体（§71） | 可证明声明边界诚实性：来源证明冒充事实/信任根自定/形式化无边界→downgrade；未覆盖不披露/部分/字面串→flag；全自洽→ok（只判边界披露诚实，不承诺证明正确/系统有效；判外部可证明声明系统，不判本仓） |
| `svagent/proactive_authorization.py` | Proactive AI 综述 PDF+项目主页（§72） | 主动介入授权正当性：目标冒充授权/无仲裁四关/形式冒充真实控制→downgrade；沉默与分级同意不披露/部分/字面串→flag；全自洽→ok（只判授权声明自洽，不承诺系统真校准；判外部主动 agent 声称，不判本仓） |
| `svagent/interface_contract_honesty.py` | DeepSeek 全家桶 API 五来源（§73） | 接口契约边界诚实性：参数被忽略/别名改路由/基础风控冒完整合规→downgrade；工具免费冒零成本/部分/字面串→flag；全自洽→ok（只判控制边界声明诚实，不承诺服务端真按声明裁决；判外部 API 契约与客户端，不判本仓） |
| `svagent/supervision_viability.py` | 认知投降谱系 18 来源（§74） | 监督可行性：无独立观点/评审能力被侵蚀/监督悖论自我消解→downgrade；表面正确冒系统正确/部分/字面串→flag；全自洽→ok（只判评审者独立判断能力前提是否诚实披露，不承诺评审真有效；判外部评审流程，不判本仓；与 §60 评审漏斗保真对象层级不同） |
| `svagent/self_knowledge_honesty.py` | 公众号 AINLP 批判性思考文（§75） | 自知诚实性：无假设/假装完整/不可证伪/隐瞒技能退化→downgrade；部分/字面串→flag；全自洽→ok（只判主体认知边界声明是否诚实自洽，不承诺真能防认知投降；洞见本体自知基础，与 §74 评审者能力前提对象层级不同；判外部主体，不判本仓） |
| `svagent/verification_boundary_honesty.py` | 公众号 AINLP"绿灯只证明一件事"簇（§76） | 验证边界诚实性：绿灯冒充全覆盖/标准事后合理化/看总结不见证据/无自我质疑→downgrade；部分/字面串→flag；全自洽→ok（只判验证边界声明诚实自洽，不承诺验证真有效；与 §71 proof_boundary_honesty 形式化证明对象不同——测试/证据覆盖边界；判外部主体，不判本仓） |
| `svagent/criterion_origin_honesty.py` | HarnessPro 论文（arXiv:2610.26770v2，§77） | 判据来源诚实性：自生成判据冒充外部锚/召回边界隐藏/无外部锚定披露/自审冒充独立评审→downgrade；部分/字面串→flag；全自洽→ok（只判自生成判据声明诚实自洽，不承诺评估判据真可靠；label-free自评估系统适用，与§71形式化证明边界/§76通过声明对象不同；preprint自报折1；判外部系统，不判本仓） |
| `svagent/selective_supervision_honesty.py` | PaperAgent 文+清华 System1/System2 Perspective（§78） | 选择性监督诚实性：压制区零概率(标签MNAR)/审计率依赖分数(自审污染)/盲点隐藏/漏判反事实损失不承认→downgrade；部分/字面串→flag；全自洽→ok（只判筛选器审查自身训练数据的机制声明自洽，不承诺筛选真带来收益；结构性偏差即使诚实声明仍存在，与§77声明诚实对象不同；Perspective折1；判外部系统，不判本仓） |
| `svagent/policy_evolution_grounding.py` | 多模态 Agent 记忆综述 arXiv:2610.19366v1 §5.3/§8.3.3（§79） | 策略演化接地诚实性：策略不可寻址/反馈未归因策略级/证据路径被静默削弱(正确率↑却少依赖原始模态)/修订未经验证持久→downgrade；部分/字面串→flag；全自洽→ok（只判 T3 自演化策略演化机制声明自洽，不承诺演化真带来收益；正确率保持≠接地保持；与self_evolving运行时机制/memory_scope单条边界/criterion_origin判据来源/selective_supervision筛选训练数据对象不同；survey二手折1；判外部系统，不判本仓） |
| `svagent/memory_provenance_honesty.py` | 多模态 Agent 记忆综述 arXiv:2610.19366v1 §8.1.1/§8.3/§6.6（§80） | 记忆溯源可恢复性诚实性：溯源是可选元数据(非设计属性)/证据不可恢复/时间有效性未跟踪(陈旧或弱接地证据)/更新不可逆→downgrade；部分/字面串→flag；全自洽→ok（只判记忆表示层把溯源/可恢复/时间有效性/可逆性当结构属性的声明自洽，不承诺记忆真可验证可纠错；召回量≠可恢复溯源+时间有效性；与memory_scope单条边界/retrieval_grounding输出引用/memory_curation内容质量/criterion_origin判据来源层级对象不同；survey二手折1；判外部系统，不判本仓） |

每道门禁都有对应测试：`tests/test_disambiguation_gate.py` `test_improvement_memory.py` `test_component_attribution.py` `test_evaluation_reliability.py` `test_scoring_integrity.py` `test_transfer_holdout.py` `test_judgment_robustness.py` `test_task_retrospective.py` `test_lineage_guard.py` `test_backtest_integrity.py` `test_call_site_integrity.py` `test_reviewer_evaluation.py` `test_serving_signal_gate.py` `test_retrieval_grounding.py` `test_session_continuity.py` `test_memory_curation.py` `test_proactive_authorization.py` `test_interface_contract_honesty.py` `test_supervision_viability.py` `test_self_knowledge_honesty.py` `test_verification_boundary_honesty.py` `test_criterion_origin_honesty.py` `test_selective_supervision_honesty.py` `test_policy_evolution_grounding.py` `test_memory_provenance_honesty.py`。

---

## 4. 复现纪律（为什么要保持文件平铺）

1. **路径被记录**：`build_*.py` 内硬编码了如 `open("/workspace/...")` 与相对文件名；预注册 JSON 记录了证据文件名。移动/改名会让脚本失效。
2. **哈希被锁存**：9 个 `*.sha256` 文件锁定了预注册与样本内容；已逐一验证一致（见整理记录）。改动内容会破坏锁存。
3. **后验不伪装**：`rsi_structure_amendment.json` 明确标注为全文到手后的增量，与 `rsi_structure_preregistration.json` 的哈希严格区分。

因此本仓采用 **"保路径 + 强导航"** 的整理策略：结构清晰靠本文档，不靠移动文件。
