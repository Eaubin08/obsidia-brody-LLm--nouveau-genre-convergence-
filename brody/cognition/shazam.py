"""brody/cognition/shazam.py — Shazam Cognitif et analyse spectrale des 34 Arbres.

Extrait les caractéristiques spectrales du texte (tension, urgence, répétition, hash)
et calcule l'activation vectorielle dans l'espace R^34 des Arbres Cognitifs.
Identifie les motifs cognitifs récurrents sous autorité KX108_ONLY (non décisionnel, sans ACT).
"""
from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from typing import Any, Mapping, Optional

from brody.cognition.trees import (
    TreeActivationVector,
    build_activation_vector,
    DominantTreeResult,
    find_dominant_trees,
    ShazamCognitifResult,
    shazam_cognitif,
    TreeSignalPacket,
    build_tree_signal_packet,
)

# Mots-clés canoniques des 34 Arbres (indices 0 à 33 correspondant aux dimensions R^34)
KEYWORDS: dict[int, list[str]] = {
    0: ["humain", "personne", "vie"],
    1: ["conscience", "présence", "perception"],
    2: ["voir", "sentir", "perception"],
    3: ["sens", "meaning", "direction"],
    4: ["identité", "moi", "nom"],
    5: ["comprendre", "comprehension", "analyse"],
    6: ["organiser", "structure", "plan"],
    7: ["pensée", "idée", "raisonnement"],
    8: ["intelligence", "ia", "agent"],
    9: ["langage", "mot", "texte"],
    10: ["science", "preuve", "test"],
    11: ["technique", "code", "outil"],
    12: ["art", "image", "création"],
    13: ["philosophie", "concept", "vérité"],
    14: ["spiritualité", "symbolique", "résonance"],
    15: ["relation", "lien", "contact"],
    16: ["collectif", "groupe", "communauté"],
    17: ["transmission", "mémoire", "héritage"],
    18: ["culture", "histoire", "tradition"],
    19: ["action", "agir", "exécuter"],
    20: ["création", "forge", "build"],
    21: ["transformation", "mutation", "changement"],
    22: ["temps", "chronologie", "frise"],
    23: ["mémoire", "trace", "souvenir"],
    24: ["histoire", "passé", "événement"],
    25: ["cohérence", "alignement", "stable"],
    26: ["vérité", "preuve", "réel"],
    27: ["valeur", "score", "poids"],
    28: ["finalité", "objectif", "but"],
    29: ["global", "cognitif", "système"],
    30: ["flux", "pipeline", "stream"],
    31: ["connexion", "graphe", "lien"],
    32: ["optimisation", "améliorer", "performance"],
    33: ["stabilité", "robuste", "freeze"],
}


def extract_features(payload: Any) -> dict[str, Any]:
    """Extrait les caractéristiques spectrales du texte d'entrée."""
    text = payload.decode("utf-8", errors="ignore") if isinstance(payload, (bytes, bytearray)) else str(payload)
    words = re.findall(r"[A-Za-zÀ-ÿ0-9_]+", text.lower())
    counts = Counter(words)
    urgency = sum(1 for w in words if w in {"urgent", "vite", "danger", "bloque", "crash", "erreur", "fail", "risque"})
    tension = min(1.0, (text.count("!") + text.count("?") + urgency) / 10.0)
    repetition = max(counts.values()) / max(1, len(words)) if counts else 0.0
    return {
        "length": min(1.0, len(text) / 1000.0),
        "word_count": min(1.0, len(words) / 200.0),
        "urgency": min(1.0, urgency / 5.0),
        "tension": tension,
        "repetition": min(1.0, repetition),
        "hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Calcul de similarité cosinus entre deux vecteurs."""
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def filter_dominant(activation: Mapping[int, float], threshold: float = 0.15) -> dict[int, float]:
    """Filtre les arbres ayant un niveau d'activation supérieur au seuil."""
    return {k: v for k, v in activation.items() if v > threshold}


def shazam(payload: Any, threshold: float = 0.15) -> dict[str, Any]:
    """
    Shazam Cognitif de base : extrait les features spectrales et produit
    l'activation des 34 arbres. Non décisionnel.
    """
    text = payload.decode("utf-8", errors="ignore").lower() if isinstance(payload, (bytes, bytearray)) else str(payload).lower()
    features = extract_features(payload)
    activations: dict[int, float] = {}
    for idx in range(34):
        keys = KEYWORDS.get(idx, [])
        hit = sum(1 for k in keys if k in text)
        base = 0.05 + min(0.8, hit * 0.25)
        boost = 0.1 * features["tension"] + 0.05 * features["urgency"]
        activations[idx] = round(min(1.0, base + boost), 4)
    dominant = {k: v for k, v in activations.items() if v > threshold}
    return {
        "spectral_hash": features,
        "tree_activation": activations,
        "dominant_trees": dominant,
        "metadata": {"shazam_trees": list(dominant.keys()), "non_decision": True},
        "non_decision": True,
    }


def shazam_full_packet(
    payload: Any,
    signal_id: str = "sig_shazam",
    threshold: float = 0.15,
    domain_sigma_envelope: Optional[dict[str, Any]] = None,
) -> TreeSignalPacket:
    """
    Analyse spectrale complète produisant un TreeSignalPacket complet et structuré.
    Raccorde le flux textuel aux motifs de gouvernance et de pertinence mémoire.
    """
    shazam_res = shazam(payload, threshold=threshold)
    activations_list = [shazam_res["tree_activation"].get(i, 0.0) for i in range(34)]
    return build_tree_signal_packet(
        signal_id=signal_id,
        activations=activations_list,
        theta=threshold,
        domain_sigma_envelope=domain_sigma_envelope,
    )
