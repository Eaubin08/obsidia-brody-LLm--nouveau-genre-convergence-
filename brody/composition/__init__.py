"""brody/composition — Moteurs éditoriaux Studio E11 et composition native de Brody.

Ce package rassemble :
- Le consommateur strict de contrat Studio E11 (OBSIDIA_STUDIO_E11_CONSUMPTION_V1)
- Le contrat éditorial déterministe Studio (build_readonly_draft)
- Les moteurs de requête et de nettoyage (editorial_intent, editorial_cleanup)
- Le moteur éditorial optionnel en loopback local (local_engine)
- Le planificateur et réalisateur rhétorique natif Brody (V1 et V2)

Zéro appel modèle non gouverné. Frontière d'autorité exclusive KX108_ONLY.
"""
from __future__ import annotations

import sys

from brody.composition import (
    contracts,
    e11_receipt_diagnostics,
    e11_consumer,
    studio_contract,
    editorial_intent,
    editorial_cleanup,
    local_engine,
    editorial_planner,
)

from brody.composition.contracts import (
    SCHEMA,
    SCHEMA_EDITORIAL_V1,
    SCHEMA_EDITORIAL_V2,
    SCHEMA_EDITORIAL_ARTIFACT_V1,
    SCHEMA_EDITORIAL_ARTIFACT_V2,
    E11_BOUNDARY,
    ContractError,
)
from brody.composition.e11_consumer import (
    consume_envelope,
    parse_envelope,
    failure_result,
    diagnostic_summary,
)
from brody.composition.e11_receipt_diagnostics import (
    extract_receipt_diagnostics,
    sanitize_receipt_diagnostics,
    SURFACES,
)
from brody.composition.studio_contract import (
    build_readonly_draft,
)
from brody.composition.editorial_intent import (
    explanatory_editorial_request,
)
from brody.composition.editorial_cleanup import (
    clean_editorial_draft,
)
from brody.composition.local_engine import (
    generate_editorial,
    EditorialEngineError,
)
from brody.composition.editorial_planner import (
    recognize_native_editorial_request,
    compose_native_editorial,
    realize_brody_editorial_plan,
    build_governed_e11_envelope,
)

# Alias de modules pour rétrocompatibilité des suites de tests Studio E11
_self = sys.modules[__name__]
sys.modules.setdefault("studio_editorial_contract", studio_contract)
sys.modules.setdefault("studio_e11_contract", e11_consumer)
sys.modules.setdefault("studio_e11_receipt_diagnostics", e11_receipt_diagnostics)
sys.modules.setdefault("editorial_intent", editorial_intent)
sys.modules.setdefault("editorial_cleanup", editorial_cleanup)
sys.modules.setdefault("studio_editorial_engine", local_engine)

__all__ = [
    "SCHEMA",
    "SCHEMA_EDITORIAL_V1",
    "SCHEMA_EDITORIAL_V2",
    "SCHEMA_EDITORIAL_ARTIFACT_V1",
    "SCHEMA_EDITORIAL_ARTIFACT_V2",
    "E11_BOUNDARY",
    "ContractError",
    "consume_envelope",
    "parse_envelope",
    "failure_result",
    "diagnostic_summary",
    "extract_receipt_diagnostics",
    "sanitize_receipt_diagnostics",
    "SURFACES",
    "build_readonly_draft",
    "explanatory_editorial_request",
    "clean_editorial_draft",
    "generate_editorial",
    "EditorialEngineError",
    "recognize_native_editorial_request",
    "compose_native_editorial",
    "realize_brody_editorial_plan",
    "build_governed_e11_envelope",
]
