"""判据来源诚实性门禁 — 把 HarnessPro 的"自生成判据评估自生成改进"编译成会判动作（§77）。

一手证据（见 audit_harnesspro/）：
  - S01 论文 PDF（arXiv:2610.26770v2, Under review, 20 Oct 2026；Tsinghua/Z.AI/SJTU/
    Warwick/Kling AI；SHA256 c633082a…，文本 6cc23e37…）：
    §4.3 label-free：候选 harness 用 LLM 合成的固定测试 S(x)=TestSynth(x,τ_h0(x)) 评估，
      无 ground-truth/official tests/grader feedback。
    Figure 2（论文自己给的诚实证据）：LLM judge 把有缺陷实现判成功（overly optimistic），
      失败召回 41.7%；自生成测试召回 83.3%（仍漏 16.7%）；混淆矩阵横轴用 Official outcome。
    Appendix C.3 指令："No separate reviewer is part of this run" / "do not launch
      another reviewer" / "Empty is only an implementation ... never an answer key"；
      coverage.json 要求记录 "what was not checked, and limitations"。
  - S03 评估说明（一手 release 文档，SHA256 ed99c5c9…）：release 不含 benchmark 数据/
    镜像/权重/凭据；GLM-5.2 evolved snapshots 不在 release，用 GPT-5.5 harness 配
    Claude Code 不复现 GLM 结果——复现边界诚实披露（加分项）。

为什么是新牙（对比现有 25 门禁）：
  proof_boundary_honesty(§71)判形式化/密码学证明边界（承诺锚独立/证明范围）；
  verification_boundary_honesty(§76)判"绿灯只证明一件事"的经验性通过声明；
  finance_blind_test/retrospective 只是文本出现 label-free/召回词，非判据；
  无一判『一个用自生成判据评估自生成改进的系统，是否诚实披露判据的可信度前提』：
    ①判据来源：评估判据是自生成还是外部锚定，是否诚实标注（criterion_origin_disclosed）；
    ②召回边界：自生成判据的失败检出率/漏检率是否披露而非声称全覆盖（recall_boundary_disclosed）；
    ③外部锚定：label-free 有效性是否用外部锚（如官方测试）事后校验并披露（external_anchor_disclosed）；
    ④独立评审缺口：判据自审无独立评审者的事实是否披露（independent_reviewer_gap_disclosed）。
  HarnessPro 是最会自曝这一边界的一手样本，但尺子对象是"任何 self-assessed/self-generated
  criterion 系统"——可迁移、会拦（把自生成判据冒充外部锚/隐藏召回边界/无外部校验还称
  label-free 有效/自审冒充独立评审都拦），KB-META01 会拦才入通过。

编译纪律（与 gate_prereg.json 一致，实现前 SHA256 锁存 ecf7d724…）：
  - 语义枚举；字面串→flag(R0，避 §56 brittle 根因)；
  - 规则 R0-R6 短路返回，不事后加权(防 Goodhart)；
  - 只判『声明是否诚实自洽』，不承诺评估判据真可靠——存在≠有效性(KB-META01/AUDIT03)；
    self-reported 实验数字/未评审 preprint 不采信(KB-RSI07)，preprint 折1。

诚实边界：定位为审读外部"自评估系统"的尺子，不判本仓；遵循 §58 选 A 不接 run_loop。
与 KB-R07（自洽 vs 有效）、proof_boundary_honesty（形式化证明）对象动作不同，拦截面独立。
"""
from __future__ import annotations

from dataclasses import dataclass

_ENUM = frozenset({"yes", "no", "partial"})


@dataclass(frozen=True)
class CriterionOriginVerdict:
    claim: str
    criterion_origin: str
    recall_boundary: str
    external_anchor: str
    independent_reviewer_gap: str
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_criterion_origin_honesty(
    claim: str,
    *,
    criterion_origin_disclosed: str,
    recall_boundary_disclosed: str,
    external_anchor_disclosed: str,
    independent_reviewer_gap_disclosed: str,
) -> CriterionOriginVerdict:
    """判一个自评估系统是否诚实披露其判据的可信度前提（不承诺判据真可靠）。

    输入须为语义枚举：四维 ∈ {yes, no, partial}

    规则按优先级短路返回（与 gate_prereg.json R0-R6 一致）：
      R0 任一非枚举 → flag
      R1 criterion_origin_disclosed=no → downgrade（自生成判据冒充外部锚定）
      R2 recall_boundary_disclosed=no → downgrade（判据召回边界隐藏）
      R3 external_anchor_disclosed=no → downgrade（label-free 有效性无外部锚定披露）
      R4 independent_reviewer_gap_disclosed=no → downgrade（自审冒充独立评审）
      R5 任一 partial → flag
      R6 全 yes → ok（只判声明自洽）
    """
    vals = (criterion_origin_disclosed, recall_boundary_disclosed,
            external_anchor_disclosed, independent_reviewer_gap_disclosed)
    if any(v not in _ENUM for v in vals):
        return CriterionOriginVerdict(
            claim, *(str(v) for v in vals),
            "flag", "CRITERION_ORIGIN.INVALID_INPUT",
            "四维须为 yes/no/partial 语义枚举；非法值（含字面串）→ flag，不进内容判定",
        )
    if criterion_origin_disclosed == "no":
        return CriterionOriginVerdict(
            claim, *vals, "downgrade", "CRITERION_ORIGIN.SELF_AS_ANCHOR",
            "自生成判据冒充外部锚定——评估判据由被评估系统同族合成却不明标来源，主体错位(KB-STRUCT05)，判定打折",
        )
    if recall_boundary_disclosed == "no":
        return CriterionOriginVerdict(
            claim, *vals, "downgrade", "CRITERION_ORIGIN.RECALL_HIDDEN",
            "判据召回边界隐藏(如失败召回仅41.7%~83.3%、仍漏16.7%却声称全覆盖)——自生成判据漏检率不披露，判定打折",
        )
    if external_anchor_disclosed == "no":
        return CriterionOriginVerdict(
            claim, *vals, "downgrade", "CRITERION_ORIGIN.NO_EXTERNAL_ANCHOR",
            "label-free 有效性无外部锚定披露(如混淆矩阵仍用官方测试做横轴却标榜无标签)——有效性靠外部锚事后校验却不披露，判定打折",
        )
    if independent_reviewer_gap_disclosed == "no":
        return CriterionOriginVerdict(
            claim, *vals, "downgrade", "CRITERION_ORIGIN.FAKE_INDEPENDENT_REVIEW",
            "自审冒充独立评审('No separate reviewer is part of this run'却不披露)——判据生成与评审同一主体，判定打折",
        )
    if any(v == "partial" for v in vals):
        return CriterionOriginVerdict(
            claim, *vals, "flag", "CRITERION_ORIGIN.PARTIAL",
            "判据可信度前提披露覆盖不全(partial)——拦截面存在但缺口未补齐，待核",
        )
    return CriterionOriginVerdict(
        claim, *vals, "ok", "CRITERION_ORIGIN.SELF_CONSISTENT",
        "四维判据来源声明自洽——只判声明诚实存在，不承诺评估判据真可靠(存在≠有效性)",
    )


def live_regression() -> dict:
    """7 个活体样例回归——对齐 gate_prereg.json 的 R0-R6 预期。"""
    cases = {
        "self_as_anchor": dict(criterion_origin_disclosed="no", recall_boundary_disclosed="yes", external_anchor_disclosed="yes", independent_reviewer_gap_disclosed="yes"),
        "recall_hidden": dict(criterion_origin_disclosed="yes", recall_boundary_disclosed="no", external_anchor_disclosed="yes", independent_reviewer_gap_disclosed="yes"),
        "no_external_anchor": dict(criterion_origin_disclosed="yes", recall_boundary_disclosed="yes", external_anchor_disclosed="no", independent_reviewer_gap_disclosed="yes"),
        "fake_independent": dict(criterion_origin_disclosed="yes", recall_boundary_disclosed="yes", external_anchor_disclosed="yes", independent_reviewer_gap_disclosed="no"),
        "partial_disclosure": dict(criterion_origin_disclosed="yes", recall_boundary_disclosed="yes", external_anchor_disclosed="partial", independent_reviewer_gap_disclosed="yes"),
        "literal_enum": dict(criterion_origin_disclosed="maybe", recall_boundary_disclosed="yes", external_anchor_disclosed="yes", independent_reviewer_gap_disclosed="yes"),
        "all_good": dict(criterion_origin_disclosed="yes", recall_boundary_disclosed="yes", external_anchor_disclosed="yes", independent_reviewer_gap_disclosed="yes"),
    }
    expects = {
        "self_as_anchor": ("downgrade", "CRITERION_ORIGIN.SELF_AS_ANCHOR"),
        "recall_hidden": ("downgrade", "CRITERION_ORIGIN.RECALL_HIDDEN"),
        "no_external_anchor": ("downgrade", "CRITERION_ORIGIN.NO_EXTERNAL_ANCHOR"),
        "fake_independent": ("downgrade", "CRITERION_ORIGIN.FAKE_INDEPENDENT_REVIEW"),
        "partial_disclosure": ("flag", "CRITERION_ORIGIN.PARTIAL"),
        "literal_enum": ("flag", "CRITERION_ORIGIN.INVALID_INPUT"),
        "all_good": ("ok", "CRITERION_ORIGIN.SELF_CONSISTENT"),
    }
    checks, detail = {}, {}
    for name, inp in cases.items():
        v = check_criterion_origin_honesty("live:" + name, **inp)
        exp_a, exp_c = expects[name]
        detail[name] = f"{v.action}/{v.code}"
        checks[name] = (v.action == exp_a and v.code == exp_c)
    return {"checks": checks, "cases": detail, "all_passed": all(checks.values())}
