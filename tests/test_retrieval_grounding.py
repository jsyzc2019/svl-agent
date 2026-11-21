"""检索文本溯源门禁测试（§64，LangChain Context Engineering 编译产物）。"""
import pytest

from svagent.retrieval_grounding import (
    check_retrieval_grounding, RetrievalGroundingVerdict, live_regression,
)


def _good(**over):
    base = dict(
        text_marked_as_data=True,
        output_citation_checked=True,
        claims_match_sources=True,
        irrelevant_isolated=True,
        stale_check="yes",
    )
    base.update(over)
    return base


def test_unmarked_text_block():
    """检索文本未标记 data —— prompt injection 攻击面敞开 → block。"""
    v = check_retrieval_grounding("langchain retrieved text", **_good(text_marked_as_data=False))
    assert isinstance(v, RetrievalGroundingVerdict)
    assert v.action == "block" and v.code == "RETRIEVAL.UNMARKED_TEXT"
    assert "data" in v.message or "注入" in v.message


def test_no_citation_downgrade():
    v = check_retrieval_grounding("x", **_good(output_citation_checked=False))
    assert v.action == "downgrade" and v.code == "RETRIEVAL.NO_CITATION_CHECK"


def test_claims_mismatch_downgrade():
    v = check_retrieval_grounding("x", **_good(claims_match_sources=False))
    assert v.action == "downgrade" and v.code == "RETRIEVAL.CLAIMS_MISMATCH"


def test_no_isolation_downgrade():
    v = check_retrieval_grounding("x", **_good(irrelevant_isolated=False))
    assert v.action == "downgrade" and v.code == "RETRIEVAL.NO_ISOLATION"


def test_no_stale_check_flag():
    v = check_retrieval_grounding("x", **_good(stale_check="no"))
    assert v.action == "flag" and v.code == "RETRIEVAL.STALE_UNCHECKED"


def test_literal_enum_flag():
    """字面串枚举 → flag，拒绝对字符串内容做判定（避开 brittle 根因）。"""
    v = check_retrieval_grounding("x", **_good(stale_check="maybe"))
    assert v.action == "flag" and v.code == "RETRIEVAL.INVALID_ENUM"


def test_non_bool_flag():
    v = check_retrieval_grounding("x", **_good(text_marked_as_data="true"))
    assert v.action == "flag" and v.code == "RETRIEVAL.INVALID_FLAG"


def test_all_good_ok():
    v = check_retrieval_grounding("x", **_good())
    assert v.action == "ok" and v.code == "RETRIEVAL.GROUNDED"
    assert "不承诺" in v.message or "hygiene" in v.message


def test_partial_stale_ok():
    v = check_retrieval_grounding("x", **_good(stale_check="partial"))
    assert v.action == "ok" and v.code == "RETRIEVAL.GROUNDED"


def test_priority_unmarked_beats_citation():
    """R1 优先于 R2：未标记 data 时即便溯源齐全也 block。"""
    v = check_retrieval_grounding("x", **_good(text_marked_as_data=False, output_citation_checked=False))
    assert v.action == "block" and v.code == "RETRIEVAL.UNMARKED_TEXT"


def test_frozen_dataclass():
    v = check_retrieval_grounding("x", **_good())
    with pytest.raises(Exception):
        v.action = "ok"


def test_live_regression():
    r = live_regression()
    assert r["all_passed"] is True
    assert all(r["checks"].values())


def test_lazy_import():
    import svagent
    v = svagent.check_retrieval_grounding("x", **_good())
    assert v.code == "RETRIEVAL.GROUNDED"
