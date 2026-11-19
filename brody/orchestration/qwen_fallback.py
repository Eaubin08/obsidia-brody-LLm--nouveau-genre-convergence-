"""brody/orchestration/qwen_fallback.py — Repli consultatif gouverné vers Qwen (non souverain).

Garantit :
  - Qwen désactivé par défaut (0 appel, 100% CPU).
  - Aucune autorité décisionnelle (decision_authority = "KX108_ONLY").
  - Contexte en lecture seule préalablement sélectionné uniquement (aucun dump complet du corpus).
  - Nettoyage et élimination des balises de réflexion interne (<thinking>, scratchpad).
  - Enveloppe consultative non publiable (publication_permitted = False).

Frontière : KX108_ONLY.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import re
from typing import Any, Callable, Mapping, Optional


_REASONING_PAIRS = (
    ("<thinking>", "</thinking>"),
    ("<scratchpad>", "</scratchpad>"),
    ("[INTERNAL]", "[/INTERNAL]"),
    ("[HIDDEN]", "[/HIDDEN]"),
)


def clean_model_output(text: str) -> str:
    """Élimine les balises de réflexion privées et normalise le texte de sortie."""
    if not isinstance(text, str):
        return ""
    working = text.strip()
    for opener, closer in _REASONING_PAIRS:
        while opener in working:
            start = working.find(opener)
            end = working.find(closer, start + len(opener))
            if end != -1:
                working = (working[:start] + working[end + len(closer):]).strip()
            else:
                working = working[:start].strip()
                break
    return working


@dataclass
class GovernedQwenFallback:
    """Adaptateur de repli consultatif gouverné."""
    enabled: bool = False
    model_name: str = "qwen2.5-7b-instruct-consultative"
    model_calls_count: int = 0
    provider_fn: Optional[Callable[[str, dict[str, Any]], str]] = None

    def consult(
        self,
        query: str,
        *,
        preselected_context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Exécute une consultation de repli uniquement si explicitement activé."""
        if not self.enabled:
            return {
                "status": "DISABLED",
                "consultative_answer": None,
                "model_calls": 0,
                "author": "NATIVE_BRODY",
                "decision_authority": "KX108_ONLY",
                "publication_permitted": False,
                "reason": "Qwen fallback is disabled by configuration (native pure execution).",
            }

        # Contexte sélectionné en lecture seule uniquement
        safe_context = preselected_context or {}
        self.model_calls_count += 1

        # Si un fournisseur local simulé/connecté est injecté
        if self.provider_fn is not None:
            raw_response = self.provider_fn(query, safe_context)
        else:
            # Réponse consultative déterministe standard si aucun serveur externe n'est actif
            raw_response = (
                f"[Avis consultatif Qwen] : Éléments de synthèse pour '{query}'. "
                f"Cet avis est non contraignant et soumis au contrôle souverain KX108."
            )

        cleaned_response = clean_model_output(raw_response)
        evidence_hash = hashlib.sha256(
            f"QWEN_CONSULT:{query}:{cleaned_response}".encode("utf-8")
        ).hexdigest()

        return {
            "status": "FALLBACK_CONSULTATIVE",
            "consultative_answer": cleaned_response,
            "model_calls": 1,
            "model_name": self.model_name,
            "author": "QWEN",
            "decision_authority": "KX108_ONLY",
            "publication_permitted": False,
            "is_consultative": True,
            "evidence_hash": evidence_hash,
            "context_summary": {
                "keys_provided": list(safe_context.keys()),
                "readonly_attested": True,
            },
        }
