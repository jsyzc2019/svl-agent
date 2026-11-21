"""机制知识库测试：去重佐证、诚实量变判据、反虚荣门禁、反哺闭环。"""
import json
import tempfile
import unittest
from pathlib import Path

from svagent.knowledge_base import (
    KnowledgeBase, KnowledgeItem, ReadinessThresholds, seed_knowledge,
    KIND_THINKING, KIND_REASONING, KIND_EXTERNAL,
    EVIDENCE_EXPERIMENT, EVIDENCE_AUDIT, EVIDENCE_REFLECTION,
    CLASS_FIX, CLASS_VANITY, CLASS_PRESERVE,
)


def _item(iid="KB-1", kind=KIND_THINKING, mech="机制A", trig=None, action="动作A",
          prov="commentary:§1", sup=None, ev=EVIDENCE_REFLECTION, addr=False, cls=""):
    return KnowledgeItem(
        item_id=iid, kind=kind, mechanism=mech,
        trigger=trig if trig is not None else ["macro", "framework"],
        action=action, provenance=prov, support=sup if sup is not None else [prov],
        evidence=ev, addressable=addr, improvement_class=cls,
    )


class TestKnowledgeItem(unittest.TestCase):
    def test_rejects_empty_mechanism(self):
        with self.assertRaises(ValueError):
            _item(mech="   ")

    def test_rejects_unknown_kind(self):
        with self.assertRaises(ValueError):
            _item(kind="random")

    def test_rejects_unknown_class(self):
        with self.assertRaises(ValueError):
            _item(cls="maybe")

    def test_autofills_timestamp(self):
        it = _item()
        self.assertTrue(it.timestamp)

    def test_corroboration_excludes_self_evidence(self):
        # 只有自身 provenance 作佐证 → 不算独立佐证
        self.assertFalse(_item(sup=["commentary:§1"]).corroborated)
        # 有不同来源 → 算独立佐证
        it = _item(sup=["commentary:§1", "commentary:§2"])
        self.assertTrue(it.corroborated)
        self.assertEqual(it.independent_supports, ["commentary:§2"])


class TestIngest(unittest.TestCase):
    def test_new_item_added(self):
        kb = KnowledgeBase()
        self.assertEqual(kb.ingest(_item()), "KB-1")
        self.assertEqual(len(kb.items), 1)

    def test_duplicate_mechanism_merged_with_corroboration(self):
        kb = KnowledgeBase()
        kb.ingest(_item(prov="commentary:§1", sup=["commentary:§1"]))
        kb.ingest(_item(iid="KB-2", prov="commentary:§2", sup=["commentary:§2"]))
        self.assertEqual(len(kb.items), 1)  # 去重
        merged = list(kb.items.values())[0]
        self.assertIn("commentary:§2", merged.support)
        self.assertTrue(merged.corroborated)

    def test_duplicate_upgrades_evidence_and_class(self):
        kb = KnowledgeBase()
        kb.ingest(_item(ev=EVIDENCE_REFLECTION))
        kb.ingest(_item(iid="KB-2", ev=EVIDENCE_EXPERIMENT, addr=True, cls=CLASS_FIX,
                        action="动作A"))  # action 相同 → 命中去重
        merged = list(kb.items.values())[0]
        self.assertEqual(merged.evidence, EVIDENCE_EXPERIMENT)
        self.assertTrue(merged.addressable)
        self.assertEqual(merged.improvement_class, CLASS_FIX)


class TestRecall(unittest.TestCase):
    def test_recall_by_trigger(self):
        kb = KnowledgeBase()
        kb.ingest(_item(iid="A", trig=["macro", "cycle_phase"]))
        kb.ingest(_item(iid="B", mech="机制B", trig=["finance"]))
        hits = kb.recall(["macro", "cycle_phase"])
        self.assertEqual([h.item_id for h in hits], ["A"])

    def test_empty_tags_return_nothing(self):
        kb = KnowledgeBase()
        kb.ingest(_item())
        self.assertEqual(kb.recall([]), [])

    def test_injections_for_nonempty_action(self):
        kb = KnowledgeBase()
        kb.ingest(_item(action="预注册判据"))
        inj = kb.injections_for(["macro", "framework"])
        self.assertTrue(any("预注册判据" in x for x in inj))


class TestReadiness(unittest.TestCase):
    def test_empty_kb_not_ready_with_gaps(self):
        r = KnowledgeBase().readiness()
        self.assertFalse(r.ready)
        self.assertTrue(r.gaps)
        self.assertFalse(r.vanity_gate["passed"])
        self.assertIsNone(r.proposal)

    def test_saturated_kb_ready_with_proposal(self):
        kb = KnowledgeBase()
        tags = [f"tag{j}" for j in range(9)]
        kb.ingest_many([
            _item(iid=f"T{i}", kind=KIND_THINKING, mech=f"思考机制{i}",
                  action=f"思考动作{i}", trig=tags,
                  prov=f"commentary:§{i}", sup=[f"commentary:§{i}", f"eval:{i}"],
                  ev=EVIDENCE_EXPERIMENT, cls=CLASS_FIX if i < 3 else "")
            for i in range(8)
        ] + [
            _item(iid=f"R{i}", kind=KIND_REASONING, mech=f"推演机制{i}",
                  action=f"推演动作{i}", trig=tags,
                  prov=f"trace:{i}", sup=[f"trace:{i}", f"eval:r{i}"],
                  ev=EVIDENCE_AUDIT)
            for i in range(8)
        ] + [
            _item(iid=f"E{i}", kind=KIND_EXTERNAL, mech=f"外部机制{i}",
                  action=f"外部动作{i}", trig=tags,
                  prov=f"external:src{i}", sup=[f"external:src{i}", f"eval:e{i}"],
                  ev=EVIDENCE_EXPERIMENT)
            for i in range(4)
        ])
        r = kb.readiness()
        self.assertTrue(r.ready, r.gaps)
        self.assertIsNotNone(r.proposal)
        self.assertIn("触发一次", r.proposal.note)

    def test_too_few_items_blocks(self):
        kb = KnowledgeBase()
        for i in range(5):
            kb.ingest(_item(iid=f"X{i}", mech=f"机制{i}", prov=f"src{i}"))
        r = kb.readiness()
        self.assertFalse(r.ready)
        self.assertFalse(r.dimensions["规模"])

    def test_proposal_only_lists_addressable_fix(self):
        kb = KnowledgeBase()
        # 造一个满足全部门槛、但只有一个 addressable fix 的库
        for i in range(20):
            cls = CLASS_FIX if i < 3 else ""   # 3 个 fix 满足门槛
            addr = i == 0                      # 只有 1 个可编译 → 提案只应列它
            kind = [KIND_THINKING, KIND_REASONING, KIND_EXTERNAL][i % 3]
            kb.ingest(_item(
                iid=f"X{i}", mech=f"机制{i}", kind=kind, action=f"动作{i}",
                prov=f"s{i}:x", sup=[f"s{i}:x", f"eval{i}"], ev=EVIDENCE_EXPERIMENT,
                trig=[f"tag{j}" for j in range(9)],
                addr=addr, cls=cls,
            ))
        r = kb.readiness()
        self.assertTrue(r.ready, r.gaps)
        self.assertEqual(len(r.proposal.candidate_opportunities), 1)


class TestAntiVanityGate(unittest.TestCase):
    def test_high_vanity_ratio_blocked(self):
        th = ReadinessThresholds()
        items = [_item(iid=f"V{i}", mech=f"虚荣{i}", prov=f"src{i}", cls=CLASS_VANITY,
                       action=f"不同的虚荣动作{i}") for i in range(5)]
        items += [_item(iid=f"N{i}", mech=f"正常{i}", prov=f"srcN{i}",
                        action=f"不同正常动作{i}") for i in range(5)]
        kb = KnowledgeBase(th)
        kb.ingest_many(items)
        ok, reason = kb._anti_vanity_gate(vanity_ratio=0.5)
        self.assertFalse(ok)
        self.assertIn("vanity", reason)

    def test_single_source_flooding_blocked(self):
        kb = KnowledgeBase()
        items = [_item(iid=f"S{i}", mech=f"机制{i}", prov="commentary:§same",
                       action=f"不同动作{i}") for i in range(10)]
        kb.ingest_many(items)
        ok, reason = kb._anti_vanity_gate(vanity_ratio=0.0)
        self.assertFalse(ok)
        self.assertIn("来源过度集中", reason)

    def test_repeated_actions_blocked(self):
        kb = KnowledgeBase()
        # 直接构造（绕过 ingest 的 action 去重），模拟「措辞微调躲避去重、但动作高度雷同」的灌水
        for i in range(10):
            it = _item(iid=f"A{i}", mech=f"机制{i}", prov=f"src{i}:p", action="同一动作")
            kb.items[it.item_id] = it
        ok, reason = kb._anti_vanity_gate(vanity_ratio=0.0)
        self.assertFalse(ok)
        self.assertIn("高度重复", reason)


class TestFeedbackToPDCA(unittest.TestCase):
    def test_to_opportunities_only_fix_addressable(self):
        kb = KnowledgeBase()
        kb.ingest(_item(iid="FIX", mech="该改的", addr=True, cls=CLASS_FIX))
        kb.ingest(_item(iid="PRES", mech="该守的", prov="src2", addr=True, cls=CLASS_PRESERVE))
        kb.ingest(_item(iid="NOADDR", mech="不可编译", prov="src3", addr=False, cls=CLASS_FIX))
        opps = kb.to_opportunities()
        self.assertEqual(len(opps), 1)
        self.assertEqual(opps[0].source, "knowledge_base:commentary:§1")


class TestPersistence(unittest.TestCase):
    def test_save_load_roundtrip(self):
        kb = KnowledgeBase(ReadinessThresholds(min_items=7))
        kb.ingest_many(seed_knowledge())
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "kb.json"
            kb.save(p)
            loaded = KnowledgeBase.load(p)
        self.assertEqual(len(loaded.items), len(kb.items))
        self.assertEqual(loaded.thresholds.min_items, 7)
        self.assertEqual(loaded.readiness().ready, kb.readiness().ready)


class TestSeedKnowledge(unittest.TestCase):
    def test_seed_has_all_three_kinds(self):
        seeds = seed_knowledge()
        kinds = {s.kind for s in seeds}
        self.assertTrue({KIND_THINKING, KIND_REASONING, KIND_EXTERNAL}.issubset(kinds))

    def test_every_seed_has_provenance_and_mechanism(self):
        for s in seed_knowledge():
            self.assertTrue(s.provenance, s.item_id)
            self.assertTrue(s.mechanism.strip(), s.item_id)

    def test_real_seeds_trigger_readiness(self):
        """23 节真实凝练 + 复盘库导入后应达到量变门槛——这是可审计的真实状态。"""
        kb = KnowledgeBase()
        kb.ingest_many(seed_knowledge())
        kb.import_retrospective("retrospective_store.json")
        r = kb.readiness()
        self.assertTrue(r.ready, r.gaps)
        self.assertTrue(r.vanity_gate["passed"])


if __name__ == "__main__":
    unittest.main()
