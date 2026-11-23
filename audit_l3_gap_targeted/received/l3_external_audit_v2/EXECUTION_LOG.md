# 执行日志（EXECUTION_LOG）

时间线：T0 承诺 2026-11-23T10:31:56Z（脚本生成）→ T1 取料 → T2 出题 → T3 判据 →
T4 定 gt → T5 执行 → T6 裁决 → T7 打包。

## T0 承诺（2026-11-23T10:31:56Z）

- 运行 make_template.py 生成空壳；随后仅填写 prereg.json 的 chosen_paper /
  sample_construction / criterion_induction / gt_definition 四个 FILL 字段，
  时间戳未改动（保持最早）。
- 承诺内容：避开清单已读并确认避开；三类断言改写（否定极性翻转 / 断言补语删尾 /
  连接/让步词增删）各至少一组的覆盖计划；三层判据归纳法；gt 独立定义法；
  裁决树四档与阈值 11/12。

## T1 取料（约 2026-11-23T10:36–10:37Z）

- 选用 arXiv 2005.14165（Language Models are Few-Shot Learners），
  不在避开清单内，与 oracle failures / FGSE 域不同。
- curl 一手直取两源，均 HTTP 200：abs 48,472 字节；full（arxiv.org/html）1,220,984 字节。
- 从 full HTML 剥离标签得到 sources/paper_flat.txt（约 251,671 字符），未改动原 HTML 字节。

## T2 出题（约 10:40Z）

- 从 paper_flat.txt 逐字摘取 10 个基准句作为 text_b（含引用括号的按原文保留）；
  text_a 为人工改写：5 组仅表面格式差异（标点/虚词/连字符/空格），3 组否定极性翻转
  （N06 删 no、N07 删 no、N08 增 cannot），2 组断言补语删尾（N09/N10 截句尾断言），2 组
  连接词删除（N11/N12 删 however）。每组只体现一种现象；id 用 N01..N12，
  samples_blind.json 中不标注类型、无任何标签字样。

## T3 判据（约 10:45Z）

- 写 criterion.py 纯函数：否定层 / 连接层 / 断言完整性层三重集合比对，
  连字符归为格式差异。无 IO、无随机、无时间、无硬编码 id。
- 初版连字符不拆分导致一处表面差异误报（closed-book vs closed book），
  在首轮执行暴露后按格式语义修正分词规则——这是判据实现修正，
  未改动 prereg 承诺的归纳方法与阈值。
- criterion_note.md 给出判据语义、三类现象各自的例子与逐字锚点、局限披露。

## T4 定 gt（约 10:50Z）

- gt_private.json 按文本客观事实标注：否定词多出/丢失即 False；句尾实义补语被截即 False；
  连接词增删即 False；仅表面格式差异即 True。标注时未参照判据代码输出。
  （构建脚本中 gt 表写在 criterion 调用之前，可核验顺序。）

## T5 执行（约 10:52Z）

- 由 criterion.judge 在 12 组上重跑生成 judgments.json；
  与自建 gt 一致率 12/12 = 1.000。各样本 reasons/anchors 为逐字差异。

## T6 裁决（约 10:53Z）

- 按 prereg 裁决树：一致率 12/12 ≥ 11/12 且纯函数准入通过 → EXTERNAL_CONFIRMED。
- 该档仅表示"自建判据在自建 gt 上内部一致"，不宣布 L3；
  l3_claimed=false、absolute_claimed=false。

## T7 打包

- pack.py 生成全部 .sha256 锁并打 zip；selfcheck.py 须 11/11 PASS 后发回。

## 禁区披露

未阅读 brief 禁止的任何文件（audit_*、knowledge_base_store.json、commentary.md、
任何 result.json）；仅使用了委托方提供的 zip 内资料（EXTERNAL_AGENT_BRIEF_V2.md、
external_kit/ 下四个文件）与公开网络取料。
