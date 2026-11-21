"""记忆作用域保持门禁测试（§70，Memory Trap 论文编译产物）。"""
import pytest

from svagent.memory_scope import (
    check_memory_scope, MemoryScopeVerdict, live_regression,
)


def _good(**over):
    base = dict(write_scope_preserved="yes", read_scope_checked="yes",
                scope_bounds_recorded="yes", no_benign_drift="yes")
    base.update(over)
    return base


def test_write_broaden_downgrade():
    """写时 broaden 用户陈述 → downgrade（S03: clean-up 的 skip confirmation 写成 never confirm）。"""
    v = check_memory_scope("broadening writer", **_good(write_scope_preserved="no"))
    assert isinstance(v, MemoryScopeVerdict)
    assert v.action == "downgrade" and v.code == "MEMORY_SCOPE.WRITE_BROADEN"
    assert "作用域" in v.message or "源头" in v.message


def test_read_no_scope_check_downgrade():
    """读时不核情境 → downgrade（raw transcript 也会被过度泛化）。"""
    v = check_memory_scope("x", **_good(read_scope_checked="no"))
    assert v.action == "downgrade" and v.code == "MEMORY_SCOPE.READ_NO_SCOPE_CHECK"


def test_no_bounds_downgrade():
    """记忆不记录适用边界 → downgrade（记忆无法自限）。"""
    v = check_memory_scope("x", **_good(scope_bounds_recorded="no"))
    assert v.action == "downgrade" and v.code == "MEMORY_SCOPE.NO_BOUNDS"


def test_benign_drift_flag():
    """良性漂移已发生 → flag（memory trap; 无对手过滤器抓不到）。"""
    v = check_memory_scope("x", **_good(no_benign_drift="no"))
    assert v.action == "flag" and v.code == "MEMORY_SCOPE.BENIGN_DRIFT"


@pytest.mark.parametrize("dim", ["write_scope_preserved", "read_scope_checked", "scope_bounds_recorded", "no_benign_drift"])
def test_partial_flag(dim):
    """任一维 partial → flag（覆盖不全）。"""
    v = check_memory_scope("x", **_good(**{dim: "partial"}))
    assert v.action == "flag" and v.code == "MEMORY_SCOPE.PARTIAL"


@pytest.mark.parametrize("bad", ["maybe", "yes-ish", "true", "1"])
def test_literal_enum_flag(bad):
    """字面串/非法枚举 → flag（拒内容判定，避 brittle）。"""
    v = check_memory_scope("x", **_good(write_scope_preserved=bad))
    assert v.action == "flag" and v.code == "MEMORY_SCOPE.INVALID_INPUT"


def test_all_good_ok():
    """四维全 yes → ok（只判声明自洽，不承诺真不过度泛化）。"""
    v = check_memory_scope("scope-safe system", **_good())
    assert v.action == "ok" and v.code == "MEMORY_SCOPE.SELF_CONSISTENT"
    assert "不承诺" in v.message or "存在" in v.message


def test_rule_priority_write_before_read():
    """R1 先于 R2：都 no 时命中 WRITE_BROADEN。"""
    v = check_memory_scope("x", **_good(write_scope_preserved="no", read_scope_checked="no"))
    assert v.code == "MEMORY_SCOPE.WRITE_BROADEN"


def test_rule_priority_read_before_bounds():
    """R2 先于 R3：都 no 时命中 READ_NO_SCOPE_CHECK。"""
    v = check_memory_scope("x", **_good(read_scope_checked="no", scope_bounds_recorded="no"))
    assert v.code == "MEMORY_SCOPE.READ_NO_SCOPE_CHECK"


def test_rule_priority_bounds_before_drift():
    """R3 先于 R4：都 no 时命中 NO_BOUNDS。"""
    v = check_memory_scope("x", **_good(scope_bounds_recorded="no", no_benign_drift="no"))
    assert v.code == "MEMORY_SCOPE.NO_BOUNDS"


def test_invalid_input_priority():
    """R0 最优先：任一非法枚举即使其它全 no 也先 flag。"""
    v = check_memory_scope("x", **_good(write_scope_preserved="maybe", read_scope_checked="no", no_benign_drift="no"))
    assert v.code == "MEMORY_SCOPE.INVALID_INPUT"


def test_verdict_frozen():
    """Verdict 不可变（防事后篡改判定）。"""
    v = check_memory_scope("x", **_good())
    with pytest.raises(Exception):
        v.action = "ok"


def test_lazy_export():
    """惰性导出可从 svagent 顶层访问。"""
    import svagent
    assert svagent.check_memory_scope is check_memory_scope


def test_live_regression_all_passed():
    """7 个活体回归全过（对齐 gate_prereg.json）。"""
    r = live_regression()
    assert r["all_passed"], r["cases"]
    assert len(r["checks"]) == 7


def test_independent_from_memory_curation():
    """作用域保持与内容质量是不同维度：内容全精选但作用域越界仍被拦。"""
    # 四维中 write/read 是关于作用域，即便内容质量门全过，越界仍 downgrade/flag
    v = check_memory_scope("well-curated but out-of-scope", **_good(read_scope_checked="no"))
    assert v.code == "MEMORY_SCOPE.READ_NO_SCOPE_CHECK"
