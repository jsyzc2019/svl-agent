# §4gm 判定态源职责分离固化日志

> 承 §4gl `ENGINE_LOG_4gl.md` 的"待改进点"：那次只靠人工规避了 engine 回写权威源的缺陷，本轮把它固化为代码不变量守卫。
> **两层裁决继续分清**：§L3-R2 子实验裁决 = `GAP_CLOSED`（独立文件 `result_4gl.json` / `result_experiment.json`）；内核判定态 `verdict=GAP_INCONCLUSIVE`（权威源 `result.json` + handoff，从未动）。

## 改动清单（改工具不改判据）

| 位置 | 改动 | 性质 |
|---|---|---|
| `engine.py` 常量 | 新增 `KERNEL_VERDICT_SOURCE`（只读权威源）、`EXPERIMENT_RESULT`（独立输出） | 职责分层 |
| `engine.py:awaiting 分支` | 待命态写 `result_experiment.json`，不再写 `result.json` | IO 目标 |
| `engine.py:main` | 开头 `before = kernel_state_snapshot()`；收尾 `assert after == before` | 不变量守卫 |
| `engine.py:EXECUTED 分支` | 裁决写 `result_experiment.json`，不再写 `result.json` | IO 目标 |
| 新增 `result_experiment.json` | 真实裁决 `GAP_CLOSED`，sha256 `4c297b29…` | 留档，与 `result_4gl.json` 一致 |
| 新增 `tests/test_verdict_source_separation.py` | 4 项守卫测试 | 回归固化 |

**一字未改**：裁决树五档阈值（`clean6/6 ∧ 断言≥3/4 ∧ canary≥3/6 → GAP_CLOSED`）、`l3_claimed=false`、`absolute_claimed=false`、`hard_bound`、`does_not_overturn`、prereg。

## 正向验证（真实现场）

- 修复后重跑：`verdict=GAP_CLOSED`、internal_replay 16/16、repo 13/18、断言 4/4、数值 0/2、clean 6/6、canary 3/6、`l3=False absolute=False`。
- 权威源 `result.json` sha256 **运行前后均 `0f3ccb1349bd75db47346dc720687c4c7f6e02244e62384de07746ea0bcf7da0`**——字节不变。
- 独立文件 `result_experiment.json` 裁决 `GAP_CLOSED` 与 `result_4gl.json` 一致，sha256 `4c297b2980b0fde660cf19b27e3eb90f8723408bb852822961eaf364a156832f`。

## 负向验证（守卫自咬，证明非摆设）

- 构造变体：仅把 engine 两处 `open(EXPERIMENT_RESULT,"w")` 改回 `open(KERNEL_VERDICT_SOURCE,"w")`，保留守卫。
- 运行 → `AssertionError: 内核判定态源被子实验裁决污染：('GAP_INCONCLUSIVE', False, False) -> ('GAP_CLOSED', False, False)`，退出码 **1**。
- 结论：任何未来 attempt 把实验输出回写权威源，都会被即时捕获，不静默放过。

## 边界与诚实上限

- 本轮证明的是"工具层职责分离机制可运行且可自咬"，**不是**新的 L3 证据、不是判据可迁移性的新检验。
- 内核 `verdict=GAP_INCONCLUSIVE` / `l3=false` / `absolute=false` / 宪法锁 `fe56291b` 全不动；§107–§115 九案与 §L3 FULLCHAIN_PARTIAL 不翻案；不编译门禁，裁定权在委托方（人）。
- 全量 1608→**1612 passed**；KB 483→484（KB-META178）；Safari 133 轮不变。
