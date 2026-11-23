# 外家执行包（傻瓜版）——先读这一页

> 这是《EXTERNAL_AGENT_BRIEF_V2.md》的可执行简化封装。**硬规则一字未改**：五权力全在你手里，本仓只做机械验收。
> 你**不需要**读本仓任何其它文件，也**不应该**读（`audit_*`、`knowledge_base_store.json`、`commentary.md`、任何 `result.json`）。
> 权威裁决口径见 `../EXTERNAL_AGENT_BRIEF_V2.md`；本页只管"怎么动手"。

---

## 你要做的事：4 步，条条可复制（1 生成 → 2 填空 → 3 打包 → 4 自检）

### 第 1 步：生成空壳
```bash
python3 make_template.py
```
得到一个 `l3_external_audit_v2/` 目录，11 个文件全在里面，需要你填的地方都标了 `<<<FILL>>>`。

### 第 2 步：填空（这是唯一需要动脑的地方）
打开目录，把所有 `<<<FILL>>>` 换成你自己的内容。逐文件说明：

| 文件 | 你填什么 |
|---|---|
| `prereg.json` | `chosen_paper`、`sample_construction`、`criterion_induction`、`gt_definition`。**时间戳自动生成，别改**（必须最早） |
| `manifest.json` | 论文编号 + 标题 + abs/full 两个 URL（避开清单见 `../EXTERNAL_AGENT_BRIEF_V2.md` §4） |
| `sources/fetch_log.json` | 两个源的实际取料 ISO 时间（必须晚于 prereg 时间）、字节数 |
| `sources/paper_flat.txt` | 论文全文纯文本 |
| `samples_blind.json` | 12 组 `text_a`/`text_b`，三类断言改写各至少一组；**只能有 id/text_a/text_b 三个键** |
| `criterion.py` | 你的判据函数 `judge()`，**纯函数**（别 import 随机/时间/os，别读文件，别硬编码 N01） |
| `criterion_note.md` | 判据语义 + 三段各举一个你自己的例子（否定翻转 / 补语删尾 / 连接词增删） |
| `gt_private.json` | 每个 id 一个 true/false，**来自文本客观事实，不从判据反推** |
| `judgments.json` | 每个 id 的 verdict/reasons/anchors，**必须和 criterion.py 重跑一致** |
| `verdict.json` | 四档选一 + why + agreement；`l3_claimed`、`absolute_claimed` 保持 false |
| `EXECUTION_LOG.md` | 如实记录过程；误读禁区文件要披露 |

### 第 3 步：打包（自动生成哈希锁）
```bash
python3 pack.py
```
这一步给全部交付文件自动生成 `.sha256` 锁，并打出 `l3_external_audit_v2.zip`。
可反复运行（每次覆盖旧锁和旧包）。

### 第 4 步：自检
```bash
python3 selfcheck.py
```
看到 **11/11 PASS** 就把那个 zip 发回。任一 FAIL 按提示改，改完**重新跑第 3、4 步**；
**失败如实封顶，不重跑到齐**。**不要附任何密钥。**

---

## 三条红线（违反即证据无效）

1. **先承诺后动手**：prereg 时间戳最早（脚本已自动处理，别手动改早/改晚）。
2. **裸样本零标签**：`samples_blind.json` 里不许出现 `gt`/`variant`/`clean`/`tampered`/`truth`/`label`/`tag`/`target` 这类字样，也不标注样本属于哪一类。
3. **判据纯函数**：无 IO、无随机、无时间、无硬编码 id。

---

## 本轮唯一新增要求（v2 相对 v1）

造样本时，三类断言改写**各至少一组**：
- 否定极性翻转：`never restores` ↔ `restores`
- 断言补语删尾：`... yields no false positive` ↔ `... yields`
- 连接/让步词增删：`The direction, however, is ...` ↔ `The direction, is ...`

怎么造句、用什么论文、判据怎么归纳，全由你决定。本仓只是把覆盖下限写在纸上，**不给你样本、标签、判据词表或历史裁决**。

---

## 四档裁决（你自己按 T0 写的树填，别等本仓）

`EXTERNAL_CONFIRMED` / `EXTERNAL_DIVERGENT` / `EXTERNAL_PARTIAL` / `EXTERNAL_INCONCLUSIVE`

`EXTERNAL_CONFIRMED` 的语义只是"你自己的判据在你自建 gt 上内部一致"，**不是宣布 L3**。本仓会把你的判据回放到冻结样本做机械比对，那是本仓的事，不改你的规格。

---

## 一句话

**你不是来复述本仓结论的，是来独立检验"判据能否看到断言级改写"的。** 五权力全在你手里，4 条命令走完，交 zip 即可。
