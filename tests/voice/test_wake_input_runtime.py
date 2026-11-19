"""tests/voice/test_wake_input_runtime.py — Tests de l'activation vocale et réutilisation de transcription."""
from __future__ import annotations

import pytest

from brody.voice.wake import (
    TranscriptWakeWordProvider,
    WakeInputRuntime,
)


class FakeMicrophone:
    def __init__(self, audio_data: bytes = b"fake_audio"):
        self.audio_data = audio_data

    def capture(self, duration_seconds: float) -> bytes:
        return self.audio_data


class FakeWakeWord:
    def __init__(self, detect_result: bool = True, last_transcript: str = ""):
        self.detect_result = detect_result
        self.last_transcript = last_transcript
        self.received_audio = None

    def detect(self, audio: bytes) -> bool:
        self.received_audio = audio
        return self.detect_result


class FakeSTT:
    def __init__(self, transcript: str = "hey brody bonjour"):
        self.transcript = transcript
        self.calls = 0

    def transcribe(self, audio: bytes) -> str:
        self.calls += 1
        return self.transcript


def test_wake_input_detects_and_transcribes():
    mic = FakeMicrophone(b"audio_chunk_1")
    wake_word = FakeWakeWord(detect_result=True)
    stt = FakeSTT("brody quelle heure est-il")

    runtime = WakeInputRuntime(mic, wake_word, stt)
    result = runtime.capture_once(1.5)

    assert result.woke is True
    assert result.transcript == "brody quelle heure est-il"
    assert stt.calls == 1


def test_wake_input_returns_not_woke_when_unrecognized():
    mic = FakeMicrophone(b"bruit_de_fond")
    wake_word = FakeWakeWord(detect_result=False)
    stt = FakeSTT("inutile")

    runtime = WakeInputRuntime(mic, wake_word, stt)
    result = runtime.capture_once(1.0)

    assert result.woke is False
    assert result.transcript is None
    assert stt.calls == 0


def test_wake_input_reuses_cached_wake_transcript_without_duplicate_stt():
    mic = FakeMicrophone(b"audio_with_wake")
    wake_word = FakeWakeWord(detect_result=True, last_transcript="hey brody aide-moi")
    stt = FakeSTT("transcription_superflue")

    runtime = WakeInputRuntime(mic, wake_word, stt)
    result = runtime.capture_once(2.0)

    assert result.woke is True
    assert result.transcript == "hey brody aide-moi"
    assert stt.calls == 0  # Évite une double inférence CPU !


def test_transcript_wakeword_provider_detects_variants():
    stt = FakeSTT("hey brody peux-tu m'aider")
    provider = TranscriptWakeWordProvider(stt, phrase="hey brody")

    assert provider.detect(b"audio") is True
    assert provider.last_transcript == "hey brody peux-tu m'aider"

    stt.transcript = "dis brody quel est le plan"
    assert provider.detect(b"audio2") is True

    stt.transcript = "conversation sans rapport"
    assert provider.detect(b"audio3") is False


def test_rolling_buffer_preserves_boundary_wake():
    mic = FakeMicrophone(b"partie1_")
    wake_word = FakeWakeWord(detect_result=False)
    stt = FakeSTT("hey brody")

    runtime = WakeInputRuntime(mic, wake_word, stt)
    res1 = runtime.capture_once(1.0)
    assert res1.woke is False
    assert runtime._previous_audio == b"partie1_"

    # Seconde fenêtre avec la suite
    mic.audio_data = b"partie2_brody"
    wake_word.detect_result = True
    res2 = runtime.capture_once(1.0)
    assert res2.woke is True
    # Le tampon de détection a bien combiné les deux fenêtres
    assert wake_word.received_audio == b"partie1_partie2_brody"
    # Le tampon glissant est nettoyé après détection
    assert runtime._previous_audio == b""
