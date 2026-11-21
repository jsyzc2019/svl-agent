"""复盘层测试：门禁、复利、反哺闭环的行为固化。"""
import unittest

from svagent.retrospective import (
    DecisionPoint, HindsightGateError, Lesson, ReasoningTrace, Retrospective,
    RetrospectiveStore, lessons_to_opportunities, framework_reflection_trace,
)
from svagent.pdca import PDCALoop


def _valid_trace(tid="t1", tags=None, conf=0.6, corr=None, measures=None):
    return ReasoningTrace(
        trace_id=tid, question="q", prior_belief="可能属实", prior_confidence=conf,
        prior_ts="2026-01-01T09:00:00", outcome_ts="2026-01-31T17:00:00",
        situation_tags=tags if tags is not None else ["macro", "narrative_truth"],
        expected_outcome="属实", actual_outcome="不属实",
        cognitive_corrections=corr if corr is not None else ["数据推翻先验"],
        anti_bias_measures=measures if measures is not None else ["预注册判据"],
    )


class TestHindsightGate(unittest.TestCase):
    """防后知先觉硬门禁：这是复盘层的第一纪律。"""

    def test_no_prior_rejected(self):
        t = _valid_trace()
        t.prior_belief = ""
        r = Retrospective().review(t)
        self.assertFalse(r.admitted)
        self.assertIn("无事前先验", r.rejected_reason)
        self.assertEqual(r.lessons, [])

    def test_missing_timestamps_rejected(self):
        t = _valid_trace()
        t.outcome_ts = ""
        r = Retrospective().review(t)
        self.assertFalse(r.admitted)
        self.assertIn("prior_ts/outcome_ts", r.rejected_reason)

    def test_reversed_chronology_rejected(self):
        """结果早于先验 = 事后编造的先验 → 拒绝。"""
        t = _valid_trace()
        t.prior_ts = "2026-02-01T09:00:00"   # 晚于 outcome
        r = Retrospective().review(t)
        self.assertFalse(r.admitted)
        self.assertIn("时序倒挂", r.rejected_reason)

    def test_no_outcome_rejected(self):
        t = _valid_trace()
        t.actual_outcome = ""
        r = Retrospective().review(t)
        self.assertFalse(r.admitted)

    def test_valid_trace_admitted(self):
        r = Retrospective().review(_valid_trace())
        self.assertTrue(r.admitted)
        self.assertGreater(len(r.lessons), 0)

    def test_gate_raises_directly(self):
        """gate() 直接调用应抛异常，供调用方主动防御。"""
        t = _valid_trace()
        t.prior_belief = ""
        with self.assertRaises(HindsightGateError):
            t.gate()


class TestLessonExtraction(unittest.TestCase):
    def test_correction_yields_pitfall(self):
        r = Retrospective().review(_valid_trace())
        kinds = {l.kind for l in r.lessons}
        self.assertIn("pitfall", kinds)
        self.assertIn("anti_bias", kinds)

    def test_overconfident_prior_yields_calibration_lesson(self):
        t = _valid_trace(conf=0.95)
        r = Retrospective().review(t)
        self.assertTrue(any("先验" in l.action and "0.7" in l.action for l in r.lessons))

    def test_no_tags_yields_tag_lesson(self):
        t = _valid_trace(tags=[])
        r = Retrospective().review(t)
        self.assertTrue(any(l.kind == "method" and "标签" in l.action for l in r.lessons))


class TestStoreAndCompounding(unittest.TestCase):
    def test_same_action_dedup_and_corroboration(self):
        store = RetrospectiveStore()
        rev = Retrospective(store)
        rev.review(_valid_trace("a", measures=["预注册判据"]))
        rev.review(_valid_trace("b", measures=["预注册判据"]))  # 同一措施，独立轨迹
        # 精确匹配 anti_bias 的 action（pitfall 类的 action 也含"预注册判据"字样）
        dup = [l for l in store.lessons.values() if l.kind == "anti_bias"
               and l.action == "复用防偏差措施：预注册判据"]
        self.assertEqual(len(dup), 1)
        self.assertEqual(dup[0].n_supports, 2)
        self.assertGreater(dup[0].confidence, 0.5)

    def test_recall_by_trigger(self):
        store = RetrospectiveStore()
        rev = Retrospective(store)
        rev.review(_valid_trace())
        hits = store.recall(["macro", "narrative_truth"])
        self.assertGreater(len(hits), 0)
        self.assertEqual(store.recall(["unrelated"]), [])

    def test_inject_into_trace_is_idempotent(self):
        store = RetrospectiveStore()
        rev = Retrospective(store)
        rev.review(_valid_trace())
        new = _valid_trace("new", measures=[])
        first = store.inject_into_trace(new)
        second = store.inject_into_trace(new)
        self.assertGreater(len(first), 0)
        self.assertEqual(len(second), 0)  # 注入过的不再重复

    def test_compounding_curve_skips_rejected(self):
        good = _valid_trace("good")
        bad = _valid_trace("bad")
        bad.prior_belief = ""
        curve = RetrospectiveStore().compounding_curve([good, bad, good])
        self.assertEqual(len(curve), 2)  # 被拒的不计入

    def test_confidence_grows_with_more_traces(self):
        t1 = _valid_trace("a", tags=["macro", "cycle_phase", "narrative_truth"],
                          measures=["预注册判据"])
        t2 = _valid_trace("b", tags=["macro", "cycle_phase", "narrative_truth"],
                          measures=["预注册判据"])
        curve = RetrospectiveStore().compounding_curve([t1, t2])
        self.assertGreaterEqual(curve[-1]["avg_confidence"], curve[0]["avg_confidence"])
        self.assertGreaterEqual(curve[-1]["corroborated"], curve[0]["corroborated"])

    def test_save_load_roundtrip(self):
        import tempfile, os
        store = RetrospectiveStore()
        Retrospective(store).review(_valid_trace())
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            store.save(path)
            loaded = RetrospectiveStore.load(path)
            self.assertEqual(len(loaded.lessons), len(store.lessons))
        finally:
            os.unlink(path)


class TestFeedbackToPdca(unittest.TestCase):
    def test_lessons_become_unsymbolizable_opportunities(self):
        store = RetrospectiveStore()
        rev = Retrospective(store)
        rev.review(_valid_trace())
        opps = lessons_to_opportunities(list(store.lessons.values()))
        self.assertGreater(len(opps), 0)
        # 认知教训不可编译成符号判据 → 全部 addressable=False
        self.assertTrue(all(not o.addressable for o in opps))
        self.assertTrue(all(o.kind == "process_gap" for o in opps))

    def test_injected_opportunities_appear_in_identify(self):
        loop = PDCALoop()
        store = RetrospectiveStore()
        rev = Retrospective(store)
        rev.review(_valid_trace())
        opps = lessons_to_opportunities(list(store.lessons.values()))
        loop.inject_opportunities(opps)
        identified = loop.identify()
        procs = [o for o in identified if o.kind == "process_gap"]
        self.assertEqual(len(procs), len(opps))

    def test_injection_is_instance_local(self):
        """两个 PDCALoop 实例不共享注入的机会。"""
        a, b = PDCALoop(), PDCALoop()
        opp = lessons_to_opportunities([Lesson("L", ["x"], "act", "why")])
        a.inject_opportunities(opp)
        self.assertEqual(len([o for o in b.identify() if o.kind == "process_gap"]), 0)


class TestFrameworkReflection(unittest.TestCase):
    """框架逻辑方法的自我反省：scope=framework 与「改进该改进的」三分法。"""

    def test_scope_distinguishes_subject_from_framework(self):
        self.assertEqual(_valid_trace().scope, "subject")  # 默认研究对象
        self.assertEqual(framework_reflection_trace().scope, "framework")

    def test_framework_trace_passes_gate(self):
        """第19节审计锚点早于第20节整改——真时序，门禁应通过。"""
        r = Retrospective().review(framework_reflection_trace())
        self.assertTrue(r.admitted, r.rejected_reason)

    def test_three_way_improvement_audit(self):
        r = Retrospective().review(framework_reflection_trace())
        a = r.improvement_audit
        # 真该改的、虚荣的、不该改的三类都非空——反省不是只挑毛病
        self.assertGreater(len(a["fix"]), 0)
        self.assertGreater(len(a["vanity"]), 0)
        self.assertGreater(len(a["preserve"]), 0)
        self.assertEqual(a["unclassified"], [])  # 所有决策都显式标记了

    def test_real_bug_not_misclassified_as_vanity(self):
        """回归：P0 criterion 符号 bug 含'而非文案'字样，不得被关键词误判成虚荣改进。"""
        r = Retrospective().review(framework_reflection_trace())
        fixes = " ".join(r.improvement_audit["fix"])
        vanity = " ".join(r.improvement_audit["vanity"])
        self.assertIn("criterion", fixes)          # 真 bug 在 fix
        self.assertNotIn("criterion", vanity)      # 不在 vanity

    def test_lessons_carry_improvement_class(self):
        r = Retrospective().review(framework_reflection_trace())
        classes = {l.improvement_class for l in r.lessons}
        self.assertIn("fix", classes)
        self.assertIn("vanity", classes)
        self.assertIn("preserve", classes)
        self.assertTrue(any(l.kind == "keep" for l in r.lessons))

    def test_unclassified_not_guessed(self):
        """无显式标记的决策不得被关键词猜测，归入 unclassified 由人补。"""
        rev = Retrospective()
        d = DecisionPoint("s", "c", "这是真缺陷而非文案")  # 含'文案'但无前缀标记
        self.assertEqual(rev._classify_framework_decision(d), "unclassified")


if __name__ == "__main__":
    unittest.main()
