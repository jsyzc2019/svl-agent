"""记忆溯源可恢复性诚实性门禁测试（§80，多模态 Agent 记忆综述 provenance 原则编译产物）。"""
import pytest

from svagent.memory_provenance_honesty import (
    check_memory_provenance_honesty, MemoryProvenanceVerdict, live_regression,
)
import svagent


def _good(**over):
    base = dict(provenance_by_design="yes", evidence_recoverable="yes",
                temporal_validity_tracked="yes", reversibility_supported="yes")
    base.update(over)
    return base


# --- R1-R4 downgrade ---
def test_provenance_optional_downgrade():
    """溯源是可选元数据 → downgrade（§8.1.1 少见被设计为表示属性）。"""
    v = check_memory_provenance_honesty("x", **_good(provenance_by_design="no"))
    assert isinstance(v, MemoryProvenanceVerdict)
    assert v.action == "downgrade" and v.code == "MEMORY_PROVENANCE.PROVENANCE_OPTIONAL"


def test_evidence_unrecoverable_downgrade():
    """证据不可恢复 → downgrade。"""
    v = check_memory_provenance_honesty("x", **_good(evidence_recoverable="no"))
    assert v.action == "downgrade" and v.code == "MEMORY_PROVENANCE.EVIDENCE_UNRECOVERABLE"


def test_temporal_invalid_downgrade():
    """时间有效性/冲突消解缺失 → downgrade（§8.3 核心命题）。"""
    v = check_memory_provenance_honesty("x", **_good(temporal_validity_tracked="no"))
    assert v.action == "downgrade" and v.code == "MEMORY_PROVENANCE.TEMPORAL_INVALID"
    assert "时间" in v.message or "陈旧" in v.message


def test_irreversible_downgrade():
    """更新不可逆 → downgrade（§6.6）。"""
    v = check_memory_provenance_honesty("x", **_good(reversibility_supported="no"))
    assert v.action == "downgrade" and v.code == "MEMORY_PROVENANCE.IRREVERSIBLE"


# --- 优先级短路 ---
def test_r1_before_r2():
    v = check_memory_provenance_honesty("x", **_good(provenance_by_design="no", evidence_recoverable="no"))
    assert v.code == "MEMORY_PROVENANCE.PROVENANCE_OPTIONAL"


def test_r2_before_r3():
    v = check_memory_provenance_honesty("x", **_good(evidence_recoverable="no", temporal_validity_tracked="no"))
    assert v.code == "MEMORY_PROVENANCE.EVIDENCE_UNRECOVERABLE"


def test_r3_before_r4():
    v = check_memory_provenance_honesty("x", **_good(temporal_validity_tracked="no", reversibility_supported="no"))
    assert v.code == "MEMORY_PROVENANCE.TEMPORAL_INVALID"


# --- R5 partial ---
@pytest.mark.parametrize("dim", ["provenance_by_design", "evidence_recoverable",
                                 "temporal_validity_tracked", "reversibility_supported"])
def test_partial_flag(dim):
    v = check_memory_provenance_honesty("x", **_good(**{dim: "partial"}))
    assert v.action == "flag" and v.code == "MEMORY_PROVENANCE.PARTIAL"


# --- R0 invalid enum ---
@pytest.mark.parametrize("bad", ["maybe", "yes-ish", "true", "", "Y", 1, None])
def test_invalid_enum_flag(bad):
    v = check_memory_provenance_honesty("x", **_good(provenance_by_design=bad))
    assert v.action == "flag" and v.code == "MEMORY_PROVENANCE.INVALID_INPUT"


# --- R6 ok ---
def test_all_good_ok():
    v = check_memory_provenance_honesty("x", **_good())
    assert v.action == "ok" and v.code == "MEMORY_PROVENANCE.SELF_CONSISTENT"
    assert "不承诺" in v.message or "存在≠有效性" in v.message


def test_immutable_verdict():
    v = check_memory_provenance_honesty("x", **_good())
    with pytest.raises(Exception):
        v.action = "downgrade"


def test_claim_passthrough():
    v = check_memory_provenance_honesty("my-memory", **_good())
    assert v.claim == "my-memory"


# --- 惰性导入 / 不接 run_loop ---
def test_lazy_export():
    assert callable(svagent.check_memory_provenance_honesty)
    assert svagent.MemoryProvenanceVerdict is MemoryProvenanceVerdict


def test_not_in_run_loop():
    import inspect
    src = inspect.getsource(svagent.run_loop) if hasattr(svagent, "run_loop") else ""
    assert "memory_provenance_honesty" not in src


# --- live regression ---
def test_live_regression_all_passed():
    r = live_regression()
    assert r["all_passed"] is True
    assert all(r["checks"].values())


def test_live_regression_cases_count():
    r = live_regression()
    assert len(r["cases"]) == 7
    assert len(r["checks"]) == 7
