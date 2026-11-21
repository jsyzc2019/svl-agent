"""记忆内容质量治理门禁 — 把22来源记忆生命周期谱系编译成会判动作（§68）。

一手/二手证据（见 audit_memory/）：
  - S02 CLS(McClelland et al.1995)：新皮层慢学结构 + 海马快速记忆 + 渐进交错整合防干扰。
  - S03 Science(Yang et al.2024): "only a small fraction are retained";清醒SPW-R标记→睡眠优先重放。
  - S07 Claude Dreams(二手区域锁)："over many sessions a memory store accumulates duplicates,
    contradictions, and stale entries";dreams去重/矛盾替换/新洞察;"input store is never modified"。
  - S17 Karpathy LLM Wiki(一手)：wiki是persistent compounding artifact;Ingest/Query/Lint;
    Lint查矛盾/过时声明/孤儿页/缺失交叉引用。
  - S11 synaptic tagging(LTP)：标记决定哪些突触进入长期增强。

为什么是新牙（对比现有15道门禁）：
  session_continuity(§65)判跨会话状态续接；improvement_memory判改进记录可证伪性；
  四要素记忆判要素存在——无一判『存进去的记忆是否精选/已整理/非破坏』。
  本门拦一个声称长期记忆的系统是否有内容质量治理，拦截面独立。

编译纪律（与 gate_prereg.json 一致，实现前 SHA256 锁存 213ed6e2…）：
  - 语义枚举 yes/no/partial + bool；字面串→flag(R0，避§56 brittle根因)；
  - 规则 R0-R5 按优先级短路返回，不事后加权(防Goodhart)；
  - 只判『机制声明是否自洽』，不承诺记忆真的有用/检索真的命中——机制存在≠有效性(KB-META01)；
    生物机制不证成AI设计(主体错位KB-STRUCT05)；self-reported数字不作独立验证(KB-RSI07)。

诚实边界：定位为审读外部长期记忆系统声称的尺子，不判本仓；按KB-STRUCT02不构成对本仓
框架的独立验证；本仓同步纯函数库非运行时记忆系统，遵循§58选A不接run_loop。
"""
from __future__ import annotations

from dataclasses import dataclass

# 语义枚举——写死；判定绝不读字符串内容（KB-AUDIT01 brittle 根因）
_ENUM = frozenset({"yes", "no", "partial"})


@dataclass(frozen=True)
class MemoryCurationVerdict:
    claim: str
    selection: str
    consolidation: str
    nondestructive: bool
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_memory_curation(
    claim: str,
    *,
    selection: str,
    consolidation: str,
    nondestructive: bool,
) -> MemoryCurationVerdict:
    """判一个长期记忆声称是否有自洽的内容治理机制（不承诺记忆真的有用）。

    输入须为语义枚举 + 布尔：
      selection, consolidation ∈ {yes, no, partial}
      nondestructive ∈ bool

    规则按优先级短路返回（与 gate_prereg.json 一致）：
      R0 非枚举/非bool → flag（拒绝字面串内容判定）
      R1 无选择（全量写入）→ downgrade（违反 only small fraction retained）
      R2 无整理（去重/矛盾/过时）→ downgrade（multi-session 退化为垃圾堆）
      R3 破坏性整理 → flag（就地覆盖不可审阅/不可丢弃）
      R4 部分选择/部分整理 → flag（覆盖不全，待核）
      R5 全自洽 → ok（只判机制声明存在，不承诺记忆真的提升效果）
    """
    # R0：语义输入校验优先
    if selection not in _ENUM or consolidation not in _ENUM:
        return MemoryCurationVerdict(
            claim, str(selection), str(consolidation), nondestructive,
            "flag", "MEMORY.INVALID_INPUT",
            "selection/consolidation 须为 yes/no/partial 语义枚举；收到非法值（含字面串）→ flag，不进内容判定",
        )
    if not isinstance(nondestructive, bool):
        return MemoryCurationVerdict(
            claim, selection, consolidation, nondestructive,
            "flag", "MEMORY.INVALID_INPUT",
            "nondestructive 非 bool → flag，拒绝对真值做内容判定",
        )

    # R1：无选择（全量写入）→ downgrade
    if selection == "no":
        return MemoryCurationVerdict(
            claim, selection, consolidation, nondestructive,
            "downgrade", "MEMORY.NO_SELECTION",
            "声称长期记忆却无选择机制(全量写入)——违反『只有小部分经历被保留』，退化为垃圾堆，判定打折",
        )

    # R2：无整理 → downgrade
    if consolidation == "no":
        return MemoryCurationVerdict(
            claim, selection, consolidation, nondestructive,
            "downgrade", "MEMORY.NO_CONSOLIDATION",
            "无去重/矛盾消解/过时替换——多会话后memory store退化为duplicates+contradictions+stale，判定打折",
        )

    # R3：破坏性整理 → flag
    if not nondestructive:
        return MemoryCurationVerdict(
            claim, selection, consolidation, nondestructive,
            "flag", "MEMORY.DESTRUCTIVE",
            "整理就地覆盖原store——不可审阅/不可丢弃(Dreams明确input store never modified)，待核",
        )

    # R4：部分选择/部分整理 → flag
    if selection == "partial" or consolidation == "partial":
        return MemoryCurationVerdict(
            claim, selection, consolidation, nondestructive,
            "flag", "MEMORY.PARTIAL",
            "部分选择或部分整理——覆盖不全，某些记忆仍未被精选/整理，待核（不是定罪）",
        )

    # R5：全自洽
    return MemoryCurationVerdict(
        claim, selection, consolidation, nondestructive,
        "ok", "MEMORY.SELF_CONSISTENT",
        "选择+整理+非破坏——声称与机制自洽"
        "（只判机制声明存在，不承诺记忆真的提升效果或检索真的命中）",
    )


def live_regression() -> dict:
    """7 个活体样例回归——对齐 gate_prereg.json 的预期。"""
    cases = {
        "no_selection": dict(selection="no", consolidation="yes", nondestructive=True),
        "no_consolidation": dict(selection="yes", consolidation="no", nondestructive=True),
        "destructive": dict(selection="yes", consolidation="yes", nondestructive=False),
        "partial_selection": dict(selection="partial", consolidation="yes", nondestructive=True),
        "partial_consolidation": dict(selection="yes", consolidation="partial", nondestructive=True),
        "literal_enum": dict(selection="maybe", consolidation="yes", nondestructive=True),
        "all_good": dict(selection="yes", consolidation="yes", nondestructive=True),
    }
    expects = {
        "no_selection": ("downgrade", "MEMORY.NO_SELECTION"),
        "no_consolidation": ("downgrade", "MEMORY.NO_CONSOLIDATION"),
        "destructive": ("flag", "MEMORY.DESTRUCTIVE"),
        "partial_selection": ("flag", "MEMORY.PARTIAL"),
        "partial_consolidation": ("flag", "MEMORY.PARTIAL"),
        "literal_enum": ("flag", "MEMORY.INVALID_INPUT"),
        "all_good": ("ok", "MEMORY.SELF_CONSISTENT"),
    }
    checks, detail = {}, {}
    for name, inp in cases.items():
        v = check_memory_curation("live:" + name, **inp)
        exp_a, exp_c = expects[name]
        detail[name] = f"{v.action}/{v.code}"
        checks[name] = (v.action == exp_a and v.code == exp_c)
    return {"checks": checks, "cases": detail, "all_passed": all(checks.values())}
