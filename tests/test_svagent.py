"""SVL 原型的回归测试：隔离、坍塌判据、修复环、人工交接。"""
from __future__ import annotations

import unittest

from svagent.core import Claim, Draft, Message, Sentence, GroundTruth, is_user_said
from svagent.demo import build_draft, build_spec, repair
from svagent.handoff import handoff_cards
from svagent.harness import run_loop
from svagent.verifiers import (
    chapter_whitelist, concrete_grounded, default_verifiers,
    first_person_boundary, narrative_vividness_flag,
)


class TestIsolation(unittest.TestCase):
    def test_is_user_said_filters_topic_and_agent(self):
        spec = build_spec()
        said = {m.id for m in spec.messages.values() if is_user_said(m)}
        self.assertEqual(said, {"m1", "m2", "m3", "m4"})
        self.assertEqual(len(spec.replay_history()), 4)

    def test_fake_anchor_and_agent_source_are_rejected(self):
        spec = build_spec()
        self.assertEqual(
            {d.code for d in spec.rejected},
            {"GT.ANCHOR_MISMATCH", "GT.SOURCE_UNTRUSTED"},
        )
        self.assertNotIn("c_bad", spec.claims)
        self.assertNotIn("c_bad2", spec.claims)


class TestVerifiers(unittest.TestCase):
    def setUp(self):
        self.spec = build_spec()
        self.draft = build_draft()

    def test_chapter_whitelist(self):
        codes = {d.code for d in chapter_whitelist(self.draft, self.spec)}
        self.assertIn("CHAPTER.WHITELIST", codes)

    def test_concrete_detail_leak(self):
        codes = {d.code for d in concrete_grounded(self.draft, self.spec)}
        self.assertIn("EVIDENCE.DETAIL_LEAK", codes)

    def test_first_person_ownership(self):
        codes = {d.code for d in first_person_boundary(self.draft, self.spec)}
        self.assertIn("AGENT.OWNERSHIP", codes)

    def test_quoted_first_person_is_allowed(self):
        draft = Draft(agent_lines=['您刚说"我小时候在村里"，那是哪一年？'])
        self.assertEqual(first_person_boundary(draft, self.spec), [])


class TestLoop(unittest.TestCase):
    def test_loop_converges_and_keeps_flags_for_human(self):
        spec = build_spec()
        result = run_loop(build_draft(), spec, default_verifiers(), repair, max_iters=5)
        self.assertTrue(result.converged)
        self.assertGreater(result.iterations, 1)
        self.assertFalse(any(d.severity == "block" for d in result.diagnostics))
        self.assertTrue(any(d.severity == "flag" for d in result.diagnostics))
        self.assertNotIn("成家以后", result.draft.chapters)
        self.assertIn("工作", result.draft.chapters)

    def test_handoff_cards_carry_source_quotes(self):
        spec = build_spec()
        result = run_loop(build_draft(), spec, default_verifiers(), repair, max_iters=5)
        cards = handoff_cards(result.draft, result.diagnostics, spec)
        self.assertTrue(cards)
        self.assertTrue(all(card["判据"] for card in cards))
        self.assertTrue(any(not card["核对原话"] for card in cards))
        self.assertTrue(any(card["核对原话"] for card in cards))

    def test_fluent_but_grounded_sentence_is_flagged_not_blocked(self):
        spec = build_spec()
        result = run_loop(build_draft(), spec, default_verifiers(), repair, max_iters=5)
        flags = narrative_vividness_flag(result.draft, spec)
        self.assertTrue(flags)
        self.assertTrue(all(d.severity == "flag" for d in flags))


class TestSelfEvolution(unittest.TestCase):
    def test_substrate_compounds_monotonically(self):
        from svagent.self_evolving import run_recursion
        substrate = run_recursion()
        metrics = substrate.metrics
        self.assertTrue(all(m.regression_passed for m in metrics))
        sizes = [(m.predicate_families, m.lexicon_size, m.regression_size,
                  m.long_term_size) for m in metrics]
        for a, b in zip(sizes, sizes[1:]):
            self.assertGreaterEqual(b, a)
        self.assertLess(metrics[-1].attack_success, metrics[0].attack_success)
        self.assertGreater(substrate.version, 0)

    def test_irreducible_plateau_is_the_human_layer(self):
        from svagent.self_evolving import run_recursion
        substrate = run_recursion()
        last = substrate.metrics[-1]
        self.assertAlmostEqual(last.attack_success, last.human_flags / 30)
        self.assertGreater(last.human_flags, 0)

    def test_frozen_test_calibration_is_stable(self):
        from svagent.self_evolving import run_recursion
        substrate = run_recursion()
        lifts = [m.rule_lift for m in substrate.metrics if m.rule_text != "-"]
        self.assertTrue(lifts)
        self.assertGreaterEqual(max(lifts), 1.5)


class TestEvolution(unittest.TestCase):
    def test_predicate_bootstrap_prioritizes_fabrications(self):
        from svagent.evolution import extract, evaluate_rule, learn_stump, lab_spec, make_attacks
        import random
        spec = lab_spec()
        items = [(extract(spec, a), not a.fabricated) for a in make_attacks(random.Random(1))]
        rng = random.Random(7)
        rng.shuffle(items)
        split = int(len(items) * 0.7)
        rule = learn_stump(items[:split])
        metrics = evaluate_rule(rule, items[split:])
        self.assertGreaterEqual(metrics["precision"], 0.9)
        self.assertGreater(metrics["top20_catch"], metrics["base_rate"])

    def test_redteam_finds_blind_spots_and_patch_closes_them(self):
        from svagent.evolution import (
            block_count, default_verifiers, lab_spec, make_attacks,
            patched_verifiers,
        )
        import random
        spec = lab_spec()
        attacks = make_attacks(random.Random(2))
        base = default_verifiers()
        before = [a for a in attacks if a.fabricated and block_count(base, spec, a) == 0]
        self.assertGreater(len(before), 0)
        discovered = {a.detail for a in before if a.detail}
        after = [
            a for a in attacks
            if a.fabricated and block_count(patched_verifiers(discovered), spec, a) == 0
        ]
        self.assertEqual(len(after), 0)


class TestExperiment(unittest.TestCase):
    def test_constrained_rework_reduces_burden(self):
        from svagent.experiment import Config, run_monte_carlo
        cfg = Config(seeds=300)
        acc = run_monte_carlo(cfg)
        self.assertLess(acc["rework_constrained"].burden, acc["gate"].burden)
        self.assertEqual(acc["rework_constrained"].corrupt, 0.0)
        self.assertGreater(acc["rework_free"].corrupt, 0.0)

    def test_break_even_is_finite_for_free_rework(self):
        from svagent.experiment import Config, analytic_break_even
        result = analytic_break_even(Config(**{"s": 0.10}))
        self.assertEqual(result["无约束返工的造假临界权重 λ*"], 97.5)


class TestAutopoiesis(unittest.TestCase):
    def test_agent_builds_its_own_environment(self):
        from svagent.autopoiesis import Environment, SelfOrganizingAgent, simulate_session
        agent = SelfOrganizingAgent(Environment())
        for session in range(3):
            agent.cycle(simulate_session(session))
        self.assertGreater(agent.env.version, 0)
        self.assertGreaterEqual(len(agent.env.predicates), 2)
        self.assertTrue(all(m.regression_passed if hasattr(m, "regression_passed") else True
                            for m in agent.env.metrics))

    def test_regression_rejects_overbroad_predicate(self):
        from svagent.autopoiesis import (
            Environment, PredicateSpec, SelfOrganizingAgent, simulate_session,
        )
        agent = SelfOrganizingAgent(Environment())
        agent.cycle(simulate_session(0))
        bad = PredicateSpec(
            name="bad", kind="regex",
            params={"pattern": "年", "scopes": ["chapter"]},
            strategy="broad_regex",
        )
        passed, why = agent.env.regression_check(list(agent.env.predicates) + [bad])
        self.assertFalse(passed)
        self.assertIn("回归失败", why)

    def test_persistence_round_trip(self):
        from svagent.autopoiesis import Environment, SelfOrganizingAgent, simulate_session
        import tempfile, os
        agent = SelfOrganizingAgent(Environment())
        agent.cycle(simulate_session(0))
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as fh:
            path = fh.name
        try:
            agent.env.save(path)
            restored = Environment.load(path)
            self.assertEqual(restored.version, agent.env.version)
            self.assertEqual(
                [p.name for p in restored.predicates],
                [p.name for p in agent.env.predicates],
            )
        finally:
            os.unlink(path)

    def test_meta_learner_demotes_rejected_strategy(self):
        from svagent.autopoiesis import Environment, SelfOrganizingAgent, simulate_session
        agent = SelfOrganizingAgent(Environment())
        for session in range(7):
            agent.cycle(simulate_session(session))
        self.assertLess(agent.env.weight("broad_regex"), agent.env.weight("token_lexicon"))

    def test_irreducible_vague_is_routed_not_blocked(self):
        from svagent.autopoiesis import Environment, SelfOrganizingAgent, simulate_session
        agent = SelfOrganizingAgent(Environment())
        for session in range(4):
            agent.cycle(simulate_session(session))
        last = agent.env.metrics[-1]
        self.assertGreater(last.human_flags, 0)
        self.assertEqual(last.attack_success, 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
