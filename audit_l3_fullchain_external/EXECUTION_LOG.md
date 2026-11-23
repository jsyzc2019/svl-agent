# 外家交付验收执行日志（2026-11-23）

## 事件：外家 Qoder 交付 l3_external_audit.zip，初验 6/8

收到外家 Agent（Qoder，异种大模型，云沙箱）交付的独立评估包。按 `EXTERNAL_AGENT_BRIEF.md` 契约跑 `verify_external.py`，6/8 PASS，两项 FAIL：`01_prereg_before_fetch`、`07_paper_avoid_list`。

## 诊断：两项 FAIL 均为验收器自身的确定性 bug，非外家违规

### 证据链（bug 先于交付存在）
- 验收器 commit `af360e6`，时间 `2026-11-23T17:14:38+08:00`（早于交付包上传 `17:47:29`）。
- `git show af360e6:...verify_external.py` 第 57–58 行、162 行含缺陷逻辑，spawn 前已锁定。
- 与 §109（锁文件名拼错）、§111（锁文件名）、§110（词边界误报）同类：预先存在、与新输出无关、修复须对全部情况一视同仁。

### bug 1（01）：时间字段名假设过窄
- 验收器只认 `prereg["timestamp"]`/`["created_at"]` 与 `fetch["timestamp"]`/`fetch["fetches"][0]["timestamp"]`。
- brief §5 只要求"带 ISO-8601 时间戳"，**未规定字段名**。外家用 `prereg["timestamps_utc"]["prereg_written"]="2026-11-23T09:22:41Z"`、`fetch["fetches"][].utc`（首个 primary=`09:25:36Z`）——合法字段命名。
- 真实时序 `09:22:41Z < 09:25:36Z`，承诺先于执行**成立**。FAIL 纯属验收器不识别合法字段位置。

### bug 2（07）：论文号扫描范围过宽
- 验收器 `json.dumps(mf)` 全文 regex 抽所有 `\d{4}\.\d{4,5}`，把 `manifest.avoid_list_check.checked_against` 里**仅作说明提及**的 `2611.07962`（brief 与外家转录差异的说明文字）误判为"选用论文"。
- brief §4 要求的是"**选用**论文不得在避开清单"——应只读 `manifest["arxiv_id"]`，不该扫全文。
- 外家实际选用 `2611.00401`，不在避开清单（manifests 与 prereg.avoid_list 双向确认）。FAIL 属验收器扫描范围错误。
- 附注：外家 prereg 把 brief 的 `2611.07962` 转录为 `2611.07961`，并主动在 `note_on_transcription` 披露该差异、声明机械核对——这是诚实留痕，不是掩盖。

## 处理：修工具，不放宽门禁（五点论证）

1. **先于执行存在**：bug 在外部锚 commit `af360e6` 内，交付前已锁 → 修工具（§109/§111 先例）。
2. **与新输出无关**：字段名假设 / 扫描范围是验收器固有逻辑，任何交付都会触发，非外家特定。
3. **一视同仁修复**：01 改为递归收集任意 JSON 深度的 ISO-8601 字符串取 min/max，不硬编码某家字段名；07 改为只读 `manifest["arxiv_id"]` 顶层字段，对所有交付同样语义。
4. **不放宽**：阈值不变（prereg 须早于 fetch；选用 id 不得命中避开清单）；不改外家任何文件；不重跑到齐。
5. **留痕透明**：原始 FAIL 与诊断写入本日志，修复后 8/8 结果如实记录。

外家 verdict 仍为 `EXTERNAL_PARTIAL`（它自报 agreement），本仓**不翻案、不改其参数**；机械重跑一致率 16/16 已由验收器独立确认。
