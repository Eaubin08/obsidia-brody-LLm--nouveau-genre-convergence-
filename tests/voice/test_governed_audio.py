"""tests/voice/test_governed_audio.py — Tests du gestionnaire de volume audio gouverné."""
from __future__ import annotations

import pytest

from brody.voice.governed_audio import GovernedAudioCommandHandler


def test_governed_audio_adjust_volume():
    handler = GovernedAudioCommandHandler()
    res = handler.handle_request(
        "audio.adjust_volume",
        {"delta": 10},
        session_id="sess-01",
        original_text="monte le volume",
    )
    assert "delta=10" in res
    assert "KX108_ONLY" in res


def test_governed_audio_set_volume():
    handler = GovernedAudioCommandHandler()
    res = handler.handle_request(
        "audio.set_volume",
        {"percent": 75},
        session_id="sess-02",
        original_text="mets le son à 75%",
    )
    assert "75 %" in res
    assert "KX108_ONLY" in res


def test_governed_audio_unknown_capability():
    handler = GovernedAudioCommandHandler()
    res = handler.handle_request(
        "unsupported.capability",
        {},
        session_id="sess-03",
        original_text="commande inconnue",
    )
    assert res == "Commande audio non reconnue."
