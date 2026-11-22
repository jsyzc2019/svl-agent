"""归纳泛化结构诚实性门禁测试（§87，Latent Taxonomies 编译产物）。"""
import pytest

from svagent.induction_structure_honesty import (
    check_induction_structure_honesty, InductionStructureVerdict, live_regression,
)
import svagent


def _good(**over):
    base = dict(induction_advantage_shown="yes", structure_recoverable="yes",
                memorize_vs_compress_split="yes", scale_effect_honest="yes")
    base.update(over)
    return base


def test_no_advantage_downgrade():
    v = check_induction_structure_honesty("x", **_good(induction_advantage_shown="no"))
    assert isinstance(v, InductionStructureVerdict)
    assert v.action == "downgrade" and v.code == "INDUCTION_STRUCT.NO_ADVANTAGE"


def test_structure_opaque_downgrade():
    v = check_induction_structure_honesty("x", **_good(structure_recoverable="no"))
    assert v.action == "downgrade" and v.code == "INDUCTION_STRUCT.STRUCTURE_OPAQUE"


def test_memorize_as_generalize_downgrade():
    v = check_induction_structure_honesty("x", **_good(memorize_vs_compress_split="no"))
    assert v.action == "downgrade" and v.code == "INDUCTION_STRUCT.MEMORIZE_AS_GENERALIZE"
    assert "记忆" in v.message or "压缩" in v.message


def test_scale_hidden_downgrade():
    v = check_induction_structure_honesty("x", **_good(scale_effect_honest="no"))
    assert v.action == "downgrade" and v.code == "INDUCTION_STRUCT.SCALE_HIDDEN"


def test_r1_before_r2():
    v = check_induction_structure_honesty("x", **_good(induction_advantage_shown="no", structure_recoverable="no"))
    assert v.code == "INDUCTION_STRUCT.NO_ADVANTAGE"


def test_r2_before_r3():
    v = check_induction_structure_honesty("x", **_good(structure_recoverable="no", memorize_vs_compress_split="no"))
    assert v.code == "INDUCTION_STRUCT.STRUCTURE_OPAQUE"


def test_r3_before_r4():
    v = check_induction_structure_honesty("x", **_good(memorize_vs_compress_split="no", scale_effect_honest="no"))
    assert v.code == "INDUCTION_STRUCT.MEMORIZE_AS_GENERALIZE"


@pytest.mark.parametrize("dim", ["induction_advantage_shown", "structure_recoverable",
                                 "memorize_vs_compress_split", "scale_effect_honest"])
def test_partial_flag(dim):
    v = check_induction_structure_honesty("x", **_good(**{dim: "partial"}))
    assert v.action == "flag" and v.code == "INDUCTION_STRUCT.PARTIAL"


@pytest.mark.parametrize("bad", ["maybe", "yes-ish", "true", "", "Y", 1, None])
def test_invalid_enum_flag(bad):
    v = check_induction_structure_honesty("x", **_good(induction_advantage_shown=bad))
    assert v.action == "flag" and v.code == "INDUCTION_STRUCT.INVALID_INPUT"


def test_all_good_ok():
    v = check_induction_structure_honesty("x", **_good())
    assert v.action == "ok" and v.code == "INDUCTION_STRUCT.SELF_CONSISTENT"
    assert "不承诺" in v.message or "存在≠有效性" in v.message


def test_claim_passthrough():
    v = check_induction_structure_honesty("my-lm", **_good())
    assert v.claim == "my-lm"


def test_lazy_export():
    assert callable(svagent.check_induction_structure_honesty)
    assert svagent.InductionStructureVerdict is InductionStructureVerdict


def test_not_in_run_loop():
    import inspect
    src = inspect.getsource(svagent.run_loop) if hasattr(svagent, "run_loop") else ""
    assert "induction_structure_honesty" not in src


def test_live_regression_all_passed():
    r = live_regression()
    assert r["all_passed"] is True
    assert all(r["checks"].values())


def test_live_regression_cases_count():
    r = live_regression()
    assert len(r["cases"]) == 7
    assert len(r["checks"]) == 7
