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
    # 计分完整性门禁（KB-AUDIT07 活体编译，DGM 附录 H）
    "ScoringChannel": ("svagent.scoring_integrity", "ScoringChannel"),
    "IntegrityVerdict": ("svagent.scoring_integrity", "IntegrityVerdict"),
    "check_scoring_integrity": ("svagent.scoring_integrity", "check_scoring_integrity"),
    "scoring_live_regression": ("svagent.scoring_integrity", "live_regression"),
    # 跨领域迁移检验门禁（KB-RSI06 / KB-SIM09 活体编译）
    "DomainPerformance": ("svagent.transfer_holdout", "DomainPerformance"),
    "HoldoutClaim": ("svagent.transfer_holdout", "HoldoutClaim"),
    "TransferVerdict": ("svagent.transfer_holdout", "TransferVerdict"),
    "check_transfer": ("svagent.transfer_holdout", "check_transfer"),
    "transfer_live_regression": ("svagent.transfer_holdout", "live_regression"),
    # 判定稳健性（SWE-Gym 工程纪律编译：bootstrap置信度/条件消融/活体样例校验）
    "StabilityReport": ("svagent.judgment_robustness", "StabilityReport"),
    "bootstrap_stability": ("svagent.judgment_robustness", "bootstrap_stability"),
    "AblationReport": ("svagent.judgment_robustness", "AblationReport"),
    "ablate_conditions": ("svagent.judgment_robustness", "ablate_conditions"),
    "LiveCase": ("svagent.judgment_robustness", "LiveCase"),
    "SuiteReport": ("svagent.judgment_robustness", "SuiteReport"),
    "validate_live_suite": ("svagent.judgment_robustness", "validate_live_suite"),
    "robustness_live_regression": ("svagent.judgment_robustness", "live_regression"),
    # 任务复盘门禁（元学习闭环泛化：双源+可证伪+目的约束）
    "KnowledgeCandidate": ("svagent.task_retrospective", "KnowledgeCandidate"),
    "RetroVerdict": ("svagent.task_retrospective", "RetroVerdict"),
    "retrospect": ("svagent.task_retrospective", "retrospect"),
    "retro_live_regression": ("svagent.task_retrospective", "live_regression"),
    "discount_claim": ("svagent.lineage_guard", "discount_claim"),
    "DiscountVerdict": ("svagent.lineage_guard", "DiscountVerdict"),
    "lineage_live_regression": ("svagent.lineage_guard", "live_regression"),
    "check_backtest_integrity": ("svagent.backtest_integrity", "check_backtest_integrity"),
    "BacktestVerdict": ("svagent.backtest_integrity", "BacktestVerdict"),
    "backtest_live_regression": ("svagent.backtest_integrity", "live_regression"),
    # 调用点完整性门禁（§59：把 §58 认知断言编译成代码，KB-AUDIT03 粒度细化）
    "audit_call_site": ("svagent.call_site_integrity", "audit_call_site"),
    "CallSiteVerdict": ("svagent.call_site_integrity", "CallSiteVerdict"),
    "call_site_live_regression": ("svagent.call_site_integrity", "live_regression"),
    # 审查者评估漏斗保真门禁（§60：从 Claude Code 验证一文 line 122-123 编译）
    "check_review_evaluation": ("svagent.reviewer_evaluation", "check_review_evaluation"),
    "ReviewEvalVerdict": ("svagent.reviewer_evaluation", "ReviewEvalVerdict"),
    "review_eval_live_regression": ("svagent.reviewer_evaluation", "live_regression"),
    # 训练-服务信号可得性门禁（§62：从 HiGR line 366-380/425-428 编译，KB-AUDIT04 延伸）
    "check_serving_signal": ("svagent.serving_signal_gate", "check_serving_signal"),
    "ServingSignalVerdict": ("svagent.serving_signal_gate", "ServingSignalVerdict"),
    "serving_gate_live_regression": ("svagent.serving_signal_gate", "live_regression"),
    # 检索文本溯源门禁（§64：从 LangChain《Context Engineering Starts with Retrieval》line 191-194 编译）
    "check_retrieval_grounding": ("svagent.retrieval_grounding", "check_retrieval_grounding"),
    "RetrievalGroundingVerdict": ("svagent.retrieval_grounding", "RetrievalGroundingVerdict"),
    "retrieval_grounding_live_regression": ("svagent.retrieval_grounding", "live_regression"),
    # 跨会话状态连续性门禁（§65：从 Anthropic《Building always-on agents》line 27/48/91/105-110 编译）
    "check_session_continuity": ("svagent.session_continuity", "check_session_continuity"),
    "SessionContinuityVerdict": ("svagent.session_continuity", "SessionContinuityVerdict"),
    "session_continuity_live_regression": ("svagent.session_continuity", "live_regression"),
    # 记忆内容质量治理门禁（§68：从22来源记忆生命周期谱系编译——选择/整理/非破坏）
    "check_memory_curation": ("svagent.memory_curation", "check_memory_curation"),
    "MemoryCurationVerdict": ("svagent.memory_curation", "MemoryCurationVerdict"),
    "memory_curation_live_regression": ("svagent.memory_curation", "live_regression"),
    # 异步/后台委派生命周期门禁（§69：从11来源异步子Agent谱系编译——解耦/可引导/穿越压缩/完成通知）
    "check_async_delegation_lifecycle": ("svagent.async_delegation_lifecycle", "check_async_delegation_lifecycle"),
    "AsyncDelegationVerdict": ("svagent.async_delegation_lifecycle", "AsyncDelegationVerdict"),
    "async_delegation_live_regression": ("svagent.async_delegation_lifecycle", "live_regression"),
    # 记忆作用域保持门禁（§70：从 Memory Trap 论文编译——写时保留边界/读时核情境/记录适用边界/良性不漂移）
    "check_memory_scope": ("svagent.memory_scope", "check_memory_scope"),
    "MemoryScopeVerdict": ("svagent.memory_scope", "MemoryScopeVerdict"),
    "memory_scope_live_regression": ("svagent.memory_scope", "live_regression"),
    # 可证明声明边界诚实性门禁（§71：从 FlashProve 编译——证明执行≠事实证明/信任根独立/形式化边界/未覆盖披露）
    "check_proof_boundary_honesty": ("svagent.proof_boundary_honesty", "check_proof_boundary_honesty"),
    "ProofBoundaryVerdict": ("svagent.proof_boundary_honesty", "ProofBoundaryVerdict"),
    "proof_boundary_live_regression": ("svagent.proof_boundary_honesty", "live_regression"),
    # 主动介入授权正当性门禁（§72：从 Proactive AI 综述编译——目标≠授权/仲裁四关/形式≠实际控制/沉默与分级同意）
    "check_proactive_authorization": ("svagent.proactive_authorization", "check_proactive_authorization"),
    "ProactiveAuthorizationVerdict": ("svagent.proactive_authorization", "ProactiveAuthorizationVerdict"),
    "proactive_authorization_live_regression": ("svagent.proactive_authorization", "live_regression"),
    # 接口契约边界诚实性门禁（§73：从 DeepSeek 全家桶 API 编译——传入≠生效/别名≠路由/基础风控≠合规/工具免费≠零成本）
    "check_interface_contract_honesty": ("svagent.interface_contract_honesty", "check_interface_contract_honesty"),
    "InterfaceContractVerdict": ("svagent.interface_contract_honesty", "InterfaceContractVerdict"),
    "interface_contract_live_regression": ("svagent.interface_contract_honesty", "live_regression"),
    # 监督可行性门禁（§74：从认知投降谱系编译——独立观点/能力未侵蚀/监督未自我消解/表面≠系统正确）
    "check_supervision_viability": ("svagent.supervision_viability", "check_supervision_viability"),
    "SupervisionViabilityVerdict": ("svagent.supervision_viability", "SupervisionViabilityVerdict"),
    "supervision_viability_live_regression": ("svagent.supervision_viability", "live_regression"),
    # 自知诚实性门禁（§75：从 AINLP 公众号 Addy Osmani 文编译——假设先行/局限自陈/可证伪自问/技能退化披露）
    "check_self_knowledge_honesty": ("svagent.self_knowledge_honesty", "check_self_knowledge_honesty"),
    "SelfKnowledgeHonestyVerdict": ("svagent.self_knowledge_honesty", "SelfKnowledgeHonestyVerdict"),
    "self_knowledge_honesty_live_regression": ("svagent.self_knowledge_honesty", "live_regression"),
    # 验证边界诚实性门禁（§76：从 AINLP 文"绿灯只证明一件事"簇编译——覆盖边界/标准事前/证据先于总结/自我质疑）
    "check_verification_boundary_honesty": ("svagent.verification_boundary_honesty", "check_verification_boundary_honesty"),
    "VerificationBoundaryVerdict": ("svagent.verification_boundary_honesty", "VerificationBoundaryVerdict"),
    "verification_boundary_honesty_live_regression": ("svagent.verification_boundary_honesty", "live_regression"),
    # 判据来源诚实性门禁（§77：从 HarnessPro 论文"自生成判据评估自生成改进"编译——判据来源/召回边界/外部锚定/独立评审缺口）
    "check_criterion_origin_honesty": ("svagent.criterion_origin_honesty", "check_criterion_origin_honesty"),
    "CriterionOriginVerdict": ("svagent.criterion_origin_honesty", "CriterionOriginVerdict"),
    "criterion_origin_honesty_live_regression": ("svagent.criterion_origin_honesty", "live_regression"),
    # 选择性监督诚实性门禁（§78：从清华 System1/System2 Perspective"门控审查自身训练数据"编译——压制区概率/审计独立/盲点披露/反事实损失）
    "check_selective_supervision_honesty": ("svagent.selective_supervision_honesty", "check_selective_supervision_honesty"),
    "SelectiveSupervisionVerdict": ("svagent.selective_supervision_honesty", "SelectiveSupervisionVerdict"),
    "selective_supervision_honesty_live_regression": ("svagent.selective_supervision_honesty", "live_regression"),
    # 策略演化接地诚实性门禁（§79：从多模态 Agent 记忆综述 T3 自演化编译——策略可寻址/反馈归因/证据接地路径/修订经验证）
    "check_policy_evolution_grounding": ("svagent.policy_evolution_grounding", "check_policy_evolution_grounding"),
    "PolicyEvolutionGroundingVerdict": ("svagent.policy_evolution_grounding", "PolicyEvolutionGroundingVerdict"),
    "policy_evolution_grounding_live_regression": ("svagent.policy_evolution_grounding", "live_regression"),
    # 记忆溯源可恢复性诚实性门禁（§80：从多模态 Agent 记忆综述 provenance/temporal-validity 原则编译——溯源设计/证据可恢复/时间有效性/可逆性）
    "check_memory_provenance_honesty": ("svagent.memory_provenance_honesty", "check_memory_provenance_honesty"),
    "MemoryProvenanceVerdict": ("svagent.memory_provenance_honesty", "MemoryProvenanceVerdict"),
    "memory_provenance_honesty_live_regression": ("svagent.memory_provenance_honesty", "live_regression"),
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
