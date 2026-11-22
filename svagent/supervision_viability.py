"""监督可行性门禁 — 把认知投降谱系编译成会判动作（§74）。

一手证据（见 audit_cognitive_surrender/）：
  - S02 cognitive-surrender（一手博客，SHA256 c73b3bf3…）：区分 cognitive
    offloading（委托 how、保留 what、仍自己判断）与 cognitive surrender（AI
    输出变成你的输出、没有独立观点可比）；转述 Shaw-Nave：AI 错时 73% 接受
    错误答案、borrowed-confidence（错误后信心反升）；"you never formed an
    independent view to compare it against"；"Surface correctness is not
    systemic correctness"。
  - S05 comprehension-debt（一手博客）：转述 Anthropic skill-formation RCT
    （52 工程师，生成式使用 comprehension 17% 更低 50% vs 67%，概念探究不掉）；
    "you can't write a test for behavior you haven't thought to specify"。
  - S06 Claude Code 代码评审（Anthropic 官方，changes/day 2500→30000、revert
    降 40%）："did a human read code is an imprecise proxy"；"we don't yet have
    circuit breakers that tighten approval when those numbers move"；评审第二职责
    （共享理解）坦承无正式流程。
  - S17 Anthropic 内部研究（官方 survey+53 深访）："paradox of supervision"
    ——有效使用 Claude 需监督，而监督所需编码技能正因 AI 使用退化；>50% 员工
    fully delegate 仅 0-20%；高/战略思维不委托。
  - S03 Shaw-Nave SSRN（preprint 未评审、abstract 二手转述，双重折扣）：三预注册
    实验 N=1372/9593 trials、+25/-15pp、Cohen's h=0.81、错误后 confidence 升。
  - S07 intent-debt / S13 orchestration-tax（Osmani 同谱系）：intent 只能来自人、
    agent 只能编造 rationale；人是 GIL、Amdahl 串行瓶颈，忙≠productive。
  - S15 Andy Clark（Nature Communications 2025，一手 API）：extended mind /
    hybrid thinking systems 观点文。
  - S10 agentic-verification（Substack 二手转述，thekb.eu 明标 without studies）：
    "verification is the bottleneck"；E2E/property/differential；慢/不稳测试让
    agent 学会 retry 而非 fix。
  - 门首篇 X、5 篇 Substack、SSRN direct、claude.com：DNS 劫持不可达，标
    unavailable，不据此下断言。

为什么是新牙（对比现有门禁）：
  reviewer_evaluation(§60) 判单次评审漏斗是否被身份/权威污染（过程保真）；
  evaluation_reliability 判 judge 独立性与复现完整性；serving_signal 判训练/服务
  口径；call_site_integrity 判调用接线；proof_boundary_honesty 判证明范围；
  proactive_authorization 判介入授权——无一判『一个声称有人类评审的流程，是否
  诚实披露评审者仍具备独立判断能力这一前提』。这是过程保真之上的能力存在性
  层次：评审环节存在≠评审者仍有独立观点、能力未被侵蚀、监督未自我消解。
  拦截面独立可迁移（任何『人评审 AI 产出』的流程都适用，KB-META01 会拦才入）。

编译纪律（与 gate_prereg.json 一致，实现前 SHA256 锁存 791f5407…）：
  - 四维语义枚举 yes/no/partial；字面串→flag(R0，避 §56 brittle 根因)；
  - 规则 R0-R6 短路返回，不事后加权(防 Goodhart)；
  - 只判『能力前提是否诚实披露』，不承诺评审真有效——存在≠有效性
    (KB-META01/AUDIT03)；self-reported/preprint 折扣(KB-RSI07)；
  - 遵循 §58 选 A，不接 run_loop。

诚实边界：定位为审读外部工程流程的尺子，不判本仓；本仓判据库是被动工具库。
与 reviewer_evaluation 对象层级不同(能力存在性 vs 过程保真)，拦截面独立。
"""
from __future__ import annotations

from dataclasses import dataclass

_ENUM = frozenset({"yes", "no", "partial"})


@dataclass(frozen=True)
class SupervisionViabilityVerdict:
    claim: str
    independent_view_formed: str
    review_capability_preserved: str
    oversight_not_self_undermining: str
    surface_vs_systemic: str
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_supervision_viability(
    claim: str,
    *,
    independent_view_formed: str,
    review_capability_preserved: str,
    oversight_not_self_undermining: str,
    surface_vs_systemic: str,
) -> SupervisionViabilityVerdict:
    """判一个人类评审流程是否诚实披露评审者的独立判断能力前提（不承诺评审真有效）。

    输入须为语义枚举：四维 ∈ {yes, no, partial}
      - independent_view_formed: 评审者是否在看产出前形成独立观点/预期
      - review_capability_preserved: 生成式使用是否未削弱评审/理解能力
      - oversight_not_self_undermining: 监督所需技能是否未被 AI 退化
      - surface_vs_systemic: 是否未用表面正确冒充系统正确

    规则按优先级短路返回（与 gate_prereg.json R0-R6 一致）：
      R0 任一非枚举 → flag
      R1 independent_view_formed=no → downgrade（认知投降）
      R2 review_capability_preserved=no → downgrade（能力侵蚀）
      R3 oversight_not_self_undermining=no → downgrade（监督悖论自我消解）
      R4 surface_vs_systemic=no → flag（表面冒充系统正确）
      R5 任一 partial → flag（覆盖不全，待核）
      R6 全 yes → ok（只判能力前提自洽，不承诺评审真有效）
    """
    vals = (independent_view_formed, review_capability_preserved,
            oversight_not_self_undermining, surface_vs_systemic)
    if any(v not in _ENUM for v in vals):
        return SupervisionViabilityVerdict(
            claim, *(str(v) for v in vals),
            "flag", "SUPERVISION.INVALID_INPUT",
            "四维须为 yes/no/partial 语义枚举；非法值（含字面串）→ flag，不进内容判定",
        )
    if independent_view_formed == "no":
        return SupervisionViabilityVerdict(
            claim, *vals, "downgrade", "SUPERVISION.NO_INDEPENDENT_VIEW",
            "有评审环节但评审者未形成独立观点——cognitive surrender，输出变成你的输出、无独立可比(73%接受错误答案)，判定打折",
        )
    if review_capability_preserved == "no":
        return SupervisionViabilityVerdict(
            claim, *vals, "downgrade", "SUPERVISION.CAPABILITY_ERODED",
            "评审/理解能力被生成式使用侵蚀(skill-formation 17%lower；概念探究不掉)——评审能力被它要评审的工具削弱，判定打折",
        )
    if oversight_not_self_undermining == "no":
        return SupervisionViabilityVerdict(
            claim, *vals, "downgrade", "SUPERVISION.PARADOX",
            "监督悖论自我消解：监督所需技能正被 AI 退化，却仍声称可靠监督——元层矛盾(paradox of supervision)，判定打折",
        )
    if surface_vs_systemic == "no":
        return SupervisionViabilityVerdict(
            claim, *vals, "flag", "SUPERVISION.SURFACE_AS_SYSTEMIC",
            "用『有人读代码/测试全绿/表面正确』冒充系统正确——imprecise proxy、无 revert/incident 断路器，待核",
        )
    if any(v == "partial" for v in vals):
        return SupervisionViabilityVerdict(
            claim, *vals, "flag", "SUPERVISION.PARTIAL",
            "监督可行性能力前提覆盖不全(partial)——拦截面存在但缺口未补齐，待核",
        )
    return SupervisionViabilityVerdict(
        claim, *vals, "ok", "SUPERVISION.SELF_CONSISTENT",
        "四维能力前提声明自洽——只判声明诚实存在，不承诺评审真有效(存在≠有效性)",
    )


def live_regression() -> dict:
    """8 个活体样例回归——对齐 gate_prereg.json 的 R0-R6 预期。"""
    base = dict(independent_view_formed="yes", review_capability_preserved="yes",
                oversight_not_self_undermining="yes", surface_vs_systemic="yes")
    cases = {
        "no_independent_view": dict(base, independent_view_formed="no"),
        "capability_eroded": dict(base, review_capability_preserved="no"),
        "paradox": dict(base, oversight_not_self_undermining="no"),
        "surface_as_systemic": dict(base, surface_vs_systemic="no"),
        "partial": dict(base, surface_vs_systemic="partial"),
        "self_consistent": dict(base),
        "literal_string": dict(base, independent_view_formed="我们有人类评审所以质量有保障"),
        "priority_view_over_capability": dict(base, independent_view_formed="no", review_capability_preserved="no"),
    }
    out = {}
    for name, kw in cases.items():
        v = check_supervision_viability("claim:" + name, **kw)
        out[name] = {"action": v.action, "code": v.code}
    expected = {
        "no_independent_view": ("downgrade", "SUPERVISION.NO_INDEPENDENT_VIEW"),
        "capability_eroded": ("downgrade", "SUPERVISION.CAPABILITY_ERODED"),
        "paradox": ("downgrade", "SUPERVISION.PARADOX"),
        "surface_as_systemic": ("flag", "SUPERVISION.SURFACE_AS_SYSTEMIC"),
        "partial": ("flag", "SUPERVISION.PARTIAL"),
        "self_consistent": ("ok", "SUPERVISION.SELF_CONSISTENT"),
        "literal_string": ("flag", "SUPERVISION.INVALID_INPUT"),
        "priority_view_over_capability": ("downgrade", "SUPERVISION.NO_INDEPENDENT_VIEW"),
    }
    ok = all(out[k]["action"] == expected[k][0] and out[k]["code"] == expected[k][1] for k in expected)
    return {"cases": out, "expected": expected, "all_match": ok}
