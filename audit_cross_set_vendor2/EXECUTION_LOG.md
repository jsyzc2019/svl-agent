# §113 执行日志：一次诚实的工具参数修正（修工具不放宽门禁）

## 背景
prereg（`7b9122d`，服务器时间 `2026-11-23T06:14:10Z`，早于任何 spawn）锁定协议：三条件各一次干净 context、AST v2 规则逐字节复用 §111/§112、Liquid AI designer、第二集冻结输入，调用参数 `max_tokens≥16000` + 429 退避 + reasoning 回退提取。

## 第一次尝试（attempt1，max_tokens=16000，留痕 `runs/attempt1_manifest_16000.json`）
- P0：`status=failed_error`，`finish=length`，content 1241 字符但 **SyntaxError: unterminated string literal**（代码块被截断）
- P1：`status=failed_no_judge_fn`，`finish=length`，reasoning 34264 字符但代码块无 `judge()` 定义
- P2：`status=ok`，`finish=length`，reasoning_fallback 提取合法 judge（3546 字符，留痕 `runs/attempt1_P2_judge_16000.py`）
- 结果：`PARTIAL_OR_FAILED`——**不伪造 judge**，engine 会按 prereg 对缺 judge 条件封顶。

## 判读：工具参数缺陷，非结果翻案
失败根因：reasoning 模型在 16000 token 预算下思考链未走完即被截断（`finish=length`），**根本没有产出可评估的 judge**——不存在"结果不满意而重跑到满意"的空间，这是生成未完成的技术问题。

按 §109/§111"修工具不放宽门禁"先例处理，且 **prereg 协议写的是 `max_tokens≥16000`（16000 是下限）**：
- 提高到 §111 已验证可完成的 **20000**，仍在 prereg 协议范围内；
- **规则/冻结输入/purpose/裁决树/指标口径一字不改**（`admission_v2.py` 哈希仍 `5e36f492...`，verify 双重断言）；
- **三条件统一用 20000 重跑**，保持 matched budget（不让不同条件用不同预算）；
- **保留 attempt1 全部留痕**（本文件 + `attempt1_manifest_16000.json` + `attempt1_P2_judge_16000.py`），不删除、不掩盖；
- 不采信异厂自报，仍 import judge 源码用第二集冻结 gt 盲评。

## 第二次尝试（attempt2，max_tokens=20000，留痕 `runs/vendor_call_manifest.json`）
- P0：`status=failed_error`，`finish=length`，reasoning 35831 字符，代码块在字符串中途截断 → SyntaxError
- P1：`status=ok`，`finish=stop`，content 1151 字符，合法 judge（sha 5c101a26...）
- P2：`status=failed_error`，`finish=length`，reasoning 35819 字符，代码块截断 → SyntaxError
- 两次尝试各有不同条件成功（attempt1 P2 ok / attempt2 P1 ok），但**无法让三条件同时产出完整 judge**。

## 最终决定：按 prereg 封顶 SET_VENDOR2_INCONCLUSIVE，不再重跑
- 失败根因是**异厂模型生成的不确定性**（Liquid AI 1.7B 在第二集 purpose 下 reasoning 链超长、常在代码块中途被 token 上限切断），不是确定性工程 bug。§109/§111 的"修工具"先例针对确定性 bug（锁文件名拼错），一次修到位；本例反复提高 token（16000→20000）属"调参到跑通"，是纪律禁止的 Goodhart 风险——**绝不进行第三次重跑**。
- 两次失败留痕全部保留（`attempt1_manifest_16000.json`、`attempt1_P2_judge_16000.py`、`vendor_call_manifest.json`），不删除、不掩盖、不手工补 judge。
- engine.py 修正一处二元状态 bug：原实现缺任一 judge 即写 PENDING，但 P1 judge 已存在导致状态矛盾；修为"三份全缺=PENDING（待命）/ 部分缺=EXECUTED + SET_VENDOR2_INCONCLUSIVE（按 prereg 失败分支封顶）"。此修正只让裁决更严格，不翻案。
- **这是诚实的负面结果**：跨集×跨厂商 2×2 的"第二集×Liquid AI"格因异厂生成不稳定未能填充；说明 §112 的跨厂商效应可能在主集上成立、在独立第二集上不稳定——样本特异性的又一例（延续 §108/§111 P0 地板跨集消失）。仍 l3=false/absolute=false。
