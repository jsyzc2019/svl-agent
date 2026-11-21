"""审查者评估漏斗保真门禁测试（§60：从 Claude Code 验证一文编译）。

含活体回归逐场景 + 判据自咬回归（控制流曾漏两处 return）+ R0 输入校验。
"""
import unittest

from svagent.reviewer_evaluation import (
    ReviewEvalVerdict, check_review_evaluation, live_regression,
)


def _base(**kw):
    b = dict(
        staged_recall=True, raw_recall=0.9, post_verification_recall=0.85,
        final_recall=0.8, stable_control_used=True, tuning_test_separated=True,
        answer_key_scored=True,
    )
    b.update(kw)
    return b


class TestReviewerEvaluation(unittest.TestCase):
    def test_credible_full_practice(self):
        v = check_review_evaluation("文章完整做法", **_base())
        self.assertEqual((v.action, v.code), ("ok", "REVIEW_EVAL.CREDIBLE"))

    def test_single_end_to_end_blocked(self):
        # 最硬的一条：三阶段压成单一分数 = block
        v = check_review_evaluation("单一分数", **_base(
            staged_recall=False, post_verification_recall=None, final_recall=None))
        self.assertEqual((v.action, v.code), ("block", "REVIEW_EVAL.SINGLE_END_TO_END"))

    def test_no_stable_control_downgraded(self):
        v = check_review_evaluation("无对照", **_base(stable_control_used=False))
        self.assertEqual((v.action, v.code), ("downgrade", "REVIEW_EVAL.NO_STABLE_CONTROL"))

    def test_tuning_test_leak_downgraded(self):
        v = check_review_evaluation("泄漏", **_base(tuning_test_separated=False))
        self.assertEqual((v.action, v.code), ("downgrade", "REVIEW_EVAL.TUNING_TEST_LEAK"))

    def test_no_answer_key_downgraded(self):
        v = check_review_evaluation("无答案键", **_base(answer_key_scored=False))
        self.assertEqual((v.action, v.code), ("downgrade", "REVIEW_EVAL.NO_ANSWER_KEY"))

    def test_funnel_inverted_flagged(self):
        v = check_review_evaluation("倒挂", **_base(raw_recall=0.7, final_recall=0.95))
        self.assertEqual((v.action, v.code), ("flag", "REVIEW_EVAL.FUNNEL_INVERTED"))

    def test_multiple_downgrade_flags_combined(self):
        # 多个口径缺口并存 → 组合代号，不漏判
        v = check_review_evaluation("多重缺口", **_base(
            stable_control_used=False, tuning_test_separated=False, answer_key_scored=False))
        self.assertEqual(v.action, "downgrade")
        self.assertIn("NO_STABLE_CONTROL", v.code)
        self.assertIn("TUNING_TEST_LEAK", v.code)
        self.assertIn("NO_ANSWER_KEY", v.code)

    def test_literal_string_rejected(self):
        v = check_review_evaluation("brittle", **_base(staged_recall="yes"))
        self.assertEqual((v.action, v.code), ("flag", "REVIEW_EVAL.NON_SEMANTIC_INPUT"))

    def test_recall_out_of_range_rejected(self):
        v = check_review_evaluation("越界", **_base(raw_recall=1.5))
        self.assertEqual((v.action, v.code), ("flag", "REVIEW_EVAL.NON_SEMANTIC_INPUT"))

    def test_bool_recall_rejected(self):
        # bool 是 int 子类，须显式排除
        v = check_review_evaluation("bool recall", **_base(raw_recall=True))
        self.assertEqual((v.action, v.code), ("flag", "REVIEW_EVAL.NON_SEMANTIC_INPUT"))

    def test_none_recall_allowed(self):
        # 分阶段为真但某些 recall 未提供：allow（不强制数值）
        v = check_review_evaluation("部分缺失", **_base(post_verification_recall=None))
        self.assertEqual(v.action, "ok")

    def test_rule_priority_r0_before_r1(self):
        # 非法 staged_recall + 未分阶段：R0 输入校验优先于 R1
        v = check_review_evaluation("双错", **_base(staged_recall="no"))
        self.assertEqual(v.code, "REVIEW_EVAL.NON_SEMANTIC_INPUT")

    def test_verdict_is_frozen(self):
        v = check_review_evaluation("冻结", **_base())
        self.assertIsInstance(v, ReviewEvalVerdict)
        with self.assertRaises(Exception):
            v.action = "block"

    def test_live_regression_all_passed(self):
        r = live_regression()
        self.assertTrue(r["all_passed"])
        self.assertEqual(len(r["cases"]), 8)
        self.assertTrue(all(r["checks"].values()))


if __name__ == "__main__":
    unittest.main()
