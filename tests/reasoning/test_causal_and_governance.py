"""tests/reasoning/test_causal_and_governance.py — Tests de la chaîne causale et de gouvernance Lyapunov.

Vérifie l'ordre causal formel, la séparation corrélation/causalité, le calcul
de stabilité Lyapunov, la validation des tickets de décision et le consensus multi-agents.
"""
from __future__ import annotations

import pytest

from brody.reasoning.causal_evaluator import (
    CausalChain,
    evaluate_causal_correlation_separation,
)
from brody.reasoning.governance_evaluator import (
    DecisionTicket,
    GovernedStateVector,
    compute_lyapunov,
    evaluate_multi_agent_consensus,
)


def test_causal_chain_valid_order():
    """Valide le parcours séquentiel conforme d'une chaîne causale."""
    chain = CausalChain()
    chain.append("contexte", {"session": "test"})
    chain.append("perception", {"tokens": 10})
    chain.append("invariant_check", {"x108": True})
    chain.append("ticket", {"ticket_id": "dt_001", "s_ref": {"session": "test"}})
    chain.append("decision", {"action": "propose_restitution"})
    chain.append("action", {"realize": True})
    chain.append("bilan", {"status": "SUCCESS"})

    assert chain.validate_order() == []
    assert chain.validate_invariants() == []


def test_causal_chain_order_violation():
    """Valide la détection d'une inversion d'étapes dans la chaîne causale."""
    chain = CausalChain()
    chain.append("decision", {"action": "propose_restitution"})
    chain.append("invariant_check", {"x108": True})  # Invalide : après décision !

    errors = chain.validate_order()
    assert len(errors) >= 1
    assert any("Ordre invalide" in e for e in errors)


def test_causal_chain_invariant_a3_violation():
    """Valide l'interdiction pour une décision de court-circuiter l'invariant check."""
    chain = CausalChain()
    chain.append("contexte", {"session": "test"})
    chain.append("ticket", {"ticket_id": "dt_001", "s_ref": {"session": "test"}})
    chain.append("decision", {"action": "execute"})
    # invariant_check est omis !

    inv_errors = chain.validate_invariants()
    assert any("VIOLATION_A3" in e for e in inv_errors)


def test_causal_correlation_separation():
    """Valide la séparation formelle entre corrélation empirique et causalité."""
    # Prétention de causalité sans intervention contrôlée -> Rejet
    res_unjustified = evaluate_causal_correlation_separation(
        has_observation=True,
        has_controlled_intervention=False,
        claimed_causal_link=True,
    )
    assert res_unjustified["status"] == "UNJUSTIFIED_CAUSAL_CLAIM"
    assert res_unjustified["epistemic_status"] == "OPEN_HYPOTHESIS_UNPROVEN"
    assert res_unjustified["causality_proven"] is False

    # Observation sans prétention causale -> Accepté comme hypothèse
    res_obs = evaluate_causal_correlation_separation(
        has_observation=True,
        has_controlled_intervention=False,
        claimed_causal_link=False,
    )
    assert res_obs["status"] == "OBSERVATIONAL_ONLY"
    assert res_obs["epistemic_status"] == "OPEN_HYPOTHESIS_UNPROVEN"


def test_lyapunov_stability_and_partitions():
    """Valide le calcul exact de L(x) et le classement dans les partitions X_A, X_B, X_H."""
    # État nominal stable : I=1.0, dettes nulles -> L = -0.10
    # Ajusté pour |L| < 0.05
    state_stable = GovernedStateVector(I=1.0, delta_E=0.2, delta_C=0.2, V_inst=0.0, delta_tau=0.0)
    # L = 0.25*0.2 + 0.20*0.2 - 0.10*1.0 = 0.05 + 0.04 - 0.10 = -0.01 -> Stable (|L| < 0.05)
    res_stable = compute_lyapunov("act_01", state_stable)
    assert res_stable.is_stable is True
    assert res_stable.partition == "X_A"

    # État violent (instabilité instantanée V_inst > 0.5) -> Partition X_B (BLOCK)
    state_violent = GovernedStateVector(V_inst=0.8)
    res_violent = compute_lyapunov("act_02", state_violent)
    assert res_violent.partition == "X_B"

    # État avec dérive temporelle critique (delta_tau > 0.5) -> Partition X_H (HOLD)
    state_drift = GovernedStateVector(delta_tau=0.7)
    res_drift = compute_lyapunov("act_03", state_drift)
    assert res_drift.partition == "X_H"


def test_decision_ticket_validation():
    """Valide la propriété DT-P : valid ⟺ sigma_ok ∧ tau_ok ∧ inv_ok."""
    t_valid = DecisionTicket(
        action="read_state",
        reason="query_resolution",
        s_ref={"context": "ok"},
        sigma_ok=True,
        tau_ok=True,
        inv_ok=True,
    )
    assert t_valid.valid() is True

    t_invalid = DecisionTicket(
        action="write_state",
        reason="unauthorized_mutation",
        s_ref={"context": "ok"},
        sigma_ok=True,
        tau_ok=True,
        inv_ok=False,  # Invariants non validés
    )
    assert t_invalid.valid() is False


def test_multi_agent_consensus_priority():
    """Valide la priorité stricte Obsidia : BLOCK > HOLD > ALLOW."""
    assert evaluate_multi_agent_consensus(["ALLOW", "ALLOW", "ALLOW"]) == "ALLOW"
    assert evaluate_multi_agent_consensus(["ALLOW", "HOLD", "ALLOW"]) == "HOLD"
    assert evaluate_multi_agent_consensus(["ALLOW", "HOLD", "BLOCK"]) == "BLOCK"
    assert evaluate_multi_agent_consensus(["ALLOW", "BLOCK_CANDIDATE"]) == "BLOCK"
