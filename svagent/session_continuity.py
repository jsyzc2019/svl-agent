"""跨会话状态连续性门禁 — 把 Anthropic《Building always-on agents》的运行时状态连续性编译成会判动作（§65）。

一手来源：
  Anthropic《Building always-on agents》(William Hu, 2026-11-13)：
  - line 27：always-on 不是字面常驻，是用户体验；agent 多数时间 asleep，被 event 唤醒短暂 run。
  - line 48：inbox should be source of truth——worker 崩溃后新 worker 重拾同一 event 重试。
  - line 70：memories outlive the worker——持久存储让记忆比 worker 长寿。
  - line 91：session 过长时 compact 或 new session 都丢细节，需持久的信息必须在过程中写入 memory。
  - line 105-110：deferred tool call——run 结束、session 中途保存(mid-call)、用户答复作为 event
    回 inbox、新 run resume saved session；等待期间 worker 处理其他 event 不阻塞。

为什么是新牙（对比现有 14 道门禁，V5 结构化核验）：
  本仓门禁覆盖计分完整性/跨领域迁移/判定稳健/任务复盘/谱系打折/回测隔离/调用点/
  审查漏斗/训练服务信号/检索溯源/术语歧义/组件归因/评估可靠/四要素记忆——
  无一覆盖『事件驱动系统的状态连续性与可恢复性』。本模块判一个声称 always-on 的系统
  是否声明了支撑跨会话连续的核心机制（持久状态/真相源/单消费者/会话续跑/非阻塞等待），
  拦截面独立，非 §64 单 run 检索 hygiene、非老条款实例。

编译纪律（与 gate_prereg.json 一致，实现前 SHA256 锁存 42b10e90…）：
  - 语义枚举 yes/no/partial + 布尔，传字面串 → flag（R0，避开 §56 brittle 根因）；
  - 规则 R0-R7 按优先级短路返回，不事后加权（防 Goodhart）；
  - 只判『机制声明是否自洽』，绝不承诺系统真的永续运行、持久化真的不丢——机制存在≠有效性，
    声明不可自证（KB-META01）；本仓同步纯函数库不做运行时编排是 §58 选 A 架构选择，非漏洞。

诚实边界：定位为审读外部 always-on 系统声称的尺子，不判本仓；按 KB-STRUCT02 不构成对本仓
框架的独立验证；不接入 run_loop（遵循 §58 选 A）。
"""
from __future__ import annotations

from dataclasses import dataclass

# 语义枚举——写死；判定绝不读字符串内容（KB-AUDIT01 brittle 根因）
_ENUM = frozenset({"yes", "no", "partial"})
_BOOL_FIELDS = ("source_of_truth", "single_consumer", "nonblocking_defer")


@dataclass(frozen=True)
class SessionContinuityVerdict:
    claim: str
    durable_state: str
    source_of_truth: bool
    single_consumer: bool
    session_resume: str
    nonblocking_defer: bool
    action: str        # ok | downgrade | flag | block
    code: str
    message: str


def check_session_continuity(
    claim: str,
    *,
    durable_state: str,
    source_of_truth: bool,
    single_consumer: bool,
    session_resume: str,
    nonblocking_defer: bool,
) -> SessionContinuityVerdict:
    """判一个 always-on 声称是否有自洽的状态连续性机制（不承诺真的永续）。

    输入须为语义枚举 + 布尔：
      durable_state, session_resume ∈ {yes, no, partial}
      三个 bool 字段见签名。

    规则按优先级短路返回（与 gate_prereg.json 一致）：
      R0 非枚举/非布尔 → flag（拒绝字面串内容判定）
      R1 无持久状态且声称 always-on → block（连续性根基不成立）
      R2 会话不可续跑 → downgrade（跨会话断裂）
      R3 无真相源 → downgrade（崩溃不可幂等重试）
      R4 多消费者 → downgrade（重复/覆盖风险）
      R5 等待阻塞 → flag（not truly always-on，待核）
      R6 部分持久化/部分续跑 → flag（覆盖不全，待核）
      R7 全满足 → ok（声称与机制自洽，仍不承诺真的永续）
    """
    # R0：语义输入校验优先
    if durable_state not in _ENUM or session_resume not in _ENUM:
        return SessionContinuityVerdict(
            claim, str(durable_state), source_of_truth, single_consumer,
            str(session_resume), nonblocking_defer, "flag", "CONTINUITY.INVALID_ENUM",
            "durable_state/session_resume 须为 yes/no/partial 语义枚举；收到非法值（含字面串）→ flag，不进内容判定",
        )
    if not all(isinstance(v, bool) for v in (
        source_of_truth, single_consumer, nonblocking_defer
    )):
        return SessionContinuityVerdict(
            claim, durable_state, source_of_truth, single_consumer,
            session_resume, nonblocking_defer, "flag", "CONTINUITY.INVALID_FLAG",
            "布尔标志位非 bool → flag，拒绝对真值做内容判定",
        )

    # R1：无跨 run 持久状态 → block
    if durable_state == "no":
        return SessionContinuityVerdict(
            claim, durable_state, source_of_truth, single_consumer,
            session_resume, nonblocking_defer, "block", "CONTINUITY.NO_DURABLE_STATE",
            "声称 always-on 却无跨 run 持久状态——memories 无法 outlive worker，连续性根基不成立，block",
        )

    # R2：会话不可续跑 → downgrade
    if session_resume == "no":
        return SessionContinuityVerdict(
            claim, durable_state, source_of_truth, single_consumer,
            session_resume, nonblocking_defer, "downgrade", "CONTINUITY.NO_SESSION_RESUME",
            "deferred/中断的 session 无法在答复回来后 resume——跨会话连续性断裂，判定打折",
        )

    # R3：无单一真相源 → downgrade
    if not source_of_truth:
        return SessionContinuityVerdict(
            claim, durable_state, source_of_truth, single_consumer,
            session_resume, nonblocking_defer, "downgrade", "CONTINUITY.NO_SOURCE_OF_TRUTH",
            "无 inbox-as-source-of-truth——worker 崩溃后不可幂等重拾同一 event，事件可丢可重，判定打折",
        )

    # R4：多消费者 → downgrade
    if not single_consumer:
        return SessionContinuityVerdict(
            claim, durable_state, source_of_truth, single_consumer,
            session_resume, nonblocking_defer, "downgrade", "CONTINUITY.MULTI_CONSUMER",
            "一个 inbox 有多个 active worker——并发重复工作/互相覆盖风险，判定打折",
        )

    # R5：等待阻塞 → flag
    if not nonblocking_defer:
        return SessionContinuityVerdict(
            claim, durable_state, source_of_truth, single_consumer,
            session_resume, nonblocking_defer, "flag", "CONTINUITY.BLOCKING_DEFER",
            "等待用户答复期间 worker 被阻塞——非真正 always-on（应可处理其他 event），待核",
        )

    # R6：部分持久化/部分续跑 → flag
    if durable_state == "partial" or session_resume == "partial":
        return SessionContinuityVerdict(
            claim, durable_state, source_of_truth, single_consumer,
            session_resume, nonblocking_defer, "flag", "CONTINUITY.PARTIAL",
            "部分持久化或部分会话续跑——覆盖不全，某些状态/中断仍会丢失，待核（不是定罪）",
        )

    # R7：全自洽
    return SessionContinuityVerdict(
        claim, durable_state, source_of_truth, single_consumer,
        session_resume, nonblocking_defer, "ok", "CONTINUITY.SELF_CONSISTENT",
        "持久状态 + 真相源 + 单消费者 + 会话续跑 + 非阻塞等待——声称与机制自洽"
        "（只判机制声明存在，不承诺系统真的永续运行、持久化真的不丢）",
    )


def live_regression() -> dict:
    """8 个活体样例回归——对齐 gate_prereg.json 的预期。"""
    cases = {
        "no_durable_state": dict(durable_state="no", source_of_truth=True,
                                 single_consumer=True, session_resume="yes", nonblocking_defer=True),
        "no_session_resume": dict(durable_state="yes", source_of_truth=True,
                                  single_consumer=True, session_resume="no", nonblocking_defer=True),
        "no_source_of_truth": dict(durable_state="yes", source_of_truth=False,
                                   single_consumer=True, session_resume="yes", nonblocking_defer=True),
        "multi_consumer": dict(durable_state="yes", source_of_truth=True,
                               single_consumer=False, session_resume="yes", nonblocking_defer=True),
        "blocking_defer": dict(durable_state="yes", source_of_truth=True,
                               single_consumer=True, session_resume="yes", nonblocking_defer=False),
        "partial_durable": dict(durable_state="partial", source_of_truth=True,
                                single_consumer=True, session_resume="yes", nonblocking_defer=True),
        "literal_enum": dict(durable_state="maybe", source_of_truth=True,
                             single_consumer=True, session_resume="yes", nonblocking_defer=True),
        "all_good": dict(durable_state="yes", source_of_truth=True,
                         single_consumer=True, session_resume="yes", nonblocking_defer=True),
    }
    expects = {
        "no_durable_state": ("block", "CONTINUITY.NO_DURABLE_STATE"),
        "no_session_resume": ("downgrade", "CONTINUITY.NO_SESSION_RESUME"),
        "no_source_of_truth": ("downgrade", "CONTINUITY.NO_SOURCE_OF_TRUTH"),
        "multi_consumer": ("downgrade", "CONTINUITY.MULTI_CONSUMER"),
        "blocking_defer": ("flag", "CONTINUITY.BLOCKING_DEFER"),
        "partial_durable": ("flag", "CONTINUITY.PARTIAL"),
        "literal_enum": ("flag", "CONTINUITY.INVALID_ENUM"),
        "all_good": ("ok", "CONTINUITY.SELF_CONSISTENT"),
    }
    checks, detail = {}, {}
    for name, inp in cases.items():
        v = check_session_continuity("live:" + name, **inp)
        exp_a, exp_c = expects[name]
        detail[name] = f"{v.action}/{v.code}"
        checks[name] = (v.action == exp_a and v.code == exp_c)
    return {"checks": checks, "cases": detail, "all_passed": all(checks.values())}
