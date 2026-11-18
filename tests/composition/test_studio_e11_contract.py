"""tests/composition/test_studio_e11_contract.py — Validation stricte du contrat Studio E11.

Vérifie l'admission des enveloppes E11 synthétiques conformes,
la détection des violations de gouvernance et le comportement fail-closed.
"""
from __future__ import annotations

import copy
import json
import uuid
import pytest

from brody.composition.contracts import (
    SCHEMA,
    E11_BOUNDARY,
    ContractError,
)
from brody.composition.e11_consumer import (
    consume_envelope,
    parse_envelope,
    failure_result,
    diagnostic_summary,
)


def envelope(status: str = "MEMORY_USABLE", completeness: str = "COMPLETE") -> dict:
    b = dict(E11_BOUNDARY)
    entry = {
        "state_id": "private-source",
        "state_type": "NATIVE_MEMORY_ITEM",
        "source_ref": "PRIVATE_PATH",
        "payload": {"excerpt": "PRIVATE_MEMORY"},
        "provenance": ["PRIVATE_REF"],
        "uncertainty": [],
        "status": "KNOWN",
        "visibility": "LONG",
        "tags": [],
        "summary": "PRIVATE_SUMMARY",
        "readonly": True,
    }
    packet = {
        "schema": "B6_STATE_EXPLICIT_CONTEXT_PACKET_V1",
        "packet_id": "b6ctx_0123456789abcdef",
        "query": "PRIVATE_QUESTION",
        "projection": {"query_tokens": [], "included": [], "omitted": []},
        "state": [copy.deepcopy(entry)],
        "instructions": [],
        "capabilities": {},
        "provenance_refs": ["PRIVATE_REF"],
        "unknowns": [],
        "omitted": [],
        "boundary": copy.deepcopy(b),
    }
    shadow = {
        "schema": "COGNITION_SHADOW_MEMORY_V0",
        "input_text": "PRIVATE_QUESTION",
        "memory_snapshot_ref": {
            "schema_version": "OBSIDIA_NATIVE_MEMORY_RETRIEVAL_V1",
            "status": status,
            "query": "PRIVATE_QUERY",
            "selected_items_count": 1 if status == "MEMORY_USABLE" else 0,
        },
        "state_entries": [],
        "memory_entries": [entry] if status == "MEMORY_USABLE" else [],
        "context_packet": packet,
        "resolution_requests": [],
        "boundary": {k: b[k] for k in ("readonly", "decision_authority", "memory_write", "emits_act", "kernel_mutation")},
    }
    receipt = {
        "version": "REAL_COGNITIVE_JOIN_C1_V1",
        "rail_mode": "SHADOW_READONLY_SUPERPOSED",
        "signal_id": "private-signal",
        "created_at": "2026-10-16T12:00:00Z",
        "status": "READY_SHADOW_READONLY",
        "completeness": completeness,
        "components": {"COGNITION_SHADOW_MEMORY": "OK"},
        "errors": [],
        "critical_action_requested": False,
        "kx108_admission": "DRY_RUN",
        "decision_ticket_dry_run": {
            "decision": "ALLOW_CONTEXT_ONLY",
            "x108_gate_status": "X108_EVALUATED_DRY_RUN",
        },
        "real_execution": False,
        "response_governance_applied": False,
        "advisory_only": True,
        **b,
        "cognition_shadow_memory": shadow,
    }
    return {
        **b,
        "advisory_only": True,
        "x108_mutation": False,
        "real_action": False,
        "emits_verdict": False,
        "source": "REAL_BRODY_RUNTIME",
        "cognitive_runtime_receipt": receipt,
    }


def at(body: dict, path: str):
    parts = path.split(".")
    for p in parts[:-1]:
        body = body[p]
    return body, parts[-1]


def consume(body: dict) -> dict:
    return consume_envelope(body, experiment_id=str(uuid.uuid4()), provenance={})


def test_valid_preserves_receipt_unknowns_omissions_and_no_truth_claim():
    body = envelope()
    packet = body["cognitive_runtime_receipt"]["cognition_shadow_memory"]["context_packet"]
    packet["unknowns"] = [{"state_id": "unknown", "status": "UNKNOWN", "uncertainty": ["PRIVATE_UNKNOWN"]}]
    packet["omitted"] = [{"state_id": "omitted", "reason": "PRIVATE_OMISSION"}]
    original = copy.deepcopy(body)
    result = consume(body)
    assert result["consumer_status"] == "CONTEXT_LIMITED"
    assert body == original
    assert result["original_receipt"] == original["cognitive_runtime_receipt"]
    assert (
        result["e11_context"]["context_packet"]["unknowns"]
        == original["cognitive_runtime_receipt"]["cognition_shadow_memory"]["context_packet"]["unknowns"]
    )
    assert (
        result["e11_context"]["context_packet"]["omitted"]
        == original["cognitive_runtime_receipt"]["cognition_shadow_memory"]["context_packet"]["omitted"]
    )
    assert result["documentary_status"] == "MEMORY_USABLE"
    assert result["publication_permitted"] is False
    assert result["human_review_required"] is False
    assert result["publication_human_review_required"] is True


@pytest.mark.parametrize("path", [
    "decision_authority", "readonly", "memory_write", "allowed_to_act", "allowed_to_decide", "emits_act", "kernel_mutation",
    "cognitive_runtime_receipt", "cognitive_runtime_receipt.version", "cognitive_runtime_receipt.rail_mode",
    "cognitive_runtime_receipt.status", "cognitive_runtime_receipt.errors", "cognitive_runtime_receipt.components",
    "cognitive_runtime_receipt.critical_action_requested", "cognitive_runtime_receipt.decision_ticket_dry_run",
    "cognitive_runtime_receipt.cognition_shadow_memory", "cognitive_runtime_receipt.cognition_shadow_memory.boundary",
    "cognitive_runtime_receipt.cognition_shadow_memory.memory_snapshot_ref.schema_version",
    "cognitive_runtime_receipt.cognition_shadow_memory.context_packet.unknowns",
    "cognitive_runtime_receipt.cognition_shadow_memory.context_packet.omitted",
    "cognitive_runtime_receipt.cognition_shadow_memory.context_packet.provenance_refs",
])
def test_required_fields_absent_fail_closed(path: str):
    body = envelope()
    obj, key = at(body, path)
    del obj[key]
    result = consume(body)
    assert result["consumer_status"] == "REFUSED"
    assert result["e11_context"] is None


@pytest.mark.parametrize("path,value", [
    ("cognitive_runtime_receipt.version", "NEXT"),
    ("cognitive_runtime_receipt.rail_mode", "NEXT"),
    ("cognitive_runtime_receipt.cognition_shadow_memory.schema", "NEXT"),
    ("cognitive_runtime_receipt.cognition_shadow_memory.context_packet.schema", "NEXT"),
    ("cognitive_runtime_receipt.cognition_shadow_memory.memory_snapshot_ref.schema_version", "NEXT"),
    ("readonly", 1),
    ("memory_write", 0),
    ("allowed_to_act", "false"),
    ("decision_authority", None),
    ("cognitive_runtime_receipt.errors", {}),
    ("cognitive_runtime_receipt.completeness", "UNKNOWN"),
    ("cognitive_runtime_receipt.cognition_shadow_memory.memory_snapshot_ref.selected_items_count", True),
    ("cognitive_runtime_receipt.cognition_shadow_memory.memory_snapshot_ref.status", "FUTURE"),
    ("cognitive_runtime_receipt.cognition_shadow_memory.state_entries", {}),
])
def test_versions_and_types(path: str, value: any):
    body = envelope()
    obj, key = at(body, path)
    obj[key] = value
    assert consume(body)["consumer_status"] == "REFUSED"


@pytest.mark.parametrize("path,value", [
    ("status", "HOLD"),
    ("gate_verdict", "BLOCK"),
    ("decision_authority", "OTHER"),
    ("memory_write", True),
    ("allowed_to_act", True),
    ("allowed_to_decide", True),
    ("emits_act", True),
    ("kernel_mutation", True),
    ("cognitive_runtime_receipt.decision_ticket_dry_run.decision", "HOLD"),
    ("cognitive_runtime_receipt.decision_ticket_dry_run.decision", "BLOCK"),
    ("cognitive_runtime_receipt.decision_authority", "OTHER"),
    ("cognitive_runtime_receipt.critical_action_requested", True),
    ("cognitive_runtime_receipt.cognition_shadow_memory.boundary.memory_write", True),
    ("cognitive_runtime_receipt.cognition_shadow_memory.context_packet.boundary.allowed_to_act", True),
])
def test_governance_refusals(path: str, value: any):
    body = envelope()
    obj, key = at(body, path)
    obj[key] = value
    result = consume(body)
    assert result["consumer_status"] == "REFUSED"
    assert result["original_receipt"] is None


@pytest.mark.parametrize("status,complete", [
    ("MEMORY_REQUIRED_EMPTY", "COMPLETE"),
    ("MEMORY_REQUIRED_NO_NATIVE_SOURCE", "COMPLETE"),
    ("MEMORY_REQUIRED_INVALID_NATIVE_SOURCE", "COMPLETE"),
    ("MEMORY_REQUIRED_EMPTY_QUERY", "COMPLETE"),
    ("MEMORY_USABLE", "DEGRADED"),
])
def test_empty_and_degraded_remain_limited(status: str, complete: str):
    assert consume(envelope(status, complete))["consumer_status"] == "CONTEXT_LIMITED"


@pytest.mark.parametrize("raw", [
    b"{", b"[]", b'{"a":1,"a":2}', b'{"a":{"b":1,"b":2}}',
    b'{"a":NaN}', b'{"a":Infinity}', b'{"a":1e999}', b"\xff"
])
def test_strict_json(raw: bytes):
    with pytest.raises(ContractError):
        parse_envelope(raw)


def test_json_roundtrip():
    assert parse_envelope(json.dumps(envelope()).encode("utf-8")) == envelope()


def test_failure_result_structure():
    fail = failure_result("exp-fail", "INVALID_INPUT")
    assert fail["schema"] == SCHEMA
    assert fail["consumer_status"] == "REFUSED"
    assert fail["error_code"] == "INVALID_INPUT"
    assert fail["publication_permitted"] is False
