"""tests/linguistic/test_native_chain_e2e.py — Validation de la chaîne native Brody minimale.

Vérifie le parcours complet déterministe :
  Demande utilisateur
  → Analyse linguistique native (FR / EN)
  → Représentation intermédiaire (IR : tokens, groupes, dépendances, accords)
  → Réalisation linguistique de surface native.

Zéro Qwen, zéro modèle externe, zéro réseau, autorité KX108_ONLY.
"""
from __future__ import annotations

import pytest

from brody.linguistic import (
    parse_utterance,
    parse_english_utterance,
    realize_semantic_relation,
    build_grammar_correction_advisory,
    decipher_frame,
    project_ordered_flows,
)


def test_native_pipeline_french_copula_cycle():
    """Vérifie le cycle analyse -> IR -> réalisation pour une copule française."""
    raw = "Nous sommes prêts."
    frame = parse_utterance(raw, language="fr")

    # 1. Validation de l'analyse linguistique native
    assert frame.raw == raw
    analysis = frame.structural_analysis
    assert analysis is not None
    assert analysis["language"] == "fr"
    assert analysis["schema"] in ("BRODY_STRUCTURAL_LANGUAGE_V0", "BRODY_STRUCTURAL_LANGUAGE_ANALYSIS_V1")
    assert len(analysis["tokens"]) >= 3
    surface_act = getattr(frame, "surface_act", analysis.get("surface_act"))
    assert surface_act in ("declarative", "none", None)

    # 2. Validation de la représentation intermédiaire (IR)
    tokens = analysis["tokens"]
    token_raws = [t["raw"] for t in tokens]
    assert "Nous" in token_raws
    assert "sommes" in token_raws
    assert "prêts" in token_raws

    # 3. Réalisation native de surface à partir des traits
    realized = realize_semantic_relation(
        subject="Nous",
        verb_lemma="être",
        obj="prêts",
        person="1",
        number="pl",
        gender="masc",
        lang="fr",
    )
    assert realized["text"] == "Nous sommes prêts."
    assert realized["lang"] == "fr"
    assert realized["decision_authority"] == "KX108_ONLY"


def test_native_pipeline_french_compound_past_cycle():
    """Vérifie le cycle pour un verbe intransitif au passé composé avec accord être."""
    raw = "Elles sont parties."
    frame = parse_utterance(raw, language="fr")

    assert frame.raw == raw
    analysis = frame.structural_analysis
    assert analysis is not None

    # Réalisation native contrôlée
    realized = realize_semantic_relation(
        subject="Elles",
        verb_lemma="partir",
        tense="compound_past",
        person="3",
        number="pl",
        gender="fem",
        lang="fr",
    )
    assert realized["text"] == "Elles sont parties."
    assert realized["decision_authority"] == "KX108_ONLY"


def test_native_pipeline_english_grammar_cycle():
    """Vérifie le cycle d'analyse et réalisation anglaise sans LLM."""
    raw = "She is ready."
    frame = parse_english_utterance(raw)

    assert frame.raw == raw
    analysis = frame.structural_analysis
    assert analysis is not None
    assert analysis["language"] == "en"
    assert analysis["status"] == "STRUCTURALLY_ANALYZED"

    # Vérification de la chaîne verbale IR
    chain = analysis["verbal_chain"]
    assert chain is not None
    assert chain["subject"] == "she"
    assert chain["finite_auxiliary"]["surface"] == "is"
    assert chain["agreement"] == "COMPATIBLE"

    # Réalisation native anglaise
    realized = realize_semantic_relation(
        subject="She",
        verb_lemma="be",
        obj="ready",
        person="3",
        number="sg",
        lang="en",
    )
    assert realized["text"] == "She is ready."
    assert realized["lang"] == "en"


def test_native_pipeline_grammar_correction_advisory_f8():
    """Vérifie le moteur consultatif de correction grammaticale F8."""
    raw_mismatch = "He don't know."
    advisory = build_grammar_correction_advisory(raw_mismatch, language="en")

    assert advisory is not None
    assert advisory["schema"] == "BRODY_NATIVE_GRAMMAR_CORRECTION_ADVISORY_V0"
    assert advisory["language"] == "en"
    assert advisory["authority"] == "KX108_ONLY"
    assert advisory["applied"] is False
    assert len(advisory["proposals"]) > 0


def test_native_pipeline_deciphering_and_flow():
    """Vérifie le décodage structurel et la projection de flux linguistique."""
    raw = "Le chat dort."
    frame = parse_utterance(raw, language="fr")

    deciphered = decipher_frame(frame)
    assert deciphered is not None
    assert "schema" in deciphered

    flows = project_ordered_flows(frame)
    assert isinstance(flows, (list, tuple))
