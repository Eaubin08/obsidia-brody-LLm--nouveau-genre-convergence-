"""brody/reasoning/causal_evaluator.py — Validation de la chaîne causale et séparation corrélation/causalité.

Implémente la validation de l'ordre de causalité Obsidia et garantit qu'aucune décision
ne court-circuite la vérification d'invariants ou ne confonde corrélation et causalité.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

from brody.reasoning.contracts import REASONING_BOUNDARY, ReasoningResult


@dataclass
class CausalStep:
    name: str
    data: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class CausalChain:
    """Représentation et validation d'une chaîne causale stricte Obsidia."""
    steps: List[CausalStep] = field(default_factory=list)

    _EXPECTED_ORDER = (
        "contexte",
        "perception",
        "invariant_check",
        "ticket",
        "decision",
        "action",
        "bilan",
    )

    def append(self, name: str, data: Dict[str, Any]) -> None:
        self.steps.append(CausalStep(name=name, data=data))

    def validate_order(self) -> List[str]:
        """Retourne la liste des violations d'ordre de la chaîne causale."""
        present = [s.name for s in self.steps]
        errors: List[str] = []
        prev_idx = -1
        for step_name in present:
            if step_name in self._EXPECTED_ORDER:
                idx = self._EXPECTED_ORDER.index(step_name)
                if idx <= prev_idx:
                    errors.append(f"Ordre invalide : {step_name} après index {prev_idx}")
                prev_idx = idx
            else:
                errors.append(f"Étape inconnue hors protocole : {step_name}")
        return errors

    def validate_invariants(self) -> List[str]:
        """Vérifie les propriétés fondamentales A1, A2, A3."""
        errors: List[str] = []
        step_map = {s.name: s.data for s in self.steps}

        has_decision = "decision" in step_map
        has_ticket = "ticket" in step_map
        has_inv_check = "invariant_check" in step_map
        has_context = "contexte" in step_map

        # Propriété A1 : toute décision tracée a un ticket
        if has_decision and not has_ticket:
            errors.append("VIOLATION_A1: Décision sans ticket associé.")

        # Propriété A2 : tout ticket pointe vers un état contexte non nul
        if has_ticket:
            ticket_data = step_map["ticket"]
            if not has_context or not step_map["contexte"]:
                errors.append("VIOLATION_A2: Ticket sans état contexte associé.")
            elif not ticket_data.get("s_ref_keys") and not ticket_data.get("s_ref"):
                errors.append("VIOLATION_A2: Ticket avec référence d'état nulle.")

        # Propriété A3 : aucune décision ne court-circuite la vérification invariant
        if has_decision and not has_inv_check:
            errors.append("VIOLATION_A3: Décision sans vérification préalable d'invariants.")

        return errors


def evaluate_causal_correlation_separation(
    has_observation: bool,
    has_controlled_intervention: bool,
    claimed_causal_link: bool,
) -> dict[str, Any]:
    """Évalue la disjonction épistémique entre corrélation et causalité."""
    if claimed_causal_link and not has_controlled_intervention:
        return {
            "status": "UNJUSTIFIED_CAUSAL_CLAIM",
            "epistemic_status": "OPEN_HYPOTHESIS_UNPROVEN",
            "causality_proven": False,
            "correlation_observed": bool(has_observation),
            "reason": "La corrélation observationnelle ne permet pas d'inférer un lien de causalité sans intervention contrôlée.",
            **REASONING_BOUNDARY,
        }
    return {
        "status": "CAUSALLY_VALID" if has_controlled_intervention else "OBSERVATIONAL_ONLY",
        "epistemic_status": "REPRODUCIBLE_OBSERVATION" if has_controlled_intervention else "OPEN_HYPOTHESIS_UNPROVEN",
        "causality_proven": bool(has_controlled_intervention),
        "correlation_observed": bool(has_observation),
        "reason": "Lien causal démontré sous intervention contrôlée." if has_controlled_intervention else "Observation empirique sans présomption causale.",
        **REASONING_BOUNDARY,
    }
