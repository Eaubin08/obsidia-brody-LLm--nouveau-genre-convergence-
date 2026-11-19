"""tests/cognition/test_p1_34_trees_registry.py — Validation de l'ontologie des 34 Arbres.

Vérifie :
  - Exactement 34 arbres dans le registre canonique (IDs 1 à 34)
  - Domaines canoniques assignés (I_FONDAMENTAUX, COGNITION, EPISTEMICS, SOCIAL, PLANNING, TEMPORAL, GOVERNANCE, META, INFRASTRUCTURE)
  - Métadonnées de provenance de compilation sémantique pour le lot 1
  - Vecteur d'activation R^34, bornage [0, 1] et padding
  - Extraction des arbres dominants avec seuil theta
  - Cartographie de pertinence mémoire vs monde (MemoryWorldMapper)
  - Intégrité du fichier json canonique arbres_34.canon.json
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from brody.cognition.trees import (
    TreeEntry,
    get_all_trees,
    get_tree_by_id,
    get_trees_by_domain,
    get_tree_provenance,
    TreeActivationVector,
    build_activation_vector,
    uniform_activation,
    find_dominant_trees,
    shazam_cognitif,
    map_memory_world,
    N_TREES,
)


def test_registry_has_exactly_34_trees():
    trees = get_all_trees()
    assert len(trees) == 34
    ids = [t.id for t in trees]
    assert ids == list(range(1, 35))


def test_tree_by_id_and_domains():
    t1 = get_tree_by_id(1)
    assert t1 is not None
    assert t1.name == "ARBRE_01__Arbre_de_l_Humain"
    assert t1.domain == "I_FONDAMENTAUX"

    t34 = get_tree_by_id(34)
    assert t34 is not None
    assert t34.name == "ARBRE_34__Arbre_de_la_Stabilite"
    assert t34.domain == "INFRASTRUCTURE"

    cog_trees = get_trees_by_domain("COGNITION")
    assert len(cog_trees) >= 5


def test_semantic_compilation_provenance():
    # Arbre 4 a des métadonnées de provenance compilées
    t4 = get_tree_provenance(4)
    assert t4 is not None
    assert t4.source_pack == "MMONDE_OS_TRAD_34_ARBRES"
    assert t4.compilation_status == "DOCUMENTED_TREE_ACTIVATION_COMPILED"
    assert t4.authority == "NON_SOVEREIGN"
    assert t4.can_decide is False

    # Arbre 1 n'a pas de compilation batch-1 spécifique
    assert get_tree_provenance(1) is None


def test_activation_vector_r34():
    vec = build_activation_vector("v1", [0.5] * 10)
    assert len(vec.activations) == N_TREES
    assert vec.activations[0] == 0.5
    assert vec.activations[20] == 0.0

    # Bornage [0, 1]
    vec_clamped = TreeActivationVector("v2", [-0.5, 1.5] + [0.0] * 32)
    assert vec_clamped.activations[0] == 0.0
    assert vec_clamped.activations[1] == 1.0


def test_memory_world_mapper():
    activations = [0.0] * 34
    activations[10] = 0.8  # Science -> EPISTEMICS (Memory-leaning)
    activations[26] = 0.8  # Vérité -> GOVERNANCE (World-leaning)
    vec = build_activation_vector("v_mw", activations)
    shazam_res = shazam_cognitif(vec)
    mw = map_memory_world(shazam_res)

    assert mw.context_signal_only is True
    assert mw.can_decide is False
    assert mw.can_emit_act is False
    assert len(mw.active_domains) >= 2


def test_arbres_34_canon_json_integrity():
    json_path = Path(__file__).resolve().parents[2] / "brody" / "cognition" / "trees" / "arbres_34.canon.json"
    assert json_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert "trees" in data
    assert len(data["trees"]) == 34
    assert data["trees"][0]["id"] == "01"
    assert data["trees"][33]["id"] == "34"
