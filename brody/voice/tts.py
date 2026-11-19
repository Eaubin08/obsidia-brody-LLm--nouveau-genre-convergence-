"""brody/voice/tts.py — Moteurs de synthèse vocale (Text-to-Speech).

Fournit le gestionnaire de parole annulable LocalSpeechHandle, l'adaptateur
Kokoro pour TTS neural sur CPU et le synthétiseur déterministe standard sans modèle lourd.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import io
import math
import struct
from threading import Event, Thread
from typing import Optional
import wave

from brody.voice.contracts import (
    SpeechEngine,
    SpeechHandle,
    TextToSpeechProvider,
)


@dataclass
class LocalSpeechHandle:
    """Poignée de contrôle sur une synthèse et lecture audio en cours d'exécution."""
    stop: Event
    thread: Thread
    errors: list[BaseException] = field(default_factory=list)

    def cancel(self) -> None:
        self.stop.set()

    def wait(self, timeout: Optional[float] = None) -> None:
        self.thread.join(timeout)
        if self.thread.is_alive():
            return
        if self.errors:
            raise RuntimeError(f"TTS playback failed: {self.errors[0]}") from self.errors[0]


class NativeWavSynthesizer(SpeechEngine):
    """Moteur de synthèse purement CPU basé sur la bibliothèque standard (wave + math).

    Génère un flux PCM16 WAV valide et audible sans exiger de GPU ni de modèle lourd.
    """
    def __init__(self, sample_rate: int = 16000, base_frequency: float = 220.0):
        self.sample_rate = sample_rate
        self.base_freq = base_frequency
        self.last_audio: Optional[bytes] = None

    def synthesize(self, text: str) -> bytes:
        clean = text.strip()
        if not clean:
            raise ValueError("text must not be empty")

        # Modifie la fréquence et la durée en fonction de la longueur du texte
        duration_per_char = 0.05
        total_duration = max(0.4, min(10.0, len(clean) * duration_per_char))
        num_samples = int(self.sample_rate * total_duration)

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(self.sample_rate)

            # Modulation harmonique simple simulant une voix phonétique
            samples = []
            for i in range(num_samples):
                t = i / self.sample_rate
                f = self.base_freq + 20.0 * math.sin(2.0 * math.pi * 3.0 * t)
                val = 0.5 * math.sin(2.0 * math.pi * f * t) + 0.25 * math.sin(2.0 * math.pi * (2 * f) * t)
                # Atténuation en enveloppe
                envelope = min(1.0, t / 0.05) * min(1.0, (total_duration - t) / 0.05)
                val *= envelope
                ival = int(val * 16383.0)
                samples.append(struct.pack("<h", ival))

            wav.writeframes(b"".join(samples))

        audio = buffer.getvalue()
        self.last_audio = audio
        return audio

    def play(self, audio: bytes, stop: Event) -> None:
        """Lecture audio non bloquante ou silencieuse si sounddevice n'est pas installé."""
        if stop.is_set():
            return
        try:
            import sounddevice as sd
            import soundfile as sf
            data, fs = sf.read(io.BytesIO(audio))
            sd.play(data, fs)
            # Attente cooperative avec vérification de l'arrêt
            duration = len(data) / fs
            elapsed = 0.0
            while elapsed < duration and not stop.is_set():
                import time
                time.sleep(0.05)
                elapsed += 0.05
            if stop.is_set():
                sd.stop()
        except ImportError:
            # Environnement sans driver audio physique : la synthèse est validée sans échec
            pass


class LocalTTS(TextToSpeechProvider):
    """Fournisseur TTS Jarvis/Brody avec gestion d'annulation (barge-in)."""
    def __init__(self, engine: SpeechEngine):
        self.engine = engine

    def speak(self, text: str) -> LocalSpeechHandle:
        if not text.strip():
            raise ValueError("speech text must not be empty")
        stop = Event()
        errors: list[BaseException] = []

        def run() -> None:
            try:
                stream_speak = getattr(self.engine, "stream_speak", None)
                if callable(stream_speak):
                    stream_speak(text, stop)
                    return

                audio = self.engine.synthesize(text)
                if not stop.is_set():
                    self.engine.play(audio, stop)
            except BaseException as exc:
                errors.append(exc)

        thread = Thread(target=run, name="brody-tts", daemon=True)
        thread.start()
        return LocalSpeechHandle(stop, thread, errors)


class KokoroEngine(SpeechEngine):
    """Adaptateur Kokoro TTS optionnel pour synthèse neurale haute fidélité sur CPU."""
    def __init__(
        self,
        *,
        lang_code: str = "f",
        voice: str = "ff_siwis",
        sample_rate: int = 24000,
        speed: float = 1.0,
    ):
        if speed <= 0:
            raise ValueError("speed must be positive")
        self.lang_code = lang_code
        self.voice = voice
        self.sample_rate = sample_rate
        self.speed = speed
        self._pipeline = None

    def _load(self):
        if self._pipeline is None:
            try:
                from kokoro import KPipeline
            except ImportError as exc:
                raise RuntimeError(
                    "kokoro is not installed; install kokoro for neural voice synthesis"
                ) from exc
            self._pipeline = KPipeline(lang_code=self.lang_code)
        return self._pipeline

    def warmup(self) -> None:
        self._load()

    def synthesize(self, text: str) -> bytes:
        clean = text.strip()
        if not clean:
            raise ValueError("text must not be empty")
        import numpy as np

        chunks = []
        for _, _, audio in self._load()(clean, voice=self.voice, speed=self.speed):
            if audio is not None:
                chunks.append(np.asarray(audio, dtype=np.float32))
        if not chunks:
            raise RuntimeError("Kokoro produced no audio")
        audio = np.concatenate(chunks)
        pcm = np.clip(audio, -1.0, 1.0)
        pcm = (pcm * 32767.0).astype("<i2").tobytes()

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(self.sample_rate)
            wav.writeframes(pcm)
        return buffer.getvalue()

    def play(self, audio: bytes, stop: Event) -> None:
        if stop.is_set():
            return
        try:
            import sounddevice as sd
            import soundfile as sf
            data, fs = sf.read(io.BytesIO(audio))
            sd.play(data, fs)
            sd.wait()
        except ImportError:
            pass
