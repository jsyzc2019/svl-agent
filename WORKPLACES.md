# 工作场所清单（自主运维 · 取料渠道地图）

> 版本：v1.0　生成：2026-11-22 12:20 (GMT+8)
> 用途：把"外部供料"从人类依赖点转为**我可自主触达的日常工作场所**。每条都标注本仓实证状态；未验证的场所标注为"待验证"，不冒充已验证。
> 纪律：一手优先、逐字锚点、取料即锁（fetch_log + SHA256）、交叉验证、self-reported 折 1（KB-RSI07）。

## 1. 已验证场所（本仓有 fetch_log / SHA256 实证）

| 场所 | 入口示例 | 取料方式 | 本仓实证 | 主要用途 |
|---|---|---|---|---|
| **arXiv** | `arxiv.org/abs/<id>`、`/pdf/<id>`、官方 HTML | curl 取 abs+pdf，HTML 转 `get_text(' ')` 扁平化逐字锚点 | 强（多个 audit_* 目录，PDF 4MB 级、abs 42KB 级均 200） | 论文一手；精研主战场 |
| **GitHub / GitHub API** | `github.com/jsyzc2019/...`、`api.github.com/repos/.../git/blobs`、`codeload.github.com/.../tar.gz` | git clone / codeload tarball / API blob | 强（本仓自身推送 + 30+ 开源 Agent 仓取料） | 代码实证、复现、claim-vs-code 核对 |
| **微信公众号（含同步站）** | `mp.weixin.qq.com/s?...`、AINLP 同步站 `52nlp.cn/?p=...`、`techmoon.xyz/?p=...` | 网页版取全文（公众号 App 付费检索通道本机未开通，用同源同步站交叉确认） | 中（addy / system1_system2 目录 fetch_log 200，中文全文 87KB+） | 中文一手评述、观点文（AGI 线） |
| **ACL Anthology** | `aclanthology.org/2025.acl-long.<n>/` | curl HTML/PDF | 中（multimodal_memory / swarm 目录引用） | NLP/记忆/多智能体论文 |
| **机构博客与技术报告** | `langchain.com/blog/...`、`academy.claude.com`、`claude.com/blog/...`、`chatgpt.com` | curl 全文 | 中（langchain_ctx / claude_verify / always_on 目录） | Agent 工程实践一手声明 |
| **项目 README / 代码仓文档** | 各 GitHub 仓 `README.md`、`docs/` | clone 后读原文 | 强（flashprove / reveal / skillmaster 等） | 机制声明自洽性核对 |

## 2. 可用但需现场验证的场所（工具层可达，尚未全部取样）

| 场所 | 入口 | 取料方式 | 状态 | 用途 |
|---|---|---|---|---|
| Web 搜索 / 网页抓取 | 内置搜索 + WebFetch | 关键词检索 → 抓正文 | 可用（本次首日试运行验证） | 发现新料、定位一手 |
| OpenReview | `openreview.net/forum?id=...` | curl HTML | 待验证 | 审稿意见、RSI 前沿 |
| HuggingFace Papers | `huggingface.co/papers` | curl / API | 待验证 | 论文热度与 trending（仅作发现，热度是虚荣指标 KB-RSI07） |
| PubMed | `pubmed.ncbi.nlm.nih.gov/<id>/` | curl HTML | 弱（reavideo 目录引用 1 次） | 记忆/认知科学交叉 |
| 财经数据源 | `cls.cn`、`eastmoney`、`cnfin.com`、`akshare`、`mcp-eastmoney` | HTTP / MCP | 中（finance 线实证） | 金融领域话题（P2） |
| 本地知识库 / 资料库 | `knowledge_base_store.json`、`library` 连接 | 读 / 语义检索 | 强（125 条，本仓自管） | 复用已有洞见，避免重造轮子 |

## 3. 取料纪律（不可放水）

1. **一手优先**：能拿论文原文/官方页/代码就不拿二手转述；二手只能做交叉验证（KB-SIM02 主体错位、KB-STRUCT09 二手不完整）。
2. **取料即锁**：每个来源落 `fetch_log.json`（url/status/bytes/sha256/ok）+ manifest；失败来源如实记 `ok:false`，不删不补。
3. **逐字锚点**：FJ 取证入口的锚点必须来自原文探测（disclose 命中、红旗零误命中），不可编造或放宽。
4. **交叉验证**：重大声称至少两个独立来源；评估器数量 ≠ 独立判断数（KB-STRUCT07）。
5. **诚实折算**：self-reported 数字按 KB-RSI07 折 1；只判机制声明自洽，不承诺真实有效。
6. **网络兜底**：GitHub DNS 偶发不可达，用 `curl --resolve` 探测可达 IP → 临时写 `/etc/hosts` → 用完立即恢复（见凭据与网络说明）。

## 4. 凭据自管（"Github 和本地就是常住地"）

- token 由用户临时提供，存放于用户上传区，**不复制进 `/workspace`、不写入 git 配置、不打印**。
- 推送封装：读上传区 token → 临时 askpass（用后即删）→ 必要时临时修 hosts → 推送 → 恢复 hosts → 核验远端=本地。
- 每次推送后确认：`git status -sb` 无 ahead、git 配置无明文凭据、临时脚本与 hosts 备份均已删除。
