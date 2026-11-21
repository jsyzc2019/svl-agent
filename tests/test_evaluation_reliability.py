"""评估可靠性门禁测试（RSI-Structure §10.3/§10.5/§10.6 编译，全文到手后新增）。"""
from svagent.evaluation_reliability import (
    REPRODUCTION_FIELDS,
    JudgePanel,
    ReproRecord,
    completeness_ratio,
    judge_independence,
    reproduction_completeness,
)


def test_shared_judge_errors_downgraded():
    # 3个judge但1个独立来源 → 数量不等于独立判断
    v = judge_independence(JudgePanel("p", 3, 1, True))
    assert v.action == "downgrade"
    assert v.code == "REL.SHARED_JUDGE_ERROR"


def test_independent_judges_ok():
    assert judge_independence(JudgePanel("p", 2, 2, True)).action == "ok"


def test_single_judge_flagged():
    assert judge_independence(JudgePanel("p", 1, 1, True)).code == "REL.SINGLE_JUDGE"


def test_evaluator_drift_without_recheck_downgraded():
    v = judge_independence(JudgePanel("p", 2, 2, True, True, False))
    assert v.code == "REL.EVALUATOR_DRIFT"


def test_evaluator_drift_with_recheck_passes_independence():
    v = judge_independence(JudgePanel("p", 2, 2, True, True, True))
    assert v.code != "REL.EVALUATOR_DRIFT"


def test_no_evaluator_version_flagged():
    assert judge_independence(JudgePanel("p", 2, 2, False)).code == "REL.NO_EVALUATOR_VERSION"


def test_purposeful_selection_undoublecoded_flagged():
    r = ReproRecord(present_fields=set(REPRODUCTION_FIELDS), purposeful_selection_only=True, double_coded=False)
    v = reproduction_completeness(r)
    assert v.code == "REL.UNDOUBLECODED"


def test_full_and_doublecoded_ok():
    r = ReproRecord(present_fields=set(REPRODUCTION_FIELDS), double_coded=True)
    assert reproduction_completeness(r).action == "ok"


def test_missing_four_fields_irreproducible():
    r = ReproRecord(present_fields=set(REPRODUCTION_FIELDS[:-4]))
    v = reproduction_completeness(r)
    assert v.code == "REL.IRREPRODUCIBLE"
    assert abs(completeness_ratio(r) - 0.667) < 0.001  # 手工核算期望值


def test_reproduction_fields_count():
    assert len(REPRODUCTION_FIELDS) == 12


# --- 评估可扩展性（DeepMind essay RSI 段编译，全文核对后的增量） ---
from svagent.evaluation_reliability import EvaluationPlan, evaluation_scalability


def test_superhuman_domain_human_only_not_scalable():
    v = evaluation_scalability(EvaluationPlan("superhuman_general", True, False))
    assert v.action == "flag"
    assert v.code == "REL.NOT_SCALABLE"


def test_superhuman_domain_with_auto_verification_ok():
    v = evaluation_scalability(EvaluationPlan("superhuman_general", True, True))
    assert v.action == "ok"


def test_human_level_domain_human_ok():
    assert evaluation_scalability(EvaluationPlan("human_level", True, False)).action == "ok"


def test_auto_verified_math_domain_ok():
    assert evaluation_scalability(EvaluationPlan("mathematical_proofs", False, True)).action == "ok"
