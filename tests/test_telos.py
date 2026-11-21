"""目标导向价值-认知协同框架的回归测试。

验证统一命题：人和 AI 是参数化认知主体；V×C 协同；渐进收敛；边界随能力外移。
"""
from __future__ import annotations

import random
import unittest

from svagent.telos import (
    Action, Belief, CognitiveAgent, CognitiveProfile, Goal, Trajectory, World,
    _batch_run, profile_set, worlds_by_difficulty,
)


def worlds(n: int = 40, seed: int = 0) -> list[World]:
    return [World(true_p_bad=0.8 if i % 2 == 0 else 0.15, seed=seed + i)
            for i in range(n)]


class TestBeliefAndCognition(unittest.TestCase):
    def test_belief_moves_toward_observation(self):
        p = CognitiveProfile("t", prior_alpha=1, prior_beta=1,
                             bandwidth=2.0, learning_rate=0.8)
        b = Belief.from_prior(p)
        before = b.p_bad
        b.update(0.9, p)
        self.assertGreater(b.p_bad, before)

    def test_bandwidth_raises_information_gain(self):
        slow = CognitiveProfile("slow", bandwidth=0.5, learning_rate=0.5)
        fast = CognitiveProfile("fast", bandwidth=3.0, learning_rate=0.5)
        bs, bf = Belief.from_prior(slow), Belief.from_prior(fast)
        bs.update(0.9, slow); bf.update(0.9, fast)
        self.assertGreater(bf.p_bad, bs.p_bad)

    def test_uncertainty_shrinks_with_evidence(self):
        p = CognitiveProfile("t", bandwidth=2.0, learning_rate=0.8, calibration=1.0)
        b = Belief.from_prior(p)
        u0 = b.uncertainty
        for _ in range(6):
            b.update(0.8, p)
        self.assertLess(b.uncertainty, u0)

    def test_overconfidence_understates_uncertainty(self):
        good = CognitiveProfile("good", calibration=1.0)
        over = CognitiveProfile("over", calibration=0.3)
        bg = Belief.from_prior(good); bg._calibration = 1.0
        bo = Belief.from_prior(over); bo._calibration = 0.3 ** 2
        self.assertLess(bo.uncertainty, bg.uncertainty)


class TestDecision(unittest.TestCase):
    def test_max_expected_value_choice(self):
        """p_bad 明确高时判坏、明确低时判好。"""
        goal = Goal(reward=10, loss=25, observe_cost=1, voi_weight=0)
        p = CognitiveProfile("t", prior_alpha=20, prior_beta=1, bandwidth=1)
        self.assertEqual(CognitiveAgent(p, goal).decide(Belief.from_prior(p))[0], "declare_bad")
        p2 = CognitiveProfile("t2", prior_alpha=1, prior_beta=20, bandwidth=1)
        self.assertEqual(CognitiveAgent(p2, goal).decide(Belief.from_prior(p2))[0], "declare_good")

    def test_uncertain_state_triggers_observation(self):
        goal = Goal(voi_weight=8, observe_cost=1)
        p = CognitiveProfile("t", prior_alpha=1, prior_beta=1, bandwidth=1)
        action, evs = CognitiveAgent(p, goal).decide(Belief.from_prior(p))
        self.assertEqual(action, "observe")
        self.assertGreater(evs["observe"], evs["declare_good"])


class TestUnifiedFramework(unittest.TestCase):
    def test_agents_differ_by_parameters_not_identity(self):
        """四类主体同一任务：准确率都高，但价值随认知能力单调提升。"""
        goal = Goal()
        ws = worlds(40)
        vals = [_batch_run(p, goal, ws)["value"] for p in profile_set()]
        # 弱AI < 普通人 < 专家人 < 强AI（认知能力越强，价值越高）
        self.assertEqual(vals, sorted(vals))
        self.assertLess(vals[0], 0)    # 低校准过自信 → 成本高，价值为负
        self.assertGreater(vals[-1], 0)

    def test_information_value_drives_observation(self):
        """信息价值权重越高 → 主体愿意观察更多次（价值函数真实参与决策）。"""
        p = profile_set()[2]  # 专家人：中等观察次数，对 voi 敏感
        ws = worlds(40)
        m_hi = _batch_run(p, Goal(voi_weight=12), ws)
        m_lo = _batch_run(p, Goal(voi_weight=2), ws)
        self.assertGreater(m_hi["obs"], m_lo["obs"])


class TestSynergy(unittest.TestCase):
    def test_synergy_beats_all_ablations(self):
        ws = worlds(40, seed=7)
        good_C = CognitiveProfile("gc", bandwidth=3.0, learning_rate=0.9, calibration=1.0)
        bad_C = CognitiveProfile("bc", bandwidth=0.4, learning_rate=0.2, calibration=0.3)
        good_V = Goal(reward=10, loss=25, observe_cost=1, voi_weight=8)
        no_V = Goal(reward=0, loss=0, observe_cost=1, voi_weight=0)
        gamble_V = Goal(reward=10, loss=2, observe_cost=1, voi_weight=0.5)

        syn = _batch_run(good_C, good_V, ws)
        ablations = [
            _batch_run(bad_C, good_V, ws),
            _batch_run(good_C, no_V, ws),
            _batch_run(good_C, gamble_V, ws),
        ]
        self.assertGreater(syn["value"], max(a["value"] for a in ablations))
        self.assertGreaterEqual(syn["accuracy"], 0.9)

    def test_no_value_loses_direction(self):
        """无 V → 准确率退化到接近随机。"""
        ws = worlds(40, seed=7)
        p = CognitiveProfile("gc", bandwidth=3.0, learning_rate=0.9, calibration=1.0)
        m = _batch_run(p, Goal(reward=0, loss=0, observe_cost=1, voi_weight=0), ws)
        self.assertAlmostEqual(m["accuracy"], 0.5, delta=0.05)


class TestConvergence(unittest.TestCase):
    def test_trajectory_converges_and_stops(self):
        goal = Goal(observe_cost=1.6, voi_weight=5.0)
        world = World(true_p_bad=0.85, seed=7, base_noise=0.42)
        p = CognitiveProfile("t", bandwidth=1.6, learning_rate=0.45, calibration=0.95)
        traj = CognitiveAgent(p, goal).run(world, max_steps=12)
        self.assertIsNotNone(traj.decision)
        self.assertTrue(traj.correct)
        self.assertGreater(traj.n_observations, 0)
        # 信念朝真值移动
        self.assertGreater(traj.steps[-1].p_bad_after, 0.5)

    def test_boundary_shifts_with_bandwidth(self):
        """带宽越高，达同等准确率所需观察越少（自主决策区扩张）。"""
        goal = Goal()
        ws = worlds(40, seed=11)
        low = _batch_run(CognitiveProfile("low", bandwidth=0.5, learning_rate=0.8,
                                          calibration=0.95), goal, ws)
        high = _batch_run(CognitiveProfile("high", bandwidth=3.5, learning_rate=0.8,
                                           calibration=0.95), goal, ws)
        self.assertEqual(low["accuracy"], high["accuracy"])
        self.assertGreater(low["obs"], high["obs"])


class TestAuditFixes(unittest.TestCase):
    """审计整改测试：难度分辨力与最优停止诚实报告。"""

    def test_difficulty_factory_produces_correct_gap(self):
        ws = worlds_by_difficulty(10, 0.10, seed=1)
        vals = sorted({round(w.true_p_bad, 3) for w in ws})
        self.assertEqual(len(vals), 2)
        self.assertAlmostEqual(vals[1] - vals[0], 0.10, places=5)

    def test_toy_task_all_perfect_hard_task_differentiates(self):
        """【核心整改】玩具难度全员满分(无分辨力)，难任务下主体能力差异现形。"""
        goal = Goal()
        toy = worlds_by_difficulty(60, 0.65, seed=100)
        hard = worlds_by_difficulty(60, 0.10, seed=100)
        weak = CognitiveProfile("weak", bandwidth=0.7, learning_rate=0.5, calibration=0.4)
        strong = CognitiveProfile("strong", bandwidth=4.0, learning_rate=0.9, calibration=1.0)
        toy_acc = [_batch_run(p, goal, toy)["accuracy"] for p in (weak, strong)]
        hard_acc = [_batch_run(p, goal, hard)["accuracy"] for p in (weak, strong)]
        # 玩具任务：两者都接近满分，几乎没有分辨力
        self.assertGreaterEqual(toy_acc[0], 0.98)
        self.assertAlmostEqual(toy_acc[0], toy_acc[1], delta=0.05)
        # 难任务：强主体显著优于弱主体——准确率恢复分辨力
        self.assertGreater(hard_acc[1], hard_acc[0] + 0.1,
                           f"难任务应显出能力差异: {hard_acc}")

    def test_exhausted_marker_set_when_forced(self):
        """撞步数上限被强制判定时，stopped_early=False / exhausted=True。"""
        world = World(true_p_bad=0.55, seed=7, base_noise=0.6)
        prof = CognitiveProfile("t", bandwidth=0.4, learning_rate=0.3, calibration=1.0)
        traj = CognitiveAgent(prof, Goal(observe_cost=0, voi_weight=100)).run(world, max_steps=3)
        self.assertFalse(traj.stopped_early)
        self.assertTrue(traj.exhausted)


if __name__ == "__main__":
    unittest.main(verbosity=2)
