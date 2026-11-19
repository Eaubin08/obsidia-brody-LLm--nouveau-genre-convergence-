"""brody/cognition — Sous-système de cognition native et représentations multidimensionnelles.

Rassemble et unifie les capacités cognitives fondamentales d'Obsidia :
  1. Shazam Cognitif et hachage spectral.
  2. Ontologie des 34 Arbres, vecteur d'activation R^34 et signaux de contexte.
  3. Nuages de points 21D et moteur transversal des 11 balances.
  4. Mécanismes bio-animaux (fourmis / abeilles), cohérence de trajectoire et stigmergie.
  5. Détection des signaux faibles et évitement des impasses cognitives (dead paths).

Frontière stricte : 100% CPU, non-décisionnel, non-autorisant, sans ACT, autorité KX108_ONLY.
"""
from __future__ import annotations

import time
from typing import Any, Mapping, Optional

from brody.cognition.micro_core import run_micro_core
from brody.cognition.balance_engine import BrodyBalanceEngine
from brody.cognition.point_cloud_21d import BrodyPointCloud21DSelector
from brody.cognition.shazam import (
    extract_features,
    cosine_similarity,
    filter_dominant,
    shazam,
    shazam_full_packet,
)
from brody.cognition.trees import (
    TreeEntry,
    get_all_trees,
    get_tree_by_id,
    get_trees_by_domain,
    get_tree_provenance,
    TreeActivationVector,
    build_activation_vector,
    uniform_activation,
    N_TREES,
    DEFAULT_THETA,
    DominantTreeResult,
    find_dominant_trees,
    ShazamCognitifResult,
    shazam_cognitif,
    MemoryWorldContext,
    map_memory_world,
    TreeSignalPacket,
    build_tree_signal_packet,
)

__all__ = [
    # Micro-Core & Stigmergie
    "run_micro_core",
    # Moteur de Balance
    "BrodyBalanceEngine",
    # Nuages de points 21D
    "BrodyPointCloud21DSelector",
    # Shazam Cognitif
    "extract_features",
    "cosine_similarity",
    "filter_dominant",
    "shazam",
    "shazam_full_packet",
    # Ontologie 34 Arbres
    "TreeEntry",
    "get_all_trees",
    "get_tree_by_id",
    "get_trees_by_domain",
    "get_tree_provenance",
    "TreeActivationVector",
    "build_activation_vector",
    "uniform_activation",
    "N_TREES",
    "DEFAULT_THETA",
    "DominantTreeResult",
    "find_dominant_trees",
    "ShazamCognitifResult",
    "shazam_cognitif",
    "MemoryWorldContext",
    "map_memory_world",
    "TreeSignalPacket",
    "build_tree_signal_packet",
    # Pipeline Cognitif Unifié
    "run_cognitive_pipeline",
]


def run_cognitive_pipeline(
    query: str,
    *,
    session_id: str = "session_cognition",
    language: str = "fr",
    balance_engine: Optional[BrodyBalanceEngine] = None,
    point_cloud_selector: Optional[BrodyPointCloud21DSelector] = None,
    theta: float = DEFAULT_THETA,
) -> dict[str, Any]:
    """
    Exécute le pipeline cognitif natif unifié sur une requête utilisateur.
    
    Combine :
      1. Micro-core (14 signaux permanents, stigmergie, détection impasses / signaux faibles)
      2. 11 Balances transversales & coordinateur
      3. Sélecteur 21D (axes dominants, couches actives/interdites, budget)
      4. Shazam Cognitif & 34 Arbres (hachage spectral, motifs de gouvernance)
      5. Cartographie mémoire vs monde
      
    Garantit l'absence d'IO externe, l'absence de décision autonome (KX108_ONLY)
    et une exécution déterministe en quelques millisecondes sur CPU.
    """
    t0 = time.perf_counter()
    be = balance_engine or BrodyBalanceEngine()
    pc = point_cloud_selector or BrodyPointCloud21DSelector()

    # 1. Micro-core cognitif (14 signaux permanents)
    micro_core_output = run_micro_core(query, session_id=session_id, language=language)

    # 2. Transversal Balance Engine (11 tensions)
    balance_output = be.compute_balances(query, micro_core_output)

    # 3. Sélecteur de nuage de points 21D
    point_cloud_output = pc.compute_vector(query, micro_core_output, balance_output)

    # 4. Shazam Cognitif & Arbres 34
    tree_packet = shazam_full_packet(
        query,
        signal_id=f"tree_{session_id}_{int(time.time() * 1000) % 1000000}",
        threshold=theta,
    )

    t_elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)

    return {
        "pipeline_version": "BRODY_COGNITION_P1_V1",
        "query": query,
        "execution_time_ms": t_elapsed_ms,
        "decision_authority": "KX108_ONLY",
        "advisory_only": True,
        "emits_act": False,
        "can_decide": False,
        # 1. Micro-Core & Stigmergie
        "micro_core": micro_core_output,
        "bio_animal_signal": micro_core_output.get("bio_animal_signal", {}),
        "weak_signals": micro_core_output.get("bio_animal_signal", {}).get("weak_signal_detection", []),
        "dead_paths": micro_core_output.get("bio_animal_signal", {}).get("dead_path_detection", []),
        "survival_risk_flag": micro_core_output.get("survival_risk_flag", False),
        # 2. Balances transversales
        "balances": balance_output.get("balances", {}),
        "balance_coordinator": balance_output.get("coordinator", {}),
        # 3. 21D Point Cloud
        "point_cloud_21d": point_cloud_output,
        "dominant_axes": point_cloud_output.get("dominant_axes", []),
        "active_layers": point_cloud_output.get("active_layers", []),
        "forbidden_layers": point_cloud_output.get("forbidden_layers", []),
        "budget_estimate": point_cloud_output.get("budget_estimate", 1792),
        # 4. Shazam & 34 Arbres
        "tree_signal_packet": tree_packet.to_dict(),
        "dominant_trees": tree_packet.dominant_trees,
        "patterns_detected": tree_packet.patterns_detected,
        "memory_relevance": tree_packet.memory_relevance,
        "world_relevance": tree_packet.world_relevance,
    }
