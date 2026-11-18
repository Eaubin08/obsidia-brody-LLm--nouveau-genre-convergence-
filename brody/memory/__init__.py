"""brody/memory — Mémoire native et continuité cognitive Brody V1.

Ce package intègre le lecteur de mémoire native déterministe, l'évaluateur de suffisance
mémorielle (Sufficiency Evaluator), la continuité de session conversationnelle
et la frontière stricte d'interdiction d'écriture automatique (Clôture 4A1).

Zéro écriture mémoire automatique, zéro RAG vectoriel opaque, autorité KX108_ONLY.
"""
from __future__ import annotations

import sys

from brody.memory.native_reader import (
    NATIVE_MEMORY_BOUNDARY,
    build_native_memory_retrieval_snapshot,
    load_native_memory_index,
    query_native_memory,
    get_native_memory_index_path,
)
from brody.memory.sufficiency import (
    evaluate_information_sufficiency,
)
from brody.memory.continuity import (
    DialogueTurn,
    SessionContinuityLedger,
)

# Shims de rétrocompatibilité pour les appels aux modules historiques
_self = sys.modules[__name__]
sys.modules.setdefault("apps.obsidia_api.brody_obsidia_native_memory", sys.modules["brody.memory.native_reader"])

__all__ = [
    "load_native_memory_index",
    "query_native_memory",
    "build_native_memory_retrieval_snapshot",
    "NATIVE_MEMORY_BOUNDARY",
    "get_native_memory_index_path",
    "evaluate_information_sufficiency",
    "DialogueTurn",
    "SessionContinuityLedger",
]
