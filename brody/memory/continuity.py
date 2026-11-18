"""brody/memory/continuity.py — Continuité cognitive et gestionnaire de session éphémère.

Maintient la continuité conversationnelle sans écriture canonique non autorisée (4A1).
Chaque tour de dialogue est scellé par son empreinte cryptographique de provenance.

Zéro mutation de noyau, autorité KX108_ONLY.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from brody.context.contracts import StateEntry, StateStatus, Visibility, canonical_json


@dataclass(frozen=True)
class DialogueTurn:
    turn_id: str
    ordinal: int
    user_query: str
    query_sha256: str
    restitution_text: str
    packet_id: str
    status: str
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "ordinal": self.ordinal,
            "user_query": self.user_query,
            "query_sha256": self.query_sha256,
            "restitution_text": self.restitution_text,
            "packet_id": self.packet_id,
            "status": self.status,
            "timestamp": self.timestamp,
        }


class SessionContinuityLedger:
    """Registre de continuité conversationnelle en mémoire vive (lecture seule / session locale)."""

    def __init__(self, session_id: str = "default_session") -> None:
        self.session_id = session_id
        self._turns: list[DialogueTurn] = []

    def record_turn(
        self,
        *,
        user_query: str,
        restitution_text: str,
        packet_id: str,
        status: str,
        timestamp: str = "",
    ) -> DialogueTurn:
        ordinal = len(self._turns) + 1
        query_sha256 = hashlib.sha256(user_query.encode("utf-8")).hexdigest()
        turn_id = f"turn_{self.session_id}_{ordinal:04d}_{query_sha256[:8]}"
        turn = DialogueTurn(
            turn_id=turn_id,
            ordinal=ordinal,
            user_query=user_query,
            query_sha256=query_sha256,
            restitution_text=restitution_text,
            packet_id=packet_id,
            status=status,
            timestamp=timestamp,
        )
        self._turns.append(turn)
        return turn

    def list_turns(self) -> tuple[DialogueTurn, ...]:
        return tuple(self._turns)

    def to_state_entries(self, *, max_turns: int = 5) -> tuple[StateEntry, ...]:
        """Convertit l'historique de session en StateEntry pour l'assemblage B6."""
        recent = self._turns[-max_turns:] if max_turns > 0 else self._turns
        out: list[StateEntry] = []
        for t in recent:
            payload = t.to_dict()
            payload.update(readonly=True, memory_write=False)
            out.append(
                StateEntry(
                    state_id=f"session_history:{t.turn_id}",
                    state_type="SESSION_HISTORY_TURN",
                    source_ref=f"session:{self.session_id}",
                    payload=payload,
                    provenance=(f"session:{self.session_id}", t.query_sha256),
                    status=StateStatus.KNOWN,
                    visibility=Visibility.LONG,
                    tags=("session", "history", "session_history", "episodic_memory"),
                    summary=f"Turn {t.ordinal}: {t.user_query[:50]}",
                )
            )
        return tuple(out)
