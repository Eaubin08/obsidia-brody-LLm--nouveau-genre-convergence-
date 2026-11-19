"""tests/orchestration/test_qwen_fallback_governance.py — Validation du repli consultatif gouverné Qwen (Lot 7).

Garantit :
  1. Zéro appel à Qwen par défaut (pure exécution native 100% CPU).
  2. Confinement consultatif strict : aucune autorité souveraine accordée à Qwen (decision_authority = KX108_ONLY).
  3. Nettoyage des balises de réflexion privées (<thinking>, scratchpad).
  4. Réception exclusive d'un contexte présélectionné en lecture seule (jamais de dump intégral de la mémoire).
  5. Publication formellement interdite (publication_permitted = False).
"""
from __future__ import annotations

import pytest

from brody.orchestration.qwen_fallback import (
    GovernedQwenFallback,
    clean_model_output,
)


def test_qwen_fallback_disabled_by_default():
    fallback = GovernedQwenFallback(enabled=False)
    res = fallback.consult("Quelles sont les règles de gouvernance ?")

    assert res["status"] == "DISABLED"
    assert res["consultative_answer"] is None
    assert res["model_calls"] == 0
    assert fallback.model_calls_count == 0
    assert res["decision_authority"] == "KX108_ONLY"
    assert res["publication_permitted"] is False


def test_qwen_output_cleaning_and_tag_stripping():
    dirty_text = (
        "<thinking>Analyse interne et déduction cachée...</thinking>"
        "Voici la proposition consultative externe."
        "<scratchpad>Notes d'ébauche</scratchpad>"
    )
    cleaned = clean_model_output(dirty_text)
    assert cleaned == "Voici la proposition consultative externe."
    assert "<thinking>" not in cleaned
    assert "scratchpad" not in cleaned


def test_qwen_fallback_governed_consultation():
    def mock_provider(query: str, ctx: dict) -> str:
        assert ctx.get("readonly_attested") is True
        return f"<thinking>plan</thinking>Réponse consultative pour {query}"

    fallback = GovernedQwenFallback(
        enabled=True,
        model_name="qwen2.5-7b-test-mock",
        provider_fn=mock_provider,
    )

    preselected_context = {
        "user_query": "Recherche avancée",
        "readonly_attested": True,
        "selected_facts": ["Fait 1 vérifié"],
    }

    res = fallback.consult("Recherche avancée", preselected_context=preselected_context)

    assert res["status"] == "FALLBACK_CONSULTATIVE"
    assert res["author"] == "QWEN"
    assert res["decision_authority"] == "KX108_ONLY"
    assert res["is_consultative"] is True
    assert res["publication_permitted"] is False
    assert res["model_calls"] == 1
    assert fallback.model_calls_count == 1
    assert res["consultative_answer"] == "Réponse consultative pour Recherche avancée"
    assert "evidence_hash" in res
    assert res["context_summary"]["readonly_attested"] is True
