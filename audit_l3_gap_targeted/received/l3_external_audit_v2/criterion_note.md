# 判据说明（criterion_note）

## 判据语义来源

判据目标语义是**"text_a 是否完整保留了 text_b 的断言"**。设计动机：判据必须看到断言层（否定词、句尾补语、让步连接词），而不能只靠数字/固定词表。实现为确定性纯函数，对 `(text_a, text_b)` 做三层核对：

1. **否定层**：比对双方核心否定词 `{not, no, never, nor, cannot, without, neither}` 的多重集合；
2. **连接层**：比对双方连接/让步词 `{however, though, although, whereas, but, yet, nevertheless, nonetheless, while, still}` 的多重集合；
3. **断言完整性层**：剔除虚词后比对**内容词多重集合**——text_a 缺失任何实义补语词（删尾）或新增任何实义词即断裂。

三层全部通过、token 序列差异仅来自空格/标点/连字符/虚词时判 True（表面格式差异不改变断言）。三层任一断裂判 False，reasons 给出层次与差异描述，anchors 给出逐字差异词。若 gt 与 judge 100% 一致，是因为 gt 与判据都忠实于同一文本客观事实（否定词/连接词/补语的有无），并非 gt 从判据反推——gt 在判据代码编写前已按文本事实独立标注，构建脚本中 gt 表位于判据调用之前。

## 否定极性翻转（negation / polarity）

例子（样本 N06）：
- text_b: `... as conditioning [ 117 ] , but no weight updates are allowed.`
- text_a: `... as conditioning [ 117 ] , but weight updates are allowed.`
- text_a 丢失否定词 `no`，导致"不允许权重更新"翻转为"允许权重更新"，断言极性改变。
- 判据命中：否定层多重集合差异 `text_a 缺失: 'no'`，anchor 为 `no`，判 False。

同族例子 N07（`except that no demonstrations are allowed` → `except that demonstrations are allowed`）、N08（`humans can generally perform` → `humans cannot generally perform`，text_a 新增否定词 `cannot`）。

## 断言补语删尾（complement / tail / truncation / assertion）

例子（样本 N09）：
- text_b: `GPT-3 2.7B outperforms the SOTA 17B parameter Turing-NLG [ 132 ] in this setting, and GPT-3 175B advances the state of the art by 18%.`
- text_a: `GPT-3 2.7B outperforms the SOTA 17B parameter Turing-NLG [ 132 ] in this setting.`
- text_a 把句子后半的断言补语 `and GPT-3 175B advances the state of the art by 18%` 整体截掉。
- 判据命中：断言完整性层内容词缺失 `advances, art, gpt-3, 175b, state, 18, by, of, the...`（实义词 `advances/175b/18%/art/state` 等缺失），判 False。

同族例子 N10（`GPT-3 achieves 86.4% accuracy in the few-shot setting` 截掉了 `, an increase of over 18% from the previous state-of-the-art`）。

## 连接/让步词增删（connector / concession / however）

例子（样本 N11）：
- text_b: `Ultimately, however, one-shot, or even sometimes zero-shot, seem like the fairest comparisons to human performance...`
- text_a: `Ultimately, one-shot, or even sometimes zero-shot, seem like the fairest comparisons...`
- text_a 删除让步连接词 `however`，原句"与前文形成转折"的断言关系被抹掉。
- 判据命中：连接层多重集合差异 `text_a 缺失: 'however'`，anchor 为 `however`，判 False。

同族例子 N12（句首 `However, we have found that unfiltered...` 被改为 `We have found that unfiltered...`）。

## 判据局限（如实披露）

- 判据基于词级多重集合，不解析句法：若改写是**同义换词**（paraphrase）而不增删否定/连接/内容词，会误判 True；若改写是**语序重排**，因内容词多重集合一致也会判 True（断言确实未变，故对本任务语义正确，但对"换词改写"存在假阴性）。
- 否定前缀词（如 `unfiltered`）不计入否定层，只有独立否定词计入；前缀造成的极性变化需依赖内容词差异捕获（`unfiltered` vs `filtered` 内容词不同，仍会判 False）。
