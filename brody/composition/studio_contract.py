"""brody/composition/studio_contract.py — Contrat éditorial déterministe Studio.

Génère une trame locale ou préserve le texte source utilisateur.
Aucun appel modèle, aucune décision d'autorité, aucune publication.
"""
from __future__ import annotations

from typing import Any, Dict


def build_readonly_draft(idea: str, source_text: str, network: str = "LinkedIn") -> Dict[str, Any]:
    """Construit un brouillon déterministe en lecture seule sans modèle d'IA."""
    subject = str(idea or "").strip()
    original = str(source_text or "").strip()
    if not subject and not original:
        raise ValueError("Sujet ou texte source requis.")
    if original:
        text = original
        source = "USER_SOURCE_TEXT_ONLY"
        warning = "Texte utilisateur conservé sans génération IA. Vérification humaine requise."
    else:
        text = (
            f"{subject}\n\n"
            "Ce sujet mérite une explication factuelle avant publication.\n\n"
            "[Contexte vérifiable à renseigner]\n\n"
            "[Ce qui a réellement été réalisé et sa source]\n\n"
            "[Limites, éléments non démontrés ou prochaines étapes]\n\n"
            "Quelle question souhaitez-vous approfondir ?"
        )
        source = "STUDIO_DETERMINISTIC_TEMPLATE"
        warning = "Trame locale non générée par Brody ni Qwen : compléter les preuves avant publication."
    return {
        "text": text,
        "warning": warning,
        "provenance": {
            "source": source,
            "network": network,
            "brody_post_model_synthesis_proven": False,
            "qwen_evidence_applied": False,
            "human_approval_required": True,
            "publication_permitted": False,
            "cognitive_gate": "NOT_CALLED",
        },
    }
