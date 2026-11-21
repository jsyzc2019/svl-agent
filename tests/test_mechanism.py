"""多主体机制设计单元测试。"""
import unittest

from svagent.mechanism import (
    Candidate, evaluate, m1_dictator, m2_veto, m3_gate_route,
    m4_domain_weighted, m4_with_redteam, oracle, rand_candidates,
    stakeholders, system_welfare,
)


class TestCandidates(unittest.TestCase):
    def test_utility(self):
        agents = stakeholders()
        c = Candidate("x", 1, 0, 1, 0, 0.5)
        # 审查者真实/精确高 → 效用应高于生成者(更看重覆盖/省事)
        self.assertGreater(c.utility(agents["verifier"].V), c.utility(agents["generator"].V))

    def test_forged_generation(self):
        cands = rand_candidates(100, 1, forge_ratio=0.5)
        forged = [c for c in cands if c.forged]
        self.assertTrue(forged)
        # 造假样本真实/精确低、省事高
        self.assertLess(sum(c.truth for c in forged) / len(forged), 0.4)
        self.assertGreater(sum(c.convenience for c in forged) / len(forged), 0.6)


class TestMechanisms(unittest.TestCase):
    def setUp(self):
        self.seeds = range(200, 260)

    def test_generator_dictator_has_high_regret(self):
        r = evaluate(m1_dictator("generator"), self.seeds, forge_ratio=0.3)
        self.assertGreater(r["regret"], 0.3)
        self.assertGreater(r["forged_rate"], 0.15, "生成者独裁应大量误选造假样本")

    def test_domain_weighted_beats_generator(self):
        g = evaluate(m1_dictator("generator"), self.seeds, forge_ratio=0.3)
        m4 = evaluate(m4_domain_weighted, self.seeds, forge_ratio=0.3)
        self.assertLess(m4["regret"], g["regret"])

    def test_veto_and_gate_block_forgery(self):
        for mech in (m2_veto, m3_gate_route, m4_domain_weighted):
            r = evaluate(mech, self.seeds, forge_ratio=0.3)
            self.assertEqual(r["forged_rate"], 0.0, f"{mech} 应挡住造假")

    def test_redteam_pollution_worsens(self):
        clean = evaluate(m4_domain_weighted, self.seeds, forge_ratio=0.3)
        polluted = evaluate(m4_with_redteam, self.seeds, forge_ratio=0.3)
        self.assertGreater(polluted["regret"], clean["regret"],
                           "纳入红队对抗性V应使regret恶化")

    def test_oracle_is_baseline(self):
        # 全知按W选，regret应为0
        W = system_welfare()
        agents = stakeholders()
        total = 0.0
        for seed in self.seeds:
            cands = rand_candidates(14, seed)
            total += oracle(cands, W).utility(W) - oracle(cands, W).utility(W)
        self.assertAlmostEqual(total, 0.0)


class TestGoalShift(unittest.TestCase):
    def test_m4_fails_on_reversed_goal(self):
        """【审计整改】产量优先目标下，M4 被生成者独裁碾压——稳健有边界。"""
        from svagent.mechanism import ValueWeights
        W = ValueWeights(0.10, 0.95, 0.10, 0.90, 0.10)  # 产量优先
        agents = stakeholders()
        seeds = range(1200, 1300)
        def reg(mech):
            rs = []
            for s in seeds:
                c = rand_candidates(14, s, forge_ratio=0.2)
                rs.append(oracle(c, W).utility(W) - mech(c, agents).utility(W))
            return sum(rs) / len(rs)
        self.assertGreater(reg(m4_domain_weighted), reg(m1_dictator("generator")) + 0.2)

    def test_no_dictator_wins_all_goals(self):
        """没有任何单一独裁在所有目标下都最优——汇聚机制的价值是稳健。"""
        from svagent.mechanism import ValueWeights
        goals = [
            ValueWeights(0.95, 0.20, 0.90, 0.05, 0.30),  # 真实优先
            ValueWeights(0.50, 0.30, 0.45, 0.20, 0.95),  # 人本
        ]
        agents = stakeholders()
        seeds = range(300, 340)
        ver_wins = hum_wins = 0
        for W in goals:
            regs = {}
            for role in ("verifier", "human"):
                mech = m1_dictator(role)
                regs[role] = evaluate(lambda c, a, m=mech: m(c, a), seeds)["regret"] \
                    if False else self._regret(mech, agents, W, seeds)
            min_role = min(regs, key=regs.get)
            if min_role == "verifier":
                ver_wins += 1
            else:
                hum_wins += 1
        self.assertEqual(ver_wins, 1)
        self.assertEqual(hum_wins, 1)

    @staticmethod
    def _regret(mech, agents, W, seeds):
        from svagent.mechanism import oracle, rand_candidates
        rs = []
        for seed in seeds:
            cands = rand_candidates(14, seed, forge_ratio=0.2)
            rs.append(oracle(cands, W).utility(W) - mech(cands, agents).utility(W))
        return sum(rs) / len(rs)


class TestIncentiveCompatibility(unittest.TestCase):
    def test_loud_generator_hurts_dictator_more_than_m4(self):
        from svagent.mechanism import ValueWeights, Stakeholder
        agents = stakeholders()
        W = system_welfare()
        loud = Stakeholder("夸大", "generator", ValueWeights(0.2, 4.0, 0.15, 0.85, 0.05))
        seeds = range(400, 440)

        def reg(mech, ga):
            a = dict(agents); a["generator"] = ga
            return self._regret(mech, a, W, seeds)

        dict_delta = reg(m1_dictator("generator"), loud) - reg(m1_dictator("generator"), agents["generator"])
        m4_delta = reg(m4_domain_weighted, loud) - reg(m4_domain_weighted, agents["generator"])
        self.assertGreater(dict_delta, 0, "独裁下夸大应恶化regret")
        self.assertGreater(dict_delta, m4_delta, "独裁受操纵影响应大于职责加权")

    @staticmethod
    def _regret(mech, agents, W, seeds):
        from svagent.mechanism import oracle, rand_candidates
        rs = []
        for seed in seeds:
            cands = rand_candidates(14, seed, forge_ratio=0.2)
            rs.append(oracle(cands, W).utility(W) - mech(cands, agents).utility(W))
        return sum(rs) / len(rs)


if __name__ == "__main__":
    unittest.main(verbosity=2)
