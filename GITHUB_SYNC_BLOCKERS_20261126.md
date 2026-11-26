# GitHub 同步阻断留档（2026-11-26）

> 用户令："记得及时更新Github仓库。" 本节按纪律第 8 条（负面断言工具覆盖律）——凡称"无/不可用"先声明用什么工具查、工具是否覆盖目标类。

## 一、现场核验（每项列工具）

| 断言 | 工具 | 结果 | 覆盖判定 |
|---|---|---|---|
| 工作区无 `.git` 历史 | `ls -la /workspace` + `find /workspace -maxdepth 2 -name .git` | 无输出 | 覆盖：tarball 快照态，与 §0 记载一致；**不得称 git commit 可回滚** |
| gh 未登录 | `gh auth status` | "You are not logged into any GitHub hosts" | 覆盖 |
| 无 GH_TOKEN / GITHUB_TOKEN | `env` 扫描 | 未设置 | 覆盖 |
| 环境变量无 GitHub PAT | 全量 env 扫 `ghp_/github_pat_` 前缀 | 无 | 覆盖 |
| credential helper 无凭据 | `git credential fill`（host=github.com） | rc=128 "could not read Username" | 覆盖：helper 返回空 |
| 上传区无 token 分片 | `ls -la /root/uploads/` | 仅 `.init`（5B） | 覆盖 |
| 无 GitHub MCP 工具 | 工具检索（"github push commit"） | 无匹配 | 覆盖 |
| 远端 API 匿名可读但写受限 | `curl api.github.com/.../commits/main` 匿名 | 200 读到 HEAD `e761b208`；`/user` 无 token 返回 403 | 覆盖：读通、写不通 |

**结论**：本沙箱无 GitHub 写凭据、无 git 历史。按 §0 与 §3 纪律，**不伪造推送成功**、**不谎称 commit 可回滚**。远端 HEAD 现场读到 `e761b208baac`（2026-11-25T02:49:12Z，"Docs(自举修正)…"），与 handoff 记忆中的 `c446e01` 不一致——再次印证"记忆≠现场"，以现场为准。

## 二、本轮待推送成果清单（燃料到位即可推）

新增/修改（均在 `/workspace`）：
- `LIFE_KERNEL.md`：新增 §4ge（独立性前提被违背）+ §4gf 预告
- `knowledge_base_store.json`：KB 466→468（KB-AUDIT205 / KB-META171）
- `life_kernel/data/safari_log.jsonl`：132→133 轮（§4ge）
- `prereg_aggregation_20261126.json`（sha256 `3b4585f4…`）
- `audit_aggregation_dependence/`：`engine.py` / `result.json` / `arxiv_abstracts.json` / `arxiv_abstracts.sha256`
- `tests/test_evidence_chain.py`：审计目录计数断言 61→62（新增目录，实测更新不放宽，附注释）
- 本文件 `GITHUB_SYNC_BLOCKERS_20261126.md`

## 三、一键推送脚本（token 运行时注入，不落盘不打印）

见 `tools/push_with_token.sh`：用法 `GITHUB_TOKEN=<PAT> bash tools/push_with_token.sh "<commit message>"`。
脚本：临时 `git init` → 设 remote → 用 `http.extraHeader` 传 basic auth（token 仅内存）→ add/commit/push → 清理临时凭据。
需用户在上传区放 token 或直接经安全通道注入；token 不入仓、不打印、不入历史。

## 四、解决记录（2026-11-26 11:xx GMT+8，同日稍后）

用户重新提供了 GitHub 全能 token（ghp_，40 位，chmod 600 存上传区、不打印不入仓）。带 token 的 `git ls-remote` / GitHub API `/user`（login=jsyzc2019）均 200 可用。但 `git clone --depth 1` 仍在 443 大包下载超时（135s，与 §0 记载一致），故**不走 clone / force push**。

采用 **GitHub Git Data API** 方案：以远端 HEAD `e761b208` 的 tree `4fab0e9085b0` 为 base_tree，把本地相对远端新增/修改的文件做成 blob 挂上去，parent 指向 `e761b208`，生成单个 commit 后更新 main ref。此方案**历史连续、远端已有的 45 个文件（本地 tarball 快照缺失）全部保留、只增不删**——这是相对 force push 的关键安全优势。

**推送结果（已成功，现场核验非记忆）**：commit `89dec3be9273`（父 `e761b208`，历史连续）；远端 main HEAD=`89dec3be9273`；提交 133 个新增/修改文件；tree `651ac30885c0`（truncated=false）。推送后核验：8/8 关键文件本地 sha256 == 远端 blob sha256（LIFE_KERNEL / KB / result / engine / handoff / test / safari_log / prereg）；父提交仍 `e761b208`；远端 blob 数 1596→**1723**（只增不删，本地缺失的 45 个远端文件全部保留）。token 仅内存使用、不打印、不入仓、不入任何提交；上传区 token 文件 chmod 600。

## 五、诚实边界

- 判定权归用户；verdict/l3/absolute/宪法/十案/§100 全不动。
- 内核 L0 不联网不 spawn；推送是外层运维动作，非内核摄食。
- 推送未完成不宣称"已更新仓库"；待燃料到位执行后，以现场 `curl` 复核远端 HEAD 为准。
