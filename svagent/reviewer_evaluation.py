"""审查者评估漏斗保真门禁 — 从 Claude Code 验证一文 line 122-123 编译（§60）。

一手来源（audit_claude_verify/article.txt，Addy Osmani，2026-11-16，source.sha256 锁存）：
  "We also evaluated the recall rate for raw findings, post-verification, and
  final review separately. This lets us see if the system is losing bugs it had
  already found. Any evaluation that treats all these as one end-to-end score
  won't capture this nuance."（line 123）
  "They use merged and stable changes as a control to prevent over-flagging.
  Their tuning set is split out from the fixed test set..."（line 122）

本仓缺口（audit_claude_verify/result.json V10 reviewer_evaluation=false）：
  finance_blind_test.py / knowledge_base.py 里的 recall 是检索/盲测指标，
  本仓从未判过『评估一个审查者时是否分阶段量 recall、是否有稳定集对照、tuning/test 是否分离』。

扬长避短（KB-META01 复述 vs 长牙）：
  - 只借工程纪律（分阶段评估 / 稳定集对照 / 口径对等），不复现其内部评测、不把 10 points 当证据。
  - 语义布尔 + [0,1] 数值 + 写死规则 + 纯函数，非法输入 → flag（避开 §56 brittle 根因 KB-AUDIT01）。
  - 会拦（三阶段压成一分数 → block）、会判（无对照/tuning泄漏/无answer key → downgrade）、
    会待核（漏斗倒挂/越界 → flag）、会放行（分阶段+对照+分离+计分 → ok）。
  - 锚定 KB-AUDIT04 / KB-STRUCT07 / KB-AUDIT02 并加固 support（认知域协同）。

诚实边界：只判『评估方案的分阶段/对照/分离/计分口径是否自洽』，不判对象对错、
不替代实质证据；方案细节须调用方如实声明；由外部工程博客启发，按 KB-STRUCT02
同构打折，不给本仓框架独立背书；遵循 §58 用户选 A，不接入 run_loop。活体样例用于
机制回归，非复现外部评测。
"""
from __future__ import annotations

from dataclasses import dataclass

_BOOL_FIELDS = ("staged_recall", "stable_control_used", "tuning_test_separated", "answer_key_scored")
_RECALL_FIELDS = ("raw_recall", "post_verification_recall", "final_recall")


@dataclass(frozen=True)
class ReviewEvalVerdict:
    claim: str
    staged_recall: bool
    action: str        # ok | downgrade | flag | block
    code: str
    flags: tuple
    message: str


def check_review_evaluation(
    claim: str,
    *,
    staged_recall: bool,
    raw_recall: float | None,
    post_verification_recall: float | None,
    final_recall: float | None,
    stable_control_used: bool,
    tuning_test_separated: bool,
    answer_key_scored: bool,
) -> ReviewEvalVerdict:
    """判定一份『审查者评估方案』是否口径自洽、能看出系统丢没丢 bug。

    规则按优先级写死（与 reviewer_eval_prereg.json 一致）：
      R0 非法输入（非 bool / recall 越界）→ flag
      R1 三阶段压成单一端到端分数 → block（看不出丢了已找到的 bug）
      R2 无稳定集对照 → downgrade（无法防 over-flagging）
      R3 tuning 与 fixed test 未分离 → downgrade（过拟合 eval）
      R4 未按 answer key 计分 → downgrade（分数口径失真）
      R5 漏斗倒挂（final > raw）→ flag（口径可疑待核）
      R6 全自洽 → ok
    """
    # R0：语义输入校验优先——非 bool / recall 越界一律 flag，不进入内容判定
    bools = (staged_recall, stable_control_used, tuning_test_separated, answer_key_scored)
    if not all(isinstance(v, bool) for v in bools):
        return ReviewEvalVerdict(
            claim, bool(staged_recall) if isinstance(staged_recall, bool) else False,
            "flag", "REVIEW_EVAL.NON_SEMANTIC_INPUT", (),
            "方案开关须为布尔；拒绝对字面串判定（避开 brittle 根因，KB-AUDIT01）",
        )
    for v in (raw_recall, post_verification_recall, final_recall):
        if v is not None:
            if not isinstance(v, (int, float)) or isinstance(v, bool) or not (0.0 <= v <= 1.0):
                return ReviewEvalVerdict(
                    claim, staged_recall, "flag", "REVIEW_EVAL.NON_SEMANTIC_INPUT", (),
                    "recall 须为 [0,1] 数值或 None；越界值拒绝判定",
                )

    flags = []

    # R1：把 raw/post/final 压成单一端到端分数——最硬的一条
    if not staged_recall:
        return ReviewEvalVerdict(
            claim, staged_recall, "block", "REVIEW_EVAL.SINGLE_END_TO_END", (),
            "把 raw/post-verification/final 三阶段压成一个端到端分数，看不出系统是否丢了"
            "已找到的 bug——口径失真，必须分阶段评估（文章 line 123，KB-AUDIT04）",
        )

    # R2/R3/R4：三项口径纪律，各自 downgrade
    if not stable_control_used:
        flags.append("NO_STABLE_CONTROL")
    if not tuning_test_separated:
        flags.append("TUNING_TEST_LEAK")
    if not answer_key_scored:
        flags.append("NO_ANSWER_KEY")

    # R5：漏斗倒挂——验证过滤不该让召回凭空变高
    if raw_recall is not None and final_recall is not None and final_recall > raw_recall:
        flags.append("FUNNEL_INVERTED")

    if flags:
        if flags == ["FUNNEL_INVERTED"]:
            return ReviewEvalVerdict(
                claim, staged_recall, "flag", "REVIEW_EVAL.FUNNEL_INVERTED", tuple(flags),
                "final recall 高于 raw recall——验证过滤本应只减不增，漏斗倒挂口径可疑，待核"
                "（文章把三阶段分开正是为抓这种异常）",
            )
        else:
            return ReviewEvalVerdict(
                claim, staged_recall, "downgrade", "REVIEW_EVAL." + "+".join(flags), tuple(flags),
                "评估口径不完整：" + ",".join(flags) + "——判定打折，不可当完整证据",
            )

    # R6：全自洽（flags 为空才会走到这里）
    return ReviewEvalVerdict(
        claim, staged_recall, "ok", "REVIEW_EVAL.CREDIBLE", (),
        "分阶段 recall + 稳定集对照 + tuning/test 分离 + answer key 计分 + 漏斗不倒挂——"
        "评估方案口径自洽（仍不替代实质证据）",
    )


def live_regression() -> dict:
    """活体回归：8 场景对应预注册 8 样例。"""
    base = dict(
        raw_recall=0.9, post_verification_recall=0.85, final_recall=0.8,
        stable_control_used=True, tuning_test_separated=True, answer_key_scored=True,
    )
    cases = [
        ("文章完整做法", dict(base, staged_recall=True), "ok", "REVIEW_EVAL.CREDIBLE"),
        ("单一端到端分数", dict(base, staged_recall=False, post_verification_recall=None, final_recall=None),
         "block", "REVIEW_EVAL.SINGLE_END_TO_END"),
        ("无稳定集对照", dict(base, staged_recall=True, stable_control_used=False),
         "downgrade", "REVIEW_EVAL.NO_STABLE_CONTROL"),
        ("tuning/test未分离", dict(base, staged_recall=True, tuning_test_separated=False),
         "downgrade", "REVIEW_EVAL.TUNING_TEST_LEAK"),
        ("不按answer key计分", dict(base, staged_recall=True, answer_key_scored=False),
         "downgrade", "REVIEW_EVAL.NO_ANSWER_KEY"),
        ("漏斗倒挂", dict(staged_recall=True, raw_recall=0.7, post_verification_recall=0.8,
                       final_recall=0.95, stable_control_used=True,
                       tuning_test_separated=True, answer_key_scored=True),
         "flag", "REVIEW_EVAL.FUNNEL_INVERTED"),
        ("字面串对照", dict(base, staged_recall="yes"), "flag", "REVIEW_EVAL.NON_SEMANTIC_INPUT"),
        ("recall越界", dict(base, staged_recall=True, raw_recall=1.5),
         "flag", "REVIEW_EVAL.NON_SEMANTIC_INPUT"),
    ]
    results, checks = {}, {}
    for name, kw, exp_action, exp_code in cases:
        v = check_review_evaluation(name, **kw)
        results[name] = {"action": v.action, "code": v.code}
        checks[name] = (v.action == exp_action and v.code == exp_code)
    return {"cases": results, "checks": checks, "all_passed": all(checks.values())}
