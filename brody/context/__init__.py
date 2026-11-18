"""brody/context — Assemblage du contexte cognitif B6 et état explicite.

Expose l'assemblage de contexte déterministe B6, la projection des entrées d'état,
la gestion des inconnus, les instructions conditionnelles et la divulgation étagée.

Zéro inférence non traçable, autorité KX108_ONLY, scellement canonique strict.
"""
from __future__ import annotations

import sys

from brody.context.contracts import (
    BOUNDARY,
    MAX_PACKET_BYTES,
    ContextBoundError,
    StateEntry,
    StateStatus,
    Visibility,
    canonical_json,
    error_entry,
    render_entry,
)
from brody.context.capabilities import (
    DisclosureLevel,
    disclose,
    load_capability_matrix,
)
from brody.context.instructions import (
    DEFAULT_INSTRUCTIONS,
    Instruction,
    activation_tags,
    select_instructions,
)
from brody.context.registry import (
    DuplicateStateError,
    WorkingStateRegistry,
)
from brody.context.projection import (
    Included,
    Omitted,
    ProjectedState,
    Relevance,
    project_entries,
)
from brody.context.context_assembly import (
    ContextPacket,
    PACKET_SCHEMA,
    assemble_context,
)
from brody.context.sens_adapter import (
    sens_state_entries,
    serialize_frame,
)
from brody.context.memory_adapter import (
    native_memory_state_entries,
)
from brody.context.rights_matrix import (
    get_brody_capability_matrix,
)

# Shims de rétrocompatibilité pour les suites de tests B6 existantes
_self = sys.modules[__name__]
sys.modules.setdefault("app.harness.state_explicit", _self)
sys.modules.setdefault("app.harness.state_explicit.contracts", sys.modules["brody.context.contracts"])
sys.modules.setdefault("app.harness.state_explicit.capabilities", sys.modules["brody.context.capabilities"])
sys.modules.setdefault("app.harness.state_explicit.instructions", sys.modules["brody.context.instructions"])
sys.modules.setdefault("app.harness.state_explicit.registry", sys.modules["brody.context.registry"])
sys.modules.setdefault("app.harness.state_explicit.projection", sys.modules["brody.context.projection"])
sys.modules.setdefault("app.harness.state_explicit.context_assembly", sys.modules["brody.context.context_assembly"])
sys.modules.setdefault("app.harness.state_explicit.sens_adapter", sys.modules["brody.context.sens_adapter"])
sys.modules.setdefault("app.harness.state_explicit.memory_adapter", sys.modules["brody.context.memory_adapter"])

__all__ = [
    "StateEntry",
    "StateStatus",
    "Visibility",
    "Relevance",
    "ContextPacket",
    "assemble_context",
    "WorkingStateRegistry",
    "DuplicateStateError",
    "Instruction",
    "DEFAULT_INSTRUCTIONS",
    "select_instructions",
    "DisclosureLevel",
    "disclose",
    "load_capability_matrix",
    "project_entries",
    "sens_state_entries",
    "serialize_frame",
    "native_memory_state_entries",
    "get_brody_capability_matrix",
    "BOUNDARY",
    "MAX_PACKET_BYTES",
    "PACKET_SCHEMA",
]
