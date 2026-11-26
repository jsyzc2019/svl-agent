#!/usr/bin/env python3
"""证据诚实运行时工具（2026-11-26，用户"时时总结很重要……自己做的也是这样"）。

两个器官，均为纯函数、不接 run_loop、不碰 verdict / l3 / absolute / 宪法层：

  guard_negative()  —— 负面断言工具覆盖律（KB-META158）：
      凡"无 / 没有 / 不存在 / 0"类断言，必须声明【用什么工具查的】+【该工具是否覆盖目标类】。
      工具照不到 → 强制改措辞为"未查到 / 读不到"，不得说"没有"。
      反面实例：目录枚举查自动化任务得"无"，实际调度器里 ACTIVE 任务一直在。

  scope_summary()   —— 总结作用域标注（用户本条指令）：
      第三方综述 = 替大家"普照"（broad illumination），不等于全面、更不等于正确；
      自己做的总结受同一条律约束（self-applied，无豁免）。
      任何总结禁止裸结论：必须带 coverage / source_tier / blind_spots / kind。
      盲区为空 → flag，因为"没有盲区"本身就是一个未被证伪的断言。

设计惯例（§3.3/§3.4）：语义枚举 yes/no/partial；字面串不进判定分支（只用集合/字典
成员运算）；中文关键词集中 _A 字典；写 live_regression() 活体样例；不编译门禁。
"""
from __future__ import annotations

from dataclasses import dataclass, field

_ENUM = frozenset({"yes", "no", "partial"})

# 中文锚点集中管理（§3.4）；判定用集合成员，不用 Compare 内中文字面量
_A = {
    "negative_markers": frozenset({
        "无", "没有", "不存在", "零", "none", "absent", "empty", "nothing", "未发现",
    }),
    "covered_yes": "yes",
    "covered_no": "no",
    "covered_partial": "partial",
}

# 目标类 → 权威查法（今晨事故的机械固化）
AUTHORITY_MAP = {
    "automation": "automation_update mode=list",
    "git_history": ".git directory presence (tarball snapshot has none)",
    "scheduler_output": "scheduler internal resultPaths (readable or not)",
    "kb_count": "len(knowledge_base_store.json['items'])",
    "test_count": "pytest junitxml / --override-ini=addopts= summary line",
    "kernel_state": "kernel.py live call, not cached doc string",
}

# 来源层级（本仓证据分级）
_TIERS = frozenset({"A", "B", "C"})


@dataclass(frozen=True)
class GuardVerdict:
    status: str                 # ok / flagged / skipped
    code: str                   # 机器码，不读中文文案判定
    required_phrasing: str = ""  # 被迫改用的措辞
    note: str = ""


def guard_negative(
    claim: str,
    *,
    tool: str | None = None,
    covers: str | None = None,
    authority: str | None = None,
    read_back: bool | None = None,
) -> GuardVerdict:
    """负面断言工具覆盖守卫。

    claim       : 待断言句
    tool        : 用什么工具查的
    covers      : 该工具是否覆盖目标类（yes/no/partial）
    authority   : 目标类（见 AUTHORITY_MAP）
    read_back   : 是否真的读到了目标；None 表示"没尝试读回"
    """
    if not any(m in claim.lower() for m in _A["negative_markers"]):
        return GuardVerdict("skipped", "NOT_NEGATIVE")

    if not tool:
        return GuardVerdict(
            "flagged", "NO_TOOL_DECLARED",
            required_phrasing="未核验（未声明查法）",
            note="负面断言必须声明工具，否则只是印象",
        )

    if covers not in _ENUM:
        return GuardVerdict(
            "flagged", "COVERAGE_UNDECLARED",
            required_phrasing="未核验（工具覆盖未声明）",
            note="covers 必须是 yes/no/partial",
        )

    if covers == _A["covered_no"]:
        return GuardVerdict(
            "flagged", "TOOL_DOES_NOT_COVER",
            required_phrasing="未查到（当前工具覆盖不到该类）",
            note="工具照不到目标类：'没查到'不得说成'没有'",
        )

    if covers == _A["covered_partial"]:
        return GuardVerdict(
            "flagged", "PARTIAL_COVERAGE",
            required_phrasing="部分未查到（工具仅部分覆盖）",
            note="部分覆盖不得输出干净的全称否定",
        )

    # covers == yes：继续核对是否用了权威查法
    if authority is not None and authority in AUTHORITY_MAP:
        expected = AUTHORITY_MAP[authority]
        if expected.split()[0] not in tool:
            return GuardVerdict(
                "flagged", "NON_AUTHORITATIVE_TOOL",
                required_phrasing=f"未核验（该类权威查法应为 {expected}）",
                note="声明覆盖 yes 但查法不是该类权威源",
            )

    if read_back is False:
        return GuardVerdict(
            "flagged", "READ_BACK_FAILED",
            required_phrasing="读不到（不签字）",
            note="实际读回失败：无输出正文时不得声称执行成功",
        )
    if read_back is None:
        return GuardVerdict(
            "flagged", "READ_BACK_UNTESTED",
            required_phrasing="未核验（未尝试读回）",
            note="声明覆盖并查过，但未确认是否真的读到目标",
        )

    return GuardVerdict("ok", "GUARDED", note="负面断言已合规：工具+覆盖+读回齐全")


@dataclass(frozen=True)
class SummaryScope:
    status: str
    code: str
    scope_note: str = ""
    required_disclaimers: tuple[str, ...] = field(default_factory=tuple)


def scope_summary(
    *,
    kind: str,                       # third_party / self
    coverage: str,                   # 覆盖范围描述
    source_tiers: tuple[str, ...],   # 每条来源的 A/B/C
    blind_spots: tuple[str, ...],    # 已知盲区（必须非空）
    self_applied: bool = False,      # 是否声明自己做的总结同受此律
) -> SummaryScope:
    """总结作用域标注：综述=普照非全知，自作总结同律。

    禁止裸结论：kind 非法 / 来源层级非法 / 盲区为空 / 自作总结未声明自洽 → flag。
    """
    if kind not in ("third_party", "self"):
        return SummaryScope("flagged", "KIND_INVALID", "kind 必须 third_party 或 self")

    bad = [t for t in source_tiers if t not in _TIERS]
    if bad:
        return SummaryScope("flagged", "SOURCE_TIER_INVALID", f"非法层级 {bad}")

    if not coverage.strip():
        return SummaryScope("flagged", "COVERAGE_EMPTY", "总结必须声明覆盖范围")

    if not blind_spots:
        return SummaryScope(
            "flagged", "NO_BLIND_SPOTS",
            "'没有盲区'本身就是一个未被证伪的断言",
        )

    disclaimers: list[str] = []
    if kind == "third_party":
        disclaimers.append("第三方综述只是普照（broad illumination），不等于全面或正确")
    if kind == "self":
        if not self_applied:
            return SummaryScope(
                "flagged", "SELF_NOT_APPLIED",
                "自己做的总结必须声明受同一条律约束，无豁免",
            )
        disclaimers.append("自作总结与第三方综述同受此律：范围有限、可能有错")

    disclaimers.append("盲区清单：" + "；".join(blind_spots))
    return SummaryScope(
        "ok", "SCOPED",
        scope_note=f"[{kind}] 覆盖：{coverage}",
        required_disclaimers=tuple(disclaimers),
    )


def live_regression() -> dict:
    """7 活体样例：今晨真实事故 + 6 个对照/边界。"""
    cases = {
        "morning_accident": guard_negative(
            "无自动化任务", tool="ls ~/.codebuddy | grep autom",
            covers="no", authority="automation", read_back=False,
        ),
        "corrected": guard_negative(
            "无自动化任务异常（已用权威查法读回确认）",
            tool="automation_update list",
            covers="yes", authority="automation", read_back=True,
        ),
        "non_negative": guard_negative("内核版本7.5.0"),
        "no_tool": guard_negative("无遗留进程", covers="yes", read_back=True),
        "authority_mismatch": guard_negative(
            "无Git历史", tool="ls -la", covers="yes",
            authority="git_history", read_back=True,
        ),
        "summary_third_party": scope_summary(
            kind="third_party", coverage="441条KB",
            source_tiers=("A", "B"), blind_spots=("未含今晨新增",),
        ),
        "summary_self_unapplied": scope_summary(
            kind="self", coverage="本次复盘", source_tiers=("A",),
            blind_spots=("确认性采样",), self_applied=False,
        ),
    }
    expect = {
        "morning_accident": "TOOL_DOES_NOT_COVER",
        "corrected": "GUARDED",
        "non_negative": "NOT_NEGATIVE",
        "no_tool": "NO_TOOL_DECLARED",
        "authority_mismatch": "NON_AUTHORITATIVE_TOOL",
        "summary_third_party": "SCOPED",
        "summary_self_unapplied": "SELF_NOT_APPLIED",
    }
    results = {k: v.code for k, v in cases.items()}
    return {
        "cases": results,
        "expected": expect,
        "all_pass": all(results[k] == expect[k] for k in expect),
        "n": len(cases),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(live_regression(), ensure_ascii=False, indent=2))
