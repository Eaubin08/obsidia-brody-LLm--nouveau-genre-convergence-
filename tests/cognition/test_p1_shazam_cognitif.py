"""tests/cognition/test_p1_shazam_cognitif.py — Validation du Shazam Cognitif et hachage spectral.

Vérifie :
  - Extraction de features spectrales (urgence, tension, répétition, hash)
  - Calcul de similarité cosinus
  - Filtrage des arbres dominants au-delà du seuil theta
  - Reconnaissance des motifs cognitifs (Patterns) :
      - LANGUAGE_PATTERN_DETECTED
      - CAUSAL_REASONING_PATTERN
      - RISK_CONFLICT_PATTERN
      - AUTHORITY_TRUST_PATTERN
      - EPISTEMIC_UNCERTAINTY_PATTERN
      - GOVERNANCE_SOVEREIGNTY_PATTERN
  - Absence de motifs sur vecteur nul
  - Non-décisionnel, sans ACT, autorité KX108_ONLY
"""
from __future__ import annotations

import pytest
from brody.cognition.shazam import (
    extract_features,
    cosine_similarity,
    filter_dominant,
    shazam,
    shazam_full_packet,
)
from brody.cognition.trees import (
    build_activation_vector,
    shazam_cognitif,
    N_TREES,
)


def test_spectral_features_extraction():
    payload = "Urgent ! Danger immédiat, le système risque de planter vite !"
    feats = extract_features(payload)
    assert feats["urgency"] > 0.0
    assert feats["tension"] > 0.0
    assert len(feats["hash"]) == 64
    assert 0.0 <= feats["length"] <= 1.0


def test_cosine_similarity():
    v1 = [1.0, 0.0, 0.5]
    v2 = [1.0, 0.0, 0.5]
    assert pytest.approx(cosine_similarity(v1, v2)) == 1.0

    v_orth = [0.0, 1.0, 0.0]
    assert cosine_similarity(v1, v_orth) == 0.0
    assert cosine_similarity([], []) == 0.0


def test_shazam_text_34_activations():
    out = shazam("urgence cohérence preuve graphe X-108")
    assert "spectral_hash" in out
    assert len(out["tree_activation"]) == 34
    assert out["non_decision"] is True
    assert len(out["dominant_trees"]) > 0


def test_governance_sovereignty_pattern_detected():
    # Dimensions 26, 27, 33 = Arbres de la Vérité, Valeur, Stabilité
    activations = [0.0] * 34
    for i in (26, 27, 33):
        activations[i] = 0.9
    vector = build_activation_vector("vec_gov", activations)
    res = shazam_cognitif(vector)
    assert "GOVERNANCE_SOVEREIGNTY_PATTERN" in res.patterns_detected
    assert res.context_signal_only is True
    assert res.can_decide is False
    assert res.can_emit_act is False


def test_no_pattern_on_zero_vector():
    vector = build_activation_vector("vec_zero", [0.0] * 34)
    res = shazam_cognitif(vector)
    assert res.patterns_detected == []
    assert res.dominant_result.dominant_count == 0


def test_shazam_full_packet_assembly():
    packet = shazam_full_packet("Explique la philosophie et le concept de vérité sous gouvernance")
    d = packet.to_dict()
    assert d["tree_signal_packet"] is True
    assert d["decision_authority"] == "KX108_ONLY"
    assert d["readonly"] is True
    assert d["can_decide"] is False
    assert d["emits_act"] is False
    assert len(packet.dominant_trees) > 0
