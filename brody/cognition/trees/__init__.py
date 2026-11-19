"""brody/cognition/trees — Ontologie des 34 Arbres, R^34, et signaux cognitifs."""
from __future__ import annotations

from .tree_registry import (
    TreeEntry,
    get_all_trees,
    get_tree_by_id,
    get_trees_by_domain,
    get_tree_provenance,
)
from .tree_activation_vector import (
    TreeActivationVector,
    build_activation_vector,
    uniform_activation,
    N_TREES,
    DEFAULT_THETA,
)
from .dominant_trees import (
    DominantTreeResult,
    find_dominant_trees,
)
from .shazam_cognitif import (
    ShazamCognitifResult,
    shazam_cognitif,
)
from .memory_world_mapper import (
    MemoryWorldContext,
    map_memory_world,
)
from .tree_signal_packet import (
    TreeSignalPacket,
    build_tree_signal_packet,
)

__all__ = [
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
]
