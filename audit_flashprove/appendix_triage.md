# 附录链接取舍（按"必须必要"原则）

文章附录列 48 个链接。逐条按"是否为核验本文核心断言所必需"分级：

## 必下（一手，直接核验核心断言）——已下载锁存
| 链接 | 用途 | 状态 |
|---|---|---|
| anthropic.com/research/provable-inference | 官方研究页，核心主张/数字/局限一手源 | ✅ 200 248KB |
| anthropic.com/document/flashprove-technical-report | 技术报告，soundness/协议细节 | ✅ PDF 3.18MB |
| github.com/anthropics/FlashProve (README) | commit/prove/verify 机制 + 研究原型/not maintained 声明 | ✅ 9.7KB |
| github.com/.../THIRD_PARTY.md | 第三方来源/许可清单，核 claim 出处与来源纯度 | ✅ 115KB |
| github.com/.../paper/paper.pdf | 协议规范/形式化依赖的底层论文 | ✅ 1.45MB |
| github.com/.../lean/STATEMENTS.html | 交互式审计可视化工具 | ⚠️ raw 超时，仅辅助工具非必需，不补 |

## 必不下（背景/二手/对比，不构成核心断言核验）
- **监管/发展节奏背景**（arxiv 2004.07213 / thefuturesociety / darioamodei pace / arxiv 2402.08797 / 2506.15867 / RAND / wiz CVE / arxiv 2511.02620 / roadmap）：这些是文章用来论证"为何需要 PI"的背景引用，非 FlashProve 机制本身的验证对象。按 KB-STRUCT05 主体错位，不拿背景来源证明 FlashProve 有效。
- **zkML 竞品对比**（SafetyNets/zkCNN/Kang/ZKML/Modulus/EZKL/zkLLM/zkGPT/zkPyTorch/ZKTorch/VerInf/DeepProve/SASH/Attestable）：文章"已有工作"段的性能对比数字，是 FlashProve 自报的对比（self-reported，KB-RSI07）；复算每个竞品吞吐超出本轮必要范围。仅记录为 S2 背景，不入证据。
- **模型/工具**（Llama 4 Maverick HF / vLLM / Starknet / Mantle / L2beat）：外部依赖与类比对象，非证明对象。
- **其他 Anthropic 页**（Frontier Red Team 团队页 / roadmap）：机构背景，非机制断言。

取舍理由：本轮判据聚焦"可证明推理的证明范围与信任根"，只需核验 Anthropic 自己对 FlashProve 说了什么（官方页+技术报告）、代码/协议是否自洽（GitHub+THIRD_PARTY+paper）。背景与竞品不构成对"证明范围声明是否诚实自洽"的独立拦截面，按必须必要原则不下。
