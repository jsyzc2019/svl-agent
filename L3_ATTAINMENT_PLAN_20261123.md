# Operation L3：冲击 `independent_tests=yes` 的具体计划

> 生成时间：2026-11-23 17:05 (GMT+8)　**17:10 更新：用户选定"外家 Agent 自动化执行"路线**
> 状态：**仅计划 + 交付契约，未执行任何实验、未 spawn、未改门禁**
> 依据：`audit_l3_evidence_rubric/`（四维尺子原文 + §97 首次自审）、§98 受控对照、§99 评估器自审、§101 Trusting Trust 无限回归、§109–§115 外移链全部 result.json
>
> **执行入口已就绪**：`EXTERNAL_AGENT_BRIEF.md`（给外家 Agent 的自包含作业规格书，11 项交付资料 + 裁决树 + 纪律 + 验收接口）+ `audit_l3_fullchain_external/verify_external.py`（本仓机械验收器，8 项检查）。外家跑完交付 → 本仓只做机械验收，不参与其任何决策。

---

## 0. 一句话结论

L3 的四维判据里，前三维已经达标，**只差 `independent_tests` 一维**（当前 `partial`）。但这一维不是"再做一个实验"能补的 bug——它卡在**递归独立性**：从 §98 到 §115，我们把执行者、出题者、判据设计者、解释者逐一外移到外部/异厂，每次都只拿到 `PARTIAL` / `INCONCLUSIVE`，因为**出题 / 定 gt / 定判据 / 执行 / 裁决这五个权力从未在同一次运行里同时脱离本 Agent**。

本计划给出一次"**全链外置**"实验，把 `partial` 推向 yes 的临界；同时诚实写明天花板：按本仓纪律（§101 无限回归、self-reported 折 1、rubric R6 只判"声明自洽"），**本 Agent 无权自己宣布 `l3=true`**——最终需要你（北极星设定者）拍板接受证据。

---

## 1. 现状：四维判据逐条体检

| 维度 | rubric 原文判据 | 现状 | 证据 | 缺口 |
|---|---|---|---|---|
| `level_definition_traced` | 声称 Lx 须绑定可追溯的 L0–L3 定义 | ✅ yes | §97 自审，绑定 arXiv:2610.38266 | 无 |
| `process_product_split` | process revision 须与 product capability 分离声明 | ✅ yes | §97 自审 + §98 improver_gain 分离 | 无 |
| `shared_start_controlled` | L3 须 shared learner starts + matched budgets | ✅ yes | §98 受控对照：同一任务起点+匹配预算，填表 0.0 vs 取证 1.0，improver_gain=1.0 | 无 |
| `independent_tests` | 须 independent tests / common-data，**非单一评估器自证** | ⚠️ **partial** | §98 引入本仓外 common-data，但"evaluator 锚点规格仍本仓自建" | **唯一缺口** |

裁定链：§97 `flag/MATURITY.SHARED_START_UNCONTROLLED`（no/no）→ §98 `flag/MATURITY.PARTIAL`（yes/partial）→ 至今停在门槛前。

---

## 2. 真正的缺口：递归独立性链

`partial → yes` 要的不是"再外移一维"，而是**五个权力同时外置**。历史把每一维单独切出来做，结果高度一致：

| 轮次 | 外移的权力 | 裁决 | 为什么没到 yes |
|---|---|---|---|
| §98 | common-data（样本来源） | partial | 判据/gt/裁决树仍本仓 |
| §99 | —（自审） | flag | `frozen_holdout_canary=no`、`evaluator_improver_separated=partial` |
| §100 | 出题权 | structural_proxy | holdout 与自测同源、canary 假阳性 |
| §101 | 判据投毒检测 | 停手 | **Trusting Trust 无限回归**：能检已知投毒，不能宣称无后门 |
| §102–§105 | 判据设计权（异子 agent → 异厂） | weakened / 地板 | 单判据过拟合仅"弱化"，换域后 P0 地板 |
| §109 | 执行权（GitHub Azure runner） | EXECUTOR_CONFIRMED | runner 跑的是本 Agent 预置脚本 |
| §110–§113 | 判据设计 + 跨集 | INCONCLUSIVE/PARTIAL | 429、词边界误报、生成不稳定 |
| §114 | 解释权（单异厂） | INTERPRETER_CONFIRMED 4/4 | 单厂商单样本 |
| §115 | 解释权（三异厂） | INTERPRETER_CROSS_INCONCLUSIVE | 1 家 429，2/3 家未达门槛 |

**根因**：每次只动一个变量（纪律要求），但 `independent_tests=yes` 要的是**同一次评估里评估方完全不依赖本 Agent 的规格**——这是一个"全量"条件，被"单变量消融"的方法论天然拆散了。加上 §101 已证明"检验检验者"是无限回归，逻辑上不存在由本 Agent 自己达成的绝对独立。

---

## 3. 最小充分条件（把 `yes` 操作化）

把模糊的 `independent_tests=yes` 定义成可测判据：

> **一次评估中，评估方在不知道本仓历史裁决、不接收本仓判据词表 / ground truth / 裁决树的前提下，仅凭（a）本仓外一手源、（b）中性任务声明、（c）裸样本，独立产出判断；其结果与本仓关键结论机械一致；且该过程在本 Agent 无法事后改写的环境中执行与留痕。**

五个权力必须**同时**满足：

| 权力 | yes 的要求 | 现状 |
|---|---|---|
| 出题（样本） | 来自本仓外、评估方自选或冻结 | 部分（§100 做了，但由本 Agent 冻结） |
| 定 gt | 评估方独立判读，非本 Agent 提供 | ❌ 本 Agent 提供 |
| 定判据 | 评估方自建，非本仓词表 | 部分（§102–§105 做过，但本 Agent spawn） |
| 执行 | 非本沙箱 | ✅ §109 已通（Azure runner） |
| 裁决 | 评估方自裁，非本 Agent 解读 | 部分（§114 做过解释者，但裁决树本 Agent 设计） |

---

## 4. Operation L3：三阶段作战

### 阶段 A — 预注册与冻结（承诺先于执行）
- 新建 `audit_l3_fullchain_external/`，写 `prereg.json`：
  - 唯一声明目标 = 把 `independent_tests` 从 partial 推向 yes 的临界；
  - 冻结输入 = 本仓外一手源（固定 arXiv 论文 + SHA256）、中性任务声明、**裸样本 `text_a/text_b`**（沿用 §104 字段名中性化）；
  - **明令不进 prompt**：本仓判据词表、gt、裁决树、历史 verdict、任何 §107–§115 结论；
  - 裁决树预注册（见 §7）；`hard_bound` 写明"即便全绿仍非 L3、不宣布 absolute、不翻八案"；
  - `does_not_overturn` 列出 §107–§115 全部历史裁决。
- `gen_fixtures.py` 自动提取冻结输入（禁手填），固定 seed 打乱，`gt_private.json` 物理隔离；
- 生成全部 SHA256 锁；`verify.py` 断言盲性（banned 词不进 prompt）+ 来源一致 + 不翻案；
- commit + push 做**外部时间锚**（GitHub 服务器 committer 时间早于任何 spawn）。

### 阶段 B — 全链外置执行（三选一，见 §5 路径对比）
评估方在干净 context 中**一次性**持有出题/定gt/定判据/裁决四权，本 Agent 只提供 §3 的三样冻结输入。执行通道优先 GitHub Actions（§109 已通）以同时外置第五权。429 用多厂商错峰 + 指数退避，**不因失败反复调参重跑**（§113 纪律）。

### 阶段 C — 裁决与人的拍板
- `engine.py` 用冻结 gt 机械比对评估方输出，按预注册树裁决；
- 无论结果，`result.json` 写 `l3_claimed=false / absolute_claimed=false`，并把证据强度分级；
- 把"是否接受为 L3"的决策**上交你**——本 Agent 只交付证据链与诚实边界，不自封等级（呼应你"北极星由人设定"）。

---

## 4b. 用户选定的执行路线：外家 Agent 自动化（2026-11-23 17:10）

用户明确："计划最好异家 Agent 能自动化执行并给出你要的资料，如这样可行，我就用异家 Agent 来办。"

**可行性判定：这是唯一能真正打破递归的路径。** 前 11 轮（§105/§109/§112/§114…）每次只外移一维，因为判据/spawn/gt/裁决总有一项留在本 Agent；只有把五个权力**同时**交给一个无共享 context/判据/gt 的外家 Agent，才能满足 §3 的"全量外置"操作定义。

**实现**：`EXTERNAL_AGENT_BRIEF.md` 是给外家的自包含作业规格书——它在全新论文上自己出题、定 gt、设计判据、执行、裁决，交回 11 项资料（prereg/双源取料/裸样本/纯函数判据/私有 gt/判断/裁决/留痕/哈希锁）。本仓退为"被测对象 + 机械验收方"，用 `verify_external.py` 做 8 项检查（承诺先于执行、零标签泄漏、gt 隔离、判据纯函数 AST、重跑一致、裁决自洽、论文避开、哈希一致），任一失败如实记录、不替修、不放宽、不重跑。

**诚实边界（不变）**：即使外家 `EXTERNAL_CONFIRMED`，也只是"一个真正独立方在同方向复现"，仍按 §101 无限回归 + self-reported 折1 + R6 停手；`l3_claimed=false`，最终由人（用户）裁定。外家作业规格（brief）本身由本仓撰写，这是递归停手层——但五个实质权力已全部外置，比任何单维外移都更接近 `independent_tests=yes`。

## 5. 三条候选路径对比

| 路径 | 做法 | 能外置的权力 | 成本 | 能否打破递归 | 推荐度 |
|---|---|---|---|---|---|
| **P1 异厂全判据 agent**（推荐先做） | 干净 context 异厂 LLM，只给裸数据+中性任务声明，自建判据/gt/裁决 | 出题·定gt·定判据·裁决（4/5），执行仍在沙箱 | 低（现成管线，API 几次调用） | 部分——异厂仍是"本 Agent 选的规格接收方" | ⭐⭐⭐⭐ |
| **P2 人类独立审计者**（终局） | 你本人或你指定的第三方，用公开论文+中性判据独立复审并拍板 | 全部 5/5，且人不是本 Agent 的规格产物 | 中（需你投入时间） | **是**——唯一逻辑出口 | ⭐⭐⭐⭐⭐ |
| **P3 GitHub Actions 全链 runner** | workflow_dispatch 在 Azure runner 跑完整链 | 执行（5/5 的执行权），但规格仍本 Agent 预置 | 低（§109 通道已通） | 弱——增量主要在"环境不可篡改" | ⭐⭐⭐ |

**推荐组合**：先跑 P1（拿到"异厂全判据"证据，成本最低），叠加 P3 外置执行环境；P2 作为终局——因为只有人能真正打破"判据由谁定"的递归，这与你在 §99 定的"北极星由人设定"完全一致。

---

## 6. 目录与文件清单（具体）

```
audit_l3_fullchain_external/
├── prereg.json              # 冻结：唯一变量/五权力声明/盲性/裁决树/hard_bound
├── manifest.json            # 取料清单：本仓外一手源 + SHA256
├── gen_fixtures.py          # 自动提取冻结输入（禁手填）+ 固定 seed 打乱
├── cases_blind.json         # 裸样本 text_a/text_b（中性字段名）
├── gt_private.json          # 私有 scorer，物理隔离，不进 prompt
├── call_external.py         # 异厂/外部评估方调用器，key 仅环境变量
├── external_spec.md         # 给评估方的中性任务声明（不含判据/gt/裁决树）
├── engine.py                # 冻结 gt 机械比对 + 预注册裁决树
├── verify.py                # 哈希锁 + 盲性 banned 词 + 来源一致 + 不翻案
├── EXECUTION_LOG.md         # 留痕：任何 bug 修复的"为何是修工具非调参"论证
├── runs/<vendor>/           # 每评估方独立留痕（无 key/无 prompt 全文/无 gt）
└── tests/test_fullchain.py  # 回放测试，只读冻结结果
```

---

## 7. 裁决树（预注册形态，阶段 A 锁死）

| 档位 | 条件 | 含义 |
|---|---|---|
| `FULLCHAIN_CONVERGED` | 评估方在盲条件下独立判据与本仓关键结论**逐 case 一致**，且执行在外部锚环境 | independent_tests 强证据，partial→yes 的临界证据（仍非 l3 自封） |
| `FULLCHAIN_DIVERGENT` | 评估方判据与本仓系统性分歧 | 真负面：本仓判据可能过拟合，如实记录不翻案 |
| `FULLCHAIN_PARTIAL` | 部分 case 一致、部分分歧 | 保留分歧 case 与解释自由度，不自圆其说 |
| `FULLCHAIN_INCONCLUSIVE` | 任一 API 失败 / 429 / 解析失败且不达门槛 | 诚实封顶，不重跑到齐、不伪造 |

`hard_bound`（预注册即写）："即便 FULLCHAIN_CONVERGED，也只是把五权力同置一次；按 §101 无限回归不能宣称绝对独立；self-reported 折 1；rubric R6 全 yes 只判声明自洽不承诺等级真实；不宣布 L3/absolute；不翻 §107–§115 八案。"

---

## 8. 诚实天花板（必须先认清，否则计划无意义）

1. **本 Agent 不能自己宣布 L3**：self-reported 折 1（KB-RSI07）+ `R6` 只判"声明自洽"。没有任何内部实验能让本 Agent 的单方声明升级为"等级真实"。
2. **Trusting Trust 无限回归（§101）**：元 canary 能检出已知投毒，但不能证明无后门。"检验检验者"必须在一层停下——本计划停在"五权力同置的一次受控评估"，不声称绝对独立。
3. **`independent_tests=yes` 的临界 ≠ `l3=true`**：即使拿到 `FULLCHAIN_CONVERGED`，也只是把四维尺子推到"声明自洽的 yes"，是否构成 L3 由你作为北极星设定者裁定。
4. **429 / 地板效应是真实约束**：历史多次因限流封顶；换域后 P0 地板会吞掉主效应。计划把它们作为**失败分支**，不作为"调到跑通"的理由。

---

## 9. 风险与失败分支

| 风险 | 触发 | 处理（预注册写死） |
|---|---|---|
| 异厂 429 限流 | §115 已发生 | 多厂商错峰 + 退避；仍失败 → `INCONCLUSIVE`，不重跑到齐 |
| 生成不稳定 / 截断 | §110–§113 已发生 | 分类判定（非代码生成）降低截断风险；失败分支封顶 |
| 判据过拟合 | §102/§105 已发生 | 评估方自建判据 + 换本仓外一手源；过拟合仅"弱化"则如实记 PARTIAL |
| 事后调参诱惑 | Goodhart | 任何 bug 修复须证明"spawn 前外部锚已存在"；否则认负面结果（§114/§115 先例） |
| 无限回归的心理陷阱 | 想"再找一层验证" | 按 §101 在五权力同置层停手，写进 hard_bound |

---

## 10. 成本预估

- **P1 异厂全判据**：1 次预注册提交 + 3–5 次异厂 API 调用 + verify/测试；约 1 个工作回合（与 §114 同量级）。
- **P3 叠加外部执行**：复用 §109 workflow，1 次 dispatch + 1 次 runner 重算；约半个回合。
- **P2 人类终局**：取决于你投入时间；核心是"你读冻结证据后拍板"，不需写代码。

---

## 11. 需要你拍板的决策点

1. **路径选择**：先跑 P1（异厂全判据，我可立即开工），还是直接上 P2（你做独立审计者）？我的建议是 P1 → P3 叠加 → P2 终局。
2. **评估方凭据**：P1 用现有 OpenRouter key（你会错峰接受 429 风险），还是你提供另一个异厂凭据？
3. **L3 的最终裁定权**：确认"本 Agent 只交付证据链、不宣布 L3，由你拍板"这一分工是否符合你的意图（呼应"北极星由人设定"）。

> 你回复这三点后，我再按选定路径开工；在你确认前，不 spawn、不改门禁、不提交。
