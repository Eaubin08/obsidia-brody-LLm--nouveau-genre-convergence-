"""brody/voice/ingress.py — Ingress vocal (déclenchement par mot d'activation et suivi de tour).

Assure la transition entre le flux audio physique, la détection de silence
et l'enregistrement de l'énoncé utilisateur.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Callable, Optional

from brody.voice.runtime import ConversationVoiceRuntime
from brody.voice.wake import WakeInputRuntime


@dataclass
class VoiceIngressRuntime:
    """Gestionnaire d'ingress par fenêtres temporelles délimitées."""
    wake_input: WakeInputRuntime
    conversation: ConversationVoiceRuntime

    def capture_and_begin_turn(self, duration_seconds: float) -> str | None:
        """Capture l'audio, vérifie le mot d'activation et amorce le tour de parole."""
        result = self.wake_input.capture_once(duration_seconds)
        if not result.woke:
            return None
        if result.transcript is None:
            raise ValueError("wake input returned no transcript")
        return self.conversation.accept_transcript(result.transcript)

    def capture_follow_up(self, duration_seconds: float) -> str:
        """Capture un tour de relance sans exiger de répétition du mot d'activation."""
        if not self.conversation.follow_up_open:
            raise RuntimeError("follow-up window is not open")

        audio = self.wake_input.microphone.capture(duration_seconds)
        if not audio:
            raise ValueError("microphone returned empty audio")

        transcript = self.wake_input.stt.transcribe(audio).strip()
        if not transcript:
            raise ValueError("empty follow-up transcript")

        return self.conversation.accept_transcript(transcript)


@dataclass
class StreamingVoiceIngress:
    """Ingress vocal continu par paquets audio avec détection de silence."""
    microphone: object
    wake_word: object
    stt: object
    conversation: ConversationVoiceRuntime
    chunk_samples: int = 1280
    max_utterance_seconds: float = 8.0
    silence_seconds: float = 0.65
    rms_threshold: int = 300
    wake_speech_start_timeout: float = 3.0
    follow_up_start_timeout: float = 2.0
    on_wake: Callable[[], None] | None = None
    _pending_fragment: str = field(default="", init=False, repr=False)

    def capture_and_begin_turn(self, _duration_seconds: float = 0.0) -> str | None:
        reset = getattr(self.wake_word, "reset", None)
        if callable(reset):
            reset()

        iter_chunks = getattr(self.microphone, "iter_chunks", None)
        if not callable(iter_chunks):
            # Fallback en capture par bloc fixe si iter_chunks non supporté
            capture = getattr(self.microphone, "capture", None)
            if callable(capture):
                audio = capture(max(1.0, _duration_seconds))
                if self.wake_word.detect(audio):
                    transcript = self.stt.transcribe(audio).strip()
                    if transcript:
                        return self.conversation.accept_transcript(transcript)
            return None

        chunks = self.microphone.iter_chunks(chunk_samples=self.chunk_samples)
        try:
            for chunk in chunks:
                detected = self.wake_word.detect(chunk)
                if detected:
                    if self.on_wake is not None:
                        self.on_wake()

                    close = getattr(chunks, "close", None)
                    if callable(close):
                        close()

                    capture_silence = getattr(self.microphone, "capture_until_silence", None)
                    if callable(capture_silence):
                        audio = capture_silence(
                            max_seconds=self.max_utterance_seconds,
                            silence_seconds=self.silence_seconds,
                            rms_threshold=self.rms_threshold,
                            speech_start_timeout=self.wake_speech_start_timeout,
                        )
                    else:
                        audio = self.microphone.capture(self.max_utterance_seconds)

                    if not audio:
                        self.conversation.follow_up_open = False
                        return None
                    transcript = self.stt.transcribe(audio).strip()
                    if not transcript:
                        self.conversation.follow_up_open = False
                        return None
                    return self.conversation.accept_transcript(transcript)
        finally:
            close = getattr(chunks, "close", None)
            if callable(close):
                close()
        return None
