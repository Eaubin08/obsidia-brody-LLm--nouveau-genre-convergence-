"""tests/voice/test_stt_and_tts.py — Tests des modules STT, TTS et du microphone virtuel."""
from __future__ import annotations

import io
import wave
import pytest

from brody.voice.stt import DeterministicSTT
from brody.voice.tts import (
    LocalTTS,
    NativeWavSynthesizer,
)
from brody.voice.microphone import VirtualMicrophone


def test_deterministic_stt_mapping_and_defaults():
    stt = DeterministicSTT(default_text="Demande par défaut.")
    stt.register(b"\x01\x02\x03", "Bonjour Brody")

    assert stt.transcribe(b"\x01\x02\x03") == "Bonjour Brody"
    assert stt.transcribe(b"\x99\x88\x77") == "Demande par défaut."

    with pytest.raises(ValueError, match="audio must not be empty"):
        stt.transcribe(b"")


def test_native_wav_synthesizer_produces_valid_pcm16_wav():
    synth = NativeWavSynthesizer(sample_rate=16000, base_frequency=240.0)
    audio = synth.synthesize("Bonjour, le système Brody est opérationnel.")

    assert len(audio) > 1000
    assert audio.startswith(b"RIFF")

    # Vérification que wave peut lire l'en-tête WAV sans erreur
    with wave.open(io.BytesIO(audio), "rb") as wav:
        assert wav.getnchannels() == 1
        assert wav.getsampwidth() == 2
        assert wav.getframerate() == 16000
        frames = wav.readframes(wav.getnframes())
        assert len(frames) > 0


def test_native_wav_synthesizer_rejects_empty():
    synth = NativeWavSynthesizer()
    with pytest.raises(ValueError, match="text must not be empty"):
        synth.synthesize("   ")


def test_local_tts_cancellable_speech():
    synth = NativeWavSynthesizer()
    tts = LocalTTS(synth)

    handle = tts.speak("Message de test synthétisé.")
    assert handle.stop.is_set() is False

    # Annulation
    handle.cancel()
    assert handle.stop.is_set() is True
    handle.wait(timeout=1.0)


def test_virtual_microphone_feed_and_capture():
    mic = VirtualMicrophone(sample_rate=16000)
    # 16000 samples @ 2 bytes = 32000 bytes per second
    mic.feed(b"\x05\x00" * 8000)  # 0.5 sec

    chunk1 = mic.capture(0.25)
    assert len(chunk1) == 8000
    assert chunk1 == b"\x05\x00" * 4000

    chunk2 = mic.capture(0.5)
    assert len(chunk2) == 16000
    # Le reste du buffer fait 0.25s, le complément est silencieux
    assert chunk2[:8000] == b"\x05\x00" * 4000
    assert chunk2[8000:] == b"\x00" * 8000


def test_virtual_microphone_iter_chunks():
    mic = VirtualMicrophone(sample_rate=16000)
    mic.feed(b"\x01\x02" * 2560)  # 2 chunks de 1280 samples

    chunks = list(mic.iter_chunks(chunk_samples=1280))
    assert len(chunks) == 2
    assert len(chunks[0]) == 1280 * 2
    assert len(chunks[1]) == 1280 * 2
