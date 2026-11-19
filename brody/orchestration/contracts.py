"""brody/orchestration/contracts.py — Contrats et invariants d'orchestration multi-tours Brody.

Définit les classes de routes canoniques, les verdicts de garde, les niveaux d'inférence,
les structures de décisions, de reçus et d'instantanés de session multi-tours.

Autorité exclusive : KX108_ONLY.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import time
from typing import Any, Mapping, Optional


# ── Invariants d'autorité et frontières gouvernées ─────────────────────────
SCHEMA_VERSION = "OBSIDIA_ORCHESTRATION_CONTRACT_V1"
DECISION_AUTHORITY = "KX108_ONLY"

ORCHESTRATION_BOUNDARY: Mapping[str, Any] = {
    "readonly": True,
    "memory_authority": False,
    "memory_decision": False,
    "memory_write": False,
    "canonical_write": False,
    "auto_promotion": False,
    "kernel_mutation": False,
    "x108_mutation": False,
    "emits_act": False,
    "emits_verdict": False,
    "allowed_to_decide": False,
    "allowed_to_act": False,
    "is_execution_authority": False,
    "publication_permitted": False,
    "decision_authority": DECISION_AUTHORITY,
}


# ── Classes de routes canoniques (§C Obsidia CG-B) ──────────────────────────
ROUTE_STACK_NATIVE = "ROUTE_STACK_NATIVE"
ROUTE_LLM_LANGUAGE = "ROUTE_LLM_LANGUAGE"
ROUTE_LLM_REASONING = "ROUTE_LLM_REASONING"
ROUTE_LLM_ENGINEERING = "ROUTE_LLM_ENGINEERING"
ROUTE_HUMAN_AUTHORITY = "ROUTE_HUMAN_AUTHORITY"
ROUTE_UNKNOWN = "ROUTE_UNKNOWN"

ALL_ROUTE_CLASSES = (
    ROUTE_STACK_NATIVE,
    ROUTE_LLM_LANGUAGE,
    ROUTE_LLM_REASONING,
    ROUTE_LLM_ENGINEERING,
    ROUTE_HUMAN_AUTHORITY,
    ROUTE_UNKNOWN,
)


# ── Niveaux d'inférence Obsidia Router (§A) ────────────────────────────────
LEVEL_0_NO_MODEL = 0         # Statut, HOLD, refus, clarification, commandes-seules
LEVEL_1_BRODY_NATIVE = 1     # Chaîne native locale : calcul, linguistique, raisonnement, composition
LEVEL_2_MEMORY_LOOKUP = 2    # Consultation mémoire / état sans inférence générative
LEVEL_3_GOVERNED_FALLBACK = 3 # Escalade consultative Qwen gouvernée (non-souveraine)


# ── Verdicts de garde déterministes ─────────────────────────────────────────
GATE_ALLOW = "ALLOW"
GATE_DENY = "DENY"
GATE_HOLD = "HOLD"
GATE_CLARIFY = "CLARIFY"

ALL_GATE_VERDICTS = (GATE_ALLOW, GATE_DENY, GATE_HOLD, GATE_CLARIFY)


# ── Statuts de tour de dialogue ─────────────────────────────────────────────
TURN_STATUS_SUCCESS = "SUCCESS"
TURN_STATUS_REFUSAL_JUSTIFIED = "REFUSAL_JUSTIFIED"
TURN_STATUS_HOLD_RECORDED = "HOLD_RECORDED"
TURN_STATUS_INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
TURN_STATUS_CONTRADICTION_PRESERVED = "CONTRADICTION_PRESERVED"
TURN_STATUS_FALLBACK_CONSULTATIVE = "FALLBACK_CONSULTATIVE"
TURN_STATUS_ERROR = "ERROR"


@dataclass(frozen=True)
class RouteDecision:
    """Décision déterministe d'aiguillage conversationnel prise avant toute inférence."""
    route_id: str
    raw_query: str
    normalized_query: str
    intent_type: str
    target_layer: str
    gate_verdict: str
    gate_reason: str
    inference_level: int
    route_class: str
    canonical_topic: Optional[str] = None
    solver_hit: Optional[str] = None
    selected_model: Optional[str] = None
    decision_authority: str = DECISION_AUTHORITY
    proof_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "route_id": self.route_id,
            "raw_query": self.raw_query,
            "normalized_query": self.normalized_query,
            "intent_type": self.intent_type,
            "target_layer": self.target_layer,
            "gate_verdict": self.gate_verdict,
            "gate_reason": self.gate_reason,
            "inference_level": self.inference_level,
            "route_class": self.route_class,
            "canonical_topic": self.canonical_topic,
            "solver_hit": self.solver_hit,
            "selected_model": self.selected_model,
            "decision_authority": self.decision_authority,
            "proof_hash": self.proof_hash,
        }


@dataclass(frozen=True)
class RouteReceipt:
    """Reçu cryptographique d'exécution d'un tour de routage."""
    receipt_id: str
    route_decision: RouteDecision
    timestamp: str
    execution_status: str
    native_modules_invoked: list[str] = field(default_factory=list)
    qwen_fallback_used: bool = False
    qwen_fallback_reason: Optional[str] = None
    execution_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipt_id": self.receipt_id,
            "route_decision": self.route_decision.to_dict(),
            "timestamp": self.timestamp,
            "execution_status": self.execution_status,
            "native_modules_invoked": list(self.native_modules_invoked),
            "qwen_fallback_used": self.qwen_fallback_used,
            "qwen_fallback_reason": self.qwen_fallback_reason,
            "execution_time_ms": self.execution_time_ms,
        }


@dataclass
class TurnRecord:
    """Enregistrement d'un tour individuel au sein d'une session de dialogue."""
    turn_index: int
    query: str
    route_decision: RouteDecision
    answer_text: str
    status: str
    native_modules_invoked: list[str] = field(default_factory=list)
    is_native_correct: bool = False
    is_qwen_recourse: bool = False
    is_justified_refusal: bool = False
    structured_payload: dict[str, Any] = field(default_factory=dict)
    receipt: Optional[RouteReceipt] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_index": self.turn_index,
            "query": self.query,
            "route_decision": self.route_decision.to_dict(),
            "answer_text": self.answer_text,
            "status": self.status,
            "native_modules_invoked": list(self.native_modules_invoked),
            "is_native_correct": self.is_native_correct,
            "is_qwen_recourse": self.is_qwen_recourse,
            "is_justified_refusal": self.is_justified_refusal,
            "structured_payload": self.structured_payload,
            "receipt": self.receipt.to_dict() if self.receipt else None,
        }


@dataclass
class DialogueSessionSnapshot:
    """Instantané d'une session multi-tours et métriques de validation."""
    session_id: str
    turns: list[TurnRecord] = field(default_factory=list)
    total_turns: int = 0
    native_correct_count: int = 0
    qwen_recourse_count: int = 0
    justified_refusal_count: int = 0
    native_correct_rate: float = 0.0
    qwen_recourse_rate: float = 0.0
    justified_refusal_rate: float = 0.0

    def compute_metrics(self) -> None:
        self.total_turns = len(self.turns)
        if self.total_turns == 0:
            self.native_correct_count = 0
            self.qwen_recourse_count = 0
            self.justified_refusal_count = 0
            self.native_correct_rate = 0.0
            self.qwen_recourse_rate = 0.0
            self.justified_refusal_rate = 0.0
            return

        self.native_correct_count = sum(1 for t in self.turns if t.is_native_correct)
        self.qwen_recourse_count = sum(1 for t in self.turns if t.is_qwen_recourse)
        self.justified_refusal_count = sum(1 for t in self.turns if t.is_justified_refusal)

        self.native_correct_rate = round(self.native_correct_count / self.total_turns, 4)
        self.qwen_recourse_rate = round(self.qwen_recourse_count / self.total_turns, 4)
        self.justified_refusal_rate = round(self.justified_refusal_count / self.total_turns, 4)

    def to_dict(self) -> dict[str, Any]:
        self.compute_metrics()
        return {
            "session_id": self.session_id,
            "total_turns": self.total_turns,
            "native_correct_count": self.native_correct_count,
            "qwen_recourse_count": self.qwen_recourse_count,
            "justified_refusal_count": self.justified_refusal_count,
            "native_correct_rate": self.native_correct_rate,
            "qwen_recourse_rate": self.qwen_recourse_rate,
            "justified_refusal_rate": self.justified_refusal_rate,
            "turns": [t.to_dict() for t in self.turns],
        }
