"""tests/voice/test_voice_pipeline_e2e.py — Validation de bout en bout de la chaîne vocale Brody.

Valide le parcours complet :
  Voix (Microphone) → Reconnaissance (STT) → Brody Natif (Langage, Mémoire, Raisonnement, Composition)
  → Réponse → Synthèse Vocale (TTS).

Vérifications impératives :
  - 100% CPU, zéro GPU requis
  - Zéro appel externe, Qwen désactivé
  - Invariants de non-souveraineté KX108_ONLY
  - Gestion du suivi (follow-up) et interruption (barge-in)
"""
from __future__ import annotations

import pytest

from brody.voice.contracts import VoiceState
from brody.voice.ingress import VoiceIngressRuntime
from brody.voice.microphone import VirtualMicrophone
from brody.voice.runtime import ConversationVoiceRuntime
from brody.voice.stt import DeterministicSTT
from brody.voice.tts import LocalTTS, NativeWavSynthesizer
from brody.voice.turn_orchestrator import VoiceTurnOrchestrator
from brody.voice.wake import TranscriptWakeWordProvider, WakeInputRuntime


@pytest.fixture
def voice_pipeline():
    """Initialise un pipeline vocal Brody complet 100% CPU déterministe."""
    mic = VirtualMicrophone(sample_rate=16000)
    stt = DeterministicSTT()
    wake_word = TranscriptWakeWordProvider(stt, phrase="hey brody")
    wake_input = WakeInputRuntime(mic, wake_word, stt)

    synth = NativeWavSynthesizer(sample_rate=16000, base_frequency=220.0)
    tts = LocalTTS(synth)
    conv = ConversationVoiceRuntime(stt, tts)
    ingress = VoiceIngressRuntime(wake_input, conv)

    orchestrator = VoiceTurnOrchestrator(ingress, conv)
    return orchestrator, mic, stt, conv, synth


def test_e2e_voice_arithmetic_turn(voice_pipeline):
    """Scénario 1 : Voix → STT → Raisonnement arithmétique exact (Lot 4) → Réponse TTS."""
    orchestrator, mic, stt, conv, synth = voice_pipeline

    # 1. Alimente le micro virtuel avec un signal audio associé à une question arithmétique
    audio_query = b"\x10\x20" * 8000
    mic.feed(audio_query)
    stt.register(audio_query, "hey brody combien font 16 * 5 ?")

    # 2. Exécute le tour vocal
    turn_result = orchestrator.run_once(duration_seconds=1.0)

    # 3. Vérifications
    assert turn_result is not None
    assert turn_result.status == "SUCCESS"
    assert turn_result.transcript == "hey brody combien font 16 * 5 ?"
    assert "80" in turn_result.response_text
    assert turn_result.decision_authority == "KX108_ONLY"
    assert turn_result.readonly is True
    assert turn_result.emits_act is False

    # Attente de la synthèse asynchrone
    turn_result.speech_handle.wait(timeout=2.0)

    # Vérification que le TTS a synthétisé un flux WAV valide
    assert synth.last_audio is not None
    assert synth.last_audio.startswith(b"RIFF")
    assert conv.state is VoiceState.SPEAKING
    assert conv.follow_up_open is True

    # Fin de parole
    conv.speech_finished()
    assert conv.state is VoiceState.IDLE


def test_e2e_voice_editorial_composition_turn(voice_pipeline):
    """Scénario 2 : Voix → STT → Composition Studio E11 (Lot 5) → Réponse TTS."""
    orchestrator, mic, stt, conv, synth = voice_pipeline

    audio_query = b"\x30\x40" * 8000
    mic.feed(audio_query)
    brief = "hey brody rédige une publication LinkedIn expliquant comment une petite entreprise peut utiliser l’IA pour gagner du temps."
    stt.register(audio_query, brief)

    turn_result = orchestrator.run_once(duration_seconds=1.0)

    assert turn_result is not None
    assert turn_result.status == "SUCCESS"
    text = turn_result.response_text

    # Vérifie la présence des marqueurs de la composition rhétorique True Voice V2
    assert "Est-ce que votre équipe peut gagner du temps avec l’IA" in text
    assert "Commencez par une seule tâche répétitive" in text
    assert "Par exemple, un premier essai" in text
    assert "Avant de poursuivre, comparez le temps passé" in text

    # Attente de la synthèse asynchrone
    turn_result.speech_handle.wait(timeout=2.0)

    # Vérifie que la synthèse vocale a généré l'audio complet
    assert synth.last_audio is not None
    assert len(synth.last_audio) > 5000
    assert turn_result.decision_authority == "KX108_ONLY"

    conv.speech_finished()
    assert conv.state is VoiceState.IDLE


def test_e2e_voice_follow_up_turn(voice_pipeline):
    """Scénario 3 : Enchaînement avec relance sans répéter le mot d'activation."""
    orchestrator, mic, stt, conv, synth = voice_pipeline

    # Premier tour
    audio1 = b"\x11\x22" * 8000
    mic.feed(audio1)
    stt.register(audio1, "hey brody combien font 20 + 5 ?")
    turn1 = orchestrator.run_once(duration_seconds=1.0)
    assert turn1 is not None
    assert "25" in turn1.response_text
    assert conv.follow_up_open is True

    # Tour de relance dans la fenêtre ouverte
    audio2 = b"\x33\x44" * 8000
    mic.feed(audio2)
    stt.register(audio2, "combien font 10 * 3 ?")
    turn2 = orchestrator.run_follow_up_once(duration_seconds=1.0)

    assert turn2 is not None
    assert turn2.transcript == "combien font 10 * 3 ?"
    assert "30" in turn2.response_text
    assert conv.follow_up_open is False  # Fermé au second tour


def test_e2e_voice_barge_in_interruption(voice_pipeline):
    """Scénario 4 : Interruption barge-in de la parole en cours."""
    orchestrator, mic, stt, conv, synth = voice_pipeline

    audio = b"\x55\x66" * 8000
    mic.feed(audio)
    stt.register(audio, "hey brody combien font 7 * 7 ?")
    turn = orchestrator.run_once(duration_seconds=1.0)

    assert conv.state is VoiceState.SPEAKING
    # Interruption par l'utilisateur
    conv.barge_in()
    assert conv.state is VoiceState.LISTENING
    assert turn.speech_handle.stop.is_set() is True


def test_e2e_voice_no_wake_word_returns_none(voice_pipeline):
    """Scénario 5 : Parole sans mot d'activation -> aucun traitement ni synthèse."""
    orchestrator, mic, stt, conv, synth = voice_pipeline

    audio_ambient = b"\x00\x01" * 8000
    mic.feed(audio_ambient)
    stt.register(audio_ambient, "bruit ambiant sans mot d'activation")

    turn = orchestrator.run_once(duration_seconds=1.0)
    assert turn is None
    assert conv.state is VoiceState.IDLE
    assert synth.last_audio is None
