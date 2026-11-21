"""任务复盘门禁 — 把『从所有既定任务本身与完成过程汲取知识』编译成可执行裁决。

用户意图（2026-11-22）：
  "完成既定任务时，也要从任务本身和完成过程汲取有利于我的知识，
   进而提升本仓认知和能力。"

相对已有能力的真实增量（非 vanity 重述）：
  - 触发泛化：KB-R06/R08/SIM05/META01 都在"审读/借鉴/改进记录"语境；本模块把触发
    扩展到【所有既定任务】收尾（含工程、推送、修 bug）。
  - 双知识源：task_content（任务结论本身）+ process（弯路/判据自咬/工具失败/修正）
    须分别显式声明——只从结论学、不从过程学，会丢掉最有价值的失败教训。
  - 目的约束：汲取须"有利于用户"、可证伪（predicted↔observed）、非复述，否则降级/拦截。

编译纪律（KB-META01 + KB-R08 + KB-SIM05）：
  - 规则写死、可测试；不事后加权；
  - 不作单点定罪（KB-AUDIT02）：多条件按优先级裁决；
  - process 源自证风险高（自己说自己学到了），故强制 predicted↔observed 与用户价值门；
  - 活体样例来自 §53 真实任务，非用户外部事实，不伪装为"用户教授的知识"。

本模块为纯函数/数据类，无外部依赖。
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class KnowledgeCandidate:
    """一次任务收尾时提炼的一条候选知识。"""
    claim: str                      # 学到的东西（一句话）
    source: str                     # task_content | process | both
    predicted: str = ""             # 事前预期（可证伪锚）
    observed: str = ""              # 事后实测
    benefits_user: bool = True      # 是否有利于用户（目的约束）
    is_restatement: bool = False    # 是否只是复述已知/复述别人
    failure_recorded: bool = True   # 若过程有失败/回滚，是否已记录
    had_failure: bool = False       # 过程是否发生过失败/判据自咬/工具失败


@dataclass(frozen=True)
class RetroVerdict:
    action: str        # ok | downgrade | flag | block
    code: str
    message: str
    classified_as: str  # fix | vanity | preserve | observe（KB-R08 三分 + observe）


def retrospect(chi: KnowledgeCandidate) -> RetroVerdict:
    """一次任务收尾的双源复盘裁决。规则写死，按优先级：

      G3 复述冒充 → block（声称认知提升但只是复述，KB-META01）
      G4 无用户价值 → flag（汲取须有利于用户）
      G1 双源缺失 → downgrade（只有任务结论、process 空）
        —— 注意此规则【有意不对称】：单 task_content 降级（这是过去"只从结论学"的旧模式），
           但单 process 放行（用户的核心增量正是"也要从过程学"，过程源单独也成立）。
      G2 不可证伪 → downgrade（无 predicted↔observed，KB-SIM05）
      G5 失败未记 → downgrade（过程有失败/回滚却没记，KB-SIM05）
      PASS → ok，classified_as=fix，可入库/强固
    """
    # G3 复述冒充：最高优先级，复述不得冒充认知提升
    if chi.is_restatement:
        return RetroVerdict(
            "block", "RETRO.RESTATEMENT",
            "这条只是复述（已知/转述他人），不算从任务汲取的认知提升——"
            "复述不得入库充数（KB-META01）", "vanity",
        )
    # G4 目的约束：有利于用户
    if not chi.benefits_user:
        return RetroVerdict(
            "flag", "RETRO.NO_USER_VALUE",
            "这条知识说不出对用户的好处——元学习须服务于用户，不为进化而进化", "observe",
        )
    # G1 双源：只从任务结论学、不从过程学
    if chi.source == "task_content":
        return RetroVerdict(
            "downgrade", "RETRO.SINGLE_SOURCE",
            "只声明了任务内容源、process 源（弯路/自咬/失败/修正）空缺——"
            "过程本身也是知识源，不记录则降级为观察，不作强结论", "observe",
        )
    if chi.source not in ("process", "both"):
        return RetroVerdict(
            "flag", "RETRO.BAD_SOURCE",
            f"未知知识源 {chi.source!r}，须为 task_content/process/both", "observe",
        )
    # G2 可证伪：predicted↔observed 配对
    if not chi.predicted or not chi.observed:
        return RetroVerdict(
            "downgrade", "RETRO.UNFALSIFIABLE",
            "有结论但无 predicted↔observed 配对——不可证伪，按 KB-SIM05 降级为观察，不给强结论", "observe",
        )
    # G5 失败尝试也要留
    if chi.had_failure and not chi.failure_recorded:
        return RetroVerdict(
            "downgrade", "RETRO.FAILURE_UNRECORDED",
            "过程发生过失败/判据自咬/工具失败却未记录——失败尝试也要保留（KB-SIM05），否则只留成功叙事", "observe",
        )
    return RetroVerdict(
        "ok", "RETRO.OK",
        "双源齐全、可证伪、有利于用户、非复述——这条认知可入库/强固", "fix",
    )


# ---------------------------------------------------------------- 活体回归（§53 真实任务）
# 来自本轮 §53 的实际复盘，非用户外部事实：
#   task_content+process 双源：借 SWE-Gym 五类工程纪律编译 C1/C2/C3（任务结论），
#     事前预测"能拦冗余条件/不稳判定"、事后活体回归确实拦住 → predicted↔observed 成立。
#   process 源：写 build_robustness_result.py 时 dict 键名前导空格致 KeyError，修复后重跑通过；
#               §51 判据自咬修正——过程里真有失败与修正。
LIVE_DUAL_SOURCE = KnowledgeCandidate(
    claim="SWE-Gym 的工程纪律可编译成本仓三道门禁；且活体样例写错时被判据自咬，如实修正为双源",
    source="both",
    predicted="编译后活体回归能拦住不稳判定/冗余条件/不可信样例集；写错的活体样例会被判据咬住",
    observed="15 项测试通过，C1/C2/C3 命中预期；单源活体样例被 G1 降级后修正为双源——自咬被记录",
    benefits_user=True,
    is_restatement=False,
)
LIVE_PROCESS = KnowledgeCandidate(
    claim="构建脚本 dict 键名前导空格致 KeyError；判据第一版误读正向增益为过拟合（§51自咬）",
    source="process",
    predicted="记录过程失败可防止下次重犯、并固化成对/口径对等判据",
    observed="修正键名后重跑通过；自咬修正固化为常驻回归测试",
    benefits_user=True,
    is_restatement=False,
    had_failure=True,
    failure_recorded=True,
)
LIVE_RESTATEMENT = KnowledgeCandidate(
    claim="要反思、要学习",
    source="both",
    predicted="",
    observed="",
    is_restatement=True,
)
LIVE_SINGLE_SOURCE = KnowledgeCandidate(
    claim="SWE-Gym verifier 可被 hacking",
    source="task_content",
    predicted="",
    observed="",
)


def live_regression() -> dict:
    """活体回归：双源齐全 → ok；process 单源 → ok；复述 → block；仅任务源 → downgrade。"""
    dual = retrospect(LIVE_DUAL_SOURCE)
    pr = retrospect(LIVE_PROCESS)
    rest = retrospect(LIVE_RESTATEMENT)
    single = retrospect(LIVE_SINGLE_SOURCE)
    dual_ok = dual.action == "ok" and dual.classified_as == "fix"
    pr_ok = pr.action == "ok" and pr.classified_as == "fix"
    rest_ok = rest.action == "block" and rest.classified_as == "vanity"
    single_ok = single.action == "downgrade" and single.code == "RETRO.SINGLE_SOURCE"
    return {
        "dual_source": {"action": dual.action, "code": dual.code, "classified_as": dual.classified_as},
        "process": {"action": pr.action, "code": pr.code, "classified_as": pr.classified_as},
        "restatement": {"action": rest.action, "code": rest.code, "classified_as": rest.classified_as},
        "single_source": {"action": single.action, "code": single.code, "classified_as": single.classified_as},
        "all_passed": dual_ok and pr_ok and rest_ok and single_ok,
    }
