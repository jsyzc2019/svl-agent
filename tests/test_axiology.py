"""价值自举层单元测试：验证 V 可被恢复、锚点防漂移、闭环收敛、可接回 telos。"""
import math
import unittest

from svagent.axiology import (
    ANCHORS, FEATURES, AxiologyLoop, DecisionEvent, ValueInducer, ValueWeights,
    _latent_truth, adversarial_robustness, make_policy, project_to_anchors,
    satisfies_anchors, synth_event, to_goal_params,
)
import random


def _seed(latent, n=60, base=20261121):
    return [synth_event(latent, random.Random(base + i)) for i in range(n)]


class TestValueWeights(unittest.TestCase):
    def test_dot_and_cosine(self):
        w = ValueWeights(truth=1, coverage=0, precision=0, convenience=0, human_discretion=0)
        e_hi = DecisionEvent(truth=1, coverage=0, precision=0, convenience=0,
                             human_discretion=0, action=True)
        e_lo = DecisionEvent(truth=0, coverage=0, precision=0, convenience=0,
                             human_discretion=0, action=True)
        self.assertGreater(w.dot(e_hi), w.dot(e_lo))
        self.assertAlmostEqual(w.cosine(w), 1.0, places=5)
        self.assertAlmostEqual(w.cosine(ValueWeights()), 0.0, places=5)

    def test_vec_roundtrip(self):
        w = ValueWeights(truth=0.9, coverage=0.3, precision=0.85,
                         convenience=0.2, human_discretion=0.55)
        self.assertEqual(ValueWeights.from_vec(w.vec()).as_dict(), w.as_dict())


class TestAnchors(unittest.TestCase):
    def test_latent_satisfies_anchors(self):
        self.assertTrue(satisfies_anchors(_latent_truth()))

    def test_project_fixes_violation(self):
        # 省事至上：违反全部三条锚点
        bad = ValueWeights(truth=0.1, coverage=0.9, precision=0.1,
                           convenience=0.9, human_discretion=0.0)
        self.assertFalse(satisfies_anchors(bad))
        fixed = project_to_anchors(bad)
        self.assertTrue(satisfies_anchors(fixed))

    def test_project_is_minimal_where_valid(self):
        w = _latent_truth()
        self.assertEqual(project_to_anchors(w).as_dict(), w.as_dict())


class TestRecovery(unittest.TestCase):
    def test_direction_recovered(self):
        latent = _latent_truth()
        events = _seed(latent)
        w = ValueInducer().recover(events)
        self.assertGreater(w.cosine(latent), 0.90,
                           f"方向余弦 {w.cosine(latent):.3f} 应 >0.90")

    def test_recovered_v_predicts_heldout(self):
        latent = _latent_truth()
        events = _seed(latent, n=100)
        split = 70
        w = ValueInducer().recover(events[:split])
        acc = ValueInducer.accuracy(w, events[split:])
        self.assertGreater(acc, 0.75, f"留一预测 {acc:.0%} 应 >75%")

    def test_more_data_better_direction(self):
        latent = _latent_truth()
        small = ValueInducer().recover(_seed(latent, n=20, base=1))
        large = ValueInducer().recover(_seed(latent, n=120, base=1))
        self.assertGreaterEqual(large.cosine(latent), small.cosine(latent) - 0.08)

    def test_scale_invariance_of_direction(self):
        """IRL 只恢复方向：把真 V 放大 10 倍，恢复方向应几乎不变。"""
        latent = _latent_truth()
        scaled = ValueWeights(**{f: getattr(latent, f) * 10 for f in FEATURES})
        w1 = ValueInducer().recover(_seed(latent, base=5))
        w2 = ValueInducer().recover(_seed(scaled, base=5))
        self.assertGreater(w1.cosine(w2), 0.90)

    def test_random_latent_also_recovers(self):
        """【审计发现固化】随机无意义 V 也能被线性 IRL 恢复——这是同构自证的证据。"""
        import random as _r
        from svagent.axiology import FEATURES as F
        rng = _r.Random(777)
        random_latent = ValueWeights(**{f: rng.uniform(-1, 1) for f in F})
        events = [synth_event(random_latent, _r.Random(3000 + i)) for i in range(60)]
        w = ValueInducer().recover(events)
        # 恢复到什么不重要，重要的是：它"能恢复"这件事对 V 的语义无鉴别力
        self.assertGreater(w.cosine(random_latent), 0.6)

    def test_nonlinear_world_degrades_recovery(self):
        """【整改】非线性决策世界里，线性 IRL 的解释率显著低于线性世界。"""
        from svagent.axiology import nonlinearity_challenge
        r = nonlinearity_challenge(n=300)
        self.assertGreater(r["线性世界"]["解释率"], r["非线性世界"]["解释率"] + 0.1)
        self.assertGreater(r["线性世界"]["余弦"], r["非线性世界"]["余弦"] + 0.05)


class TestBootstrap(unittest.TestCase):
    def test_converges(self):
        latent = _latent_truth()
        loop = AxiologyLoop(make_policy(latent), latent=latent)
        res = loop.bootstrap(_seed(latent))
        self.assertTrue(res.converged, "自举应在有限轮内方向收敛")
        self.assertGreater(res.rounds[-1].cosine_to_latent, 0.90)

    def test_delta_decreases(self):
        latent = _latent_truth()
        res = AxiologyLoop(make_policy(latent), latent=latent).bootstrap(_seed(latent))
        deltas = [r.delta for r in res.rounds[1:]]
        self.assertLess(deltas[-1], deltas[0] + 1e-6)

    def test_anchors_hold_every_round(self):
        latent = _latent_truth()
        res = AxiologyLoop(make_policy(latent), latent=latent).bootstrap(_seed(latent))
        self.assertTrue(all(r.anchor_ok for r in res.rounds))

    def test_policy_uses_latent_not_recovered(self):
        """自证循环禁令：policy 必须忽略传入的 recovered_w，只看 latent。"""
        latent = _latent_truth()
        policy = make_policy(latent)
        e1 = policy(ValueWeights(), t=42)
        e2 = policy(ValueWeights(truth=99, coverage=-99, precision=0,
                                 convenience=0, human_discretion=0), t=42)
        self.assertEqual(e1, e2, "相同 t 下决策应与传入的 recovered_w 无关")


class TestAdversarial(unittest.TestCase):
    def test_anchored_v_passes_adversarial(self):
        w = ValueInducer().recover(_seed(_latent_truth()))
        passed, total, _ = adversarial_robustness(w)
        self.assertEqual(passed, total)

    def test_unanchored_corrupt_v_fails(self):
        corrupt = ValueWeights(truth=0.15, coverage=0.70, precision=0.10,
                               convenience=0.95, human_discretion=0.05)
        seed = _seed(corrupt, base=999)
        w = AxiologyLoop(make_policy(corrupt), ValueInducer(anchors=()),
                         latent=corrupt).bootstrap(seed).final
        self.assertFalse(satisfies_anchors(w))
        passed, _, _ = adversarial_robustness(w)
        self.assertLess(passed, 3, "无锚点的腐败 V 应放行至少一个危险判据")

    def test_anchored_corrupt_v_still_safe(self):
        """关键因果对照：同样是腐败轨迹，有锚点就安全。"""
        corrupt = ValueWeights(truth=0.15, coverage=0.70, precision=0.10,
                               convenience=0.95, human_discretion=0.05)
        seed = _seed(corrupt, base=999)
        w = AxiologyLoop(make_policy(corrupt), latent=corrupt).bootstrap(seed).final
        self.assertTrue(satisfies_anchors(w))
        passed, total, _ = adversarial_robustness(w)
        self.assertEqual(passed, total)


class TestBridge(unittest.TestCase):
    def test_to_goal_params(self):
        w = ValueInducer().recover(_seed(_latent_truth()))
        p = to_goal_params(w)
        self.assertGreater(p["reward"], 0)
        self.assertGreater(p["loss"], p["reward"], "回忆录场景应损失厌恶")
        self.assertGreater(p["voi_weight"], 0)

    def test_recovered_v_drives_telos(self):
        from svagent.telos import CognitiveProfile, Goal, World, _batch_run
        w = ValueInducer().recover(_seed(_latent_truth()))
        goal = Goal(**to_goal_params(w))
        worlds = [World(0.8 if i % 2 == 0 else 0.15, seed=400 + i) for i in range(30)]
        prof = CognitiveProfile("t", bandwidth=2.2, learning_rate=0.7, calibration=0.95)
        m = _batch_run(prof, goal, worlds)
        self.assertGreater(m["accuracy"], 0.8)
        self.assertGreater(m["value"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
