"""自学习成长桥测试（阶段4：两条线接合 + 真实消费痕迹）。"""
from pathlib import Path

from svagent.growth_bridge import (
    kb_to_opportunities, forensic_gaps_to_opportunities,
    bridge_into_pdca, save_consumption, live_regression,
)
from svagent.knowledge_base import KnowledgeBase
from svagent.pdca import PDCALoop, Budget

_ROOT = Path(__file__).resolve().parent.parent


def _kb():
    return KnowledgeBase.load(_ROOT / "knowledge_base_store.json")


def test_kb_to_opportunities_traced():
    rep = kb_to_opportunities(_kb())
    assert len(rep.opportunities) > 0
    assert all(c.source_kind == "knowledge_base" and c.source_id.startswith("KB-")
               for c in rep.consumption)
    assert len(rep.cognitive_deferred) > 0  # 认知机制交人，不伪造可编译


def test_addressable_false_not_compiled():
    """addressable=False 的 KB 条目不进机会，只列 cognitive_deferred。"""
    rep = kb_to_opportunities(_kb())
    deferred = set(rep.cognitive_deferred)
    op_ids = {o.signal.split(":")[0] for o in rep.opportunities}
    assert not (deferred & op_ids), "认知机制不得同时出现在机会里"


def test_forensic_gaps_become_opportunities():
    rep = forensic_gaps_to_opportunities({
        "crit": {"action": "downgrade", "code": "CRITERION_ORIGIN.RECALL_HIDDEN"},
        "proof": {"action": "ok", "code": "PROOF_BOUNDARY.SELF_CONSISTENT"},
    })
    assert len(rep.opportunities) == 1
    assert rep.consumption[0].source_id == "CRITERION_ORIGIN.RECALL_HIDDEN"


def test_all_ok_no_gap():
    rep = forensic_gaps_to_opportunities({"x": {"action": "ok", "code": "X.OK"}})
    assert len(rep.opportunities) == 0 and len(rep.consumption) == 0


def test_bridge_injects_into_pdca():
    loop = PDCALoop(budget=Budget(max_cycles=2, patience=1, max_attempts=1))
    rep = bridge_into_pdca(loop, kb=_kb(),
                           adjudications={"x": {"action": "flag", "code": "X.FLAG"}})
    assert len(loop._injected_opps) == len(rep.opportunities)
    assert any(c.source_id == "X.FLAG" for c in rep.consumption)


def test_save_consumption_roundtrip(tmp_path):
    rep = kb_to_opportunities(_kb())
    p = tmp_path / "trace.json"
    save_consumption(rep, p)
    assert p.exists() and len(rep.consumption) > 0


def test_live_regression():
    r = live_regression()
    assert r["all_passed"] and all(r["checks"].values())
