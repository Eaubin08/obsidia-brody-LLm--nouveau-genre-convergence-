"""brody/voice/stt.py — Moteurs de transcription vocale (Speech-to-Text).

Contient l'adaptateur Faster-Whisper confiné sur CPU (int8) et le transcripteur
déterministe natif sans téléchargement de poids externe.
"""
from __future__ import annotations

import io
from pathlib import Path
import re
import tempfile
import unicodedata
from typing import Optional, Union
import wave

from brody.voice.contracts import SpeechToTextProvider


_KNOWN_HALLUCINATIONS = (
    "sous titres realises par la communaute d amara org",
    "les sous titres de cette session ont ete realises par la communaute d amara org",
    "merci d avoir regarde cette video",
    "merci d avoir visionne cette video",
    "n oubliez pas de vous abonner",
)


def _normalize_gate_text(text: str) -> str:
    value = unicodedata.normalize("NFKD", text.casefold())
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def _is_known_hallucination(text: str) -> bool:
    value = _normalize_gate_text(text)
    return any(phrase in value for phrase in _KNOWN_HALLUCINATIONS)


class DeterministicSTT(SpeechToTextProvider):
    """Transcripteur déterministe CPU sans modèle de poids neuronal.

    Fournit une transcription reproductible basée sur des métadonnées WAV
    ou un dictionnaire de correspondances sonores pour tests et exécution locale.
    """
    def __init__(self, mapping: Optional[dict[bytes, str]] = None, default_text: str = ""):
        self.mapping = dict(mapping or {})
        self.default_text = default_text
        self.last_audio: Optional[bytes] = None

    def register(self, audio: bytes, text: str) -> None:
        self.mapping[audio] = text

    def transcribe(self, audio: bytes) -> str:
        if not audio:
            raise ValueError("audio must not be empty")
        self.last_audio = audio

        # 1. Correspondance exacte par octets
        if audio in self.mapping:
            return self.mapping[audio]

        # 2. Correspondance par sous-chaîne ou préfixe (gestion du padding de silence)
        for key, text in self.mapping.items():
            if key and key in audio:
                return text

        # 2. Si l'audio contient des métadonnées texte ou un en-tête WAV embarqué
        if audio.startswith(b"RIFF") and len(audio) > 44:
            # Recherche d'un marqueur textuel embarqué
            sub = audio[44:]
            try:
                decoded = sub.decode("utf-8", errors="ignore").strip()
                if decoded and len(decoded) > 2:
                    return decoded
            except Exception:
                pass

        if self.default_text:
            return self.default_text
        return "Demande vocale reconnue."


class FasterWhisperSTT(SpeechToTextProvider):
    """Adaptateur local Faster-Whisper confiné sur CPU (device='cpu', compute_type='int8')."""
    def __init__(
        self,
        model_size: str = "tiny",
        *,
        device: str = "cpu",
        compute_type: str = "int8",
        language: Optional[str] = "fr",
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self._model = None

    def _load(self):
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                raise RuntimeError(
                    "faster-whisper is not installed; install faster-whisper for local STT"
                ) from exc
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
        return self._model

    def warmup(self) -> None:
        self._load()

    def _write_pcm16_wav(self, audio: bytes) -> Path:
        fd, name = tempfile.mkstemp(suffix=".wav")
        path = Path(name)
        with io.open(fd, "wb") as f, wave.open(f, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(audio)
        return path

    def transcribe(self, audio: bytes) -> str:
        if not audio:
            raise ValueError("audio must not be empty")
        path = self._write_pcm16_wav(audio)
        try:
            kwargs = {
                "vad_filter": True,
                "beam_size": 5,
                "best_of": 5,
                "temperature": 0.0,
                "condition_on_previous_text": False,
            }
            if self.language:
                kwargs["language"] = self.language
            segments, _ = self._load().transcribe(str(path), **kwargs)
            accepted: list[str] = []
            for segment in segments:
                text = segment.text.strip()
                if not text:
                    continue
                no_speech_prob = float(getattr(segment, "no_speech_prob", 0.0) or 0.0)
                avg_logprob = float(getattr(segment, "avg_logprob", 0.0) or 0.0)
                if no_speech_prob >= 0.92 and avg_logprob <= -1.20:
                    continue
                if _is_known_hallucination(text):
                    continue
                accepted.append(text)
            return " ".join(accepted).strip()
        finally:
            path.unlink(missing_ok=True)
