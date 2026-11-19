"""tests/voice/test_voice_contracts.py — Validation des contrats et invariants vocaux."""
from __future__ import annotations

import pytest

from brody.voice.contracts import (
    VoiceState,
    VoiceTurnResult,
    WakeInputResult,
    VOICE_BOUNDARY,
)


def test_voice_state_values():
    assert VoiceState.IDLE.value == "idle"
    assert VoiceState.LISTENING.value == "listening"
    assert VoiceState.THINKING.value == "thinking"
    assert VoiceState.SPEAKING.value == "speaking"


def test_wake_input_result():
    res = WakeInputResult(woke=True, transcript="bonjour")
    assert res.woke is True
    assert res.transcript == "bonjour"

    res_no_wake = WakeInputResult(woke=False)
    assert res_no_wake.woke is False
    assert res_no_wake.transcript is None


def test_voice_turn_result_invariants():
    res = VoiceTurnResult(
        audio_in_size=32000,
        transcript="combien font 2 + 2 ?",
        response_text="4",
        state=VoiceState.SPEAKING,
        follow_up_open=True,
    )
    assert res.decision_authority == "KX108_ONLY"
    assert res.readonly is True
    assert res.emits_act is False
    assert res.memory_write is False
    assert res.kernel_mutation is False

    d = res.to_dict()
    assert d["transcript"] == "combien font 2 + 2 ?"
    assert d["response_text"] == "4"
    assert d["state"] == "speaking"
    assert d["decision_authority"] == "KX108_ONLY"
