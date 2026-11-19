"""brody/voice/runtime.py — Runtime de dialogue conversationnel vocal.

Gère les transitions d'état vocal (IDLE, LISTENING, THINKING, SPEAKING),
la fenêtre de relance (follow-up) et l'interruption utilisateur (barge-in).
Zéro code dépendant d'un modèle lourd spécifique.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from brody.voice.contracts import (
    SpeechHandle,
    SpeechToTextProvider,
    TextToSpeechProvider,
    VoiceState,
)


@dataclass
class ConversationVoiceRuntime:
    stt: SpeechToTextProvider
    tts: TextToSpeechProvider
    state: VoiceState = VoiceState.IDLE
    follow_up_open: bool = False
    _speech: SpeechHandle | None = field(default=None, init=False, repr=False)

    def transcribe_turn(self, audio: bytes) -> str:
        """Transcrit un segment audio et gère la transition d'état."""
        self.state = VoiceState.LISTENING
        try:
            text = self.stt.transcribe(audio).strip()
        finally:
            self.state = VoiceState.IDLE
        if not text:
            raise ValueError("empty transcript")
        return text

    def accept_transcript(self, text: str) -> str:
        """Accepte une transcription validée et passe en état de réflexion."""
        transcript = text.strip()
        if not transcript:
            raise ValueError("empty transcript")
        self.state = VoiceState.THINKING
        self.follow_up_open = False
        return transcript

    def speak(self, text: str, *, open_follow_up: bool = True) -> SpeechHandle:
        """Déclenche la synthèse et l'émission vocale."""
        if not text.strip():
            raise ValueError("speech text must not be empty")
        self._speech = self.tts.speak(text)
        self.state = VoiceState.SPEAKING
        self.follow_up_open = open_follow_up
        return self._speech

    def barge_in(self) -> None:
        """Interrompt la parole en cours si l'utilisateur prend la parole."""
        if self._speech is not None:
            self._speech.cancel()
            self._speech = None
        self.state = VoiceState.LISTENING
        self.follow_up_open = True

    def speech_finished(self) -> None:
        """Notifie la fin de la diffusion audio."""
        self._speech = None
        self.state = VoiceState.IDLE
