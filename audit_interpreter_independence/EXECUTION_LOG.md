# §114 执行日志（解释者独立性）

## 时间线
- 2026-11-23T06:29:30Z：commit `7b1f1644` push 成功，GitHub 服务器 committer 时间作外部锚，证明预注册/冻结输入/调用器先于 spawn 锁定。
- spawn：异厂解释者 `baidu/ernie-5.5-flash-preview:free`（OpenRouter 免费端点，非 NVIDIA/Hunyuan），干净 context、key 仅环境变量、留痕不含 key/prompt 全文/私有 gt。
- 异厂输出：`{"case_1":"FULL","case_2":"PARTIAL","case_3":"PARTIAL","case_4":"PARTIAL"}`，finish=stop、JSON 解析、ALL_OK。

## 确定性工程 bug 发现与修复（§109/§111"修工具不放宽门禁"先例）
- **现象**：初版 engine 用字符串精确匹配 `interpreter_tier == expected_neutral_tier`，case_1 的异厂标签 `FULL` 与私有 gt 档位 `CONFIRMED` 不相等 → 被误判为不匹配（假 agreement=3/4）。
- **根因（预先存在，与异厂输出无关）**：中性规则给异厂的档位词表是 `FULL/PARTIAL/REFUTED/INCONCLUSIVE`（见 spawn 前已锁 `cases_blind.json` 哈希 `172f8089…`），而私有 gt 从四轮历史 verdict 后缀提取时写成 `CONFIRMED/PARTIAL/...`（见 spawn 前已锁 `gt_private.json` 哈希 `407485c8…`）。`FULL` 与 `CONFIRMED` 语义同指"确认档"，仅命名不同——这是本轮生成冻结输入时的字段命名不一致，非异厂判错。证据：两文件哈希均在外部锚 commit `7b1f1644` 内，早于 spawn。
- **为何是修工具而非调参/翻案**：① 不改异厂输出的任何 tier 标签（原样保留 `FULL`）；② 不改私有 gt 的任何中性档；③ 不改裁决树任一阈值与档位定义；④ 档位规范化映射（FULL↔CONFIRMED 同档，其余逐字）对全部档位一视同仁，不是针对 case_1 的特判；⑤ 与 §109 修锁文件名、§111 修锁文件名同类——修复确定性字段 bug 让引擎正确反映已验证事实。
- **修复**：engine 比对前把异厂 tier 与 gt 档都经同一个 `canon()` 归一化（FULL→CONFIRMED，其余不变），再逐 case 比对。异厂原始标签、gt 原始档位、归一化结果三者全部写入 result 留痕，可回放核验。
- **不放宽项**：verify 的盲性/来源一致/不翻案/l3=false 断言全部保留；失败态封顶规则不变；case_2（SECONDARY=1.0 关键区分点）仍单独校验。

## 关键纪律
- 异厂自报不采信：只采信其产出的 tier 标签，与冻结 gt 机械比对。
- 不反复 spawn：一次异厂调用成功即止，不因结果反复重跑（反 Goodhart）。
- 不翻案：§107-§113 七案裁决保留并列。
- key 零入仓、askpass/临时 key 即用即删；系统安全红线全程遵守。
