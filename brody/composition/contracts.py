"""brody/composition/contracts.py — Contrats et invariants du Studio E11 et de la composition éditoriale.

Définit le schéma E11 (OBSIDIA_STUDIO_E11_CONSUMPTION_V1), les statuts,
les codes d'erreur, les invariants de non-souveraineté et la frontière de gouvernance KX108_ONLY.
"""
from __future__ import annotations

import copy
import math
from typing import Any, Dict, FrozenSet, Mapping, Optional

SCHEMA = "OBSIDIA_STUDIO_E11_CONSUMPTION_V1"
BASELINE_CHECKPOINT = "2729000c63915dd8a7749a3d6f6aa820eaab5d91"
PREVIOUS_CHECKPOINT = "aba5e8bbac68dfae707c6015d69e27eb948c4fed"
CHECKPOINT = "cbad01257c027e5861a1c0610d418dfd02fc8342"
MAX_RESPONSE_BYTES = 5_000_000

STATUSES: FrozenSet[str] = frozenset({"CONTEXT_AVAILABLE", "CONTEXT_LIMITED", "REFUSED", "UNAVAILABLE"})

ERROR_CODES: FrozenSet[str] = frozenset({
    "NONE", "DISABLED", "INVALID_INPUT", "AUTH_REQUIRED", "AUTH_REJECTED",
    "AUTH_MISCONFIGURED", "HOLD_ACTIVATION", "ENDPOINT_INVALID", "SERVICE_UNAVAILABLE", "TIMEOUT",
    "REDIRECT_REFUSED", "HTTP_ERROR", "RESPONSE_TOO_LARGE", "INVALID_JSON", "SCHEMA_MISMATCH",
    "GOVERNANCE_REFUSED", "UPSTREAM_HOLD", "UPSTREAM_BLOCK", "JOURNAL_UNAVAILABLE"
})

MEMORY_STATUSES: FrozenSet[str] = frozenset({
    "MEMORY_USABLE", "MEMORY_NOT_REQUIRED", "MEMORY_REQUIRED_EMPTY_QUERY",
    "MEMORY_REQUIRED_NO_NATIVE_SOURCE", "MEMORY_REQUIRED_INVALID_NATIVE_SOURCE", "MEMORY_REQUIRED_EMPTY",
    "MEMORY_UNAVAILABLE"
})

DIAGNOSTICS_VERSION = "OBSIDIA_STUDIO_E11_DIAGNOSTICS_V2"

LIMIT_REASONS: FrozenSet[str] = frozenset({
    "MEMORY_STATUS_UNKNOWN", "RECEIPT_DEGRADED", "RECEIPT_SURFACES_UNAVAILABLE",
    "B6_UNKNOWNS", "B6_OMISSIONS", "B6_STATE_ERROR", "B6_REDUCED_VISIBILITY",
    "E11_UNRESOLVED_REQUESTS", "E11_INVALID", "B6_INVALID",
    "GOVERNANCE_HOLD", "GOVERNANCE_BLOCK", "GOVERNANCE_REFUSED",
    "MEMORY_REQUIRED_EMPTY_QUERY", "MEMORY_REQUIRED_NO_NATIVE_SOURCE",
    "MEMORY_REQUIRED_INVALID_NATIVE_SOURCE", "MEMORY_REQUIRED_EMPTY", "MEMORY_UNAVAILABLE"
})

DIAGNOSTIC_ENUMS: Dict[str, FrozenSet[str]] = {
    "memory_retrieval_status": MEMORY_STATUSES | {"UNKNOWN", "NOT_OBSERVED"},
    "e11_contract_status": frozenset({"VALID", "INVALID", "NOT_CHECKED"}),
    "b6_context_status": frozenset({"VALID", "LIMITED", "INVALID", "NOT_CHECKED"}),
    "governance_status": frozenset({"CONTEXT_ALLOWED", "HOLD", "BLOCK", "REFUSED", "NOT_CHECKED"}),
    "receipt_availability": frozenset({"VALIDATED", "PRESENT_UNVALIDATED", "MISSING", "NOT_OBSERVED"}),
}

# Brody native editorial schemas
SCHEMA_EDITORIAL_V1 = "BRODY_NATIVE_EDITORIAL_V1"
SCHEMA_EDITORIAL_V2 = "BRODY_NATIVE_EDITORIAL_V2"
SCHEMA_EDITORIAL_ARTIFACT_V1 = "BRODY_PUBLIC_EDITORIAL_ARTIFACT_V1"
SCHEMA_EDITORIAL_ARTIFACT_V2 = "BRODY_PUBLIC_EDITORIAL_ARTIFACT_V2"

# Invariants stricts de non-mutation et frontière d'autorité
_FALSE = frozenset({
    "memory_write", "emits_act", "kernel_mutation", "allowed_to_act", "allowed_to_decide",
    "x108_mutation", "real_action", "emits_verdict", "real_execution", "response_governance_applied",
    "canonical_write", "graphiti_write", "neo4j_write", "external_io", "durable_state_write", "kx108_mutation"
})

E11_BOUNDARY: Dict[str, Any] = {
    "decision_authority": "KX108_ONLY",
    "readonly": True,
    "memory_write": False,
    "emits_act": False,
    "kernel_mutation": False,
    "allowed_to_act": False,
    "allowed_to_decide": False,
}


class ContractError(ValueError):
    """Exception levée en cas de violation d'un invariant de contrat Studio E11."""
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)  # never include source values, paths or exception text
