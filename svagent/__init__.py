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
    # 在线修复诚实性门禁（§81：从 EvoSteer 在线自演化图编排编译——运行中途编辑/rerun-drop/执行特征驱动/参考锚定价值）
    "check_online_repair_honesty": ("svagent.online_repair_honesty", "check_online_repair_honesty"),
    "OnlineRepairVerdict": ("svagent.online_repair_honesty", "OnlineRepairVerdict"),
    "online_repair_honesty_live_regression": ("svagent.online_repair_honesty", "live_regression"),
    # 技能准入校准门禁（§82：从 EvoSteer Validated Skill Admission 编译——先试用/配对反事实/共享预算序贯检验/退役机制）
    "check_skill_admission_calibration": ("svagent.skill_admission_calibration", "check_skill_admission_calibration"),
    "SkillAdmissionVerdict": ("svagent.skill_admission_calibration", "SkillAdmissionVerdict"),
    "skill_admission_calibration_live_regression": ("svagent.skill_admission_calibration", "live_regression"),
    # 失败因果可识别性门禁（§83：从 MLLM 因果任务分解编译——端到端/共现/受控干预/上游vs内在）
    "check_failure_causal_identifiability": ("svagent.failure_causal_identifiability", "check_failure_causal_identifiability"),
    "FailureCausalVerdict": ("svagent.failure_causal_identifiability", "FailureCausalVerdict"),
    "failure_causal_identifiability_live_regression": ("svagent.failure_causal_identifiability", "live_regression"),
    # 因果贡献诚实性门禁（§84：从 MLLM N-Score/S-Score 编译——必要充分/下界/单调性/瓶颈稀疏）
    "check_causal_contribution_honesty": ("svagent.causal_contribution_honesty", "check_causal_contribution_honesty"),
    "CausalContributionVerdict": ("svagent.causal_contribution_honesty", "CausalContributionVerdict"),
    "causal_contribution_honesty_live_regression": ("svagent.causal_contribution_honesty", "live_regression"),
    # 配置冲突隔离门禁（§85：从 UltraBERT 掩码比冲突编译——冲突识别/机制隔离/饱和后比较/不一刀切折中）
    "check_config_conflict_isolation": ("svagent.config_conflict_isolation", "check_config_conflict_isolation"),
    "ConfigConflictVerdict": ("svagent.config_conflict_isolation", "ConfigConflictVerdict"),
    "config_conflict_isolation_live_regression": ("svagent.config_conflict_isolation", "live_regression"),
    # 计算饱和诚实性门禁（§86：从 UltraBERT loss≠下游编译——饱和报告/loss与下游分离/边际收益/不冒充）
    "check_compute_saturation_honesty": ("svagent.compute_saturation_honesty", "check_compute_saturation_honesty"),
    "ComputeSaturationVerdict": ("svagent.compute_saturation_honesty", "ComputeSaturationVerdict"),
    "compute_saturation_honesty_live_regression": ("svagent.compute_saturation_honesty", "live_regression"),
    # 归纳泛化结构诚实性门禁（§87：从 Latent Taxonomies 编译——归纳优势/结构可恢复/记忆vs压缩/规模效应）
    "check_induction_structure_honesty": ("svagent.induction_structure_honesty", "check_induction_structure_honesty"),
    "InductionStructureVerdict": ("svagent.induction_structure_honesty", "InductionStructureVerdict"),
    "induction_structure_honesty_live_regression": ("svagent.induction_structure_honesty", "live_regression"),
    # 结构覆盖边界诚实性门禁（§88：从 Latent Taxonomies context覆盖weights 编译——权重上下文分离/覆盖披露/冲突测试/上限陈述）
    "check_context_override_boundary": ("svagent.context_override_boundary", "check_context_override_boundary"),
    "ContextOverrideVerdict": ("svagent.context_override_boundary", "ContextOverrideVerdict"),
    "context_override_boundary_live_regression": ("svagent.context_override_boundary", "live_regression"),
    # FJ 取证内核（阶段1-2：把门禁从填表裁判改成取证法官）
    "EvidenceBundle": ("svagent.forensics", "EvidenceBundle"),
    "ForensicSpec": ("svagent.forensics", "ForensicSpec"),
    "DimensionSpec": ("svagent.forensics", "DimensionSpec"),
    "adjudicate": ("svagent.forensics", "adjudicate"),
    "forensics_live_regression": ("svagent.forensics", "live_regression"),
    "adjudicate_criterion_origin_honesty": ("svagent.forensic_gates", "adjudicate_criterion_origin_honesty"),
    "adjudicate_verification_boundary_honesty": ("svagent.forensic_gates", "adjudicate_verification_boundary_honesty"),
    "adjudicate_proof_boundary_honesty": ("svagent.forensic_gates", "adjudicate_proof_boundary_honesty"),
    "adjudicate_all": ("svagent.forensic_gates", "adjudicate_all"),
    "forensic_gates_live_regression": ("svagent.forensic_gates", "live_regression"),
    "verify_chain": ("svagent.evidence_chain", "verify_chain"),
    "require_intact": ("svagent.evidence_chain", "require_intact"),
    "ChainIntegrityError": ("svagent.evidence_chain", "ChainIntegrityError"),
    "audit_all": ("svagent.evidence_chain", "audit_all"),
    "evidence_chain_live_regression": ("svagent.evidence_chain", "live_regression"),
    # FJ 成长桥（阶段4：真实精研线 → 模拟自进化线的转换层）
    "ConsumptionRecord": ("svagent.growth_bridge", "ConsumptionRecord"),
    "BridgeReport": ("svagent.growth_bridge", "BridgeReport"),
    "kb_to_opportunities": ("svagent.growth_bridge", "kb_to_opportunities"),
    "forensic_gaps_to_opportunities": ("svagent.growth_bridge", "forensic_gaps_to_opportunities"),
    "bridge_into_pdca": ("svagent.growth_bridge", "bridge_into_pdca"),
    "save_consumption": ("svagent.growth_bridge", "save_consumption"),
    "growth_bridge_live_regression": ("svagent.growth_bridge", "live_regression"),
    # §90 自主运维首日：静默失败诚实性门禁 + FJ 取证扩展入口
    "SilentFailureVerdict": ("svagent.silent_failure_honesty", "SilentFailureVerdict"),
    "check_silent_failure_honesty": ("svagent.silent_failure_honesty", "check_silent_failure_honesty"),
    "silent_failure_honesty_live_regression": ("svagent.silent_failure_honesty", "live_regression"),
    "adjudicate_silent_failure_honesty": ("svagent.forensic_gates_ext", "adjudicate_silent_failure_honesty"),
    "forensic_gates_ext_live_regression": ("svagent.forensic_gates_ext", "live_regression"),
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
