"""brody/orchestration — Module d'orchestration conversationnelle unifiée Brody (Lot 7).

Fournit le point d'entrée unique raccordant l'ensemble des six lots :
  - Routage sémantique déterministe pré-inférence
  - Gardes de sécurité (DENY, HOLD, CLARIFY, ALLOW)
  - Sessions de dialogue multi-tours avec mémoire d'état persistante (B6)
  - Repli consultatif gouverné Qwen (isolé, non-souverain, désactivé par défaut)
  - Reçus d'exécution cryptographiques et métriques de validation

Autorité décisionnelle : KX108_ONLY.
"""
from __future__ import annotations

from brody.orchestration.contracts import (
    SCHEMA_VERSION,
    DECISION_AUTHORITY,
    ORCHESTRATION_BOUNDARY,
    ROUTE_STACK_NATIVE,
    ROUTE_LLM_LANGUAGE,
    ROUTE_LLM_REASONING,
    ROUTE_LLM_ENGINEERING,
    ROUTE_HUMAN_AUTHORITY,
    ROUTE_UNKNOWN,
    ALL_ROUTE_CLASSES,
    LEVEL_0_NO_MODEL,
    LEVEL_1_BRODY_NATIVE,
    LEVEL_2_MEMORY_LOOKUP,
    LEVEL_3_GOVERNED_FALLBACK,
    GATE_ALLOW,
    GATE_DENY,
    GATE_HOLD,
    GATE_CLARIFY,
    ALL_GATE_VERDICTS,
    TURN_STATUS_SUCCESS,
    TURN_STATUS_REFUSAL_JUSTIFIED,
    TURN_STATUS_HOLD_RECORDED,
    TURN_STATUS_INSUFFICIENT_EVIDENCE,
    TURN_STATUS_CONTRADICTION_PRESERVED,
    TURN_STATUS_FALLBACK_CONSULTATIVE,
    TURN_STATUS_ERROR,
    RouteDecision,
    RouteReceipt,
    TurnRecord,
    DialogueSessionSnapshot,
)

from brody.orchestration.router_core import (
    SemanticRouter,
    build_ir,
    evaluate_gates,
    normalize_utf8_mojibake,
    fold_accents,
    match_canonical_topic,
)

from brody.orchestration.qwen_fallback import (
    GovernedQwenFallback,
    clean_model_output,
)

from brody.orchestration.session_orchestrator import (
    BrodyDialogueSession,
    BrodyConversationalPipeline,
)

__all__ = [
    "SCHEMA_VERSION",
    "DECISION_AUTHORITY",
    "ORCHESTRATION_BOUNDARY",
    "ROUTE_STACK_NATIVE",
    "ROUTE_LLM_LANGUAGE",
    "ROUTE_LLM_REASONING",
    "ROUTE_LLM_ENGINEERING",
    "ROUTE_HUMAN_AUTHORITY",
    "ROUTE_UNKNOWN",
    "ALL_ROUTE_CLASSES",
    "LEVEL_0_NO_MODEL",
    "LEVEL_1_BRODY_NATIVE",
    "LEVEL_2_MEMORY_LOOKUP",
    "LEVEL_3_GOVERNED_FALLBACK",
    "GATE_ALLOW",
    "GATE_DENY",
    "GATE_HOLD",
    "GATE_CLARIFY",
    "ALL_GATE_VERDICTS",
    "TURN_STATUS_SUCCESS",
    "TURN_STATUS_REFUSAL_JUSTIFIED",
    "TURN_STATUS_HOLD_RECORDED",
    "TURN_STATUS_INSUFFICIENT_EVIDENCE",
    "TURN_STATUS_CONTRADICTION_PRESERVED",
    "TURN_STATUS_FALLBACK_CONSULTATIVE",
    "TURN_STATUS_ERROR",
    "RouteDecision",
    "RouteReceipt",
    "TurnRecord",
    "DialogueSessionSnapshot",
    "SemanticRouter",
    "build_ir",
    "evaluate_gates",
    "normalize_utf8_mojibake",
    "fold_accents",
    "match_canonical_topic",
    "GovernedQwenFallback",
    "clean_model_output",
    "BrodyDialogueSession",
    "BrodyConversationalPipeline",
]
