"""tests/voice/test_voice_ingress.py — Tests d'ingress vocal et de suivi de dialogue."""
from __future__ import annotations

import pytest

from brody.voice.contracts import VoiceState
from brody.voice.ingress import (
    StreamingVoiceIngress,
    VoiceIngressRuntime,
)
from brody.voice.runtime import ConversationVoiceRuntime
from brody.voice.wake import WakeInputRuntime


class FakeMicrophone:
    def __init__(self, audio_data: bytes = b"fake_mic_audio"):
        self.audio_data = audio_data

    def capture(self, duration_seconds: float) -> bytes:
        return self.audio_data


class FakeWakeWord:
    def __init__(self, woke=True):
        self.woke = woke

    def detect(self, audio):
        return self.woke


class FakeSTT:
    def __init__(self, text="requête initiale"):
        self.text = text

    def transcribe(self, audio):
        return self.text


class FakeSpeech:
    def cancel(self): pass
    def wait(self, timeout=None): pass


class FakeTTS:
    def speak(self, text):
        return FakeSpeech()


def test_ingress_capture_and_begin_turn():
    mic = FakeMicrophone(b"audio_sample")
    stt = FakeSTT("dis brody active le système")
    wake_input = WakeInputRuntime(mic, FakeWakeWord(True), stt)
    conv = ConversationVoiceRuntime(stt, FakeTTS())
    ingress = VoiceIngressRuntime(wake_input, conv)

    transcript = ingress.capture_and_begin_turn(2.0)
    assert transcript == "dis brody active le système"
    assert conv.state is VoiceState.THINKING


def test_ingress_capture_follow_up_success():
    mic = FakeMicrophone(b"audio_follow_up")
    stt = FakeSTT("oui confirme")
    wake_input = WakeInputRuntime(mic, FakeWakeWord(True), stt)
    conv = ConversationVoiceRuntime(stt, FakeTTS())
    conv.speak("Voulez-vous confirmer ?", open_follow_up=True)
    assert conv.follow_up_open is True

    ingress = VoiceIngressRuntime(wake_input, conv)
    transcript = ingress.capture_follow_up(2.0)
    assert transcript == "oui confirme"
    assert conv.state is VoiceState.THINKING
    assert conv.follow_up_open is False


def test_ingress_capture_follow_up_refuses_when_window_closed():
    mic = FakeMicrophone(b"audio_follow_up")
    stt = FakeSTT("relance refusée")
    wake_input = WakeInputRuntime(mic, FakeWakeWord(True), stt)
    conv = ConversationVoiceRuntime(stt, FakeTTS())
    conv.follow_up_open = False

    ingress = VoiceIngressRuntime(wake_input, conv)
    with pytest.raises(RuntimeError, match="follow-up window is not open"):
        ingress.capture_follow_up(2.0)


def test_streaming_voice_ingress_turn_detection():
    class StreamMic:
        def iter_chunks(self, chunk_samples=1280):
            yield b"chunk_1"
            yield b"chunk_2"

        def capture_until_silence(self, **kwargs):
            return b"utterance_audio"

    stt = FakeSTT("lance le calcul")
    conv = ConversationVoiceRuntime(stt, FakeTTS())
    streaming = StreamingVoiceIngress(
        microphone=StreamMic(),
        wake_word=FakeWakeWord(woke=True),
        stt=stt,
        conversation=conv,
    )

    transcript = streaming.capture_and_begin_turn(0.0)
    assert transcript == "lance le calcul"
    assert conv.state is VoiceState.THINKING
