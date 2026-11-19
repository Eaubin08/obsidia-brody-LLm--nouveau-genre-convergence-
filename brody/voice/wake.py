"""brody/voice/wake.py — Pipeline de détection d'activation vocale (Wake Word).

Implémente le buffer glissant à double fenêtre pour éviter les coupures
aux frontières de capture et la réutilisation de transcriptions existantes.
Fournit le TranscriptWakeWordProvider déterministe et l'OpenWakeWordProvider.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Optional

from brody.voice.contracts import (
    MicrophoneProvider,
    SpeechToTextProvider,
    WakeInputResult,
    WakeWordProvider,
)


def _normalize_phrase(text: str) -> str:
    return " ".join(re.findall(r"\w+", text.casefold(), flags=re.UNICODE))


def _wake_variants(phrase: str) -> tuple[str, ...]:
    normalized = _normalize_phrase(phrase)
    variants = {normalized}
    if "brody" in normalized:
        variants.update({
            "brody",
            "hey brody",
            "hé brody",
            "eh brody",
            "dis brody",
            "ok brody",
        })
    if "jarvis" in normalized:
        variants.update({
            "jarvis",
            "hey jarvis",
            "hé jarvis",
            "eh jarvis",
            "et jarvis",
            "hey j arvisse",
        })
    return tuple(sorted(variants))


@dataclass
class TranscriptWakeWordProvider:
    """Détecte un mot d'activation via transcription ou correspondance textuelle."""
    stt: SpeechToTextProvider
    phrase: str = "hey brody"
    last_transcript: str = field(default="", init=False)
    last_normalized_transcript: str = field(default="", init=False)

    def __post_init__(self) -> None:
        normalized = _normalize_phrase(self.phrase)
        if not normalized:
            raise ValueError("wake phrase must not be empty")
        self._normalized_phrase = normalized
        self._accepted_variants = _wake_variants(self.phrase)

    def detect(self, audio: bytes) -> bool:
        if not audio:
            raise ValueError("audio must not be empty")
        transcript = self.stt.transcribe(audio)
        normalized = _normalize_phrase(transcript)
        self.last_transcript = transcript
        self.last_normalized_transcript = normalized
        if not normalized:
            return False

        haystack = f" {normalized} "
        for variant in self._accepted_variants:
            if f" {variant} " in haystack:
                return True
        return False


@dataclass
class WakeInputRuntime:
    """Pipeline d'entrée déclenché par détection du mot d'activation."""
    microphone: MicrophoneProvider
    wake_word: WakeWordProvider
    stt: SpeechToTextProvider
    _previous_audio: bytes = field(default=b"", init=False, repr=False)

    def capture_once(self, duration_seconds: float) -> WakeInputResult:
        audio = self.microphone.capture(duration_seconds)
        if not audio:
            raise ValueError("microphone returned empty audio")

        # Buffer glissant à deux fenêtres pour capturer les phrases à cheval
        detection_audio = self._previous_audio + audio if self._previous_audio else audio
        self._previous_audio = audio

        if not self.wake_word.detect(detection_audio):
            return WakeInputResult(woke=False)

        # Réutilisation de la transcription si le détecteur l'a déjà calculée
        cached = getattr(self.wake_word, "last_transcript", None)
        if isinstance(cached, str) and cached.strip():
            transcript = cached.strip()
        else:
            transcript = self.stt.transcribe(detection_audio).strip()

        if not transcript:
            raise ValueError("empty transcript after wake detection")

        # Réinitialisation du buffer après détection validée
        self._previous_audio = b""
        return WakeInputResult(woke=True, transcript=transcript)


class OpenWakeWordProvider:
    """Adaptateur optionnel openWakeWord pour modèles ONNX pré-entraînés."""
    def __init__(
        self,
        model_path: str | Path,
        *,
        threshold: float = 0.5,
        inference_framework: str = "onnx",
    ):
        path = Path(model_path).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"wake-word model does not exist: {path}")
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold must be between 0 and 1")
        if inference_framework not in {"onnx", "tflite"}:
            raise ValueError("inference_framework must be 'onnx' or 'tflite'")

        self.model_path = path.resolve()
        self.threshold = threshold
        self.inference_framework = inference_framework
        self._model = None
        self.last_score = 0.0
        self.last_model = ""

    def _load(self):
        if self._model is None:
            try:
                from openwakeword.model import Model
            except ImportError as exc:
                raise RuntimeError(
                    "openwakeword is not installed; install the wakeword optional dependency"
                ) from exc

            self._model = Model(
                wakeword_models=[str(self.model_path)],
                inference_framework=self.inference_framework,
            )
        return self._model

    def reset(self) -> None:
        model = self._model
        if model is not None:
            reset = getattr(model, "reset", None)
            if callable(reset):
                reset()

    def detect(self, audio: bytes) -> bool:
        if not audio:
            raise ValueError("audio must not be empty")
        if len(audio) % 2:
            raise ValueError("PCM16 audio byte length must be even")

        try:
            import numpy as np
        except ImportError as exc:
            raise RuntimeError(
                "numpy is not installed; install the wakeword optional dependency"
            ) from exc

        model = self._load()
        frames = np.frombuffer(audio, dtype=np.int16)
        scores = model.predict(frames)

        for model_name, score in scores.items():
            self.last_score = float(score)
            self.last_model = model_name
            if score >= self.threshold:
                return True
        return False
