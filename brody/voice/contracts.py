"""brody/voice/contracts.py — Contrats et protocoles du sous-système vocal natif Brody/Jarvis.

Définit les interfaces de fournisseurs audio, états de dialogue vocal,
et garanties de non-souveraineté sous autorité KX108_ONLY.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from threading import Event
from typing import Any, Dict, Optional, Protocol


class VoiceState(str, Enum):
    """États du cycle conversationnel vocal."""
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"


class MicrophoneProvider(Protocol):
    """Fournisseur de capture audio microphone."""
    def capture(self, duration_seconds: float) -> bytes: ...


class WakeWordProvider(Protocol):
    """Fournisseur de détection de mot d'activation."""
    def detect(self, audio: bytes) -> bool: ...


class SpeechToTextProvider(Protocol):
    """Fournisseur de transcription audio en texte."""
    def transcribe(self, audio: bytes) -> str: ...


class SpeechHandle(Protocol):
    """Poignée de contrôle sur une émission vocale en cours."""
    def cancel(self) -> None: ...
    def wait(self, timeout: float | None = None) -> None: ...


class TextToSpeechProvider(Protocol):
    """Fournisseur de synthèse vocale."""
    def speak(self, text: str) -> SpeechHandle: ...


class SpeechEngine(Protocol):
    """Moteur bas niveau de synthèse et lecture audio."""
    def synthesize(self, text: str) -> bytes: ...
    def play(self, audio: bytes, stop: Event) -> None: ...


@dataclass(frozen=True)
class WakeInputResult:
    """Résultat d'une tentative de détection de mot d'activation."""
    woke: bool
    transcript: str | None = None


@dataclass
class VoiceTurnResult:
    """Enveloppe normalisée du résultat d'un tour de dialogue vocal complet."""
    audio_in_size: int = 0
    transcript: str = ""
    reasoning_type: str = "VOICE_TURN"
    status: str = "SUCCESS"
    response_text: str = ""
    reasoning_result: Optional[Any] = None
    speech_handle: Optional[SpeechHandle] = None
    state: VoiceState = VoiceState.IDLE
    follow_up_open: bool = False

    # Invariants de non-souveraineté KX108
    decision_authority: str = "KX108_ONLY"
    readonly: bool = True
    emits_act: bool = False
    emits_verdict: bool = False
    memory_write: bool = False
    kernel_mutation: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "audio_in_size": self.audio_in_size,
            "transcript": self.transcript,
            "reasoning_type": self.reasoning_type,
            "status": self.status,
            "response_text": self.response_text,
            "state": self.state.value,
            "follow_up_open": self.follow_up_open,
            "decision_authority": self.decision_authority,
            "readonly": self.readonly,
            "emits_act": self.emits_act,
            "memory_write": self.memory_write,
        }


VOICE_BOUNDARY: Dict[str, Any] = {
    "decision_authority": "KX108_ONLY",
    "readonly": True,
    "memory_write": False,
    "emits_act": False,
    "emits_verdict": False,
    "kernel_mutation": False,
}
