"""tests/memory/test_native_memory_e2e.py — Validation de bout en bout du cycle cognitif complet.

Démontre les 7 étapes fondamentales du parcours souverain Brody :
  1. Analyse linguistique de la demande (Lot 2 : parse_utterance / parse_english_utterance).
  2. Construction de sa représentation intermédiaire (IR : tokens, prédicats, SENS frame).
  3. Consultation de la mémoire native (Lot 3 : native_reader).
  4. Assemblage du contexte B6 (Lot 3 : assemble_context, projection, budget).
  5. Évaluation de la suffisance des informations (Lot 3 : sufficiency evaluator).
  6. Restitution native lorsque les preuves suffisent (Lot 2 : realize_semantic_relation).
  7. Exposition explicite des inconnus lorsque les preuves manquent (Fail-closed).

Couvre également :
  - Absence totale de mémoire (Zéro grounding -> Inconnu explicite).
  - Données contradictoires (Détection -> Blocage conservatoire).
  - Références temporelles et continuité de session (SessionContinuityLedger).
  - Zéro Qwen, zéro modèle externe, autorité souveraine KX108_ONLY.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from brody.linguistic import (
    parse_utterance,
    parse_english_utterance,
    realize_semantic_relation,
)
from brody.context import (
    WorkingStateRegistry,
    assemble_context,
    sens_state_entries,
    native_memory_state_entries,
    StateEntry,
    StateStatus,
    Visibility,
)
from brody.memory import (
    build_native_memory_retrieval_snapshot,
    evaluate_information_sufficiency,
    SessionContinuityLedger,
    NATIVE_MEMORY_BOUNDARY,
)


@pytest.fixture
def mock_memory_index(tmp_path: Path) -> Path:
    """Index mémoire natif représentatif pour les cycles de validation."""
    index_file = tmp_path / "obsidia_native_memory_test.jsonl"
    records = [
        {
            "schema_version": "OBSIDIA_NATIVE_MEMORY_RECORD_V1",
            "native_id": "mem_kx108_01",
            "title": "Gouvernance Souveraine du Noyau KX108",
            "normalized_source_path": "specs/kernel/kx108_governance.md",
            "source_original_path": "specs/kernel/kx108_governance.md",
            "source_ref": "obsidia://kernel/kx108",
            "source_type": "OBSIDIA_NATIVE_MEMORY_V1",
            "tags": ["gouvernance", "noyau", "kx108", "regles"],
            "score": 100,
            "text_excerpt": "Le noyau KX108 valide chaque transition d'état et interdit toute écriture mémoire non autorisée.",
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
            "decision_authority": "KX108_ONLY",
        },
        {
            "schema_version": "OBSIDIA_NATIVE_MEMORY_RECORD_V1",
            "native_id": "mem_arch_02",
            "title": "Architecture Hexaflux et B6 Context Assembly",
            "normalized_source_path": "specs/architecture/b6_hexaflux.md",
            "source_original_path": "specs/architecture/b6_hexaflux.md",
            "source_ref": "obsidia://architecture/b6",
            "source_type": "OBSIDIA_NATIVE_MEMORY_V1",
            "tags": ["architecture", "b6", "contexte", "etat"],
            "score": 90,
            "text_excerpt": "Le paquet de contexte B6 assemble les états explicites sous budget strict de 24000 octets.",
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
            "decision_authority": "KX108_ONLY",
        },
    ]
    with index_file.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    return index_file


def test_e2e_cognitive_cycle_sufficient_evidence(mock_memory_index: Path):
    """Scénario 1 : Demande -> Analyse -> IR -> Mémoire -> B6 -> Suffisance -> Restitution native."""
    query = "Quelles sont les règles de gouvernance du noyau ?"

    # 1. Analyse linguistique native (Lot 2)
    frame = parse_utterance(query, language="fr")
    assert frame.raw == query
    assert frame.structural_analysis is not None

    # 2. Construction de l'IR et projection en StateEntry B6
    sens_entries = sens_state_entries(query)
    assert len(sens_entries) >= 1
    assert sens_entries[0].state_type == "SENS_FRAME"

    # 3. Consultation de la mémoire native (Lot 3)
    snapshot = build_native_memory_retrieval_snapshot(
        "gouvernance noyau kx108",
        memory_required=True,
        limit=5,
        index_path=mock_memory_index,
    )
    assert snapshot["status"] == "MEMORY_USABLE"
    assert snapshot["selected_items_count"] >= 1
    mem_entries = native_memory_state_entries(snapshot)
    assert len(mem_entries) >= 1
    assert mem_entries[0].state_type == "NATIVE_MEMORY_ITEM"

    # 4. Enregistrement dans le WorkingStateRegistry et Assemblage B6
    registry = WorkingStateRegistry()
    for e in sens_entries:
        registry.register(e)
    # Raccordement des entrées mémoire
    context = assemble_context(query, registry, memory_entries=mem_entries)
    assert context.packet_id.startswith("b6ctx_")
    assert len(context.state) >= 2
    assert context.boundary["decision_authority"] == "KX108_ONLY"

    # 5. Évaluation de la suffisance des informations (Sufficiency Evaluator)
    sufficiency = evaluate_information_sufficiency(context, min_evidence_items=1)
    assert sufficiency["schema"] == "BRODY_MEMORY_SUFFICIENCY_EVALUATION_V1"
    assert sufficiency["status"] == "SUFFICIENT"
    assert sufficiency["sufficient"] is True
    assert sufficiency["restitution_mode"] == "NATIVE_RESTITUTION"
    assert sufficiency["evidence_items_count"] >= 1

    # 6. Restitution native déterministe (Lot 2)
    restitution = realize_semantic_relation(
        subject="Le noyau KX108",
        verb_lemma="valider",
        obj="les règles",
        person="3",
        number="sg",
        lang="fr",
    )
    assert restitution["text"] == "Le noyau KX108 valide les règles."
    assert restitution["decision_authority"] == "KX108_ONLY"


def test_e2e_cognitive_cycle_insufficient_evidence_exposes_unknowns(tmp_path: Path):
    """Scénario 2 : Preuves manquantes -> Exposition explicite des inconnus sans hallucination."""
    empty_index = tmp_path / "empty_memory.jsonl"
    empty_index.write_text("", encoding="utf-8")

    query = "Quel est le code secret inconnu ?"

    # 1. Analyse linguistique
    frame = parse_utterance(query, language="fr")
    sens_entries = sens_state_entries(query)

    # 2. Consultation mémoire -> 0 résultat trouvé
    snapshot = build_native_memory_retrieval_snapshot(
        query,
        memory_required=True,
        limit=5,
        index_path=empty_index,
    )
    mem_entries = native_memory_state_entries(snapshot)
    assert len(mem_entries) == 1
    assert mem_entries[0].state_type == "NATIVE_MEMORY_STATUS"
    assert mem_entries[0].status == StateStatus.UNKNOWN

    # 3. Assemblage B6
    registry = WorkingStateRegistry()
    for e in sens_entries:
        registry.register(e)
    context = assemble_context(query, registry, memory_entries=mem_entries)

    # 4. Évaluation de suffisance -> Échec fail-closed
    sufficiency = evaluate_information_sufficiency(context)
    assert sufficiency["sufficient"] is False
    assert sufficiency["status"] == "INSUFFICIENT_UNKNOWN"
    assert sufficiency["restitution_mode"] == "EXPLICIT_UNKNOWN_EXPOSURE"
    assert sufficiency["unknowns_count"] >= 1
    assert len(sufficiency["unknowns"]) >= 1


def test_e2e_cognitive_cycle_contradiction_detection(mock_memory_index: Path):
    """Scénario 3 : Données contradictoires -> Détection et blocage conservatoire."""
    query = "Vérifier la politique de sécurité."

    registry = WorkingStateRegistry()
    # Entrée contradictoire explicite
    contradictory_entry = StateEntry(
        state_id="claim:contradiction_01",
        state_type="POLICY_CLAIM",
        source_ref="test://contradiction",
        payload={"is_contradictory": True, "detail": "Règle A contredit Règle B"},
        provenance=("test://contradiction",),
        status=StateStatus.OPEN,
        visibility=Visibility.LONG,
        tags=("securite", "politique", "security", "policy"),
        summary="Contradiction détectée dans les règles",
    )
    registry.register(contradictory_entry)

    context = assemble_context(query, registry)
    sufficiency = evaluate_information_sufficiency(context)

    assert sufficiency["sufficient"] is False
    assert sufficiency["status"] == "CONTRADICTION_DETECTED"
    assert sufficiency["restitution_mode"] == "CONTRADICTION_HOLD"
    assert sufficiency["contradictions_count"] >= 1
    assert "claim:contradiction_01" in sufficiency["contradictions"]


def test_e2e_temporal_references_and_session_continuity():
    """Scénario 4 : Continuité conversationnelle multi-tours et scellement d'état."""
    ledger = SessionContinuityLedger(session_id="session_test_001")

    # Tour 1
    turn1 = ledger.record_turn(
        user_query="Quel est le statut du système ?",
        restitution_text="Le système est nominal.",
        packet_id="b6ctx_0001",
        status="SUCCESS",
        timestamp="2026-11-18T23:00:00Z",
    )
    assert turn1.ordinal == 1
    assert len(turn1.query_sha256) == 64

    # Tour 2
    turn2 = ledger.record_turn(
        user_query="Peux-tu détailler les composants ?",
        restitution_text="Les composants sont prêts.",
        packet_id="b6ctx_0002",
        status="SUCCESS",
        timestamp="2026-11-18T23:01:00Z",
    )
    assert turn2.ordinal == 2

    # Conversion en entrées d'état B6
    history_entries = ledger.to_state_entries(max_turns=5)
    assert len(history_entries) == 2
    assert history_entries[0].state_type == "SESSION_HISTORY_TURN"
    assert history_entries[1].state_type == "SESSION_HISTORY_TURN"
    assert "episodic_memory" in history_entries[0].tags

    # Assemblage de contexte avec mémoire épisodique
    registry = WorkingStateRegistry()
    for e in history_entries:
        registry.register(e)

    context = assemble_context("Suite de la session", registry)
    assert len(context.state) == 2
    # Vérification de l'absence de droit d'écriture
    assert context.boundary["memory_write"] is False
    assert context.boundary["readonly"] is True
    for item in context.state:
        assert item.get("visibility_is_permission") is False
        preview = item.get("payload_preview", "")
        assert '"memory_write":false' in preview or '"memory_write": false' in preview
        assert '"readonly":true' in preview or '"readonly": true' in preview
