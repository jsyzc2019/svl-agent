"""判定稳健性门禁回归测试 — SWE-Gym 工程纪律编译（认知+代码强固协同）。"""
import pytest

from svagent.judgment_robustness import (
    DEFAULT_SEED,
    LiveCase,
    ablate_conditions,
    bootstrap_stability,
    live_regression,
    validate_live_suite,
)


# ---------------- C1 bootstrap 稳定性 ----------------
def test_bootstrap_empty_flagged():
    r = bootstrap_stability([])
    assert r.action == "flag" and r.code == "ROBUST.NO_SAMPLES"


def test_bootstrap_stable_ok():
    r = bootstrap_stability([1, 1, 1, 1, 1, 1, 1, 1], n_resamples=200)
    assert r.action == "ok" and r.std < 0.10
    assert r.point_estimate == 1.0


def test_bootstrap_unstable_downgraded():
    r = bootstrap_stability([1, 0, 1, 0, 1, 0, 1, 0], n_resamples=200)
    assert r.action == "downgrade" and r.code == "ROBUST.UNSTABLE_VERDICT"
    assert r.std >= 0.10


def test_bootstrap_fixed_seed_reproducible():
    a = bootstrap_stability([1, 0, 1, 1, 0, 1], n_resamples=300, seed=7)
    b = bootstrap_stability([1, 0, 1, 1, 0, 1], n_resamples=300, seed=7)
    assert (a.std, a.ci_low, a.ci_high) == (b.std, b.ci_low, b.ci_high)
    assert a.seed == 7


def test_bootstrap_ci_contains_point():
    r = bootstrap_stability([1, 0, 1, 1, 0, 1, 1, 0, 1, 1], n_resamples=500)
    assert r.ci_low <= r.point_estimate <= r.ci_high


# ---------------- C2 条件消融 ----------------
def _rule(case, active):
    return all(case[c] for c in active)


def test_ablation_all_conditions_contribute_ok():
    full = {"a", "b"}
    cases = [{"a": 1, "b": 1}, {"a": 1, "b": 0}, {"a": 0, "b": 1}]
    base = [_rule(c, full) for c in cases]
    ablated = {n: [_rule(c, full - {n}) for c in cases] for n in full}
    r = ablate_conditions(base, ablated)
    assert r.action == "ok" and r.redundant == ()
    assert all(c.net_contribution > 0 for c in r.contributions)


def test_ablation_redundant_condition_flagged():
    full = {"a", "b", "tautology"}
    cases = [{"a": 1, "b": 1, "tautology": 1}, {"a": 1, "b": 0, "tautology": 1},
             {"a": 0, "b": 1, "tautology": 1}]
    base = [_rule(c, full) for c in cases]
    ablated = {n: [_rule(c, full - {n}) for c in cases] for n in full}
    r = ablate_conditions(base, ablated)
    assert r.action == "flag" and r.redundant == ("tautology",)


def test_ablation_length_mismatch_flagged():
    r = ablate_conditions([True, False], {"a": [True]})
    assert r.action == "flag" and r.code == "ROBUST.ABLATION_MISMATCH"


# ---------------- C3 活体样例集校验 ----------------
def _good_suite():
    return [
        LiveCase("f1", "positive", "p1"), LiveCase("f1", "negative", "n1"),
        LiveCase("f2", "positive", "p2"), LiveCase("f2", "negative", "n2"),
    ]


def test_suite_good_ok():
    r = validate_live_suite(_good_suite(), seed=DEFAULT_SEED)
    assert r.ok and r.action == "ok" and r.family_count == 2 and r.case_count == 4


def test_suite_no_seed_flagged():
    r = validate_live_suite(_good_suite(), seed=None)
    assert not r.ok and any(i.startswith("NO_FIXED_SEED") for i in r.issues)


def test_suite_unpaired_flagged():
    cases = [LiveCase("f1", "negative", "n1"), LiveCase("f1", "negative", "n2")]
    r = validate_live_suite(cases, seed=DEFAULT_SEED)
    assert any(i.startswith("UNPAIRED") for i in r.issues)


def test_suite_cap_exceeded_flagged():
    cases = [LiveCase("f1", "positive", "p1"), LiveCase("f1", "negative", "n1"),
             LiveCase("f1", "negative", "n2"), LiveCase("f1", "negative", "n3")]
    r = validate_live_suite(cases, seed=DEFAULT_SEED, cap_per_family=2)
    assert any(i.startswith("CAP_EXCEEDED") for i in r.issues)


def test_suite_duplicate_flagged():
    cases = [LiveCase("f1", "positive", "dup"), LiveCase("f1", "negative", "n1"),
             LiveCase("f2", "positive", "dup"), LiveCase("f2", "negative", "n2")]
    r = validate_live_suite(cases, seed=DEFAULT_SEED)
    assert any(i.startswith("DUPLICATE_CASE") for i in r.issues)


# ---------------- 活体回归 + 惰性导入 ----------------
def test_live_regression_all_passed():
    r = live_regression()
    assert r["all_passed"], r
    assert r["C1"]["passed"] and r["C2"]["passed"] and r["C3"]["passed"]


def test_lazy_import_registered():
    import svagent
    assert "bootstrap_stability" in svagent.__all__
    assert "ablate_conditions" in svagent.__all__
    assert "validate_live_suite" in svagent.__all__
