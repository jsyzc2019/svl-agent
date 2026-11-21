"""谱系打折门禁测试：会拦/会判/会降级 + 活体回归 + brittle 对照。"""
import pytest

from svagent.lineage_guard import DiscountVerdict, discount_claim, live_regression


def test_r1_circular_claim_blocked():
    """判据从对象长出又声称独立验证对象 → block（本次 SIM 再审的真场景）。"""
    v = discount_claim(
        "新框架优于 SIM", source_overlap="full", isomorphism="high",
        claimed_independence=True,
    )
    assert v.action == "block"
    assert v.code == "LINEAGE.CIRCULAR_CLAIM"


def test_r2_high_isomorphism_downgraded():
    """高同构 + 声称独立 → downgrade，不是拦截（同谱系印证可保留但打折）。"""
    v = discount_claim(
        "框架被论文验证", source_overlap="partial", isomorphism="high",
        claimed_independence=True,
    )
    assert v.action == "downgrade"
    assert v.code == "LINEAGE.ISOMORPHIC_NOT_INDEPENDENT"


def test_r3_partial_overlap_flagged():
    v = discount_claim(
        "部分重叠也独立", source_overlap="partial", isomorphism="partial",
        claimed_independence=True,
    )
    assert v.action == "flag"
    assert v.code == "LINEAGE.PARTIAL_OVERLAP"


def test_r4_honest_label_preserved():
    """诚实标注机制借鉴、不声称独立 → ok/preserve，门禁不误伤。"""
    v = discount_claim(
        "借鉴 SWE-Gym 工程纪律", source_overlap="partial", isomorphism="high",
        claimed_independence=False,
    )
    assert v.action == "ok"
    assert v.code == "LINEAGE.PRESERVE_HONEST_LABEL"


def test_r5_true_independent_ok():
    v = discount_claim(
        "独立来源佐证", source_overlap="none", isomorphism="none",
        claimed_independence=True,
    )
    assert v.action == "ok"
    assert v.code == "LINEAGE.INDEPENDENT"


def test_r6_source_literal_string_rejected():
    """字面串来源 → flag，绝不读其内容（避开 t2 brittle 根因）。"""
    v = discount_claim(
        "x", source_overlap="同谱系", isomorphism="high", claimed_independence=True,
    )
    assert v.action == "flag"
    assert v.code == "LINEAGE.NON_SEMANTIC_INPUT"


def test_r6_isomorphism_literal_string_rejected():
    v = discount_claim(
        "x", source_overlap="full", isomorphism="高度同构", claimed_independence=True,
    )
    assert v.action == "flag"
    assert v.code == "LINEAGE.NON_SEMANTIC_INPUT"


def test_r6_no_content_matching():
    """不同字面串得到同一 flag——证明判定不看字符串内容（KB-AUDIT01 反向验证）。"""
    a = discount_claim("x", source_overlap="同谱系", isomorphism="high", claimed_independence=True)
    b = discount_claim("x", source_overlap="随便什么串", isomorphism="high", claimed_independence=True)
    assert (a.action, a.code) == (b.action, b.code) == ("flag", "LINEAGE.NON_SEMANTIC_INPUT")


def test_r6_non_bool_independence_rejected():
    v = discount_claim(
        "x", source_overlap="none", isomorphism="none", claimed_independence="true",
    )
    assert v.code == "LINEAGE.NON_SEMANTIC_INPUT"


def test_r1_priority_over_r2():
    """全同源+高同构同时命中 R1/R2 → 取更重的 block（规则优先级写死）。"""
    v = discount_claim(
        "x", source_overlap="full", isomorphism="high", claimed_independence=True,
    )
    assert v.code == "LINEAGE.CIRCULAR_CLAIM"  # 不是 ISOMORPHIC_NOT_INDEPENDENT


def test_pure_and_frozen():
    """纯函数同输入同输出；结果为冻结数据类，不可事后篡改判定。"""
    kw = dict(source_overlap="full", isomorphism="high", claimed_independence=True)
    assert discount_claim("x", **kw) == discount_claim("x", **kw)
    v = discount_claim("x", **kw)
    assert isinstance(v, DiscountVerdict)
    with pytest.raises(Exception):
        v.action = "ok"


def test_live_regression_all_passed():
    r = live_regression()
    assert r["all_passed"] is True
    assert all(r["checks"].values())


def test_live_regression_covers_four_scenarios():
    r = live_regression()
    assert r["sim_review"]["action"] == "block"
    assert r["swe_borrow"]["action"] == "ok"
    assert r["independent"]["action"] == "ok"
    assert r["brittle_control"]["action"] == "flag"
