# §4gl 第二家异厂执行 + 首次 GAP_CLOSED 裁决日志（诚实分层）

> 本文件记录 DeepSeek 直连 key 后重跑 §L3-R2 的完整链，以及一次关键的工具职责分离。
> **两层裁决必须分清**：§L3-R2 子实验裁决 = `GAP_CLOSED`（独立文件 `result_4gl.json`）；内核判定态 `verdict` = `GAP_INCONCLUSIVE`（权威源 `result.json` + handoff，从未动）。

## 执行主体与独立性

- 异厂 = DeepSeek（`deepseek-chat`，直连，异于 Qoder / nemotron / Hunyuan）。key 现场验证：`/user/balance` 200、余额 57.97 CNY、`deepseek-chat` 实调 PONG/finish=stop，tool calling 干净可用（无 reasoning 截断）。
- 投喂仅 brief v2 + external_kit；禁用串 `family_taxonomy`/`ground_truth_supported`/`audit_frozen_holdout`/`samples.json` 零命中；`GAP_CLOSED` 仅 brief §9 透明告知段。
- 外部时间锚 `f8e7f3f1`（2026-11-23T10:03:40Z）早于 spawn（2026-11-26T06:31Z）。
- **执行环境边界**：本沙箱 harness 机械执行异厂 tool call；"执行"一维非纯外置，如实标注，不冒充完美五权力外置。

## T0→T7 完整交付（对照 §4gk 的空样本）

| 阶段 | 结果 |
|---|---|
| T0 prereg | 异厂自选 arXiv 2405.14831（HippoRAG，避开清单零命中），三层判据归纳法 + 裁决树阈值 0.85 |
| T1 一手源 | abs/full 均 HTTP 200（43KB/482KB），paper_flat 105K 字符 |
| T2 出题 | 16 组裸样本，从论文原句自构，三类断言现象齐全（否定 N05/N13、截尾 N06/N10/N16、连接词 N08/N14），零标签词 |
| T3 判据 | `criterion.py` 纯函数（否定集合+短语、截尾双向、连接词等价白名单）；**异厂自修一处语法错误**（unmatched `)`），逻辑未变 |
| T4 定 gt | 从文本事实定义，16/16 与词级 diff 一致，未参照判据 |
| T5 执行 | judgments 与 criterion 重跑一致 16/16 |
| T6 裁决 | 异厂自填 `EXTERNAL_CONFIRMED`（其语义=自建判据在自建 gt 上内部一致，非宣布 L3） |
| T7 日志 | EXECUTION_LOG.md + pack.py 13 锁 + zip |

## 权威验收与回放裁决

- 异厂本地 `selfcheck.py`：**11/11 PASS**。
- 本仓 `run_acceptance.py`（调权威 `verify_external.py`，passed 由真实 exit0+9/9+ACCEPTED 决定，附三重 SHA256）：**9/9 PASS，passed=true**。
- `engine.py` 把异厂 criterion 回放到本仓冻结 18 样本：`internal_replay=16/16`、`repo=13/18`、**断言类 `4/4`**（基线 Qoder 0/4）、数值类 0/2、`clean=6/6`、`canary=3/6`。
- 按 prereg 预注册五档树：`clean 6/6 且 断言类≥3/4 且 canary≥3/6` → **`GAP_CLOSED`**（相对基线 0/4 实质突破，第二家判据看到了断言层）。逐 case 独立重算确认 S01/S02/S04/S05 全 DETECT。
- 数值类 0/2 保留：该断言层判据本就不看数字，prereg 明确数值类由数值型判据覆盖，不调参补。

## 关键工具职责分离（self-bite + 修正）

- **问题**：`engine.py` 把子实验裁决写进 `audit_l3_gap_targeted/result.json`，而该文件被 `numeric_honesty.truth_snapshot()` 当作**内核判定态真值源**。写入 `GAP_CLOSED` 后，handoff 权威行 `verdict=GAP_INCONCLUSIVE` 与现场不一致，26 个判定态守卫连锁失败。
- **不是**：不能改 handoff 为 `GAP_CLOSED`（变相自抬内核判定态），也不能把 engine 结果改回 `GAP_INCONCLUSIVE`（抹掉真实突破）。
- **修正**：把 engine 完整裁决 `GAP_CLOSED` 原样保存到独立文件 `result_4gl.json`（sha256 锁 `b977b89b…`）；把 `result.json` 恢复为内核权威态 `GAP_INCONCLUSIVE`（与 handoff 一致）；两层职责分离。全量回 1608 passed。
- **根因**：engine.py 把"子实验裁决"与"内核判定态源"混在同一文件——这是工具设计的历史包袱，本轮不动 engine（避免放宽/改规则），用文件分层规避，并记录此待改进点。

## 其余 self-bites（改工具不改判据）

1. **异厂语法错误**：criterion.py 末尾 `return ...)` 多括号，AST fail；让 DeepSeek 自己修自己的交付（逻辑不变），非本仓代改。
2. **幻觉时间戳**：tool call 内写幻觉旧 ISO；harness 按真实命令时序机械覆盖（prereg 06:32:00Z < 取料 06:32:39Z）。
3. **验收器读说明文字**：selfcheck `coll()` 递归 findall 把 `_timestamp_note` 里提及的旧 ISO 当真 → 说明字段改不嵌 ISO 字面，旧值留痕到 EXECUTION_LOG（历史 §114 同类）。
4. **fetch_log 格式**：初版用 `+00:00` 后缀 + 无 `role`，selfcheck 正则只认 `Z` 且找 `role:primary`；改契约格式（工具层）。
5. **verify 默认路径**：不传参时读相对 `l3_external_audit_v2` 而非 `received/...`，导致首次 0/1；带正确参数后 9/9。调用层问题，非交付问题。

## 诚实上限

- 证明：第二个异厂家（DeepSeek）的判据独立归纳 + 通过本仓机械验收 + 回放到冻结集断言类 4/4，相对 Qoder 0/4 是真实、可复现的突破。
- 不证明：L3 达成、判据普遍可迁移、内核 verdict 改变。`hard_bound` 明列：即便 GAP_CLOSED 也只是单次单维部分复现、两家仍属 LLM 家族、族标注/冻结样本/裁决树仍本仓、§107–§115 九案与 FULLCHAIN_PARTIAL 不翻案。
- **内核 `verdict=GAP_INCONCLUSIVE`、`l3=false`、`absolute=false`、宪法锁 `fe56291b` 全不动；最终裁定权在委托方（人）。**
