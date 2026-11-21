"""双色球随机性检验的工具函数测试（固化方法纪律，不固化数据结论）。"""
import unittest
import numpy as np

from svagent.ssq_randomness import (
    chi2_gof, feature_vector, draw_sequence, ks_distance, _lag1_autocorr,
)
import random


class TestStatTools(unittest.TestCase):
    def test_chi2_gof_perfect_fit(self):
        # 观测完全等于期望 → 卡方为 0
        obs = [100, 100, 100]
        self.assertAlmostEqual(chi2_gof(obs, [1 / 3] * 3), 0.0, places=6)

    def test_ks_distance_identical(self):
        a = [1, 2, 3, 4, 5]
        self.assertAlmostEqual(ks_distance(a, a), 0.0, places=6)

    def test_ks_distance_disjoint(self):
        a = [0, 0, 0]
        b = [10, 10, 10]
        self.assertAlmostEqual(ks_distance(a, b), 1.0, places=6)

    def test_lag1_autocorr_random_near_zero(self):
        rng = random.Random(1)
        xs = [rng.random() for _ in range(5000)]
        self.assertLess(abs(_lag1_autocorr(xs)), 0.05)

    def test_draw_sequence_valid(self):
        rng = random.Random(42)
        reds, blues = draw_sequence(rng, 100)
        self.assertEqual(len(reds), 100)
        self.assertEqual(len(blues), 100)
        for r in reds:
            self.assertEqual(len(r), 6)
            self.assertEqual(len(set(r)), 6)  # 无放回
            self.assertTrue(all(1 <= x <= 33 for x in r))
        self.assertTrue(all(1 <= b <= 16 for b in blues))

    def test_feature_vector_counts(self):
        rng = random.Random(7)
        reds, blues = draw_sequence(rng, 50)
        feat = feature_vector(reds, blues)
        self.assertEqual(sum(feat["red_count"]), 50 * 6)
        self.assertEqual(sum(feat["blue_count"]), 50)
        self.assertEqual(len(feat["red_count"]), 33)
        self.assertEqual(len(feat["blue_count"]), 16)
        self.assertEqual(len(feat["ac_values"]), 50)


if __name__ == "__main__":
    unittest.main()
