"""对复盘机制的独立审计测试：固化门禁、分类、反哺的边界发现。"""
import unittest

from svagent.retro_audit import (
    audit_1_gate, audit_2_classifier, audit_3_worked_failed,
    audit_4_feedback_loop, audit_5_three_sentences,
)


class TestRetroAudit(unittest.TestCase):
    def test_gate_form_checks_pass(self):
        a = audit_1_gate()
        self.assertTrue(a["passed"])
        self.assertTrue(a["checks"]["无先验被拒"])
        self.assertTrue(a["checks"]["时序倒挂被拒"])
        # 已知弱点被如实暴露
        self.assertTrue(a["checks"]["空泛先验被放行_弱点"])

    def test_classifier_explicit_marks_robust(self):
        a = audit_2_classifier()
        self.assertTrue(a["passed"])
        self.assertTrue(a["checks"]["关键词无标记→unclassified"])
        self.assertTrue(a["checks"]["大写FIX→fix"])
        # 深位标记漏判被如实暴露
        self.assertTrue(a["checks"]["深位标记漏判_弱点"])

    def test_worked_failed_hollowness_confirmed(self):
        """元教训：framework 轨迹的经验/教训抽取仍空洞——这项预期'失败'(缺陷存在)。"""
        a = audit_3_worked_failed()
        self.assertFalse(a["passed"])  # 缺陷确实存在
        self.assertEqual(a["framework_specific_worked"], 0)
        self.assertEqual(a["failed_total"], 0)
        self.assertGreater(a["n_cognitive_corrections"], 0)

    def test_feedback_loop_landed(self):
        a = audit_4_feedback_loop()
        self.assertTrue(a["passed"])
        self.assertEqual(a["lessons_emitted"], a["lessons_in_store"])
        self.assertEqual(a["fix_lessons"], a["fix_to_pdca_opps"])

    def test_three_sentences_direction_affirmed(self):
        a = audit_5_three_sentences()
        self.assertTrue(a["passed"])
        for s in a["sentences"]:
            self.assertTrue(s["direction_correct"])
            self.assertIn(s["evidence_strength"], ["强", "中", "中偏弱", "弱"])


if __name__ == "__main__":
    unittest.main()
