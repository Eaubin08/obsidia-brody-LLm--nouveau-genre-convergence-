"""brody/reasoning — Moteurs de raisonnement natif et déduction formelle.

Exporte les moteurs arithmétiques exacts, d'inférence déductive, de causalité,
de gouvernance Lyapunov et le pont de pipeline cognitif complet.
"""
from __future__ import annotations

from brody.reasoning.contracts import (
    REASONING_BOUNDARY,
    EpistemicStatus,
    InferenceRule,
    EvidencePremise,
    EvidenceRelation,
    EvidenceConclusion,
    TypedInferenceRule,
    NegativeControlEvaluation,
    ReasoningResult,
    ActionCandidate,
    PeripheralSignalPacket,
    run_provenance_gate,
)
from brody.reasoning.arithmetic_engine import (
    ExactArithmeticEvaluator,
    ArithmeticEvaluationError,
    extract_arithmetic_expression,
    solve_arithmetic_query,
)
from brody.reasoning.causal_evaluator import (
    CausalStep,
    CausalChain,
    evaluate_causal_correlation_separation,
)
from brody.reasoning.governance_evaluator import (
    GovernedStateVector,
    LyapunovResult,
    compute_lyapunov,
    DecisionTicket,
    evaluate_multi_agent_consensus,
)
from brody.reasoning.evidence_reasoner import (
    GenericEvidenceReasoner,
    TYPED_INFERENCE_RULES,
)
from brody.reasoning.pipeline_bridge import (
    run_reasoning_pipeline,
)

__all__ = [
    "REASONING_BOUNDARY",
    "EpistemicStatus",
    "InferenceRule",
    "EvidencePremise",
    "EvidenceRelation",
    "EvidenceConclusion",
    "TypedInferenceRule",
    "NegativeControlEvaluation",
    "ReasoningResult",
    "ActionCandidate",
    "PeripheralSignalPacket",
    "run_provenance_gate",
    "ExactArithmeticEvaluator",
    "ArithmeticEvaluationError",
    "extract_arithmetic_expression",
    "solve_arithmetic_query",
    "CausalStep",
    "CausalChain",
    "evaluate_causal_correlation_separation",
    "GovernedStateVector",
    "LyapunovResult",
    "compute_lyapunov",
    "DecisionTicket",
    "evaluate_multi_agent_consensus",
    "GenericEvidenceReasoner",
    "TYPED_INFERENCE_RULES",
    "run_reasoning_pipeline",
]
