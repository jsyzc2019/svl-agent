"""SIM 四要素改进记忆判据固化测试。

期望常数已在写测试前手工预核算（2/3、['b']、0.6667），
以规避本项目反复出现的"测试期望值自身算错"陷阱(见 commentary §33.3/§34.3/§35.3)。
"""
import pytest

from svagent.improvement_memory import (
    EvaluationContext, ImprovementMemory, ImprovementRecord, TransferDecision,
)

CTX = EvaluationContext("Claude Opus 5.5", "workspace", "git_config", 1)


def _rec(rid="r1", predicted=None, fixed=None, broken=None, cause="c1", **kw):
    return ImprovementRecord(
        record_id=rid, root_cause=cause, rationale="测试改动", code_ref="f.py:10",
        predicted=list(predicted or []), observed_fixed=list(fixed or []),
        observed_broken=list(broken or []), context=kw.pop("context", CTX), **kw
    )


# --- 四要素 / 配对 ---
def test_prediction_pairing_and_hit_rate():
    r = _rec(predicted=["a", "b", "c"], fixed=["a", "c"])
    assert r.prediction_hit_rate() == pytest.approx(2 / 3)   # 手工预核算
    assert r.predictions_missed() == ["b"]                    # 手工预核算
    assert r.unexpected_fixes() == []


def test_unexpected_fix_detected():
    r = _rec(predicted=["a"], fixed=["a", "b"])
    assert r.unexpected_fixes() == ["b"]
    assert r.prediction_hit_rate() == 1.0


def test_no_prediction_is_unfalsifiable():
    r = _rec(predicted=[], fixed=["a"])
    assert r.falsifiable is False
    assert r.prediction_hit_rate() is None


def test_regression_flag():
    assert _rec(broken=["new_bug"]).has_regression() is True
    assert _rec(broken=[]).has_regression() is False


def test_causality_gate_rejects_hindsight():
    bad = _rec(predicted=["a"], predicted_at="2026-10-02", observed_at="2026-10-01")
    ok = _rec(predicted=["a"], predicted_at="2026-10-01", observed_at="2026-10-02")
    assert bad.causality_ok() is False
    assert ok.causality_ok() is True
    assert _rec().causality_ok() is True  # 缺时间戳不判违规


# --- 分组 / 可证伪率 ---
def test_group_by_root_cause_and_falsifiability_rate():
    mem = ImprovementMemory()
    mem.record_many([
        _rec("1", predicted=["a"], cause="causeA"),
        _rec("2", predicted=[], cause="causeA"),
        _rec("3", predicted=["b"], cause="causeB"),
    ])
    g = mem.group_by_root_cause()
    assert len(g["causeA"]) == 2 and len(g["causeB"]) == 1
    assert mem.falsifiability_rate() == pytest.approx(2 / 3)  # 手工预核算


# --- 迁移决策（规则写死，优先级可测）---
def test_transfer_regression_beats_high_hitrate():
    """即使历史命中率高，只要有回归就必须 revise。"""
    mem = ImprovementMemory()
    mem.record_many([
        _rec("1", predicted=["a"], fixed=["a"], cause="c"),      # hit=1.0
        _rec("2", predicted=["a"], fixed=["a"], broken=["x"], cause="c"),  # 有回归
    ])
    d = mem.transfer_decision(CTX)[0]
    assert d.action == "revise" and d.regression is True


def test_transfer_hindsight_or_unfalsifiable_downgrades():
    mem = ImprovementMemory()
    bad = _rec("1", predicted=["a"], cause="c", predicted_at="2026-10-02", observed_at="2026-10-01")
    mem.record(bad)
    assert mem.transfer_decision(CTX)[0].action == "verify"

    mem2 = ImprovementMemory()
    mem2.record(_rec("2", predicted=[], fixed=["a"], cause="c"))
    assert mem2.transfer_decision(CTX)[0].action == "verify"


def test_transfer_low_hitrate_revise():
    mem = ImprovementMemory()
    mem.record(_rec("1", predicted=["a", "b"], fixed=["a"], cause="c"))  # hit=0.5 < 0.5? 等于0.5
    # 0.5 不满足 <0.5，落到上下文兼容→因无兼容差异且hit<0.8→verify；用0.25验证revise分支
    mem2 = ImprovementMemory()
    mem2.record(_rec("2", predicted=["a", "b", "c", "d"], fixed=["a"], cause="c"))  # hit=0.25
    assert mem2.transfer_decision(CTX)[0].action == "revise"


def test_transfer_context_mismatch_verify():
    mem = ImprovementMemory()
    mem.record(_rec("1", predicted=["a"], fixed=["a"], cause="c"))  # hit=1.0 兼容
    d = mem.transfer_decision(EvaluationContext("Gemini 3.8 Flash", "TB4", "coding", 9))[0]
    assert d.action == "verify" and "上下文" in d.reason


def test_transfer_retain_when_compatible_and_high():
    mem = ImprovementMemory()
    mem.record(_rec("1", predicted=["a"], fixed=["a"], cause="c"))
    d = mem.transfer_decision(CTX)[0]
    assert d.action == "retain" and d.hit_rate == 1.0


# --- 知识库桥接 ---
def test_bridge_includes_prediction_and_observation():
    mem = ImprovementMemory()
    mem.record(_rec("b", predicted=["a"], fixed=["a"]))
    kw = mem.to_knowledge_item_kwargs()[0]
    assert "predicted=a" in kw["support"][0]
    assert "ctx=" in kw["support"][-1]
    assert "事前预测" in kw["action"] and "落空" in kw["action"]


if __name__ == "__main__":
    pytest.main([__file__, "-q"])


# --- 元原则固化：复述 vs 长牙 ---
def test_meta_principle_codified_and_recallable():
    """KB-META01：借鉴的终点是长出会拦/会判/会降级的动作，不是复述。"""
    from svagent.knowledge_base import KnowledgeBase
    kb = KnowledgeBase.load("knowledge_base_store.json")
    it = kb.items.get("KB-META01")
    assert it is not None
    assert it.improvement_class == "preserve"
    assert "复述" in it.mechanism and "牙齿" in it.mechanism
    assert it.addressable is True
    tags = ["借鉴", "复述", "内化", "方法迁移", "读到好方法", "外部高知", "研究借鉴"]
    assert any(h.item_id == "KB-META01" for h in kb.recall(tags))
    inj = kb.injections_for(tags)
    assert any("复述" in s for s in inj)
