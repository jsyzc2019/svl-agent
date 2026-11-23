# §115 执行日志（解释者跨厂商交叉确认）

## 时间线
- 2026-11-23T06:45:04Z：commit `d6a6aa4` push 成功，GitHub 服务器 committer 时间作外部锚，证明预注册/冻结输入/调用器/engine 先于 spawn 锁定。
- 空间探测：用 §114 原 prompt 探测全部非 baidu 免费模型——gemma 429 排除；dots-studio / inclusionai / liquid / particle-ai / recursive 均 finish=stop + JSON 解析正确分类。选三家真正不同厂商 dots-studio / inclusionai / liquid（与 baidu 不同厂、彼此不同厂）。
- spawn（run_all.py 逐字节调用 §114 的 call_interpreter.py，唯一变量=厂商）：
  - dots-studio/dots-3-note-preview:free → ok，tiers 4/4，finish=stop
  - inclusionai/ling-3.2-flash:free → **HTTP 429 失败**（probe 时可用，正式跑时限流），无 tiers
  - liquid/lfm-3-1.7b:free → ok，tiers 4/4，finish=stop

## 确定性工程 bug 发现与修复（§109/§111/§113 先例）
- **现象**：初版 engine 的 `present` 只按 manifest 文件是否存在判定（`git show d6a6aa4:.../engine.py` 第 44 行，spawn 前已锁），于是把 429 失败的 ling 也计入 present，三家"齐了"且 2 家 4/4 → 会误落 `INTERPRETER_CROSS_PARTIAL`（语义="1 家判错"）。但 ling 是 **API 失败没判**，不是"判了判错"——把它当分歧是伪造语义。
- **依据**：prereg 裁决树原文明确列 `INTERPRETER_CROSS_INCONCLUSIVE：任一厂商 API/解析失败且不达判定门槛 → 诚实封顶，不放宽、不伪造`。失败厂商本应走此分支。
- **根因（预先存在，与结果无关）**：`present` 定义只看文件存在，不校验 status==ok。这是 §113"二元状态 bug"同类——状态机没区分"文件在/成功产出/失败"。证据在外部锚 commit `d6a6aa4` 内，早于 spawn。
- **修复**：`present` 改为只计 status==ok 且产出 tiers 的厂商；失败厂商不计入、不伪造其 tiers；`len(present) < 3` → INTERPRETER_CROSS_INCONCLUSIVE。不改裁决树阈值、不改 prereg、不改任何厂商输出、不放宽 verify 断言。
- **为何不是调参/翻案**：① 不重跑 ling（429 重跑=调到跑通，§113 明禁，probe 可用不能作为正式结果）；② 不改 prereg 规则；③ 修的是 spawn 前已锁的状态机 bug；④ 修复让裁决更严格（INCONCLUSIVE < PARTIAL），只收紧不放松。

## 关键纪律
- 成功两家（dots/liquid）的 4/4 如实记录为部分证据，但因第三家失败，整体按 prereg 失败分支封顶 INTERPRETER_CROSS_INCONCLUSIVE，不宣布"三家交叉确认"。
- §114 单厂商 INTERPRETER_CONFIRMED 与 §107-§113 全部保留并列，不翻案。
- key 零入仓、askpass/临时 key/hosts 即用即删；系统安全红线全程遵守。
