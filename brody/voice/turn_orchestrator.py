"""brody/voice/turn_orchestrator.py — Orchestrateur de dialogue vocal de bout en bout.

Raccorde le cycle complet :
  Voix (Microphone) → Reconnaissance (STT) → Brody Natif (Langage, Mémoire, Raisonnement, Composition)
  → Réponse → Synthèse Vocale (TTS).

Garantit zéro modèle externe (Qwen désactivé) et confinement souverain KX108_ONLY.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Callable, Optional

from brody.voice.contracts import (
    SpeechHandle,
    VoiceState,
    VoiceTurnResult,
    VOICE_BOUNDARY,
)
from brody.voice.ingress import VoiceIngressRuntime
from brody.voice.runtime import ConversationVoiceRuntime


def strip_wake_prefix(text: str) -> str:
    """Retire le préfixe d'activation vocale pour transmettre l'intention pure à Brody."""
    patterns = [
        r"^(?:hey|hé|eh|dis|ok)?\s*brody[\s,:\.\?!-]*",
        r"^(?:hey|hé|eh|dis|ok)?\s*jarvis[\s,:\.\?!-]*",
    ]
    cleaned = str(text or "").strip()
    for p in patterns:
        stripped = re.sub(p, "", cleaned, flags=re.IGNORECASE).strip()
        if stripped:
            return stripped
    return cleaned


def default_brody_cognition(query: str) -> Any:
    """Point de raccordement par défaut avec le pipeline de raisonnement déterministe Brody."""
    from brody.reasoning.pipeline_bridge import run_reasoning_pipeline
    return run_reasoning_pipeline(query)


@dataclass
class VoiceTurnOrchestrator:
    """Orchestrateur de bout en bout d'un tour de parole vocal Brody."""
    ingress: VoiceIngressRuntime
    conversation: ConversationVoiceRuntime
    cognition_fn: Callable[[str], Any] = default_brody_cognition

    def run_once(self, duration_seconds: float = 3.0) -> Optional[VoiceTurnResult]:
        """Capture un énoncé audio, exécute le raisonnement natif et déclenche la réponse vocale."""
        transcript = self.ingress.capture_and_begin_turn(duration_seconds)
        if transcript is None:
            return None

        clean_transcript = transcript.strip()
        if not clean_transcript:
            raise ValueError("empty transcript captured")

        # 1. Élimination du préfixe d'activation pour le raisonnement souverain Brody
        cognition_query = strip_wake_prefix(clean_transcript)

        # 2. Traitement par la chaîne native Brody (Lot 1 à Lot 5)
        reasoning_res = self.cognition_fn(cognition_query)

        # 3. Extraction du texte de restitution souverain
        if hasattr(reasoning_res, "result_text"):
            response_text = reasoning_res.result_text
        elif isinstance(reasoning_res, dict) and "text" in reasoning_res:
            response_text = reasoning_res["text"]
        else:
            response_text = str(reasoning_res)

        if not response_text.strip():
            raise ValueError("empty cognition response produced")

        # 4. Synthèse et émission vocale (TTS)
        speech_handle = self.conversation.speak(response_text, open_follow_up=True)

        return VoiceTurnResult(
            transcript=clean_transcript,
            response_text=response_text,
            reasoning_result=reasoning_res,
            speech_handle=speech_handle,
            state=self.conversation.state,
            follow_up_open=self.conversation.follow_up_open,
            status="SUCCESS",
            **VOICE_BOUNDARY,
        )

    def run_follow_up_once(self, duration_seconds: float = 3.0) -> VoiceTurnResult:
        """Capture un tour de relance sans réexiger le mot d'activation."""
        transcript = self.ingress.capture_follow_up(duration_seconds)
        clean_transcript = transcript.strip()
        if not clean_transcript:
            raise ValueError("empty follow-up transcript")

        cognition_query = strip_wake_prefix(clean_transcript)
        reasoning_res = self.cognition_fn(cognition_query)
        if hasattr(reasoning_res, "result_text"):
            response_text = reasoning_res.result_text
        elif isinstance(reasoning_res, dict) and "text" in reasoning_res:
            response_text = reasoning_res["text"]
        else:
            response_text = str(reasoning_res)

        speech_handle = self.conversation.speak(response_text, open_follow_up=False)

        return VoiceTurnResult(
            transcript=clean_transcript,
            response_text=response_text,
            reasoning_result=reasoning_res,
            speech_handle=speech_handle,
            state=self.conversation.state,
            follow_up_open=self.conversation.follow_up_open,
            status="SUCCESS",
            **VOICE_BOUNDARY,
        )
