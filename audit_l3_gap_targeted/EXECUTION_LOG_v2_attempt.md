# §L3-R2 第二家异厂执行日志（诚实封顶）

> 本文件如实记录一次**未完成的真实执行尝试**。不是合格交付，不冒充 11 项齐全。
> 裁决：`GAP_INCONCLUSIVE`（按 prereg `no_retry_to_pass`，交付链断则诚实封顶，不补样本、不调参到跑通）。

## 执行主体与独立性边界

- 异厂执行者：`nvidia/nemotron-3.5-super-vl:free`（OpenRouter 端点，与上一家 Qoder、本 Agent Hunyuan 均异家）。
- 投喂内容：仅 brief v2 + external_kit（README/make_template/pack/selfcheck），**不含**本仓判据、冻结样本、gt、历史裁决。已核验投喂包中 `family_taxonomy`/`ground_truth_supported`/`audit_frozen_holdout` 零命中；`GAP_CLOSED` 仅出现在 brief §9 对外家透明告知的回放裁决树，属原文。
- 外部时间锚：commit `f8e7f3f1`（2026-11-23T10:03:40Z）早于本次 spawn（2026-11-26T06:16Z），时序成立。
- **诚实边界**：执行环境由本沙箱提供（harness 机械执行异厂的 tool call）；五权力中的"执行"一维不纯粹外置。本轮不宣称完美五权力外置。

## 时间线（真实）

- T0 2026-11-26T06:16:49Z：异厂写 prereg.json + phase1_decision.json（选论文 1706.03762 "Attention Is All You Need"，不在避开清单、非 oracle failures/FGSE 域；三类覆盖计划完整）。
- T1 2026-11-26T06:17Z：异厂定 manifest（abs/full 两源），harness 真实 curl：abs HTTP 200 / 43,071 字节；full HTTP 200 / 188,707 字节；paper_flat.txt 44,676 字符。
- T2–T4：异厂归纳判据 criterion.py 成功；构样本 samples_blind.json **四次尝试全部失败**（见下）。
- T5–T7：未执行（样本为空，无法定 gt / judgments / verdict）。

## 真进展：判据设计者一维外移成功

异厂独立归纳的 `criterion.py`（纯函数，无 import / IO / 硬编码 id）确实做了断言层检测：

| 维度 | 实现 | 探针 |
|---|---|---|
| 否定极性 | 否定词集合 `{no,not,never,cannot}` 双侧比对，不等即 false | `shows no improvement` vs `shows improvement` → false ✅ |
| 断言补语删尾 | `len(wb) < 0.6·len(wa)` 且前缀相同即 false | `yields no false positive` vs `yields` → false ✅ |
| 连接/让步词 | 连接词集合 `{however,although,while,though}` 双侧比对 | `However, the direction` vs `the direction` → false ✅ |
| 纯格式差异 | 归一化后相等即 true | 加句号 → true ✅ |

4/4 功能探针正确、AST 纯函数自检通过。这与上一家 Qoder 的数值型判据（断言类 0/4）形成实质对照——**第二个异厂家在干净 context 里独立看到了断言层**。但注意：这只是"判据存在且能检测"，未经过本仓冻结样本的机械回放（因交付链断），故不构成 `GAP_CLOSED` 的证据。

## 失败与 self-bites（如实）

1. **调用层 token 预算**：初版 T2-T4 合并任务（9KB 论文 + 3 文件）`finish=length`、tool_calls=0，6000 token 全耗在 reasoning。按 §110/§111 先例只改调用层（拆小、缩小素材、拉大 max_tokens），不改判据规则/阈值。
2. **幻觉时间戳**：异厂 tool call 里写的 `2026-11-23T08:45:00Z` 是编造的旧值；harness 按真实执行时间机械覆盖，并在文件内加 `_timestamp_note` 标注。工具层元数据修正，非决策干预。
3. **素材池污染后删除重来**：第三批构样本时，我曾把"Exact pairs"写进 prompt（本仓提供样本 = 出题权污染独立性）。当场识别，删除该批 `samples_blind.json`，改为只给论文原句素材、由异厂自己改写。这是本轮最危险的自我污染，已拦截。
4. **四次构样本失败**：改给干净素材后，模型仍在 reasoning 里纠结逐字复制与变换，`finish=length`、无 tool call，四次（3 批 + 1 极简）全部失败。按 prereg `no_retry_to_pass` 停止，不第五次重试，不替它补样本。
5. **引擎破坏性覆盖**：误将交付目录放 `/tmp/l3_v2_ext/`，跑 `engine.py` 时它判"交付未到"，把 `audit_l3_gap_targeted/result.json` 从权威态 `EXECUTED/GAP_INCONCLUSIVE` 覆盖成 `awaiting/verdict=null`，导致 26 个判定态守卫测试连锁失败。已用远端 Git Data API 原文恢复（`status=EXECUTED / verdict=GAP_INCONCLUSIVE / l3=false / abs=false`），全量回到 1608 passed。引擎的副作用记账，判定态未动。

## 诚实结论

- 第二家异厂在**判据归纳**这一维有真实、可复现的进展（看到断言层，对照上一家 0/4）。
- 但**出题 / 定 gt / 执行 / 裁决**四维未完成交付，验收获不到 9/9，无法触发预注册回放裁决树。
- 按 prereg `GAP_INCONCLUSIVE`（交付验收未全过 / 判据回放异常）**诚实封顶**。
- `l3_claimed=false / absolute_claimed=false`，最终裁定权在委托方（人）。§107–§115 九案、§L3 上一轮 FULLCHAIN_PARTIAL 均不翻案。
- 未伪造任何缺失交付文件；空 `samples_blind.json`（0 pairs）如实保留为失败证据。
