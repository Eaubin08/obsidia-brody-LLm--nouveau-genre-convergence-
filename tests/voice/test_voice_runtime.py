"""tests/voice/test_voice_runtime.py — Tests du cycle conversationnel vocal."""
from __future__ import annotations

import pytest

from brody.voice.contracts import VoiceState
from brody.voice.runtime import ConversationVoiceRuntime


class FakeSTT:
    def __init__(self, text="bonjour"):
        self.text = text
        self.audio = None

    def transcribe(self, audio):
        self.audio = audio
        return self.text


class FakeSpeech:
    def __init__(self):
        self.cancelled = False

    def cancel(self):
        self.cancelled = True

    def wait(self, timeout=None):
        pass


class FakeTTS:
    def __init__(self):
        self.text = None
        self.handle = FakeSpeech()

    def speak(self, text):
        self.text = text
        return self.handle


def test_transcribe_turn_is_provider_neutral():
    stt = FakeSTT("bonjour brody")
    runtime = ConversationVoiceRuntime(stt, FakeTTS())
    assert runtime.transcribe_turn(b"audio_bytes") == "bonjour brody"
    assert stt.audio == b"audio_bytes"
    assert runtime.state is VoiceState.IDLE


def test_speech_opens_follow_up_window():
    tts = FakeTTS()
    runtime = ConversationVoiceRuntime(FakeSTT(), tts)
    runtime.speak("Je suis prêt.")
    assert runtime.state is VoiceState.SPEAKING
    assert runtime.follow_up_open is True
    assert tts.text == "Je suis prêt."


def test_barge_in_cancels_active_speech_without_destroying_runtime():
    tts = FakeTTS()
    runtime = ConversationVoiceRuntime(FakeSTT(), tts)
    handle = runtime.speak("Explication longue en cours...")
    runtime.barge_in()
    assert handle.cancelled is True
    assert runtime.state is VoiceState.LISTENING
    assert runtime.follow_up_open is True


def test_empty_transcript_fails_closed():
    runtime = ConversationVoiceRuntime(FakeSTT("   "), FakeTTS())
    with pytest.raises(ValueError, match="empty transcript"):
        runtime.transcribe_turn(b"audio")


def test_empty_speech_fails_closed():
    runtime = ConversationVoiceRuntime(FakeSTT(), FakeTTS())
    with pytest.raises(ValueError, match="speech text must not be empty"):
        runtime.speak("   ")


def test_accept_transcript_enters_thinking_without_calling_stt():
    stt = FakeSTT("ne pas utiliser")
    runtime = ConversationVoiceRuntime(stt, FakeTTS())
    assert runtime.accept_transcript("  requête utilisateur  ") == "requête utilisateur"
    assert stt.audio is None
    assert runtime.state is VoiceState.THINKING
    assert runtime.follow_up_open is False


def test_speech_finished_resets_idle():
    runtime = ConversationVoiceRuntime(FakeSTT(), FakeTTS())
    runtime.speak("Réponse.")
    assert runtime.state is VoiceState.SPEAKING
    runtime.speech_finished()
    assert runtime.state is VoiceState.IDLE
