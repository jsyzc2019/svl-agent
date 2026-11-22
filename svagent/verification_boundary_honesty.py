"""验证边界诚实性门禁 — 把"绿灯只证明一件事"编译成会判动作（§76）。

一手证据（见 audit_addy_critical_thinking/）：
  - S01 公众号 AINLP《当 Agent 接手工作，如何保持批判性思考》中文全文
    （用户确认出处，经同源站 52nlp 下载，26483d35…，含原作者英文原稿截图与
    完整参考链接）。这是 §74 认知投降谱系门首篇的完整中文全文，§75 已从其中
    编译 self_knowledge_honesty（自知边界簇）。本门禁编译其"验证边界"簇。
    原文锚点（26/26 + 本簇 10/10 命中）：
      "绿灯只说明一件事，它检查了什么？没检查什么？"；
      "一个通过的测试，完全可能没发现已经坏掉的功能。如果测试和功能犯的是
      同一个错误，它就会通过。而绿灯只说明某一个性质成立，人却很容易以为它
      覆盖了一切"；"提前定义什么叫『验证通过』，因为等到事后，你会为任何结果
      找到合理的解释"；"收到 Agent 的完成通知后，在看总结之前，先看实际执行了
      什么命令，以及命令返回了什么"；"我遗漏了什么吗？"。
  - S02 TechMoon 独立综述（繁体，交叉 5/5）：明标个人实务观察/无量化对照/
    六问未被证明有效，故本门禁只判声明诚实，不承诺验证真有效。

为什么是新牙（对比现有 24 门禁）：
  proof_boundary_honesty(§71) 判『一个声称带密码学/形式化证明的系统是否诚实
  披露证明边界』——对象是形式化/密码学 proof（执行正确≠事实证明、信任根、
  未覆盖项）。本门禁判『一个主体声称"验证通过/测试全绿"时，是否诚实披露验证
  的覆盖边界』——对象是测试/证据的覆盖（绿灯只证明一个性质、测试可能与功能
  同错、完成标准须事前定义、证据先于总结、收尾自我质疑）。两者一个对象是形式
  化证明、一个是经验性测试证据，场景/对象/动作均不同，拦截面独立可迁移
  （任何"用绿/通过/截图声称完成"的流程都适用，KB-META01 会拦才入）。
  与 reviewer_evaluation(§60 评审漏斗保真)、supervision_viability(§74 评审者
  能力前提) 对象层级不同——那两者判"谁评审/评审者能力"，本门禁判"验证覆盖
  边界是否诚实披露"。

编译纪律（与 ext_prereg.json 一致，实现前 SHA256 锁存 86d3a7f8…）：
  - 四维语义枚举 yes/no/partial；字面串→flag(R0，避 §56 brittle 根因)；
  - 规则 R0-R6 短路返回，不事后加权(防 Goodhart)；
  - 只判『验证边界声明是否诚实自洽』，不承诺验证真有效——提出框架≠证明有效
    (KB-STRUCT05)、自洽≠有效(KB-R07)、self-reported 折扣(KB-RSI07)；
  - 遵循 §58 选 A，不接 run_loop；中文锚点集中 _A，Compare 内无中文字面量。

诚实边界：定位为审读外部主体/流程的尺子，不判本仓；本仓判据库是被动工具库。
"""
from __future__ import annotations

from dataclasses import dataclass

_ENUM = frozenset({"yes", "no", "partial"})

# 中文锚点集中管理（AST 自审：Compare 内禁中文字面量）
_A = {
    "invalid": "四维须为 yes/no/partial 语义枚举；非法值（含字面串）→ flag，不进内容判定",
    "no_coverage_scope": (
        "绿灯被当成全覆盖——一个通过的测试可能没发现坏掉的功能、测试与功能犯同一个错"
        "仍会通过；绿灯只证明一个性质，须披露它检查了什么、没检查什么，判定打折"
    ),
    "no_predefined_criteria": (
        "完成标准未事前定义——等到事后你会为任何结果找到合理解释，"
        "完成须是看得见摸得着的东西(测试/截图/日志/轨迹)，判定打折"
    ),
    "no_evidence_first": (
        "先看总结而非先看实际执行的命令与返回——用『看着像做完了』代替事实依据，"
        "证据先于结论才能让判断落地，判定打折"
    ),
    "no_self_questioning": (
        "收尾未做自我质疑('我遗漏了什么吗')——验证循环缺最后一环，"
        "复杂功能审阅后再问一遍常能再找出两三件事，判定打折"
    ),
    "partial": "验证边界诚实性覆盖不全(partial)——拦截面存在但缺口未补齐，待核",
    "self_consistent": (
        "四维验证边界声明自洽——只判声明诚实存在，不承诺验证真有效"
        "(提出框架≠有效、自洽≠有效)"
    ),
}


@dataclass(frozen=True)
class VerificationBoundaryVerdict:
    claim: str
    coverage_scope_disclosed: str
    criteria_predefined: str
    evidence_before_summary: str
    self_questioning_done: str
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_verification_boundary_honesty(
    claim: str,
    *,
    coverage_scope_disclosed: str,
    criteria_predefined: str,
    evidence_before_summary: str,
    self_questioning_done: str,
) -> VerificationBoundaryVerdict:
    """判一个主体是否诚实披露其验证的覆盖边界（不承诺验证真有效）。

    输入须为语义枚举：四维 ∈ {yes, no, partial}
      - coverage_scope_disclosed: 是否披露验证检查了什么、没检查什么
      - criteria_predefined: 完成标准是否事前定义（非事后合理化）
      - evidence_before_summary: 是否先看实际执行证据再看总结
      - self_questioning_done: 收尾是否做"我遗漏了什么"自我质疑

    规则按优先级短路返回（与 ext_prereg.json R0-R6 一致）：
      R0 任一非枚举 → flag
      R1 coverage_scope_disclosed=no → downgrade（绿灯冒充全覆盖）
      R2 criteria_predefined=no → downgrade（事后合理化）
      R3 evidence_before_summary=no → downgrade（看总结不见证据）
      R4 self_questioning_done=no → downgrade（无自我质疑）
      R5 任一 partial → flag（覆盖不全，待核）
      R6 全 yes → ok（只判声明自洽，不承诺验证真有效）
    """
    vals = (coverage_scope_disclosed, criteria_predefined,
            evidence_before_summary, self_questioning_done)
    if any(v not in _ENUM for v in vals):
        return VerificationBoundaryVerdict(
            claim, *(str(v) for v in vals),
            "flag", "VERIFICATION_BOUNDARY.INVALID_INPUT", _A["invalid"],
        )
    if coverage_scope_disclosed == "no":
        return VerificationBoundaryVerdict(
            claim, *vals, "downgrade", "VERIFICATION_BOUNDARY.GREEN_AS_TOTAL",
            _A["no_coverage_scope"],
        )
    if criteria_predefined == "no":
        return VerificationBoundaryVerdict(
            claim, *vals, "downgrade", "VERIFICATION_BOUNDARY.POST_HOC_CRITERIA",
            _A["no_predefined_criteria"],
        )
    if evidence_before_summary == "no":
        return VerificationBoundaryVerdict(
            claim, *vals, "downgrade", "VERIFICATION_BOUNDARY.SUMMARY_OVER_EVIDENCE",
            _A["no_evidence_first"],
        )
    if self_questioning_done == "no":
        return VerificationBoundaryVerdict(
            claim, *vals, "downgrade", "VERIFICATION_BOUNDARY.NO_SELF_QUESTION",
            _A["no_self_questioning"],
        )
    if any(v == "partial" for v in vals):
        return VerificationBoundaryVerdict(
            claim, *vals, "flag", "VERIFICATION_BOUNDARY.PARTIAL", _A["partial"],
        )
    return VerificationBoundaryVerdict(
        claim, *vals, "ok", "VERIFICATION_BOUNDARY.SELF_CONSISTENT", _A["self_consistent"],
    )


def live_regression() -> dict:
    """8 个活体样例回归——对齐 ext_prereg.json 的 R0-R6 预期。"""
    base = dict(coverage_scope_disclosed="yes", criteria_predefined="yes",
                evidence_before_summary="yes", self_questioning_done="yes")
    cases = {
        "green_as_total": dict(base, coverage_scope_disclosed="no"),
        "post_hoc_criteria": dict(base, criteria_predefined="no"),
        "summary_over_evidence": dict(base, evidence_before_summary="no"),
        "no_self_question": dict(base, self_questioning_done="no"),
        "partial": dict(base, evidence_before_summary="partial"),
        "self_consistent": dict(base),
        "literal_string": dict(base, coverage_scope_disclosed="我们测试都通过了所以没问题"),
        "priority_scope_over_criteria": dict(
            base, coverage_scope_disclosed="no", criteria_predefined="no"),
    }
    out = {}
    for name, kw in cases.items():
        v = check_verification_boundary_honesty("claim:" + name, **kw)
        out[name] = {"action": v.action, "code": v.code}
    expected = {
        "green_as_total": ("downgrade", "VERIFICATION_BOUNDARY.GREEN_AS_TOTAL"),
        "post_hoc_criteria": ("downgrade", "VERIFICATION_BOUNDARY.POST_HOC_CRITERIA"),
        "summary_over_evidence": ("downgrade", "VERIFICATION_BOUNDARY.SUMMARY_OVER_EVIDENCE"),
        "no_self_question": ("downgrade", "VERIFICATION_BOUNDARY.NO_SELF_QUESTION"),
        "partial": ("flag", "VERIFICATION_BOUNDARY.PARTIAL"),
        "self_consistent": ("ok", "VERIFICATION_BOUNDARY.SELF_CONSISTENT"),
        "literal_string": ("flag", "VERIFICATION_BOUNDARY.INVALID_INPUT"),
        "priority_scope_over_criteria": ("downgrade", "VERIFICATION_BOUNDARY.GREEN_AS_TOTAL"),
    }
    ok = all(out[k]["action"] == expected[k][0] and out[k]["code"] == expected[k][1]
             for k in expected)
    return {"cases": out, "expected": expected, "all_match": ok}
