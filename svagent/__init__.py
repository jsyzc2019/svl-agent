"""SVL — 自组织判据环境与可验证叙事 Agent 原型。

核心命题：coding agent 能自证，不是因为模型懂代码，而是因为它把「对不对」
交给了会越来越完整的外置判据。本仓库把这条判据环境做成可被 agent 自己
递归构造的开放系统。
"""
from __future__ import annotations

import importlib

from .core import (
    Message, Claim, Sentence, Draft, Locus, Diagnostic, GroundTruth,
    is_user_said, strip_punctuation,
)
from .verifiers import (
    chapter_whitelist, claim_reference_valid, concrete_grounded,
    first_person_boundary, monologue_flag, narrative_vividness_flag,
    repeated_question_flag, coverage_check, default_verifiers,
)
from .harness import VerificationResult, check, run_loop
from .handoff import handoff_cards

__version__ = "0.13.1"

# 重型子模块按需加载：避免 `python -m svagent.experiment` 时的重复执行警告
_LAZY: dict[str, tuple[str, str]] = {
    "ExperimentConfig": ("svagent.experiment", "Config"),
    "run_monte_carlo": ("svagent.experiment", "run_monte_carlo"),
    "analytic_break_even": ("svagent.experiment", "analytic_break_even"),
    "Attack": ("svagent.evolution", "Attack"),
    "Features": ("svagent.evolution", "Features"),
    "Rule": ("svagent.evolution", "Rule"),
    "evolution_lab_spec": ("svagent.evolution", "lab_spec"),
    "make_attacks": ("svagent.evolution", "make_attacks"),
    "extract": ("svagent.evolution", "extract"),
    "learn_stump": ("svagent.evolution", "learn_stump"),
    "evaluate_rule": ("svagent.evolution", "evaluate_rule"),
    "patched_verifiers": ("svagent.evolution", "patched_verifiers"),
    "JudgmentSubstrate": ("svagent.self_evolving", "JudgmentSubstrate"),
    "Generator": ("svagent.self_evolving", "Generator"),
    "Verifier": ("svagent.self_evolving", "Verifier"),
    "RedTeam": ("svagent.self_evolving", "RedTeam"),
    "Calibrator": ("svagent.self_evolving", "Calibrator"),
    "Archivist": ("svagent.self_evolving", "Archivist"),
    "run_recursion": ("svagent.self_evolving", "run_recursion"),
    "compounding_report": ("svagent.self_evolving", "compounding_report"),
    "Environment": ("svagent.autopoiesis", "Environment"),
    "LogRecord": ("svagent.autopoiesis", "LogRecord"),
    "PredicateSpec": ("svagent.autopoiesis", "PredicateSpec"),
    "SelfOrganizingAgent": ("svagent.autopoiesis", "SelfOrganizingAgent"),
    "LogIngestor": ("svagent.autopoiesis", "LogIngestor"),
    "PredicateInducer": ("svagent.autopoiesis", "PredicateInducer"),
    "MetaLearner": ("svagent.autopoiesis", "MetaLearner"),
    "IsolatedView": ("svagent.autopoiesis", "IsolatedView"),
    "simulate_session": ("svagent.autopoiesis", "simulate_session"),
    "KnowledgeItem": ("svagent.knowledge_base", "KnowledgeItem"),
    "KnowledgeBase": ("svagent.knowledge_base", "KnowledgeBase"),
    "ReadinessThresholds": ("svagent.knowledge_base", "ReadinessThresholds"),
    "ReadinessReport": ("svagent.knowledge_base", "ReadinessReport"),
    "seed_knowledge": ("svagent.knowledge_base", "seed_knowledge"),
    # 术语歧义前置门禁（KB-SIM01 的可执行编译产物）
    "guard_disambiguation": ("svagent.disambiguation_gate", "guard"),
    "detect_ambiguous_terms": ("svagent.disambiguation_gate", "detect_ambiguous_terms"),
    "Confirmation": ("svagent.disambiguation_gate", "Confirmation"),
    "AmbiguousTerm": ("svagent.disambiguation_gate", "AmbiguousTerm"),
    "Sense": ("svagent.disambiguation_gate", "Sense"),
    "verify_gate_wiring": ("svagent.disambiguation_gate", "verify_wiring"),
    # SIM 四要素改进记忆（predicted↔observed 配对，可证伪化）
    "EvaluationContext": ("svagent.improvement_memory", "EvaluationContext"),
    "ImprovementRecord": ("svagent.improvement_memory", "ImprovementRecord"),
    "ImprovementMemory": ("svagent.improvement_memory", "ImprovementMemory"),
    "TransferDecision": ("svagent.improvement_memory", "TransferDecision"),
    # 组件归因门禁（RSI-Structure 综述 Where 维度编译，V3/V6 缺口）
    "AttributionClaim": ("svagent.component_attribution", "AttributionClaim"),
    "component_guard": ("svagent.component_attribution", "guard"),
    "verification_for": ("svagent.component_attribution", "verification_for"),
    # 评估可靠性（judge独立性/复现完整性/可扩展性）
    "JudgePanel": ("svagent.evaluation_reliability", "JudgePanel"),
    "ReproRecord": ("svagent.evaluation_reliability", "ReproRecord"),
    "EvaluationPlan": ("svagent.evaluation_reliability", "EvaluationPlan"),
    "judge_independence": ("svagent.evaluation_reliability", "judge_independence"),
    "evaluation_scalability": ("svagent.evaluation_reliability", "evaluation_scalability"),
}


def __getattr__(name: str):
    if name in _LAZY:
        module_name, attr = _LAZY[name]
        value = getattr(importlib.import_module(module_name), attr)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Message", "Claim", "Sentence", "Draft", "Locus", "Diagnostic",
    "GroundTruth", "is_user_said", "strip_punctuation",
    "chapter_whitelist", "claim_reference_valid", "concrete_grounded",
    "first_person_boundary", "monologue_flag", "narrative_vividness_flag",
    "repeated_question_flag", "coverage_check", "default_verifiers",
    "VerificationResult", "check", "run_loop", "handoff_cards",
    *sorted(_LAZY),
]
