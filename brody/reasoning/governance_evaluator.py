"""brody/reasoning/governance_evaluator.py — Évaluateur de gouvernance mathématique Lyapunov et Proof of Governance.

Calcule la fonction de Lyapunov L(x), vérifie les tickets de décision et les consensus multi-agents,
sous frontière absolue KX108_ONLY (les résultats sont des avis consultatifs, jamais une autorisation).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

from brody.reasoning.contracts import REASONING_BOUNDARY

_ALPHA = 0.25  # Dette thermique (thermo debt)
_BETA = 0.20   # Dette computationnelle
_GAMMA = 0.30  # Instabilité instantanée (violence score)
_DELTA = 0.15  # Dérive de la ligne temporelle (timeline drift)
_ETA = 0.10    # Intention / correction de contrôle


@dataclass
class GovernedStateVector:
    """Vecteur d'état gouverné : ω = (I, ΔE, ΔC, V_inst, Δτ, F)."""
    I: float = 1.0
    delta_E: float = 0.0
    delta_C: float = 0.0
    V_inst: float = 0.0
    delta_tau: float = 0.0
    F: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "I": self.I,
            "delta_E": self.delta_E,
            "delta_C": self.delta_C,
            "V_inst": self.V_inst,
            "delta_tau": self.delta_tau,
            "F": self.F,
        }


@dataclass
class LyapunovResult:
    action_id: str
    L_value: float
    is_stable: bool
    partition: str  # "X_A" (ALLOW), "X_H" (HOLD), "X_B" (BLOCK), "X_UNKNOWN"

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "L_value": self.L_value,
            "is_stable": self.is_stable,
            "partition": self.partition,
            **REASONING_BOUNDARY,
        }


def compute_lyapunov(action_id: str, sv: GovernedStateVector) -> LyapunovResult:
    """Calcule la fonction de gouvernance de Lyapunov L(x)."""
    L = (
        _ALPHA * sv.delta_E
        + _BETA * sv.delta_C
        + _GAMMA * sv.V_inst
        + _DELTA * sv.delta_tau
        - _ETA * sv.I
    )
    is_stable = abs(L) < 0.05
    if sv.V_inst > 0.5:
        partition = "X_B"
    elif sv.delta_tau > 0.5:
        partition = "X_H"
    elif is_stable:
        partition = "X_A"
    else:
        partition = "X_UNKNOWN"

    return LyapunovResult(
        action_id=action_id,
        L_value=round(L, 6),
        is_stable=is_stable,
        partition=partition,
    )


@dataclass
class DecisionTicket:
    """Ticket de décision formel : valid ⟺ sigma_ok ∧ tau_ok ∧ inv_ok."""
    action: str
    reason: str
    s_ref: Dict[str, Any]
    sigma_ok: bool
    tau_ok: bool
    inv_ok: bool
    ticket_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def valid(self) -> bool:
        return self.sigma_ok and self.tau_ok and self.inv_ok

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticket_id": self.ticket_id,
            "timestamp": self.timestamp,
            "action": self.action,
            "reason": self.reason,
            "s_ref_keys": list(self.s_ref.keys()),
            "sigma_ok": self.sigma_ok,
            "tau_ok": self.tau_ok,
            "inv_ok": self.inv_ok,
            "valid": self.valid(),
            **REASONING_BOUNDARY,
        }


def evaluate_multi_agent_consensus(votes: List[str]) -> str:
    """Règle de priorité stricte Obsidia : BLOCK > HOLD > ALLOW."""
    cleaned = [str(v).strip().upper() for v in votes]
    if "BLOCK" in cleaned or "BLOCK_CANDIDATE" in cleaned:
        return "BLOCK"
    if "HOLD" in cleaned:
        return "HOLD"
    if all(v == "ALLOW" for v in cleaned) and cleaned:
        return "ALLOW"
    return "HOLD"
