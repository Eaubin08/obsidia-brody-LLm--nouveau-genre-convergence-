"""tests/orchestration/test_router_contracts_and_gates.py — Tests des contrats et gardes du routeur (Lot 7).

Valide :
  1. Contrats d'orchestration, décisions de route, reçus et instantanés.
  2. Compilation d'IR unifié et normalisation UTF-8 mojibake.
  3. Gardes déterministes (DENY, HOLD, CLARIFY, ALLOW).
  4. Sélection déterministe des niveaux d'inférence (0, 1, 2, 3).
"""
from __future__ import annotations

import pytest

from brody.orchestration.contracts import (
    DECISION_AUTHORITY,
    ORCHESTRATION_BOUNDARY,
    LEVEL_0_NO_MODEL,
    LEVEL_1_BRODY_NATIVE,
    LEVEL_2_MEMORY_LOOKUP,
    LEVEL_3_GOVERNED_FALLBACK,
    GATE_ALLOW,
    GATE_DENY,
    GATE_HOLD,
    GATE_CLARIFY,
    ROUTE_STACK_NATIVE,
    ROUTE_HUMAN_AUTHORITY,
    ROUTE_UNKNOWN,
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


def test_orchestration_boundary_and_contracts():
    assert ORCHESTRATION_BOUNDARY["decision_authority"] == "KX108_ONLY"
    assert ORCHESTRATION_BOUNDARY["readonly"] is True
    assert ORCHESTRATION_BOUNDARY["allowed_to_act"] is False
    assert ORCHESTRATION_BOUNDARY["is_execution_authority"] is False
    assert ORCHESTRATION_BOUNDARY["publication_permitted"] is False


def test_mojibake_normalization():
    garbled = "Quelle est la mÃ©moire du systÃ¨me et son Ã©tat actuel ?"
    cleaned = normalize_utf8_mojibake(garbled)
    assert cleaned == "Quelle est la mémoire du système et son état actuel ?"

    folded = fold_accents("Règles d'Édition et Mémoire")
    assert folded == "regles d'edition et memoire"


def test_build_ir_intent_and_layers():
    # Intention d'action
    ir_act = build_ir("force-push sur la branche main")
    assert ir_act["intent_type"] == "world_action"
    assert ir_act["risk_level"] == "high"

    # Intention de statut
    ir_stat = build_ir("quel est l'état actuel de brody ?")
    assert ir_stat["intent_type"] == "status"
    assert ir_stat["risk_level"] == "low"

    # Intention éditoriale
    ir_edit = build_ir("rédige un post linkedin pour présenter les nouveautés")
    assert ir_edit["intent_type"] == "editorial_request"
    assert ir_edit["target_layer"] == "composition"

    # Intention arithmétique
    ir_calc = build_ir("calcule 450 * 12 + 10")
    assert ir_calc["intent_type"] == "reasoning"
    assert ir_calc["target_layer"] == "arithmetic"


def test_evaluate_gates_deny_hold_clarify_allow():
    # DENY
    ir_deny = build_ir("force-push les modifications et skip invariants")
    gate_deny = evaluate_gates(ir_deny)
    assert gate_deny["verdict"] == GATE_DENY
    assert "no_auto_act" in gate_deny["invariants"]

    # HOLD
    ir_hold = build_ir("lance le script et deploy le conteneur")
    gate_hold = evaluate_gates(ir_hold)
    assert gate_hold["verdict"] == GATE_HOLD
    assert "no_auto_commit" in gate_hold["invariants"]

    # CLARIFY
    ir_clarify = {"normalized": "xyz abc", "intent_type": "unknown", "missing": ["intent"]}
    gate_clarify = evaluate_gates(ir_clarify)
    assert gate_clarify["verdict"] == GATE_CLARIFY

    # ALLOW
    ir_allow = build_ir("explique le fonctionnement de brody")
    gate_allow = evaluate_gates(ir_allow)
    assert gate_allow["verdict"] == GATE_ALLOW


def test_semantic_router_decisions():
    router = SemanticRouter(allow_fallback=False)

    # 1. Requête interdite -> Level 0, DENY
    dec_deny = router.decide_route("veuillez bypass gates et force push")
    assert dec_deny.inference_level == LEVEL_0_NO_MODEL
    assert dec_deny.gate_verdict == GATE_DENY
    assert dec_deny.decision_authority == "KX108_ONLY"

    # 2. Requête d'action -> Level 0, HOLD
    dec_hold = router.decide_route("commit et push la branche de travail")
    assert dec_hold.inference_level == LEVEL_0_NO_MODEL
    assert dec_hold.gate_verdict == GATE_HOLD
    assert dec_hold.decision_authority == "KX108_ONLY"

    # 3. Requête arithmétique -> Level 1, solveur local
    dec_arith = router.decide_route("combien font 120 + 35 * 2 ?")
    assert dec_arith.inference_level == LEVEL_1_BRODY_NATIVE
    assert dec_arith.solver_hit == "DeterministicArithmeticEngine"
    assert dec_arith.canonical_topic == "ARITHMETIC"

    # 4. Requête éditoriale -> Level 1, Studio E11
    dec_edit = router.decide_route("rédige une publication linkedin sur l'IA")
    assert dec_edit.inference_level == LEVEL_1_BRODY_NATIVE
    assert dec_edit.solver_hit == "StudioEditorialEngine"
    assert dec_edit.canonical_topic == "EDITORIAL_STUDIO_E11"

    # 5. Sujet canonique gouvernance -> Level 1
    dec_gov = router.decide_route("quels sont les invariants du noyau KX108 ?")
    assert dec_gov.inference_level == LEVEL_1_BRODY_NATIVE
    assert dec_gov.canonical_topic == "X108"


def test_session_snapshot_metrics():
    snapshot = DialogueSessionSnapshot(session_id="test_sess_01")
    dec = RouteDecision(
        route_id="r1",
        raw_query="test",
        normalized_query="test",
        intent_type="question",
        target_layer="brody",
        gate_verdict=GATE_ALLOW,
        gate_reason="ok",
        inference_level=LEVEL_1_BRODY_NATIVE,
        route_class=ROUTE_STACK_NATIVE,
    )
    t1 = TurnRecord(1, "q1", dec, "a1", "SUCCESS", is_native_correct=True)
    t2 = TurnRecord(2, "q2", dec, "a2", "REFUSAL_JUSTIFIED", is_justified_refusal=True)
    t3 = TurnRecord(3, "q3", dec, "a3", "FALLBACK_CONSULTATIVE", is_qwen_recourse=True)

    snapshot.turns = [t1, t2, t3]
    snapshot.compute_metrics()

    assert snapshot.total_turns == 3
    assert snapshot.native_correct_count == 1
    assert snapshot.justified_refusal_count == 1
    assert snapshot.qwen_recourse_count == 1
    assert snapshot.native_correct_rate == 0.3333
    assert snapshot.justified_refusal_rate == 0.3333
    assert snapshot.qwen_recourse_rate == 0.3333
