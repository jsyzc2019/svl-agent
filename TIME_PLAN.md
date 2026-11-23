# 时间计划清单（自主运维 · 一日节奏）

> 版本：v1.1　生成：2026-11-22 12:20 (GMT+8)　更新：2026-11-22 12:55 (GMT+8)　§93 第 2-4 轮已闭环
> v1.1 变更：记录自主运维第 2/3/4 轮已按①→⑧闭环完成；清单获授权可动态扩展领域（§93 新增安全/合规 P3）。玩法不变：取料—精研—编译—接合—验收—提交—复盘。
> 使用权：用户已赋予"独立运维本仓一天的全部权限"。本清单把一天切成可验证的时段，每段有明确产出与红线。
> 原则：**取料—精研—编译—接合—验收—提交—复盘**闭环；每段留痕，全程可回放。

## 一日闭环（建议时段，可按实际伸缩）

| 时段 | 环节 | 具体动作 | 产出（可验证） | 红线 |
|---|---|---|---|---|
| ① 晨间 | 自检 | 读 SESSION_HANDOFF → git status → 全量 pytest → 链审 | 现状确认：全绿 / 无 ahead / 工作区干净 | 不带病开工；有红先修 |
| ② 上午 | 取料 | 按 WORK_ITEMS P0 话题，从 WORKPLACES 已验证场所拉 1-2 篇一手料 | `audit_<topic>/downloads/fetch_log.json` + SHA256 + 原文切片 | 一手优先；失败来源记 ok:false 不删 |
| ③ 上午 | 预注册 | 分析前锁 prereg + 分析规格；实现前锁 gate_prereg；逐字锚点探测 | 3 份 SHA256 锁 + 锚点清单（disclose 必中、红旗零误中） | 锚点不可编造；先锁后看 |
| ④ 下午 | 精研 | 坍塌映射→check_* 实现（四维 yes/no/partial）→25 测试→AST 自审→FJ adjudicate_* | 新门禁模块 + 测试 + 取证入口 + result.json | 不动 R0-R6；不接 run_loop（§58） |
| ⑤ 下午 | 接合 | growth_bridge 把 KB fix + 取证缺口注入 PDCA，落消费痕迹 | `growth_bridge_consumption.json`（数量一致可回放） | 认知机制交人不假装可编译 |
| ⑥ 傍晚 | 验收 | 全量 pytest → live_regression → 链审 → README 统计刷新 | 全绿数字 + 一致核对 | 数字必真实，不虚报 |
| ⑦ 傍晚 | 提交 | 本地提交（两批次一推）；需要时自管凭据推送 | 提交哈希 + 远端=本地核验 | 凭据用后即删；hosts 即改即恢复 |
| ⑧ 夜间 | 复盘 | commentary 追加 + REPOSITORY_MAP / HANDOFF 同步 + 次日话题候选 | 文档现状与统计一致 | 只判自洽不承诺有效 |

## 首日试运行（2026-11-22，Pilot Day）· 已跑完四轮

- **目标**：跑通①→⑧全链，验证"三处人类依赖点"确有自我实现路径。✅ 已达成。
- **取料主题**：从 P0 自主扩展到 P1/P3，四轮各自独立发现一手料。
- **产物**：四道新门禁 + 四个 FJ 取证入口 + KB 洞见 + 全量回归 + 提交。
- **结束判据**：全链闭环 + 全绿 + 工作区干净（或明确提交）；不追求数量，追求"可回放的真实闭环"。

| 轮次 | 章节 | 领域 | 一手料 | 新门禁（FJ 入口） | 测试 | KB |
|---|---|---|---|---|---|---|
| 第一轮 | §90 | P0 自我验证 | arXiv:2611.10063 | silent_failure_honesty (ext) | 1041 | KB-AUDIT32 |
| 第二轮 | §91 | P0 RSI | arXiv:2610.27610 | rsi_claim_audit_honesty (ext2) | 1066 | KB-AUDIT33 |
| 第三轮 | §92 | P0 记忆治理 | arXiv:2609.33013 | memory_consolidation_governance_honesty (ext3) | 1091 | KB-AUDIT34 |
| 第四轮 | §93 | P3 安全/合规 | arXiv:2611.24362 | redteam_robustness_honesty (ext4) | 1116 | KB-AUDIT35 |

> **受控实验轮（§98–§108，不编译新门禁）**：第五轮起从"刷门禁数量"转向"补证据链独立性缺口"，不再逐轮加门禁。§98 shared-start 受控对照（improver_gain=1.0）、§99 评估器独立性自审（flag）、§100 冻结 held-out 独立性验证（tamper 6/6 可迁移）、§101 元 canary 投毒检测（poison_detection=1.0）、§102 判据设计权外移（复用 §100 冻结集，唯一变量=判据设计者；独立设计的 judge_D 与 G 在 core 逐样本一致率 1.0 → CRIT.PORTABLE_SINGLE_DESIGN_OVERFIT_WEAKENED；刻意不编译第 39 道门禁）、§103 设计者约束消融 de-steering（抽 prompt 规则词 + id 中性化打乱 + gt 文本反查物理隔离；D1b core 全对强加固、D1a 暴露任务解释自由度 → DESTEER_PARTIAL）、§104 字段名语义消融（用户"进一步放松"→字段名 claim/evidence→text_a/text_b，唯一变量=字段名方向语义；两设计者均过准入但未恢复上游判据 D2a tamper0.0/D2b tamper0.5 → FIELD_NEUTRAL_DEPENDENT，结论首次翻转，定位"可迁移"依赖字段名语义这一更外层脚手架；不编译新门禁）、§105 跨数据域字段名消融 2×2（用户"再放飞"→换全新论文 2611.14326 检验 §104 外部效度；出题权外移独立标注者 + 四全新 context 设计者；四设计者全 core0.5 地板效应、field_gap 新0.0旧0.667、条件A在新域也未恢复D1b→CROSS_DOMAIN_INCONCLUSIVE；根因取证=旧D1b与新B2同构算法相反正类，真杠杆是"删限定成分=负类"正类语义取向；不编译新门禁）、§106 任务目的语义注入受控实验（用户"攻新方向"→把 §105 根因从事后观察升级为因果验证；唯一变量=目的叙事 P0无目的/P1忠实性/P2近似重复，样本/字段/id/gt 全锁死；三全新 context 设计者盲评 P0 core0.50地板/P1 core1.00从地板跃迁到全对/P2 core0.67；主指标 orient_gap=0.667<0.8→PURPOSE_INCONCLUSIVE 强提示但不翻案；post-hoc 分层非否定gap1.0/否定gap0.0=指标异质性错配，诊断不进裁决；不编译新门禁）、§107 预注册分层确认性实验（用户"下一方向"→把 §106 post-hoc 分层假设升级为独立确认集上的预注册确认；三重加固=换全新论文 2611.22027 独立确认集+spawn 前锁死分层主指标 PRIMARY=非否定限定 gap≥0.8+异 model 路由 default/reasoning/lite；PRIMARY=1.0/SECONDARY=0.0/P1.core=1.0/P0 地板→STRATIFIED_CONFIRMED；能力对照 clean 全对/canary 全错逐样本一致排除 model 能力替代解释；单一确认集不宣布 L3；不编译新门禁）、§108 跨集复现+外部时间戳锚（用户"按真正冲击去做"→先审计外部 orchestrator/异厂商 evaluator 通道：repo scope 无 workflow + 无 LLM key，均不可达，留档 BLOCKERS.md；改做可达最大增量=第三确认集全新论文 2611.20899 SciWorldBench+spawn 前把全部锁/裁决器 sha256 commit+push 做外部时间戳锚 b8daa96 服务器 10:03:01Z 证明承诺先于执行；盲评 PRIMARY1.0/SECONDARY0.0 跨集复现但 P0 地板消失(core0.5→1.0)+canary 能力对照失效→CROSS_SET_PARTIAL 不翻案 REPRODUCED；时间锚≠执行者独立仍 l3=false；不编译新门禁）、§109 外部 orchestrator 执行者独立性受控验证（用户"给你token，继续"+三次 token 识别纠正→新 PAT 含 workflow scope 解除 §108 硬障碍；probe workflow push 成功 a4d1da9+Azure runner attestation run 45013089276 hostname=runnervm0hi8g/whoami=runner/azure 内核/nonce 绑定不可伪造；外部重跑哈希锁定 §107 engine.py，spawn 前 prereg d96e1f0 锁哈希，首触发 422 修重复 env（e26d5ef）→run 45013693112 success，外部 result sha cf6d0f2b… 三方逐字节一致、verdict/core 独立复现→EXECUTOR_INDEPENDENCE_CONFIRMED 10/10；确认执行者独立一维≠达 L3，设计者/样本/解释未动+外部跑本 Agent 预置脚本，仍 l3=false；不编译新门禁）。测试 1141→1387，KB 131→160。详见 SESSION_HANDOFF §4k–§4v。守恒：最高杠杆≠最高产出数（KB-META10）、放松=抽脚手架不是降门槛（KB-META11）、脚手架消融层级图谱与负面结果价值（KB-META12）、对照组先决与未复现≠推翻（KB-META13）、任务目的语义决定正类取向的加法受控（KB-AUDIT48）、指标语义与样本异质性错配/post-hoc 不翻案（KB-META14）、从 post-hoc 分层到预注册确认的方法学升级与独立确认集（KB-AUDIT49）、能力对照排除替代解释+单一确认集不抬级（KB-META15）、跨集复现+外部时间戳锚（KB-AUDIT50）、单集完美模式样本特异+地板/能力对照未跨集复现的分层陈述（KB-META16）、排除一个替代解释≠证明绝对属性，不宣布 L3。§113 跨集×跨厂商 2×2 闭合尝试（用户"最有性价比推"→填第二集×Liquid AI唯一空格，规则/厂商逐字节复用§112只换§108第二集冻结输入，spawn前锁7b9122d 06:14:10Z外部锚；两次spawn(16000/20000)均部分失败三条件无法同时完成→区分确定性bug与生成不确定性、拒绝第三次重跑(Goodhart)、按prereg失败分支封顶SET_VENDOR2_INCONCLUSIVE、保留失败留痕+EXECUTION_LOG、修引擎三态bug不放宽；2×2格未填充=§112效应主集特异样本特异性又一例；仍l3=false；不编译新门禁）。§114 解释者独立性（用户"请继续下一步"→补L3最后未外移维=解释权；四轮充分统计量gen_fixtures自动提取固定seed匿名化+档位中性化,私有gt物理隔离不进prompt,spawn前锁7b1f1644 06:29:30Z外部锚；异厂ernie干净context盲评4/4复现本Agent四轮裁决含关键case_2→INTERPRETER_CONFIRMED解释一维获受控外移证据；FULL≡CONFIRMED字段bug按§109/§111修工具不放宽,KB-META22辨析vs Goodhart;仍l3=false/absolute=false;不编译新门禁）。§115 解释者跨厂商交叉确认（用户"继续"→§114单厂商证据升级多厂商;逐字节复用§114冻结输入与调用器唯一变量=厂商,空间探测选dots-studio/inclusionai/liquid三家真异厂,spawn前锁d6a6aa4 06:45:04Z;dots与liquid均4/4但inclusionai正式spawn 429失败→不重跑不包装,按prereg封顶INTERPRETER_CROSS_INCONCLUSIVE;present状态机bug按§113修工具不放宽,KB-META23失败厂商≠判错厂商;仍l3=false;不编译新门禁）。Operation L3真正异家Agent全链外置(用户"异家Agent异种大模型已出结果"→Qoder五权力同时外置零共享context,自包含作业书EXTERNAL_AGENT_BRIEF+8项验收器外部锚af360e6;交付合规8/8但跨判据目标迁移11/18 clean6/6 tampered2/6→FULLCHAIN_PARTIAL独立性做满≠结论YES,验收器2项bug按§109修工具不放宽复验违规FAIL3项,KB-AUDIT58/META24,仍l3=false由人裁定;不编译新门禁）。§112 真正跨厂商 designer 交叉（用户"最有性价比事项"→识破§110/§111都nvidia只跨模型未跨厂商→换Liquid AI真异厂，AST v2规则逐字节复用§111哈希断言证明唯一变量=厂商+spawn前锁ff0403e 06:02:22Z外部锚；主效应PRIMARY1.0首次真正跨厂商复现，但SECONDARY1.0否定翻转豁免细分语义没复现+P0地板消失→CROSS_VENDOR2_PARTIAL不翻§110/§111案；测试断言finish=length+reasoning_fallback按§109修工具不放宽；仍l3=false；不编译新门禁）。§111 准入规则粒度修订确认（用户"开工，按计划推"→KB-META18 弱点：§110 词边界把 notes 提 negation/variant 误判泄漏→spawn 前 commit+push 锁 AST 控制流级准入 v2+对偶测试(6真泄漏拒/notes放行/§110三judge放行)+外部时间戳锚 37bd2e4 05:40:09Z；跨模型异厂 nemotron-ultra-550b 三条件准入全过+PRIMARY1.0 主效应复现但 P0 地板消失(core1.0，同§108)→AST_V2_PARTIAL 不翻案，§110 INCONCLUSIVE 保留；工具锁文件名 bug 按§109修工具不放宽；仍 l3=false；不编译新门禁）。§110 异厂商 designer 设计者独立性（用户"用户提供 OpenRouter key"→异厂 NVIDIA nemotron-3.5-super-vl 经 OpenRouter 免费端点在干净 context 生成三 judge，spawn 前锁哈希+裸样本物理隔离标签+429退避+reasoning回退；冻结gt盲评数值完全复现 PRIMARY1.0/SECONDARY0.0/P1.core1.0/P0地板，但 notes 词命中事前锁禁用词表→准入未全过→按裁决树封顶 CROSS_VENDOR_INCONCLUSIVE 不翻案，定位"准入词边界粒度误报"弱点 KB-META18；设计者一维外移但受封顶、样本/gt/盲评/裁决/解释仍本Agent，仍 l3=false；不编译新门禁）。

## 守恒条款（一天内必须守住）

1. **不伪造证据**：所有锚点/数字来自一手原文；篡改测试只在临时副本。
2. **不动 R0-R6 骨架**：新门禁沿用四维 {yes,no,partial} 与中文 `_A` 字典。
3. **不接 run_loop**（§58）：自检选 A，不把死循环塞进生产路径。
4. **凭据自管**：token 不入仓、不入配置、不打印；askpass 用后即删；hosts 即改即恢复。
5. **诚实边界**：self-reported 折 1；只判声明/证据自洽，不承诺真实有效；模拟标 synthetic。
6. **两批次一推**：本地可按批提交；推送前核验远端=本地，无遗留。
7. **守法（§93 用户强调）**：领域/话题可动态扩展但必须守法；安全线只做防御性诚实审读，不产出可利用攻击载荷、不协助绕过防护。
8. **系统安全红线（§99 用户明确）**：本 Agent 无删除操作系统、系统文件、格式化硬盘的权限，也不得尝试。hosts 即改即恢复、临时凭据/脚本用后即删、篡改只在临时副本；绝不做删系统目录 / `rm -rf /` / 格式化 / 改引导等破坏性操作。

## 失败处理

- 取料失败（网络/付费墙）：如实记录 ok:false，换同源同步站或交叉源，不用二手冒充一手。
- 测试失败：定位根因，改机制不放宽断言；三次不成如实报告并暂停该话题。
- 链失配：拒判（ChainIntegrityError），不绕过；先查是否误报（清单格式/历史目录）。
