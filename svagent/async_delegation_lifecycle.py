"""异步/后台委派生命周期门禁 — 把 11 来源异步子Agent谱系编译成会判动作（§69）。

一手/二手证据（见 audit_async_subagents/）：
  - S10 async-deep-agents 仓库 README（一手 code+doc）："decoupling task submission from
    result collection"；launch "return immediately with a tracking ID"；同步委派
    "cannot be interrupted"；mid-task "Send follow-up instructions via update"；
    job 存于 "non-message state channel" 否则 "would be lost during compaction"；
    fire-and-forget gap → completion notifier 用 "runs.create()" 唤醒 supervisor；
    通知是 "Bring-Your-Own"——不是框架内置承诺。
  - S06 LangChain Python async docs（一手，与 S10 同源）：background tasks "return
    immediately"，可 "send follow-up instructions" / "cancel it at any point"，
    Agent Server 上 "subagents also report back when they finish"。
  - S02 Claude Code subagents（一手，Anthropic 独立主体）：background subagents
    "run concurrently while you continue working"，各有 "separate context window"。
  - S04 DeepSeek Harness（一手，独立主体）：Super-agent 四特征 Continuous/Productive/
    Proactive/Persistent，两级 Router/Worker + event-driven —— 与本仓 always-on 讨论
    (§61-§66)同构，按 KB-STRUCT02 不视为独立验证。
  - S03 dots / S08 async-tool-calling（二手区域锁聚合，标 S3，OpenAI 独立主体）：
    "launch parallel background agents"；"Pausing does not cancel delegated work"；
    async: true + call_id + task_handle/wait_for_tasks。

为什么是新牙（对比现有门禁）：
  session_continuity(§65)判跨 run 会话状态续接；memory_curation(§68)判记忆内容质量；
  各 *gate 判检索污染/信号口径/证据阶梯——无一判『后台委派任务的生命周期完整性』：
  提交与收集解耦 / 可引导可取消 / 句柄穿越 compaction / 完成主动通知。拦截面独立，
  且 ≥2 独立主体(S10/S02/S04/S03+S08)给出同类硬锚点 → KB-META01 会拦才入通过。

编译纪律（与 gate_prereg.json 一致，实现前 SHA256 锁存 0b78ad89…）：
  - 语义枚举 + bool；字面串→flag(R0，避 §56 brittle 根因)；
  - 规则 R0-R6 按优先级短路返回，不事后加权(防 Goodhart)；
  - 只判『机制声明是否自洽』，不承诺委派真的高效/完成真的被通知——存在≠有效性(KB-META01)；
    self-reported 数字不作独立验证(KB-RSI07)；通知 Bring-Your-Own 不是内置承诺。

诚实边界：定位为审读外部异步系统的尺子，不判本仓；本仓同步纯函数库非运行时编排系统，
遵循 §58 选 A 不接 run_loop。
"""
from __future__ import annotations

from dataclasses import dataclass

# 语义枚举——写死；判定绝不读字符串内容（KB-AUDIT01 brittle 根因）
_ENUM = frozenset({"yes", "no", "partial"})


@dataclass(frozen=True)
class AsyncDelegationVerdict:
    claim: str
    decoupled: str
    steerable: str
    survives_compaction: str
    completion_notified: str
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_async_delegation_lifecycle(
    claim: str,
    *,
    decoupled: str,
    steerable: str,
    survives_compaction: str,
    completion_notified: str,
) -> AsyncDelegationVerdict:
    """判一个异步/后台委派声称是否有自洽的生命周期机制（不承诺真的高效可靠）。

    输入须为语义枚举：
      decoupled, steerable, survives_compaction, completion_notified ∈ {yes, no, partial}

    规则按优先级短路返回（与 gate_prereg.json R0-R6 一致）：
      R0 任一非枚举 → flag（拒绝字面串内容判定）
      R1 decoupled=no → downgrade（同步阻塞，无并发根基）
      R2 steerable=no → downgrade（无法中断/引导，需求变更即失控）
      R3 survives_compaction=no → downgrade（句柄随消息压缩丢失，忘记在跑的任务）
      R4 completion_notified=no → flag（fire-and-forget，轮询依赖）
      R5 任一 partial → flag（覆盖不全，待核）
      R6 全 yes → ok（只判机制声明存在，不承诺真的高效/可靠）
    """
    vals = (decoupled, steerable, survives_compaction, completion_notified)

    # R0：语义输入校验优先
    if any(v not in _ENUM for v in vals):
        bad = next((v for v in vals if v not in _ENUM), None)
        return AsyncDelegationVerdict(
            claim, str(decoupled), str(steerable), str(survives_compaction),
            str(completion_notified), "flag", "ASYNC_DELEGATION.INVALID_INPUT",
            "四维须为 yes/no/partial 语义枚举；收到非法值（含字面串）→ flag，不进内容判定",
        )

    # R1：提交/收集未解耦 → downgrade
    if decoupled == "no":
        return AsyncDelegationVerdict(
            claim, decoupled, steerable, survives_compaction, completion_notified,
            "downgrade", "ASYNC_DELEGATION.SYNC_BLOCK",
            "声称异步却同步阻塞提交(无tracking ID/提交即等结果)——无并发根基，判定打折",
        )

    # R2：不可引导/取消 → downgrade
    if steerable == "no":
        return AsyncDelegationVerdict(
            claim, decoupled, steerable, survives_compaction, completion_notified,
            "downgrade", "ASYNC_DELEGATION.NO_STEER",
            "后台任务无中途指令/取消机制(Synchronous delegation cannot be interrupted)——需求变更即失控，判定打折",
        )

    # R3：句柄不穿越 compaction → downgrade
    if survives_compaction == "no":
        return AsyncDelegationVerdict(
            claim, decoupled, steerable, survives_compaction, completion_notified,
            "downgrade", "ASYNC_DELEGATION.COMPACTION_LOSS",
            "任务句柄仅存于消息、随上下文压缩丢失(non-message state channel缺失)——忘记在跑的任务，判定打折",
        )

    # R4：完成不主动通知 → flag
    if completion_notified == "no":
        return AsyncDelegationVerdict(
            claim, decoupled, steerable, survives_compaction, completion_notified,
            "flag", "ASYNC_DELEGATION.FIRE_AND_FORGET",
            "完成任务无主动通知、依赖轮询(fire-and-forget)——长任务用户需反复追问，待核",
        )

    # R5：任一 partial → flag
    if any(v == "partial" for v in vals):
        return AsyncDelegationVerdict(
            claim, decoupled, steerable, survives_compaction, completion_notified,
            "flag", "ASYNC_DELEGATION.PARTIAL",
            "生命周期维度覆盖不全(partial)——拦截面存在但缺口未补齐，待核",
        )

    # R6：全自洽 → ok
    return AsyncDelegationVerdict(
        claim, decoupled, steerable, survives_compaction, completion_notified,
        "ok", "ASYNC_DELEGATION.SELF_CONSISTENT",
        "四维机制声明自洽——只判声明存在，不承诺委派真高效/完成真被通知(存在≠有效性)",
    )


def live_regression() -> dict:
    """7 个活体样例回归——对齐 gate_prereg.json 的 R0-R6 预期。"""
    cases = {
        "sync_block": dict(decoupled="no", steerable="yes", survives_compaction="yes", completion_notified="yes"),
        "no_steer": dict(decoupled="yes", steerable="no", survives_compaction="yes", completion_notified="yes"),
        "compaction_loss": dict(decoupled="yes", steerable="yes", survives_compaction="no", completion_notified="yes"),
        "fire_and_forget": dict(decoupled="yes", steerable="yes", survives_compaction="yes", completion_notified="no"),
        "partial_steer": dict(decoupled="yes", steerable="partial", survives_compaction="yes", completion_notified="yes"),
        "literal_enum": dict(decoupled="maybe", steerable="yes", survives_compaction="yes", completion_notified="yes"),
        "all_good": dict(decoupled="yes", steerable="yes", survives_compaction="yes", completion_notified="yes"),
    }
    expects = {
        "sync_block": ("downgrade", "ASYNC_DELEGATION.SYNC_BLOCK"),
        "no_steer": ("downgrade", "ASYNC_DELEGATION.NO_STEER"),
        "compaction_loss": ("downgrade", "ASYNC_DELEGATION.COMPACTION_LOSS"),
        "fire_and_forget": ("flag", "ASYNC_DELEGATION.FIRE_AND_FORGET"),
        "partial_steer": ("flag", "ASYNC_DELEGATION.PARTIAL"),
        "literal_enum": ("flag", "ASYNC_DELEGATION.INVALID_INPUT"),
        "all_good": ("ok", "ASYNC_DELEGATION.SELF_CONSISTENT"),
    }
    checks, detail = {}, {}
    for name, inp in cases.items():
        v = check_async_delegation_lifecycle("live:" + name, **inp)
        exp_a, exp_c = expects[name]
        detail[name] = f"{v.action}/{v.code}"
        checks[name] = (v.action == exp_a and v.code == exp_c)
    return {"checks": checks, "cases": detail, "all_passed": all(checks.values())}
