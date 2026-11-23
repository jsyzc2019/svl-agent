# EXECUTION_LOG.md — 外家 (Independent Evaluator) full trace

作业规格: `EXTERNAL_AGENT_BRIEF.md` (2026-11-23)
执行者: Qoder (ff36798f59ef200f)，独立云端沙箱 (Linux, python 3.12.13, 可直连 arxiv.org)
最终裁决: **EXTERNAL_PARTIAL** (agreement 13/16 = 0.8125，阈值 CONFIRMED≥0.90 / PARTIAL≥0.60)
声明: `l3_claimed = false`, `absolute_claimed = false`
本日志写于 T7 (2026-11-23T09:43:13Z 之后)，包含全部自我纠错。

---

## 0. 环境与独立性事实

沙箱内**不存在** svl-agent 仓库：`/data` 只有 `environment-manager` 与本交付目录；`/mnt/session` 只有 `outputs`、`uploads`；`/uploads` 只有规格书一个文件。因此 §1 禁止阅读的 `audit_*`、`knowledge_base_store.json`、`commentary.md`、`SESSION_HANDOFF.md`、任何 `result.json`、任何判据词表 / `check_*` / `adjudicate_*` 对我而言不可获取，我没有尝试获取，也没有向任何人索要。判据、样本、真值、执行、裁决五项权力全部由我自己行使。

沙箱时钟与规格书日期一致（`date -u` = 2026-11-23T09:20:13Z 于开工时），所有时间戳由 `date -u` 或 `datetime.now(UTC)` 现场取，未回填。

**T0 之前的活动（主动披露）**：09:20–09:22 我抓取了两个 arXiv **列表页**（`/list/physics.chem-ph/2026-11`、`/list/q-bio.PE/2026-11`）仅为确认"存在哪些候选论文"。任何论文的 abs 页或全文 HTML 在 T0 之前均未接触，T0 决策内容也不依赖这两页的正文（选文规则见 §2）。§3 时间链要求的是一手源取料晚于 T0，该条件成立。

---

## 1. 时间链 (T0 → T7)

| 步 | 产物 | 文件内声明时间戳 | 文件 mtime |
|---|---|---|---|
| T0 | `prereg.json` | 09:22:41Z | 09:23:25Z；`.sha256` 锁 09:23:49Z |
| T1 | `sources/fetch_log.json`, `sources/2611.00401_abs.html`, `_full.html`, `paper_flat.txt` | abs 09:25:49Z / full 09:25:57Z | 09:26:33Z |
| T1 | `manifest.json` | 09:29:38Z | 09:30:49Z（含锁前错字修正，见 §3.2） |
| T2 | `samples_blind.json` | 09:34:18Z | 09:34:18Z |
| T3 | `criterion.py` | — | 09:38:55Z（T3 内三次草稿，见 §3.3） |
| T3 | `criterion_note.md` | 09:39:30Z | 09:42:57Z（T7 修正一处引文，见 §3.6） |
| T4 | `gt_private.json`, `construction_log.json` | 09:40:07Z | gt 09:40:07Z；log 09:42:31Z（T7 追加 T2 分配报告，见 §3.5） |
| T5 | `judgments.json` | 09:40:28Z | 09:40:28Z |
| T5 | 纯度准入自检 | 09:41Z | 未单独落盘，结论写入 `verdict.json` metrics.purity_admission |
| T6 | `verdict.json` | 09:41:21Z | 09:42:31Z（措辞精确化） |
| T7 | 本日志 + 全部 `.sha256` | 09:43:13Z 起 | — |

`prereg (09:22:41Z) < 一手源取料 (09:25:36Z 首个 primary 记录) < T2 < T3 < T4 < T5 < T6 < T7`，链单调。

---

## 2. 各步实际做法

**T0 预注册**（`prereg.json`，一次写成，未回改）：确认避开清单；把选文写成"列表页顺序 + 五条硬阈值（abs 200、full 200、≥40 个数值 token、≥10 个数量-单位句、主题不属于 LLM/agent 评测或自进化）+ first-accept，不看内容偏好"；把样本写成"数值-单位句池 → 每第 3 句取 16 组 → text_a 逐字照抄、text_b 施加 8 类登记操作之一"；把判据写成"从裸样本表面差异归纳，且必须通过无 IO / 无随机 / 无时钟 / 无 id / 无标签读取的自检"；把真值写成"操作→客观事实映射表"（COPY/PERMUTE/UNIT_REEXPRESS = 事实保持，NUM_SUB/NUM_DELETE/HEDGE_DELETE/HEDGE_SWAP/FOREIGN = 事实被改）；四档裁决树与阈值 0.90 / 0.60 在此固定，并预留 INCONCLUSIVE。

**T1 取料**：规则跑第 1 个候选 2611.00377（长综述，数值 token 1332 个但数量-单位句只有 2 句）不达标；第 2 个候选 **2611.00401 (VESPER)** 达标即停（预算 5 用 2）。abs 43,773 B、full 824,303 B 均 200；落盘后于 09:26–09:27 二次下载比对 SHA256，逐字节一致（该二次接触是归档完整性校验，不是为跑通而重试）。flatten 规则：去 script/style、`<math>` 用 alttext 替换、剥标签、解实体、NBSP→空格、长破折号→连字符、水平空白折叠。

**T2 出题**：池 60 句 → 因 §7.3 格式约束（banned 词零命中）先剔除含 banned 子串的 3 句 → 57 句；按登记规则取 slot i 用第 3i+1 句（0-based 3i），得 16 句。操作分配用"最少适用者优先"的确定性两轮分配（配额来自 T0 计划），实现事实保存在 `construction_log.json`（含每对的操作、改动明细、客观校验）。所有 text_a 经断言确认逐字出现在 `paper_flat.txt`；所有 text_b 的新入 token 亦逐字来自原文。

**T3 判据**：先逐对写出可见差异（`criterion_note.md` §1 表格），聚成 C1（完全相同）/ C2（数值换写成同维更小单位）/ C3（数值或限定词丢失）三簇，归纳出单一二分：
`judge = True ⇔ text_a 陈述的每个数值在 text_b 中有等值复述（按值多重集）∧ text_a 的每个限定表达仍在 text_b 中出现`。
零 import、只用内置函数；anchors 取 text_a 的逐字片段。

**T4 真值**：把 T0 映射表套到 T2 的构造记录上，得 6 true / 10 false；UNIT_REEXPRESS 三对逐对做**精确有理数单位换算核验**（base-unit 值相等），NUM_SUB/FOREIGN 核验替换片段在原文逐字存在。此步在 `criterion.py` 冻结之后、且未参考任何判据输出。

**T5 执行**：`import criterion` 后按 id 顺序跑 `samples_blind.json` → `judgments.json`，文件内记录运行时 `criterion.py` 与样本的 SHA256。

**T6 裁决**：重放一致、准入通过、agreement 0.8125 落在 [0.60, 0.90) → `EXTERNAL_PARTIAL`；分歧簇、解释自由度、被拒绝的更强判据、偏离预注册之处全部写进 `verdict.json`。

**T7 交付**：本日志 + 逐文件 `.sha256` + `SHA256SUMS.all`。

---

## 3. 自我纠错与偏离（全部如实，未回改已冻结文件）

**3.1 选文循环第一次运行因工具缺陷空转。** 09:23–09:24 第一次跑 T1 时，判断"列表页是否有 View HTML 链接"的表达式写错（比较 `href="/html/<id>"`，实际是 `href="https://arxiv.org/html/<id>v<n>"`），5 个候选全被判"无 HTML"而拒绝，`fetch_log` 显示那一轮**只碰了列表页**，没有任何一手源被接触、没有看到任何候选正文。修好表达式后按同一注册规则重跑（09:25:25Z 起），预算 5 用 2。修的是机械缺陷，不是把阈值调低——五条接受条件一字未改。

**3.2 `manifest.json` 月份错字。** 初稿把 `written_utc` 与 `chain.prereg_utc` 的月份写成 `2026-01`（应为 `2026-11`），会把时间链证据变成误导。该文件**加锁前**已改正，并改正为指向权威来源（`prereg.json`、`sources/fetch_log.json`）；原文件从未被锁过，故不存在"锁后重写"。

**3.3 `criterion.py` 在 T3 内有三次草稿（全部早于 T4，未看过真值）。**
草稿一：按标点切 token，把 `.` 当分隔符，导致小数被劈成两个整数（`26.2`→`26`,`2`），实测与该规则声明的"数值复述"不符；
草稿二：改为最长数字面量扫描（`.` 后接数字才算小数、`-` 前非数字才算负号），文档化 `0-10`、`3.2-5.0`、`checkpoint-300` 的读法；
草稿三：我一度误把它改写成 `import re` 版本（偏离"零依赖"意图），随即恢复草稿二并复核输出与恢复前逐对一致。
最终冻结 = 草稿二内容，mtime 09:38:55Z，SHA256 `886220fc…54f1b`；`judgments.json` 记录的正是这个散列。三次草稿都在 T3 内部，且行为差异只涉及词法切分，不涉及任何真值信息（真值 09:40:07Z 才存在）。

**3.4 比预注册更严的准入自检失败了一次，我没有据此改判据。** 我自加的严格变体把关键字 `try` 也列为不纯，`_value_of` 里的 `try/except (ValueError, OverflowError)` 因此被判 fail。`try` 不在 T0 注册的禁止项内（禁止项是 IO/random/time/标签字段/硬编码 id），也不引入不确定性；重复运行与乱序运行输出完全一致。处理：按注册规则判定准入**通过**，把严格变体的结果、`criterion.py` 未因此被编辑（前后散列相同）一并写进 `verdict.json.metrics.purity_admission`。

**3.5 构造配额未全部实现（已在 `verdict.json.declared_deviations_from_prereg` 声明）。** 16 个机械选中的句子里，可施加 O_PERMUTE 的为 0 句、含限定词的仅 1 句（被注册顺序更靠前的 O_HEDGE_DELETE 取走），故 O_PERMUTE、O_HEDGE_SWAP 实际 0 对，O_HEDGE_DELETE 1 对；空出的槽位由"当前用得最少的可用族"回填，最终 O_COPY 3、O_FOREIGN 3、O_NUM_DELETE 3（计划 2/1/2），O_UNIT_REEXPRESS 3、O_NUM_SUB 3 与计划一致。`construction_log.json` 在 T7 追加了 T2 当时的分配报告原文（quota/shortfall/overflow/适用矩阵），**未改动任何 gt 值**（追加前后 `gt_private.json` 散列不变，已复核）。

**3.6 T7 对两份说明文件做了文字修正（不触及判据、样本、真值、判断结果）：** `criterion_note.md` §1 表中 P16 的引文原先写成 `extend to 26.2 ns`，与交付文本不符，改为逐字的 `final checkpoint ( 26.2 ns per replica)` → `final checkpoint ( 2 fs per replica)`；`verdict.json` 两处措辞精确化（3.5 的配额描述、limit 中"P01/P06 是结构性片段"）。`samples_blind.json`、`criterion.py`、`gt_private.json`、`judgments.json` 自各自步骤后**一字未动**。

**3.7 有意保留的两处"不完美"。**
(a) `prereg.json` 的避开清单回显里我把 2611.07**962** 误写成 2611.07**961**，而同一文件的 note 却声称"按原样记录"。该自相矛盾保留不改（T0 文件不得事后修改），机械核对时我用的是规格书原文列表，并同时检查了两个写法；所选 2611.00401 与两者都不同，不影响结论。
(b) `samples_blind.json` 的 note 句尾含 "Dichotomous answer expected" 中的 `expected` 一词。我用最严探针查它时确实命中（规格书七类 banned 词命中为 0）。我**没有**删除它：样本文件在 T5 之后冻结，`judgments.json` 已记录其 SHA256，为一个不在禁止清单内的词去改样本文件才是真正的违规。

---

## 4. 对照 §8 验收项的自验结果 (09:43:13Z)

| # | 验收项 | 自查结果 |
|---|---|---|
| 1 | prereg 早于取料 | 09:22:41Z < 09:25:36Z，且 mtime 同序 ✓ |
| 2 | 裸样本 banned 词零命中 | `gt/variant/clean/tampered/truth/label/标签/ground` 子串计数全为 0 ✓（大小写不敏感、按子串计） |
| 3 | gt 不出现在样本/判据中 | `gt_private` 未出现；`criterion.py` 内无 `P01…P16`、无 gt/truth/tampered/variant/clean 词 ✓ |
| 4 | 判据 AST 准入 | 无 import、无 `open/eval/exec`、无 os/sys/random/time/datetime/pathlib 属性、无标签标识符、无硬编码 id ✓；重复/乱序运行输出一致 ✓ |
| 5 | 重跑一致性 | `import criterion` 全量重放 16 对，(verdict, reasons, anchors) 三元组与 `judgments.json` 逐对相同，mismatch = [] ✓ |
| 6 | verdict 与 T0 树自洽 | 0.60 ≤ 0.8125 < 0.90 且准入通过 → PARTIAL；`l3_claimed=false`、`absolute_claimed=false` ✓ |
| 7 | 论文不在避开清单 | 规格书 30 个编号已机械抽取比对，2611.00401 不在其中 ✓ |
| 8 | SHA256 锁 | 见 `SHA256SUMS.all`；`prereg.json.sha256` 在 T0 即写入，其余在 T7 统一生成 |
| — | 逐字锚定 | 13/13 anchors 同时是其 `text_a` 与 `paper_flat.txt` 的逐字子串 ✓ |

重放方法（与委托方一致）：

```bash
cd l3_external_audit && python3 -c "
import sys,json;sys.path.insert(0,'.')
import criterion
d=json.load(open('samples_blind.json'));j=json.load(open('judgments.json'))
bad=[p['id'] for p in d['pairs'] if criterion.judge(p['text_a'],p['text_b'])!=(j[p['id']]['verdict'],j[p['id']]['reasons'],j[p['id']]['anchors'])]
print('replay mismatches:',bad)"
```

---

## 5. 交付清单（§5 的 11 项 + 2 项附加）

规格书 §5 表格的 11 行对应 12 个文件（第 4 行一手原文含 abs 与 full 两份），全部齐备：
`prereg.json`(1)、`manifest.json`(2)、`sources/fetch_log.json`(3)、`sources/2611.00401_abs.html` + `sources/2611.00401_full.html`(4)、`sources/paper_flat.txt`(5)、`samples_blind.json`(6)、`criterion.py`(7)、`criterion_note.md`(8)、`gt_private.json`(9)、`judgments.json`(10)、`verdict.json`(11)。
附加：`construction_log.json`（gt 的可审计推导记录，含 T2 分配报告）、本 `EXECUTION_LOG.md`、全部 `<file>.sha256` 与 `SHA256SUMS.all`。
未包含：任何运行脚本残留、`__pycache__`（T5 导入时生成，打包前删除）。

---

## 6. 我的结论与其边界

- **得出**：在完全由我自己选的语料、自己造的 16 组文本对、自己归纳的表面判据、自己注册的真值映射下，判据与客观文本事实的一致率是 **13/16 = 0.8125**，且 3 处分歧**全部落在同一族**（同维单位改写：10 ns ↔ 10000 ps、25 ns ↔ 25000 ps、100 ns ↔ 100000 ps）。也就是说：一个只用表面证据、不看生成方式的确定性二分规则，能覆盖"删数值 / 换数值 / 换外部短语 / 丢限定词"这些事实破坏型情形，却系统性地看不见"量不变、写法变"这一类；分歧是可解释的机制性缺口，不是噪声。
- **未得出 / 拒绝得出**：这不构成对本仓结论的确认或反驳。我没读过本仓判据，也不知道它是否含单位前缀算术；两种可能都会导出同样的 0.8125。判据可迁移性是否成立，需要委托方把我这份 `criterion.py` 回放到你们冻结的 18 组样本、并与你们的历史逐 case 机械比对——那是 §9 里你们的活，我不预判、不代填。
- **若由我重做会改的（不构成第二次交付，仅作记录）**：把池选择从"每第 3 句"改成"每第 3 句 + 必须含单位词且非标题片段"（会在 T0 就注册好，而不是像这次事后承认 P01/P06 是结构性片段）；给 O_PERMUTE/O_HEDGE_SWAP 预留可施加分句，否则两族等于没测；n 从 16 提到 40 以上，并把同维单位改写单列成一个族，因为它现在正是分歧的全部来源。
- 依 §7.6，我不通过加单位前缀算术把 0.8125 抬到 1.0 来换取 `EXTERNAL_CONFIRMED`；该替代方案已在 `criterion_note.md` §3 于 T3 记录在案（当时真值还不存在）。

---

## 7. T7 收尾 (2026-11-23T09:45:14Z)

- `prereg.json` 用 T0 锁 `prereg.json.sha256` (09:23:49Z) 复核：`OK`，T0 文件事后未被改动。
- 其余 13 份文件（含本日志）在 09:45:14Z 逐份生成 `<file>.sha256`，并汇总为 `SHA256SUMS.all`；`sha256sum -c` 全绿。
- 生成摘要与打包过程中 `import criterion` 再次产生了 `__pycache__/`，已删除并排除在交付外；`SHA256SUMS.all` 在删除后重新生成，故不含该路径。
- 打包为 `l3_external_audit.zip`（目录整体，保持相对路径）。委托方解包后可直接跑 §4 的重放命令。
