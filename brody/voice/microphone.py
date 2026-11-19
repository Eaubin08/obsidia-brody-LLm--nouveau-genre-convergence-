"""brody/voice/microphone.py — Adaptateurs de capture audio microphone.

Fournit le VirtualMicrophone déterministe pour tests/rejeu audio sans micro physique,
et le SoundDeviceMicrophone pour la capture en conditions réelles.
"""
from __future__ import annotations

import io
import time
from typing import Generator, Optional
import wave

from brody.voice.contracts import MicrophoneProvider


class VirtualMicrophone(MicrophoneProvider):
    """Microphone virtuel déterministe alimenté par mémoire tampon ou fichiers WAV."""
    def __init__(self, sample_rate: int = 16000, initial_audio: bytes = b""):
        self.sample_rate = sample_rate
        self.buffer = bytearray(initial_audio)
        self.position = 0

    def feed(self, audio: bytes) -> None:
        """Injecte des octets audio PCM16 dans le microphone virtuel."""
        self.buffer.extend(audio)

    def feed_wav_text(self, text: str, duration_seconds: float = 1.0) -> bytes:
        """Génère un flux WAV synthétique contenant du texte pour les tests STT."""
        num_samples = int(self.sample_rate * duration_seconds)
        raw_pcm = b"\x00\x00" * num_samples
        # Embarque le texte dans les données
        text_bytes = text.encode("utf-8")
        if len(text_bytes) <= len(raw_pcm):
            raw_pcm = text_bytes + raw_pcm[len(text_bytes):]
        self.feed(raw_pcm)
        return raw_pcm

    def capture(self, duration_seconds: float) -> bytes:
        if duration_seconds <= 0:
            raise ValueError("duration_seconds must be positive")
        num_bytes = int(self.sample_rate * 2 * duration_seconds)
        if self.position >= len(self.buffer):
            # Génère du silence si le buffer est épuisé
            return b"\x00" * num_bytes
        chunk = bytes(self.buffer[self.position : self.position + num_bytes])
        self.position += len(chunk)
        if len(chunk) < num_bytes:
            chunk = chunk + b"\x00" * (num_bytes - len(chunk))
        return chunk

    def iter_chunks(self, *, chunk_samples: int = 1280) -> Generator[bytes, None, None]:
        chunk_bytes = chunk_samples * 2
        while self.position < len(self.buffer):
            chunk = bytes(self.buffer[self.position : self.position + chunk_bytes])
            self.position += len(chunk)
            if len(chunk) < chunk_bytes:
                chunk = chunk + b"\x00" * (chunk_bytes - len(chunk))
            yield chunk


class SoundDeviceMicrophone(MicrophoneProvider):
    """Adaptateur local SoundDevice pour microphone matériel."""
    def __init__(
        self,
        *,
        sample_rate: int = 16000,
        channels: int = 1,
        device: Optional[int | str] = None,
    ):
        if sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        if channels != 1:
            raise ValueError("canonical microphone capture must be mono")
        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device

    @staticmethod
    def _sounddevice():
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise RuntimeError(
                "sounddevice is not installed; install sounddevice for physical microphone capture"
            ) from exc
        return sd

    def capture(self, duration_seconds: float) -> bytes:
        if duration_seconds <= 0:
            raise ValueError("duration_seconds must be positive")
        sd = self._sounddevice()
        frames = max(1, round(self.sample_rate * duration_seconds))
        recording = sd.rec(
            frames,
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="int16",
            device=self.device,
        )
        sd.wait()
        return recording.astype("<i2", copy=False).tobytes()

    def iter_chunks(self, *, chunk_samples: int = 1280):
        if chunk_samples <= 0:
            raise ValueError("chunk_samples must be positive")
        sd = self._sounddevice()
        with sd.RawInputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="int16",
            blocksize=chunk_samples,
            device=self.device,
        ) as stream:
            while True:
                data, _overflowed = stream.read(chunk_samples)
                yield bytes(data)
