"""brody/memory/sufficiency.py — Évaluateur de suffisance mémorielle et cognitive.

Évalue si le ContextPacket B6 assemblé contient des preuves mémorielles et des états
suffisants pour autoriser une restitution déterministe native, ou si les inconnus
doivent être exposés explicitement.

Zéro inférence hasardeuse, autorité KX108_ONLY.
"""
from __future__ import annotations

from typing import Any, Mapping

from brody.context.context_assembly import ContextPacket
from brody.context.contracts import StateStatus


def evaluate_information_sufficiency(
    context: ContextPacket,
    *,
    min_evidence_items: int = 1,
) -> dict[str, Any]:
    """Évalue la complétude et la cohérence des preuves mémorielles dans le contexte B6."""
    state_items = list(context.state)
    unknowns = list(context.unknowns)

    # 1. Détection des éléments de mémoire native connus
    memory_items = [
        item for item in state_items
        if str(item.get("state_type", "")).startswith("NATIVE_MEMORY_ITEM")
    ]

    # 2. Détection des statuts explicites d'inconnu ou d'absence
    memory_unknowns = [
        u for u in unknowns
        if "native_memory" in str(u.get("state_id", ""))
    ]

    # 3. Détection des contradictions déclarées dans les payloads
    contradictions: list[str] = []
    for item in state_items:
        payload = item.get("payload")
        if payload is None and "payload_preview" in item:
            try:
                payload = json.loads(item["payload_preview"])
            except Exception:
                payload = None

        if isinstance(payload, Mapping):
            if payload.get("is_contradictory") is True or payload.get("contradiction") is True:
                contradictions.append(str(item.get("state_id")))
            raw_contras = payload.get("contradictions")
            if isinstance(raw_contras, (list, tuple)) and len(raw_contras) > 0:
                for c in raw_contras:
                    contradictions.append(f"{item.get('state_id')}:{c}")
            sens_frame = payload.get("semantic_frame")
            if isinstance(sens_frame, Mapping):
                s_contras = sens_frame.get("contradictions")
                if isinstance(s_contras, (list, tuple)) and len(s_contras) > 0:
                    for c in s_contras:
                        contradictions.append(f"{item.get('state_id')}:{c}")
        elif "payload_preview" in item:
            preview = str(item.get("payload_preview") or "")
            if ('"is_contradictory":true' in preview or '"is_contradictory": true' in preview
                    or '"contradiction":true' in preview or '"contradiction": true' in preview):
                contradictions.append(str(item.get("state_id")))

    contradictions = sorted(set(contradictions))

    # 4. Décision d'évaluation de suffisance (déterministe et fail-closed)
    if contradictions:
        status = "CONTRADICTION_DETECTED"
        sufficient = False
        restitution_mode = "CONTRADICTION_HOLD"
        reason = f"CONTRADICTION_EXPOSED:{len(contradictions)}"
    elif memory_unknowns or (len(memory_items) < min_evidence_items and not memory_items):
        if not memory_items and not memory_unknowns:
            status = "NO_MEMORY_EVIDENCE"
            sufficient = False
            restitution_mode = "EXPLICIT_UNKNOWN_EXPOSURE"
            reason = "ZERO_MEMORY_GROUNDING"
        else:
            status = "INSUFFICIENT_UNKNOWN"
            sufficient = False
            restitution_mode = "EXPLICIT_UNKNOWN_EXPOSURE"
            reason = f"EXPLICIT_UNKNOWNS_PRESENT:{len(unknowns)}"
    else:
        status = "SUFFICIENT"
        sufficient = True
        restitution_mode = "NATIVE_RESTITUTION"
        reason = f"VERIFIED_EVIDENCE_COUNT:{len(memory_items)}"

    return {
        "schema": "BRODY_MEMORY_SUFFICIENCY_EVALUATION_V1",
        "packet_id": context.packet_id,
        "query": context.query,
        "status": status,
        "sufficient": sufficient,
        "restitution_mode": restitution_mode,
        "reason": reason,
        "evidence_items_count": len(memory_items),
        "unknowns_count": len(unknowns),
        "contradictions_count": len(contradictions),
        "contradictions": contradictions,
        "unknowns": unknowns,
        "decision_authority": "KX108_ONLY",
        "allowed_to_decide": False,
        "provenance_refs": list(context.provenance_refs),
    }
