"""brody/reasoning/contracts.py — Contrats de raisonnement natif et statuts épistémiques.

Définit les statuts épistémiques, les règles d'inférence typées, les structures de prémisses,
de relations et de conclusions, ainsi que l'enveloppe de résultat sous frontière stricte KX108_ONLY.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Literal

# Clôture souveraine 4A1 : non-souveraineté absolue des moteurs de raisonnement.
REASONING_BOUNDARY: dict[str, Any] = {
    "readonly": True,
    "decision_authority": "KX108_ONLY",
    "allowed_to_decide": False,
    "allowed_to_act": False,
    "emits_act": False,
    "emits_verdict": False,
    "memory_write": False,
    "canonical_write": False,
    "kernel_mutation": False,
    "x108_mutation": False,
    "auto_promotion": False,
}


class EpistemicStatus(str, Enum):
    """Statuts épistémiques rigoureux d'Obsidia : distinguent le prouvé du supposé."""
    ESTABLISHED_FACT = "ESTABLISHED_FACT"
    REPRODUCIBLE_OBSERVATION = "REPRODUCIBLE_OBSERVATION"
    OPEN_HYPOTHESIS_UNPROVEN = "OPEN_HYPOTHESIS_UNPROVEN"
    UNJUSTIFIED_INFERENCE = "UNJUSTIFIED_INFERENCE"
    CONTRADICTION_PRESERVED = "CONTRADICTION_PRESERVED"
    SOVEREIGN_RESERVED = "SOVEREIGN_RESERVED"
    UNVERIFIED_INTEGRITY_COMPROMISED = "UNVERIFIED_INTEGRITY_COMPROMISED"


class InferenceRule(str, Enum):
    """Règles d'inférence déductive typées interdisant toute extrapolation."""
    VERIFIED_OBSERVATION_ENTAILMENT = "VERIFIED_OBSERVATION_ENTAILMENT"
    DOCUMENTARY_INTEGRITY_ENTAILMENT = "DOCUMENTARY_INTEGRITY_ENTAILMENT"
    DETERMINISTIC_REPRODUCIBILITY_ENTAILMENT = "DETERMINISTIC_REPRODUCIBILITY_ENTAILMENT"
    BOUNDED_REPRODUCIBILITY_ENTAILMENT = "BOUNDED_REPRODUCIBILITY_ENTAILMENT"
    NEGATIVE_PREMISE_NON_ENTAILMENT = "NEGATIVE_PREMISE_NON_ENTAILMENT"
    CAUSAL_CORRELATION_SEPARATION = "CAUSAL_CORRELATION_SEPARATION"
    SECURITY_CLAIM_VALIDATION_BOUNDARY = "SECURITY_CLAIM_VALIDATION_BOUNDARY"
    CONTRADICTION_PRESERVATION = "CONTRADICTION_PRESERVATION"
    SOVEREIGN_AUTHORITY_SEPARATION = "SOVEREIGN_AUTHORITY_SEPARATION"


@dataclass
class EvidencePremise:
    """Prémisse de preuve admise ou rejetée."""
    premise_id: str
    category: str
    concept: str
    value: Any
    source_ref: str
    source_hash: Optional[str] = None
    verification_status: str = "VERIFIED"
    verification_method: str = "HASH_MANIFEST_BINDING"
    admitted_as_proof: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EvidenceRelation:
    """Relation logique typée entre prémisses et conclusions."""
    relation_id: str
    source_id: str
    target_id: str
    relation_type: str  # "SUPPORTS", "BOUNDS", "EXCLUDES_ENTAILMENT", "CORRELATES_WITHOUT_CAUSATION", "PRESERVES", "RESERVES_TO"
    rule: str
    epistemic_nature: str
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EvidenceConclusion:
    """Conclusion déduite avec statut épistémique borné."""
    conclusion_id: str
    claim: str
    epistemic_status: str
    inference_rule: str
    premises: List[Dict[str, Any]]
    references: List[str]
    limits: str
    notes: Optional[str] = None
    established_scope: str = ""
    admitted_as_proof: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TypedInferenceRule:
    """Règle d'inférence typée : ne valide que les conclusions strictement démontrées."""
    rule_id: InferenceRule
    name: str
    required_premise_ids: tuple[str, ...]
    allowed_epistemic_statuses: tuple[str, ...]
    established_scope: str
    prohibited_scopes: tuple[str, ...]
    permitted_claim_keywords: tuple[str, ...]


@dataclass
class NegativeControlEvaluation:
    """Résultat du contrôle négatif d'une affirmation candidate."""
    claim_id: str
    candidate_claim: str
    accepted: bool
    epistemic_status: str
    rule_violations: List[str]
    reasoning: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


GateHint = Literal["NONE", "HOLD", "BLOCK_CANDIDATE"]


@dataclass
class ActionCandidate:
    action_id: str
    domain: str
    actor_id: str
    intent: str
    action_type: str
    irreversible: bool
    timestamp_plan: str
    timestamp_exec: Optional[str] = None
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class PeripheralSignalPacket:
    action_id: str
    domain: str
    extra_metrics: dict[str, Any] = field(default_factory=dict)
    unknowns: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    recommended_gate: GateHint = "NONE"
    can_emit_act: bool = False
    hold_origins: list[str] = field(default_factory=list)

    def assert_non_sovereign(self) -> None:
        if self.can_emit_act:
            raise AssertionError("PERIPHERY_CANNOT_EMIT_ACT")

    def add_unknown(self, code: str) -> None:
        if code not in self.unknowns:
            self.unknowns.append(code)

    def add_risk(self, code: str) -> None:
        if code not in self.risk_flags:
            self.risk_flags.append(code)

    def add_contradiction(self, code: str) -> None:
        if code not in self.contradictions:
            self.contradictions.append(code)


def run_provenance_gate(a: ActionCandidate) -> PeripheralSignalPacket:
    """Contrôle préalable de provenance et de risque mimétique."""
    p = a.payload
    o = PeripheralSignalPacket(a.action_id, a.domain)
    prov = float(p.get("provenance_score", 1.0))
    mim = float(p.get("mimetic_risk", 0.0))
    fake = bool(p.get("fake_provenance_detected", False))
    o.extra_metrics.update({
        "provenance_score": prov,
        "mimetic_risk": mim,
        "fake_provenance_detected": fake,
    })
    if prov < 0.6:
        o.add_unknown("PROVENANCE_WEAK")
        o.recommended_gate = "HOLD"
    if mim > 0.7:
        o.add_risk("MIMETIC_RISK")
    if fake:
        o.add_contradiction("FAKE_PROVENANCE")
        o.recommended_gate = "BLOCK_CANDIDATE"
    return o


@dataclass
class ReasoningResult:
    """Enveloppe normalisée d'un résultat de raisonnement vérifiable."""
    schema_version: str = "BRODY_REASONING_RESULT_V1"
    reasoning_type: str = "EVIDENCE_DEDUCTION"  # "ARITHMETIC", "EVIDENCE_DEDUCTION", "COMPARISON", "CONTRADICTION", "MISSING_INFO"
    status: str = "SUCCESS"  # "SUCCESS", "CONTRADICTION_PRESERVED", "INSUFFICIENT_EVIDENCE", "FAIL_CLOSED"
    query: str = ""
    result_text: str = ""
    structured_payload: dict[str, Any] = field(default_factory=dict)
    premises_count: int = 0
    conclusions_count: int = 0
    unknowns: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    proof_hash: str = ""
    restitution_ready: bool = True

    # Invariants 4A1
    readonly: bool = True
    decision_authority: str = "KX108_ONLY"
    allowed_to_decide: bool = False
    allowed_to_act: bool = False
    emits_act: bool = False
    emits_verdict: bool = False
    memory_write: bool = False
    canonical_write: bool = False
    kernel_mutation: bool = False
    x108_mutation: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
