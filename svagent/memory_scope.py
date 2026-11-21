"""记忆作用域保持门禁 — 把 Memory Trap 论文编译成会判动作（§70）。

一手证据（见 audit_memory_trap/）：
  - S03 Memory Trap（Princeton+Anthropic, arXiv 2611.07554v1, 6 模型对照, 有 code）：
    "memory trap" = 良性交互("benign interactions")产生的记忆在超出原作用域时导致
    unsafe/unreliable 行为。两条路径：write-time（写笔记时 broaden 用户陈述——
    "skip confirmation" during clean-up 被写成 "never confirm before actions"）与
    read-time（用记忆时 overgeneralize，即使是 raw transcript）。"no adversary"——
    每次交互都良性、记忆是 agent 自己的，所以 "malicious-content filters have nothing
    to catch"。实验：skip confirmation 迁移到高风险任务、情感支持记忆导致 sycophancy/
    over-critique、stale-test 修复记忆削弱正确测试并在 ImpossibleBench 增加作弊。
    结论：agent 应 "preserve the scope of their memories"。
  - S01 components（一手，Anthropic 2026-11-06）：与 §68 记忆谱系同源（hippocampus→
    neocortex 巩固 + dreaming + salience 判断），按 KB-STRUCT02 打折，不单独造牙。
  - S02 Dreams（二手区域锁，§68 S07 同源）：内容治理（去重/矛盾/过时/非破坏），
    已由 memory_curation 覆盖，打折。

为什么是新牙（对比现有门禁）：
  memory_curation(§68)判记忆内容质量（选择/整理/非破坏）；retrieval_grounding(§64)
  判检索外部文本是 data 非 instruction；improvement_memory 判记录可证伪——
  无一判『记忆的作用域是否保持』：写时保留原始边界、读时核当前情境仍在作用域内、
  条目记录适用边界、良性交互不越界漂移。Memory Trap 有 6 模型对照 + code +
  明确拦截面 → KB-META01 会拦才入通过。

编译纪律（与 gate_prereg.json 一致，实现前 SHA256 锁存 a34e50c0…）：
  - 语义枚举；字面串→flag(R0，避 §56 brittle 根因)；
  - 规则 R0-R6 短路返回，不事后加权(防 Goodhart)；
  - 只判『机制声明是否自洽』，不承诺记忆真的不过度泛化——存在≠有效性(KB-META01)；
    Memory Trap 是 6 闭源模型经验证据，不普适为定律(KB-SIM09 上下文是经验一部分)。

诚实边界：定位为审读外部记忆系统的尺子，不判本仓；本仓同步纯函数库非运行时记忆系统，
遵循 §58 选 A 不接 run_loop。
"""
from __future__ import annotations

from dataclasses import dataclass

_ENUM = frozenset({"yes", "no", "partial"})


@dataclass(frozen=True)
class MemoryScopeVerdict:
    claim: str
    write_scope: str
    read_scope: str
    scope_bounds: str
    no_benign_drift: str
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_memory_scope(
    claim: str,
    *,
    write_scope_preserved: str,
    read_scope_checked: str,
    scope_bounds_recorded: str,
    no_benign_drift: str,
) -> MemoryScopeVerdict:
    """判一个有持久记忆的系统是否有自洽的作用域保持机制（不承诺真不过度泛化）。

    输入须为语义枚举：四维 ∈ {yes, no, partial}

    规则按优先级短路返回（与 gate_prereg.json R0-R6 一致）：
      R0 任一非枚举 → flag
      R1 write_scope_preserved=no → downgrade（写时 broadening，源头丢作用域）
      R2 read_scope_checked=no → downgrade（读时不核情境，越界应用）
      R3 scope_bounds_recorded=no → downgrade（无适用边界，记忆无法自限）
      R4 no_benign_drift=no → flag（良性漂移已发生，memory trap 待核）
      R5 任一 partial → flag（覆盖不全，待核）
      R6 全 yes → ok（只判声明自洽）
    """
    vals = (write_scope_preserved, read_scope_checked, scope_bounds_recorded, no_benign_drift)
    if any(v not in _ENUM for v in vals):
        return MemoryScopeVerdict(
            claim, str(write_scope_preserved), str(read_scope_checked),
            str(scope_bounds_recorded), str(no_benign_drift),
            "flag", "MEMORY_SCOPE.INVALID_INPUT",
            "四维须为 yes/no/partial 语义枚举；非法值（含字面串）→ flag，不进内容判定",
        )
    if write_scope_preserved == "no":
        return MemoryScopeVerdict(
            claim, *vals, "downgrade", "MEMORY_SCOPE.WRITE_BROADEN",
            "写记忆时 broaden 用户陈述(clean-up 的 skip confirmation 写成 never confirm)——作用域在源头丢失，判定打折",
        )
    if read_scope_checked == "no":
        return MemoryScopeVerdict(
            claim, *vals, "downgrade", "MEMORY_SCOPE.READ_NO_SCOPE_CHECK",
            "用记忆时不核当前情境是否仍在原作用域(raw transcript 也会被过度泛化)——越界应用，判定打折",
        )
    if scope_bounds_recorded == "no":
        return MemoryScopeVerdict(
            claim, *vals, "downgrade", "MEMORY_SCOPE.NO_BOUNDS",
            "记忆条目不记录适用边界(何时/何地/对谁有效)——记忆无法自限，判定打折",
        )
    if no_benign_drift == "no":
        return MemoryScopeVerdict(
            claim, *vals, "flag", "MEMORY_SCOPE.BENIGN_DRIFT",
            "良性交互已因自写记忆在越界任务上漂移(memory trap;无对手、过滤器抓不到)——待核",
        )
    if any(v == "partial" for v in vals):
        return MemoryScopeVerdict(
            claim, *vals, "flag", "MEMORY_SCOPE.PARTIAL",
            "作用域保持覆盖不全(partial)——拦截面存在但缺口未补齐，待核",
        )
    return MemoryScopeVerdict(
        claim, *vals, "ok", "MEMORY_SCOPE.SELF_CONSISTENT",
        "四维机制声明自洽——只判声明存在，不承诺记忆真的不过度泛化(存在≠有效性)",
    )


def live_regression() -> dict:
    """7 个活体样例回归——对齐 gate_prereg.json 的 R0-R6 预期。"""
    cases = {
        "write_broaden": dict(write_scope_preserved="no", read_scope_checked="yes", scope_bounds_recorded="yes", no_benign_drift="yes"),
        "read_no_check": dict(write_scope_preserved="yes", read_scope_checked="no", scope_bounds_recorded="yes", no_benign_drift="yes"),
        "no_bounds": dict(write_scope_preserved="yes", read_scope_checked="yes", scope_bounds_recorded="no", no_benign_drift="yes"),
        "benign_drift": dict(write_scope_preserved="yes", read_scope_checked="yes", scope_bounds_recorded="yes", no_benign_drift="no"),
        "partial_write": dict(write_scope_preserved="partial", read_scope_checked="yes", scope_bounds_recorded="yes", no_benign_drift="yes"),
        "literal_enum": dict(write_scope_preserved="maybe", read_scope_checked="yes", scope_bounds_recorded="yes", no_benign_drift="yes"),
        "all_good": dict(write_scope_preserved="yes", read_scope_checked="yes", scope_bounds_recorded="yes", no_benign_drift="yes"),
    }
    expects = {
        "write_broaden": ("downgrade", "MEMORY_SCOPE.WRITE_BROADEN"),
        "read_no_check": ("downgrade", "MEMORY_SCOPE.READ_NO_SCOPE_CHECK"),
        "no_bounds": ("downgrade", "MEMORY_SCOPE.NO_BOUNDS"),
        "benign_drift": ("flag", "MEMORY_SCOPE.BENIGN_DRIFT"),
        "partial_write": ("flag", "MEMORY_SCOPE.PARTIAL"),
        "literal_enum": ("flag", "MEMORY_SCOPE.INVALID_INPUT"),
        "all_good": ("ok", "MEMORY_SCOPE.SELF_CONSISTENT"),
    }
    checks, detail = {}, {}
    for name, inp in cases.items():
        v = check_memory_scope("live:" + name, **inp)
        exp_a, exp_c = expects[name]
        detail[name] = f"{v.action}/{v.code}"
        checks[name] = (v.action == exp_a and v.code == exp_c)
    return {"checks": checks, "cases": detail, "all_passed": all(checks.values())}
