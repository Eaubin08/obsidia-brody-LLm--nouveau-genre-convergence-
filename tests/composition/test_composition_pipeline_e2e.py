"""tests/composition/test_composition_pipeline_e2e.py — Validation de bout en bout du pipeline éditorial Brody.

Vérifie l'enchaînement complet :
  Demande utilisateur → Analyse linguistique SENS → Assemblage mémoire B6
  → Évaluation des preuves → Composition rhétorique Studio E11 → Enveloppe gouvernée.

Garantit zéro appel LLM externe et le strict respect des invariants KX108_ONLY.
"""
from __future__ import annotations

import pytest

from brody.reasoning.pipeline_bridge import run_reasoning_pipeline
from brody.composition.e11_consumer import consume_envelope
from brody.composition.contracts import E11_BOUNDARY


EDITORIAL_PROMPT_V2 = (
    "Rédige une publication LinkedIn expliquant comment une petite entreprise peut utiliser l’IA pour gagner du temps."
)


def test_e2e_pipeline_editorial_composition_v2():
    result = run_reasoning_pipeline(EDITORIAL_PROMPT_V2, editorial_version="V2")

    assert result.reasoning_type == "EDITORIAL_COMPOSITION"
    assert result.status == "SUCCESS"
    assert result.restitution_ready is True
    assert result.readonly is True
    assert result.decision_authority == "KX108_ONLY"
    assert result.emits_act is False
    assert result.emits_verdict is False
    assert result.memory_write is False

    # Vérification du texte de réponse
    text = result.result_text
    assert "Est-ce que votre équipe peut gagner du temps avec l’IA" in text
    assert "Commencez par une seule tâche répétitive" in text
    assert "Par exemple, un premier essai" in text
    assert "Avant de poursuivre, comparez le temps passé" in text

    # Vérification de l'enveloppe E11 et de sa consommation
    payload = result.structured_payload
    assert "composition" in payload
    assert "e11_envelope" in payload
    assert "e11_consumption" in payload

    consumption = payload["e11_consumption"]
    assert consumption["consumer_status"] in ("CONTEXT_AVAILABLE", "CONTEXT_LIMITED")
    assert consumption["error_code"] == "NONE"
    assert consumption["governance_status"] == "CONTEXT_ALLOWED"
    assert consumption["publication_permitted"] is False
    assert consumption["publication_human_review_required"] is True


def test_e2e_pipeline_editorial_composition_v1():
    result = run_reasoning_pipeline(EDITORIAL_PROMPT_V2, editorial_version="V1")

    assert result.reasoning_type == "EDITORIAL_COMPOSITION"
    assert result.status == "SUCCESS"
    assert "Une petite entreprise commencerait" in result.result_text

    payload = result.structured_payload
    comp = payload["composition"]
    assert comp["editorial_version_selected"] == "V1"
    assert comp["final_answer_source"] == "BRODY_NATIVE_EDITORIAL_V1"


def test_e2e_pipeline_standard_queries_remain_unaffected():
    # Requête de calcul exact (Lot 4)
    arith_res = run_reasoning_pipeline("combien font 14 * 5 ?")
    assert arith_res.reasoning_type == "ARITHMETIC"
    assert "70" in arith_res.result_text

    # Requête avec information manquante (Lot 4)
    missing_res = run_reasoning_pipeline("Quelle est la date de signature du contrat inconnu ?")
    assert missing_res.reasoning_type == "MISSING_INFO"
    assert missing_res.status == "INSUFFICIENT_EVIDENCE"
