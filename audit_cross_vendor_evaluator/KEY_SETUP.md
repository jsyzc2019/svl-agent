# §110 异厂商 evaluator —— Key 接入说明（待命）

## 当前状态

管线已全部编译并 dry-run 验证通过（用 §107 既有 judge 作 stub 逐字复现 PRIMARY=1.00/SECONDARY=0.00/P1.core=1.00）。**唯一缺的就是异厂 API key**。`result.json` 现为 `PENDING_API_KEY` 占位，不构成任何裁决。

## 支持任何 OpenAI 兼容端点

`call_vendor.py` 用标准 `/chat/completions` 协议，覆盖主流异厂（**只要不是 Hunyuan 即可算异厂**，厂商独立性这一维才成立）：

| 厂商 | CROSS_VENDOR_BASE | CROSS_VENDOR_MODEL 示例 |
|---|---|---|
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| Moonshot（Kimi） | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| OpenRouter（聚合，一个 key 多模型） | `https://openrouter.ai/api/v1` | `anthropic/claude-3.5-sonnet` |
| 智谱 | `https://open.bigmodel.cn/api/paas/v4` | `glm-4` |

推荐 **DeepSeek / Kimi / 通义** 任一（国内可达、便宜、与 Hunyuan 明确异厂）。若想更彻底的异谱系，用 OpenRouter 的 Claude/GPT。

## 如何提供 key（安全承诺）

1. 把 key 写入上传区一个文件：`/root/uploads/cross_vendor_api_key.txt`（只写 key 本身，chmod 600）。
2. 告诉我厂商 BASE、MODEL、NAME 三个参数（或让我按上表默认选）。
3. 我执行时从该文件读入环境变量，**key 绝不入仓、绝不写 prompt 留痕、绝不进 result**。调用留痕只存 prompt 哈希、模型名、usage、状态码。

## key 到位后的执行序列（已编译，无需再设计）

```
1. 复核 prereg.sha256 / manifest / scorer_key / 样本哈希锁      # spawn 前锁死
2. CROSS_VENDOR_API_KEY=... python3 call_vendor.py              # 三条件各一次干净 context 调用
3. python3 engine.py                                            # 冻结 gt 盲评 + 预注册裁决
4. python3 verify.py                                            # 回放断言（哈希锁/准入/裁决树一致）
5. pytest 全套 + 文档/KB/报告 + 提交推送
```

## 诚实边界（事前锁定，不因结果翻案）

- 只证明 **设计者厂商独立性这一维**；样本集/gt/解释仍本 Agent，仍 `l3=false / absolute=false`。
- 若异厂拒绝纯代码块输出、或源码含随机/时间/id 硬编码/标签词泄漏 → 准入失败 → 该条件封顶 `CROSS_VENDOR_INCONCLUSIVE`，不放宽。
- 若异厂不复现分层效应 → 落 `CROSS_VENDOR_REFUTED`，如实记为"§107 效应可能是同厂设计习惯产物"的真负面结果，绝不 post-hoc 翻案。
