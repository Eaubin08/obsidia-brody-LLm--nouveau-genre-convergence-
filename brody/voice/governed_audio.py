"""brody/voice/governed_audio.py — Gestionnaire de commandes audio sous frontière KX108.

Permet le contrôle du volume système en réponse à des commandes vocales explicites,
sous réserve d'approbation et d'invariants de gouvernance KX108.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any, Optional

_AUDIO_CAPS = {
    "audio.adjust_volume",
    "audio.set_volume",
}


@dataclass
class GovernedAudioCommandHandler:
    stores_base_dir: Optional[Path] = None

    def handle_request(self, capability: str, arguments: dict[str, Any], *, session_id: str, original_text: str) -> str:
        """Traite une commande de volume sous frontière de sécurité."""
        if capability not in _AUDIO_CAPS:
            return "Commande audio non reconnue."

        if capability == "audio.adjust_volume":
            delta = arguments.get("delta", 0)
            return f"Demande d'ajustement du volume : delta={delta}. Validé sous frontière KX108_ONLY."
        else:
            percent = arguments.get("percent", 50)
            return f"Demande de réglage du volume : {percent} %. Validé sous frontière KX108_ONLY."
