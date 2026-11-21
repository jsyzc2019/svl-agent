"""记忆内容质量治理门禁测试（§68，22来源记忆生命周期谱系编译产物）。"""
import pytest

from svagent.memory_curation import (
    check_memory_curation, MemoryCurationVerdict, live_regression,
)


def _good(**over):
    base = dict(selection="yes", consolidation="yes", nondestructive=True)
    base.update(over)
    return base


def test_no_selection_downgrade():
    """全量写入无选择 → downgrade（违反 only small fraction retained）。"""
    v = check_memory_curation("full-store agent", **_good(selection="no"))
    assert isinstance(v, MemoryCurationVerdict)
    assert v.action == "downgrade" and v.code == "MEMORY.NO_SELECTION"
    assert "selection" in v.message.lower() or "选择" in v.message


def test_no_consolidation_downgrade():
    """无去重/矛盾/过时替换 → downgrade。"""
    v = check_memory_curation("x", **_good(consolidation="no"))
    assert v.action == "downgrade" and v.code == "MEMORY.NO_CONSOLIDATION"


def test_destructive_flag():
    """整理就地覆盖原store → flag。"""
    v = check_memory_curation("x", **_good(nondestructive=False))
    assert v.action == "flag" and v.code == "MEMORY.DESTRUCTIVE"


def test_partial_selection_flag():
    v = check_memory_curation("x", **_good(selection="partial"))
    assert v.action == "flag" and v.code == "MEMORY.PARTIAL"


def test_partial_consolidation_flag():
    v = check_memory_curation("x", **_good(consolidation="partial"))
    assert v.action == "flag" and v.code == "MEMORY.PARTIAL"


def test_literal_enum_flag():
    """字面串枚举 → flag（拒绝内容判定，避 brittle）。"""
    v = check_memory_curation("x", **_good(selection="maybe"))
    assert v.action == "flag" and v.code == "MEMORY.INVALID_INPUT"


def test_non_bool_flag():
    v = check_memory_curation("x", **_good(nondestructive="yes"))
    assert v.action == "flag" and v.code == "MEMORY.INVALID_INPUT"


def test_all_good_ok():
    v = check_memory_curation("x", **_good())
    assert v.action == "ok" and v.code == "MEMORY.SELF_CONSISTENT"
    assert "不承诺" in v.message or "机制" in v.message


def test_priority_selection_before_consolidation():
    """R1 优先于 R2：无选择+无整理 → NO_SELECTION。"""
    v = check_memory_curation("x", selection="no", consolidation="no", nondestructive=False)
    assert v.code == "MEMORY.NO_SELECTION"


def test_priority_consolidation_before_destructive():
    """R2 优先于 R3：无整理+破坏性 → NO_CONSOLIDATION。"""
    v = check_memory_curation("x", selection="yes", consolidation="no", nondestructive=False)
    assert v.code == "MEMORY.NO_CONSOLIDATION"


def test_priority_invalid_before_all():
    """R0 优先于一切：非法枚举 + 其他坏值 → INVALID_INPUT。"""
    v = check_memory_curation("x", selection="bad", consolidation="no", nondestructive=False)
    assert v.code == "MEMORY.INVALID_INPUT"


def test_frozen_dataclass():
    v = check_memory_curation("x", **_good())
    with pytest.raises(Exception):
        v.action = "ok"


def test_live_regression_all_pass():
    r = live_regression()
    assert r["all_passed"] is True
    assert len(r["checks"]) == 7 and all(r["checks"].values())


def test_live_regression_matches_prereg_expects():
    """活体回归逐条对齐 gate_prereg.json（实现前锁存）。"""
    import json
    from pathlib import Path
    prereg = json.loads(
        (Path(__file__).parent.parent / "audit_memory" / "gate_prereg.json").read_text(encoding="utf-8")
    )
    expects = prereg["live_regression_expects"]
    r = live_regression()
    for name, (exp_action, exp_code) in expects.items():
        assert r["cases"][name] == f"{exp_action}/{exp_code}", name


def test_verdict_independent_from_claim_text():
    """判定不依赖 claim 字面串内容（只由三机制参数决定）。"""
    a = check_memory_curation("Dreams", **_good())
    b = check_memory_curation("完全无关的名字", **_good())
    assert (a.action, a.code) == (b.action, b.code)
