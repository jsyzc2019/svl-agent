"""PDCA 自动化运行机制的回归测试。

验证的不是单步能力，而是「机制」：能自己停、单调包含、不可约交人、
回滚自纠、审计可追溯、跨批再识别。
"""
from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from svagent.autopoiesis import Environment, LogRecord, PredicateSpec
from svagent.core import Draft, Sentence
from svagent.pdca import (
    Budget, PDCALoop, Snapshot, _sample_batches, _sample_stream,
    is_irreducible, report,
)
from svagent.autopoiesis import _lab_ground_truth


def make_loop(**budget) -> PDCALoop:
    return PDCALoop(Environment(), Budget(**budget))


class TestIdentify(unittest.TestCase):
    def test_splits_addressable_and_irreducible(self):
        loop = make_loop()
        loop.feed(_sample_stream())
        opps = loop.identify()
        addressable = [o for o in opps if o.addressable]
        human = [o for o in opps if not o.addressable]
        self.assertGreater(len(addressable), 0)
        self.assertTrue(any(o.kind == "irreducible_human" for o in human))
        self.assertTrue(any(is_irreducible(o.signal) for o in human))

    def test_blocked_gap_disappears_after_environment_learns(self):
        loop = make_loop()
        rec = _sample_batches()[0][0]
        loop.feed([rec])
        self.assertTrue(any(o.addressable for o in loop.identify()))
        # 手动装一条能挡住它的判据，再识别时该缺口应消解
        loop.env.predicates.append(PredicateSpec(
            name="guard", kind="token", params={"tokens": ["收音机"], "scopes": ["chapter"]},
            strategy="token_lexicon",
        ))
        self.assertFalse(any(o.addressable for o in loop.identify()))

    def test_exhausted_signal_routes_to_human(self):
        loop = make_loop(max_attempts=0)
        loop.feed(_sample_batches()[0])
        opps = loop.identify()
        self.assertTrue(all(not o.addressable for o in opps))


class TestCycle(unittest.TestCase):
    def test_adopt_lowers_leak_and_bumps_version(self):
        loop = make_loop()
        loop.feed(_sample_batches()[0])
        rec = loop.cycle()
        self.assertEqual(rec.decision, "adopt")
        self.assertLess(rec.after.leak_rate, rec.before.leak_rate)
        self.assertGreater(rec.after.version, rec.before.version)
        self.assertIsNotNone(rec.adopted)

    def test_irreducible_batch_converges_without_installing(self):
        loop = make_loop()
        loop.feed(_sample_batches()[3])  # 不可约模糊句
        rec = loop.cycle()
        self.assertEqual(rec.decision, "converged")
        self.assertEqual(rec.after.predicates, 0)
        self.assertEqual(rec.after.human_queue, 1)

    def test_monotonic_inclusion_across_batches(self):
        loop = make_loop()
        counts = []
        for batch in _sample_batches():
            loop.feed(batch)
            loop.run()
            counts.append(len(loop.env.predicates))
        # 判据数单调不减；不可约批次不安装
        self.assertEqual(counts, sorted(counts))
        self.assertEqual(counts[3], counts[2])
        self.assertGreater(counts[4], counts[3])

    def test_overbroad_candidate_rejected_by_guard(self):
        loop = make_loop()
        bad = PredicateSpec(
            name="bad", kind="regex", params={"pattern": "年", "scopes": ["agent"]},
            strategy="broad_regex",
        )
        ok, why = loop.verify(__import__("svagent.pdca", fromlist=["Proposal"]).Proposal(
            name="bad", strategy="broad_regex", spec=bad,
        ))
        self.assertFalse(ok)
        self.assertIn("回归失败", why)


class TestEvaluateAndStop(unittest.TestCase):
    def test_rollback_when_no_gain(self):
        loop = make_loop()
        before = Snapshot(version=1, predicates=1, open_gaps=1, human_queue=0, total_signals=1)
        after = Snapshot(version=2, predicates=2, open_gaps=1, human_queue=0, total_signals=1)
        decision, rationale = loop._evaluate_decision(before, after, "bad", 1, 1)
        self.assertEqual(decision, "rollback")
        self.assertIn("回滚", rationale)

    def test_run_stops_within_budget(self):
        loop = make_loop(max_cycles=5, patience=2)
        loop.feed(_sample_stream())
        records = loop.run()
        self.assertLessEqual(len(records), 5)
        self.assertEqual(records[-1].decision, "converged")

    def test_run_auto_converges_on_empty_inbox(self):
        loop = make_loop(patience=2)
        records = loop.run()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].decision, "converged")

    def test_status_reflects_state(self):
        loop = make_loop()
        loop.feed(_sample_batches()[0])
        loop.run()
        s = loop.status()
        self.assertEqual(s["version"], loop.env.version)
        self.assertGreater(s["audit_records"], 0)


class TestAuditAndPersistence(unittest.TestCase):
    def test_audit_is_traceable_and_json_serializable(self):
        loop = make_loop()
        loop.feed(_sample_batches()[0])
        loop.run()
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "audit.jsonl"
            loop.save_audit(path)
            lines = path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), len(loop.history))
        for line in lines:
            obj = json.loads(line)
            for key in ("cycle", "decision", "detected", "researched", "verified",
                        "adopted", "before_leak", "after_leak"):
                self.assertIn(key, obj)

    def test_persist_reload_blocks_old_attack(self):
        loop = make_loop()
        loop.feed(_sample_stream())
        loop.run()
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "env.json"
            loop.save_environment(path)
            reloaded = PDCALoop(Environment.load(path))
        first = _sample_stream()[0]
        draft = Draft(chapters={"工作": [Sentence(first.text, ("k1",))]})
        blocked = any(x.severity == "block" for x in reloaded.env.check(draft, _lab_ground_truth()))
        self.assertTrue(blocked)

    def test_report_runs(self):
        loop = make_loop()
        loop.feed(_sample_batches()[0])
        loop.run()
        buf = io.StringIO()
        with redirect_stdout(buf):
            report(loop)
        self.assertIn("PDCA 自动化运行机制", buf.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
