"""认知升级层的回归测试：自主洞见 + 理性决策 + 边界随能力移动。"""
from __future__ import annotations

import math
import random
import unittest

from svagent.insight import (
    CalibratedConfidence, CognitiveLoop, DecisionConfig, Fingerprint, Insight,
    InsightEngine, Verdict, _blind_spots, _calibration_pool, _elder_corpus,
    _passed, _test_set, fingerprint, profile_of, rational_decide,
)


class TestFingerprint(unittest.TestCase):
    def test_fingerprint_is_deterministic_and_symbolic(self):
        f1 = fingerprint("1998年我在镇上的供销社上班。")
        f2 = fingerprint("1998年我在镇上的供销社上班。")
        self.assertEqual(f1.values, f2.values)
        self.assertIn("avg_len", f1.values)
        self.assertTrue(all(isinstance(v, float) for v in f1.values.values()))

    def test_profile_averages_corpus(self):
        fp = profile_of(["我小时候在村里。", "后来去了镇上上班。"])
        self.assertGreater(fp.values["avg_len"], 0)
        self.assertIn("time_ratio", fp.values)

    def test_distance_symmetric(self):
        a, b = fingerprint("短句。"), fingerprint("这是一个非常非常长的句子用来测试。")
        self.assertAlmostEqual(a.distance_to(b)["avg_len"], b.distance_to(a)["avg_len"])


class TestInsightDiscovery(unittest.TestCase):
    def setUp(self):
        self.engine = InsightEngine(_elder_corpus())

    def test_discovers_high_separation_dimensions(self):
        found = self.engine.discover(_blind_spots(), _passed(), min_auc=0.85)
        self.assertGreater(len(found), 0)
        self.assertTrue(all(f.auc >= 0.85 for f in found))
        # 系统自动找到的维度中应包含区分度最高的句长
        self.assertEqual(found[0].dimension, "avg_len")
        self.assertGreater(found[0].auc, 0.95)

    def test_to_signal_bounded_and_monotonic_around_threshold(self):
        found = self.engine.discover(_blind_spots(), _passed())[0]
        prof = self.engine.profile
        below = fingerprint("短。").distance_to(prof)[found.dimension]
        above = fingerprint("这是一个特别特别长的句子" * 5).distance_to(prof)[found.dimension]
        # 低于阈值的信号 < 高于阈值的信号
        sig_below = 1 / (1 + math.exp(-max(-40, min(40,
            (below - found.threshold) / max(1e-4, abs(found.threshold) * 0.25)))))
        sig_above = found.to_signal("这是一个特别特别长的句子" * 5, prof)
        self.assertLess(sig_below, sig_above)
        self.assertTrue(0.0 <= found.to_signal("短。", prof) <= 1.0)

    def test_candidate_dimensions_are_enumerated(self):
        self.assertGreaterEqual(len(self.engine.discover(_blind_spots(), _passed())), 1)


class TestRationalDecision(unittest.TestCase):
    def test_extreme_scores_trigger_auto_decision(self):
        cfg = DecisionConfig()
        # p_bad 极低 → ACCEPT；极高 → REJECT
        self.assertEqual(rational_decide(0.02, cfg).action, "ACCEPT")
        self.assertEqual(rational_decide(0.97, cfg).action, "REJECT")

    def test_uncertain_score_escalates(self):
        # 中间区间交人（这正是 "边界" 所在）
        self.assertEqual(rational_decide(0.35, DecisionConfig()).action, "ESCALATE")

    def test_cost_config_shifts_boundary(self):
        # 人工成本升高 → 更倾向自动决策（边界外移）
        cheap = rational_decide(0.5, DecisionConfig(cost_human=2.0))
        expensive = rational_decide(0.5, DecisionConfig(cost_human=60.0))
        self.assertEqual(cheap.action, "ESCALATE")
        self.assertNotEqual(expensive.action, "ESCALATE")

    def test_expected_utility_is_consistent(self):
        d = rational_decide(0.5)
        self.assertAlmostEqual(sum(d.eu.values()),
                               -0.5 * 100 - 0.5 * 30 - 12)


class TestCalibration(unittest.TestCase):
    def test_smoothing_guards_unseen_bins(self):
        c = CalibratedConfidence()
        self.assertEqual(c.p_bad(0.9), 0.5)  # 未见过 → 保守 0.5
        c.fit([(0.9, True)] * 10)
        self.assertGreater(c.p_bad(0.9), 0.8)

    def test_calibration_moves_p_bad_with_evidence(self):
        c = CalibratedConfidence()
        c.fit([(0.1, False)] * 10)
        self.assertLess(c.p_bad(0.1), 0.2)


class TestBoundaryMovement(unittest.TestCase):
    def test_escalate_rate_decreases_with_capability(self):
        corpus, blind, passed, test = _elder_corpus(), _blind_spots(), _passed(), _test_set()
        rng = random.Random(20261121)
        pool = _calibration_pool(per_class=40)
        rng.shuffle(pool)

        loop = CognitiveLoop(corpus)
        loop.discover_insights(blind, passed)
        loop.calibrate([])
        first = loop.measure(test, capability=3)
        loop.calibrate(pool[:80])
        last = loop.measure(test, capability=13)
        self.assertGreater(last.auto_rate, first.auto_rate)
        self.assertLess(last.escalate_rate, first.escalate_rate)
        self.assertLessEqual(last.error_rate, 0.20)  # 边界外移但错误受控

    def test_ablation_without_insights_stays_at_full_escalation(self):
        corpus, blind, passed, test = _elder_corpus(), _blind_spots(), _passed(), _test_set()
        # 无洞见：信号全 0.5，校准后 p 都回落到中间 → 100% 交人
        loop = CognitiveLoop(corpus)
        loop.calibrate(_calibration_pool(per_class=40))
        m = loop.measure(test, capability=0)
        self.assertEqual(m.escalate_rate, 1.0)
        self.assertEqual(m.auto_rate, 0.0)

    def test_full_pipeline_outperforms_ablation(self):
        corpus, blind, passed, test = _elder_corpus(), _blind_spots(), _passed(), _test_set()
        rng = random.Random(1)
        pool = _calibration_pool(per_class=40)
        rng.shuffle(pool)
        full = CognitiveLoop(corpus)
        full.discover_insights(blind, passed)
        full.calibrate(pool[:80])
        m = full.measure(test, capability=13)
        self.assertGreater(m.auto_rate, 0.5)  # 完整能力显著外移边界


if __name__ == "__main__":
    unittest.main(verbosity=2)
