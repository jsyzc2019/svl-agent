"""跨领域迁移检验门禁测试 — KB-RSI06 / KB-SIM09 的活体编译。"""
from svagent.transfer_holdout import (
    DomainPerformance,
    HoldoutClaim,
    TransferVerdict,
    check_transfer,
    DGM_SWE_TO_POLY,
    DGM_POLY_TO_SWE,
    SYNTHETIC_OVERFIT,
    live_regression,
)


def test_dgm_swe_to_poly_absolute_drop_is_not_overfit():
    # 关键回归：SWE 0.50→Poly 0.289 绝对值降，但相对基线 0.142 增益正 → 放行
    v = check_transfer(DGM_SWE_TO_POLY)
    assert v.action == "ok"
    assert v.decision == "retain"
    assert v.gain == 0.147


def test_dgm_poly_to_swe_transfer_ok():
    v = check_transfer(DGM_POLY_TO_SWE)
    assert v.action == "ok"
    assert v.decision == "retain"
    assert v.gain == 0.045


def test_synthetic_overfit_downgraded():
    # 真 held-out 但迁移增益为负 → 过拟合源域，revise
    v = check_transfer(SYNTHETIC_OVERFIT)
    assert v.action == "downgrade"
    assert v.code == "XDOM.OVERFIT_SOURCE"
    assert v.decision == "revise"
    assert v.gain == -0.01


def test_not_held_out_flagged():
    # 目标域已被访问 → 样本内，不是迁移证据
    c = HoldoutClaim(
        DomainPerformance("s", 0.9, 100), DomainPerformance("t", 0.85, 100),
        target_baseline=0.5, target_held_out=False,
    )
    v = check_transfer(c)
    assert v.action == "flag"
    assert v.code == "XDOM.NOT_HELD_OUT"


def test_context_drift_revise():
    # 上下文变化且目标低于源 → revise
    c = HoldoutClaim(
        DomainPerformance("s", 0.9, 100), DomainPerformance("t", 0.7, 100),
        target_baseline=0.5, target_held_out=True,
        source_context="opus@bench#r3", target_context="gemini@bench#r3",
    )
    v = check_transfer(c)
    assert v.action == "downgrade"
    assert v.code == "XDOM.CONTEXT_DRIFT"
    assert v.decision == "revise"


def test_invalid_sample_flagged():
    c = HoldoutClaim(
        DomainPerformance("s", 0.9, 0), DomainPerformance("t", 0.7, 100),
        target_baseline=0.5, target_held_out=True,
    )
    assert check_transfer(c).code == "XDOM.INVALID_SAMPLE"


def test_live_regression_all_passed():
    r = live_regression()
    assert r["dgm_swe_to_poly"]["passed"] is True
    assert r["dgm_poly_to_swe"]["passed"] is True
    assert r["synthetic_overfit"]["passed"] is True
    assert r["all_passed"] is True
