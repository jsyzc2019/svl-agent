"""日志估参单元测试。"""
import unittest

from svagent.estimation import (
    CognitiveParams, ParameterEstimator, VerdictRecord,
    _baseline, _prediction_accuracy, sigmoid, simulate_verdicts,
)
from svagent.telos import CognitiveProfile, Goal, World, _batch_run


class TestSigmoidRecords(unittest.TestCase):
    def test_sigmoid(self):
        self.assertAlmostEqual(sigmoid(0), 0.5)
        self.assertGreater(sigmoid(10), 0.99)
        self.assertLess(sigmoid(-10), 0.01)

    def test_simulation_structure(self):
        recs = simulate_verdicts(3.0, 0.2, 200, seed=1)
        self.assertEqual(len(recs), 200)
        # 高辨别力：伪造卡的证据应显著高于真实卡
        pos = [r.evidence for r in recs if r.forged]
        neg = [r.evidence for r in recs if not r.forged]
        self.assertGreater(sum(pos) / len(pos), sum(neg) / len(neg))


class TestEstimator(unittest.TestCase):
    def test_empty(self):
        p = ParameterEstimator().fit([])
        self.assertEqual(p.discernibility, 0.0)

    def test_prediction_beats_baseline(self):
        train = simulate_verdicts(3.0, 0.2, 500, seed=11)
        test = simulate_verdicts(3.0, 0.2, 300, seed=99)
        est = ParameterEstimator().fit(train)
        acc = _prediction_accuracy(est, test)
        self.assertGreater(acc, _baseline(test) + 0.15,
                           f"留出预测 {acc:.0%} 应显著高于基线")

    def test_discernibility_ranks_with_dprime(self):
        """辨别力相对量应随真 d' 单调（绝对值不可辨识，只测排序）。"""
        ests = []
        for dp in (0.6, 1.5, 3.0, 4.0):
            ests.append(ParameterEstimator().fit(simulate_verdicts(dp, 0, 600, seed=7)))
        # AUC 对真 d' 应单调升（AUC 是可观测量，比 slope 可靠）
        aucs = [e.auc for e in ests]
        self.assertEqual(aucs, sorted(aucs), f"AUC 应随d'单调: {aucs}")
        self.assertGreater(aucs[-1], aucs[0] + 0.2)

    def test_criterion_sign_separates_conservative_liberal(self):
        """【审计整改P0】criterion 与生成模型同号：保守者>0，激进者<0。"""
        cons = ParameterEstimator().fit(simulate_verdicts(2.5, 1.5, 600, seed=3))
        lib = ParameterEstimator().fit(simulate_verdicts(2.5, -1.4, 600, seed=3))
        # 修复后：criterion=-b，与真值同号；保守(+1.5)应估出正，激进(-1.4)应估出负
        self.assertGreater(cons.criterion, 0, "保守者 criterion 应为正")
        self.assertLess(lib.criterion, 0, "激进者 criterion 应为负")
        self.assertGreater(cons.criterion, lib.criterion)

    def test_criterion_matches_generative_sign(self):
        """逐点验证：估出的 criterion 符号与生成模型传入的 criterion 一致。"""
        for true_crit in (-2.0, -1.0, 1.0, 2.0):
            est = ParameterEstimator().fit(simulate_verdicts(2.5, true_crit, 800, seed=42))
            self.assertEqual(est.criterion > 0, true_crit > 0,
                             f"真criterion={true_crit} 估出={est.criterion:.2f} 符号须一致")

    def test_auc_in_range(self):
        est = ParameterEstimator().fit(simulate_verdicts(2.0, 0.5, 300, seed=5))
        self.assertTrue(0.0 <= est.auc <= 1.0)
        # 合成日志带 confidence → 真校准 ECE 可算，落在 [0,1]
        self.assertIsNotNone(est.calibration)
        self.assertTrue(0.0 <= est.calibration <= 1.0)

    def test_calibration_is_none_without_confidence(self):
        """无置信度字段时，校准必须如实返回 None，绝不拿 AUC 冒充。"""
        from svagent.estimation import VerdictRecord
        recs = [VerdictRecord(evidence=float(i % 5) - 2, forged=bool(i % 2),
                              rejected=bool(i % 3), confidence=0.5) for i in range(100)]
        est = ParameterEstimator().fit(recs)
        self.assertIsNone(est.calibration, "缺省置信度时校准应为 None")

    def test_calibration_separate_from_discrimination(self):
        """【整改】高辨别的两组，过度自信者校准更低——两维度可分离。"""
        from svagent.estimation import VerdictRecord
        import random as _r
        rng = _r.Random(2026)
        core = []
        for _ in range(600):
            forged = rng.random() < 0.5
            internal = (1.0 if forged else -1.0) + rng.gauss(0, 1)
            evidence = internal + rng.gauss(0, 0.5)
            rejected = internal + rng.gauss(0, 0.3) > 0
            core.append((evidence, forged, rejected))
        acc = sum(int(r == f) for _, f, r in core) / len(core)
        over = [VerdictRecord(e, f, r, 0.95) for e, f, r in core]      # 全报0.95→过度自信
        good = [VerdictRecord(e, f, r, acc) for e, f, r in core]        # 全报真实正确率→校准
        e_over = ParameterEstimator().fit(over)
        e_good = ParameterEstimator().fit(good)
        # 辨别力相近（同一批证据）
        self.assertAlmostEqual(e_over.auc, e_good.auc, delta=0.05)
        # 但校准显著不同：过度自信者更低
        self.assertLess(e_over.calibration, e_good.calibration - 0.1)


class TestBoundaryBridge(unittest.TestCase):
    def test_calibration_maps_to_autonomy(self):
        """高校准 → 少观察 → 更自主（B(c) 方向）。"""
        goal = Goal()
        worlds = [World(0.8 if i % 2 == 0 else 0.15, seed=700 + i) for i in range(40)]
        results = {}
        for cal in (0.6, 0.99):
            prof = CognitiveProfile("t", bandwidth=max(0.4, cal * 3.0),
                                    learning_rate=0.6, calibration=cal)
            results[cal] = _batch_run(prof, goal, worlds)["obs"]
        self.assertLess(results[0.99], results[0.6],
                        "高校准应需更少观察")


if __name__ == "__main__":
    unittest.main(verbosity=2)
