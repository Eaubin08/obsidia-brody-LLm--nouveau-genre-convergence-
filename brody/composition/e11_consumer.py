"""brody/composition/e11_consumer.py — Consommateur strict de l'enveloppe E11.

Consommateur indépendant du contrat JSON E11 épinglé.
Aucun import producteur, aucune inférence externe, aucune écriture mémoire ou action réelle.
"""
from __future__ import annotations

import copy
import json
import math
from typing import Any, Dict, List, Mapping, Optional

from brody.composition.contracts import (
    SCHEMA,
    MAX_RESPONSE_BYTES,
    STATUSES,
    ERROR_CODES,
    MEMORY_STATUSES,
    DIAGNOSTICS_VERSION,
    LIMIT_REASONS,
    DIAGNOSTIC_ENUMS,
    _FALSE,
    ContractError,
)
from brody.composition.e11_receipt_diagnostics import (
    extract_receipt_diagnostics,
    sanitize_receipt_diagnostics,
)


def diagnostic_summary(result: Any) -> Dict[str, Any]:
    """One closed metadata vocabulary for consumer, journal and diagnostic clients.

    Unknown strings/payloads are never copied into a persisted diagnostic.
    This summary does not validate a receipt or authorize context use.
    """
    summary: Dict[str, Any] = {"diagnostics_version": DIAGNOSTICS_VERSION}
    for key, allowed in DIAGNOSTIC_ENUMS.items():
        value = result.get(key) if type(result) is dict else None
        default = "NOT_OBSERVED" if key in {"memory_retrieval_status", "receipt_availability"} else "NOT_CHECKED"
        summary[key] = value if type(value) is str and value in allowed else default
    reasons = result.get("context_limit_reasons", []) if type(result) is dict else []
    summary["context_limit_reasons"] = sorted({v for v in reasons if type(v) is str and v in LIMIT_REASONS}) \
        if type(reasons) is list else []
    summary.update(sanitize_receipt_diagnostics(result))
    return summary


def _need(condition: bool, code: str = "SCHEMA_MISMATCH") -> None:
    if not condition:
        raise ContractError(code)


def _json(value: Any, depth: int = 0) -> None:
    _need(depth <= 64, "INVALID_JSON")
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float:
        _need(math.isfinite(value), "INVALID_JSON")
    elif type(value) is list:
        for item in value:
            _json(item, depth + 1)
    elif type(value) is dict:
        for key, item in value.items():
            _need(type(key) is str, "INVALID_JSON")
            _json(item, depth + 1)
    else:
        raise ContractError("INVALID_JSON")


def parse_envelope(raw: bytes) -> Dict[str, Any]:
    """Reject duplicate keys at any depth, invalid UTF-8 and nonfinite numbers."""
    def pairs(items: List[tuple]) -> Dict[str, Any]:
        obj: Dict[str, Any] = {}
        for key, value in items:
            _need(key not in obj, "INVALID_JSON")
            obj[key] = value
        return obj

    def constant(_: Any) -> None:
        raise ContractError("INVALID_JSON")

    try:
        _need(type(raw) is bytes, "INVALID_JSON")
        _need(len(raw) <= MAX_RESPONSE_BYTES, "RESPONSE_TOO_LARGE")
        body = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)
        _need(type(body) is dict, "INVALID_JSON")
        _json(body)
        return body
    except ContractError:
        raise
    except (ValueError, RecursionError, OverflowError):
        raise ContractError("INVALID_JSON") from None


def failure_result(experiment_id: str, code: str, *, unavailable: bool = False, provenance: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _need(code in ERROR_CODES)
    return {
        "schema": SCHEMA,
        "experiment_id": experiment_id,
        "consumer_status": "UNAVAILABLE" if unavailable else "REFUSED",
        "error_code": code,
        "documentary_status": None,
        "provenance": copy.deepcopy(provenance or {}),
        "original_receipt": None,
        "e11_context": None,
        "human_review_required": False,
        "publication_human_review_required": True,
        "publication_permitted": False,
        **diagnostic_summary({}),
    }


def _fields(obj: Any, requirements: Mapping[str, type]) -> None:
    _need(type(obj) is dict)
    for name, typ in requirements.items():
        _need(name in obj and type(obj[name]) is typ)


def _control(obj: Any, required: Any) -> None:
    _need(type(obj) is dict)
    for name in required:
        _need(name in obj, "GOVERNANCE_REFUSED")
    for name, value in obj.items():
        if name == "decision_authority":
            _need(type(value) is str and value == "KX108_ONLY", "GOVERNANCE_REFUSED")
        elif name in ("readonly", "advisory_only", "context_signal_only"):
            _need(value is True, "GOVERNANCE_REFUSED")
        elif name in _FALSE:
            _need(value is False, "GOVERNANCE_REFUSED")


def _entries(entries: Any) -> None:
    _need(type(entries) is list)
    for entry in entries:
        _fields(entry, {
            "state_id": str, "state_type": str, "source_ref": str, "provenance": list,
            "uncertainty": list, "status": str, "visibility": str, "tags": list, "summary": str
        })
        _need("payload" in entry and entry.get("readonly") is True)
        _need(all(entry[k].strip() for k in ("state_id", "state_type", "source_ref")))
        _need(entry["status"] in {"KNOWN", "OPEN", "UNKNOWN", "ERROR"})
        _need(entry["visibility"] in {"HIDE", "SHORT", "LONG", "FULL"})
        for key in ("provenance", "uncertainty", "tags"):
            _need(all(type(v) is str for v in entry[key]))
        if "observed_at" in entry:
            _need(type(entry["observed_at"]) is str)


def consume_envelope(body: Any, *, experiment_id: str, provenance: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Validate, then detach the original receipt without synthesizing any producer field."""
    diagnostics = diagnostic_summary({})
    stage = "RECEIPT"
    try:
        _json(body)
        if type(body) is dict:
            diagnostics["receipt_availability"] = "PRESENT_UNVALIDATED" if type(body.get("cognitive_runtime_receipt")) is dict else "MISSING"
        core = (
            "decision_authority", "readonly", "memory_write", "emits_act", "kernel_mutation",
            "allowed_to_act", "allowed_to_decide"
        )
        _control(body, (*core, "advisory_only", "x108_mutation", "real_action", "emits_verdict"))
        receipt_hint = body.get("cognitive_runtime_receipt")
        receipt_hint = receipt_hint if type(receipt_hint) is dict else {}
        ticket_hint = receipt_hint.get("decision_ticket_dry_run")
        ticket_hint = ticket_hint if type(ticket_hint) is dict else {}
        route_hint = body.get("route_decision")
        route_hint = route_hint if type(route_hint) is dict else {}
        refusal_values = [body.get(k) for k in ("status", "gate_verdict", "x108_gate", "source_pack_x108_decision")]
        refusal_values += [
            receipt_hint.get("status"), receipt_hint.get("completeness"),
            ticket_hint.get("decision"), ticket_hint.get("x108_gate_status"),
            route_hint.get("gate_verdict")
        ]
        if any(type(v) is str and v in {"BLOCK", "BLOCKED", "BLOCKED_READONLY", "X108_FAIL_CLOSED"}
               for v in refusal_values):
            raise ContractError("UPSTREAM_BLOCK")
        if any(type(v) is str and v in {"HOLD", "HOLD_REQUIRED"} for v in refusal_values) \
                or route_hint.get("fail_closed_hold") is True:
            raise ContractError("UPSTREAM_HOLD")

        for name in ("status", "gate_verdict", "x108_gate", "source_pack_x108_decision"):
            if name in body:
                value = body[name]
                allowed = {"OK", "ok", "READY_READONLY", "READY_SHADOW_READONLY"} if name == "status" else {
                    "ALLOW", "ALLOW_CONTEXT_ONLY", "N/A", "NOT_REQUIRED", "NONE"
                }
                _need(type(value) is str and value in allowed, "GOVERNANCE_REFUSED")
        if "route_decision" in body:
            route = body["route_decision"]
            _fields(route, {"gate_verdict": str, "fail_closed_hold": bool})
            _need(route["gate_verdict"] in {"ALLOW", "ALLOW_CONTEXT_ONLY"}
                  and route["fail_closed_hold"] is False, "GOVERNANCE_REFUSED")
        _fields(body, {"cognitive_runtime_receipt": dict})
        receipt = body["cognitive_runtime_receipt"]
        _control(receipt, (*core, "advisory_only", "real_execution", "response_governance_applied"))
        _fields(receipt, {
            "version": str, "rail_mode": str, "signal_id": str, "created_at": str,
            "status": str, "completeness": str, "components": dict, "errors": list,
            "critical_action_requested": bool, "kx108_admission": str, "decision_ticket_dry_run": dict,
            "cognition_shadow_memory": dict
        })
        _need(receipt["version"] == "REAL_COGNITIVE_JOIN_C1_V1"
              and receipt["rail_mode"] == "SHADOW_READONLY_SUPERPOSED")
        _need(bool(receipt["signal_id"].strip()) and bool(receipt["created_at"].strip()))
        _need(receipt["status"] == "READY_SHADOW_READONLY" and receipt["critical_action_requested"] is False
              and receipt["kx108_admission"] == "DRY_RUN", "GOVERNANCE_REFUSED")
        _need(receipt["completeness"] in {"COMPLETE", "DEGRADED"})
        if receipt["components"].get("COGNITION_SHADOW_MEMORY") != "OK":
            diagnostics["e11_contract_status"] = "INVALID"
            diagnostics["context_limit_reasons"].append("E11_INVALID")
        _need(receipt["components"].get("COGNITION_SHADOW_MEMORY") == "OK" and receipt["errors"] == [],
              "GOVERNANCE_REFUSED")
        ticket = receipt["decision_ticket_dry_run"]
        _need(ticket.get("decision") == "ALLOW_CONTEXT_ONLY"
              and ticket.get("x108_gate_status") == "X108_EVALUATED_DRY_RUN", "GOVERNANCE_REFUSED")
        _control(ticket, ())
        diagnostics["governance_status"] = "CONTEXT_ALLOWED"
        stage = "E11"
        e11 = receipt["cognition_shadow_memory"]
        _fields(e11, {
            "schema": str, "input_text": str, "memory_snapshot_ref": dict, "state_entries": list,
            "memory_entries": list, "context_packet": dict, "resolution_requests": list, "boundary": dict
        })
        _need(e11["schema"] == "COGNITION_SHADOW_MEMORY_V0")
        _control(e11["boundary"], ("readonly", "decision_authority", "memory_write", "emits_act", "kernel_mutation"))
        snapshot = e11["memory_snapshot_ref"]
        _fields(snapshot, {"schema_version": str, "status": str, "query": str, "selected_items_count": int})
        _need(snapshot["schema_version"] == "OBSIDIA_NATIVE_MEMORY_RETRIEVAL_V1")
        diagnostics["memory_retrieval_status"] = snapshot["status"] if snapshot["status"] in MEMORY_STATUSES else "UNKNOWN"
        if diagnostics["memory_retrieval_status"] == "UNKNOWN":
            diagnostics["context_limit_reasons"].append("MEMORY_STATUS_UNKNOWN")
            raise ContractError("SCHEMA_MISMATCH")
        count = snapshot["selected_items_count"]
        _need(count > 0 if snapshot["status"] == "MEMORY_USABLE" else count == 0)
        _entries(e11["state_entries"])
        _entries(e11["memory_entries"])
        if snapshot["status"] == "MEMORY_USABLE":
            _need(len(e11["memory_entries"]) == count)
        elif snapshot["status"] == "MEMORY_NOT_REQUIRED":
            _need(e11["memory_entries"] == [])
        _need(all(type(v) is dict for v in e11["resolution_requests"]))
        diagnostics["e11_contract_status"] = "VALID"
        stage = "B6"
        packet = e11["context_packet"]
        _fields(packet, {
            "schema": str, "packet_id": str, "query": str, "projection": dict, "state": list,
            "instructions": list, "capabilities": dict, "provenance_refs": list, "unknowns": list,
            "omitted": list, "boundary": dict
        })
        _need(packet["schema"] == "B6_STATE_EXPLICIT_CONTEXT_PACKET_V1" and bool(packet["packet_id"]))
        _control(packet["boundary"], core)
        _fields(packet["projection"], {"query_tokens": list, "included": list, "omitted": list})
        _need(all(type(ref) is str for ref in packet["provenance_refs"]))
        _entries(packet["state"])
        diagnostics["b6_context_status"] = "VALID"

        if packet["unknowns"] or packet["omitted"] or snapshot["status"] != "MEMORY_USABLE" or receipt["completeness"] == "DEGRADED":
            consumer_status = "CONTEXT_LIMITED"
        else:
            consumer_status = "CONTEXT_AVAILABLE"

        diagnostics.update(extract_receipt_diagnostics(receipt))

        return {
            "schema": SCHEMA,
            "experiment_id": experiment_id,
            "consumer_status": consumer_status,
            "error_code": "NONE",
            "documentary_status": snapshot["status"],
            "provenance": copy.deepcopy(provenance or {}),
            "original_receipt": copy.deepcopy(receipt),
            "e11_context": copy.deepcopy(e11),
            "human_review_required": False,
            "publication_human_review_required": True,
            "publication_permitted": False,
            **diagnostics,
        }
    except ContractError as exc:
        code = exc.code
        unavailable = code in {"SERVICE_UNAVAILABLE", "TIMEOUT", "JOURNAL_UNAVAILABLE"}
        res = failure_result(experiment_id, code, unavailable=unavailable, provenance=provenance)
        res.update(diagnostics)
        return res
