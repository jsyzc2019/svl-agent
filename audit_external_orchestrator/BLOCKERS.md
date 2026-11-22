# 外部 orchestrator / 异厂商 evaluator 通道可行性审计（§108 前置）

本轮目标（用户"按真正冲击去做"）：冲击 L3 的两个必要条件——① 第三独立确认集（跨集复现）；② 把独立性从"异路由同厂商 spawn"推到"本仓外 orchestrator + 异厂商 evaluator"。本文件记录 ② 的可行性审计结论：**在当前沙箱凭据下不可达**，如实记负面结果，不伪造、不自欺抬级（KB-META05/KB-STRUCT02）。

## 尝试 1：GitHub Actions 作为外部 runner orchestrator
- 写了最小 probe workflow（`.github/workflows/external_orchestrator_probe.yml`，保留为 `attempted_workflow_BLOCKED.yml`），意图：workflow_dispatch 触发 → GitHub 托管 runner 独立于本沙箱执行 → 写回带 runner 身份（hostname/RUNNER_NAME/GITHUB_RUN_ID，本沙箱无法伪造）的 attestation。
- 本地提交 `eb7bde1`，push 被拒：`refusing to allow a Personal Access Token to create or update workflow ... without 'workflow' scope`。
- 诊断：上传区三个 token 全部 `x-oauth-scopes: repo`；远端 `actions/workflows` total_count=0（无现成 workflow 可复用）；无 `workflow` scope。
- 判定：**硬权限障碍，不可达**。未反复纠缠（错误性质非抖动，是权限拒绝）。

## 尝试 2：异厂商 LLM 作为外部 evaluator / 设计者
- 扫描环境变量 OPENAI/ANTHROPIC/GOOGLE/GEMINI/DEEPSEEK/GROQ/TOGETHER/OPENROUTER 等 API key：全部为空。
- 无 ~/.openai、~/.anthropic 配置；gh CLI 未登录其它账号。
- 判定：**无凭据，不可达**。

## 可达的最大增量（本轮实际执行）
把"外部性"从"执行者独立"降级为可达的"信任锚独立 + 跨集复现"：
1. 第三独立确认集（全新论文，独立于 2611.14326/2611.22027）验证分层效应跨集复现。
2. 预注册 + 确定性裁决器的 sha256 在 spawn 前 commit 到 GitHub 远端——用 GitHub 服务器时间戳锚定"承诺先于执行"，本 Agent 无法事后回改而不留痕（外部不可篡改时间锚，非外部执行者）。
3. 裁决器纯确定性、哈希锁定，本 Agent 只搬运输入/输出，不改写裁决逻辑。

## 诚实边界
以上增量**不等于**达成外部 orchestrator 或异厂商 evaluator：执行仍在本沙箱、裁决器仍同厂商环境。因此即使跨集复现成功，**仍 l3=false / absolute=false**。真正的 L3 仍需：带 workflow scope 的 token（GitHub Actions）或异厂商 API 凭据——本沙箱二者皆无。

---

## §109 更新（2026-11-22）：workflow scope 解锁，外部 orchestrator 已真实可达

**状态翻转**：本轮用户新 token（API `x-oauth-scopes=repo, workflow, write:packages`，login=jsyzc2019）具备 `workflow` scope，尝试 1 的硬障碍已解除。本节记录解锁后的真实执行，不覆盖上方历史失败审计（保留证据链）。

- workflow 文件 `.github/workflows/external_orchestrator_attest.yml` 推送成功（commit `a4d1da9`，上一轮同样操作因缺 scope 被拒）。
- `workflow_dispatch` 触发后 GitHub Azure runner 真实执行：run `45013089276`，conclusion=success，写回 `runs/attestation_45013089276.json`，含本沙箱不可伪造字段 `hostname=runnervm0hi8g` / `whoami=runner` / `runner_name=GitHub Actions 1000018421` / azure 内核 / nonce 逐字绑定。
- 进一步落地 §109 外部执行者独立性受控验证：`.github/workflows/external_recompute.yml` 在 GitHub runner 上重跑哈希锁定的 §107 裁决引擎（commit `e26d5ef`），run `45013693112` success，外部产出 `result.json` sha256=`cf6d0f2b...` 与本沙箱本地重算、仓库存档**三方逐字节一致**，verdict/core/P0_floor 独立复现。裁决 `EXECUTOR_INDEPENDENCE_CONFIRMED`（10 项检查全过）。

**诚实边界（未变）**：这只证明执行环境可外移、裁决可复现；judge 设计者/样本/解释三处独立性未动，且外部 runner 执行的是本 Agent 预置的确定性脚本而非异厂商 LLM 评判。**仍 l3=false / absolute=false**。真正 L3 仍需异厂商 evaluator API 凭据（尝试 2 仍不可达）。
