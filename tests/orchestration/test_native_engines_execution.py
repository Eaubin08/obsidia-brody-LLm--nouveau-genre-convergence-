"""tests/orchestration/test_native_engines_execution.py — Vérification de l'exécution réelle des 6 lots natifs.

Démontre sans équivoque que les moteurs des Lots 1 à 6 sont effectivement appelés,
exécutés et vérifiés lors du traitement conversationnel unifié (et non simplement importés).
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from brody.orchestration import (
    BrodyConversationalPipeline,
    BrodyDialogueSession,
    TURN_STATUS_SUCCESS,
)
from brody.voice.contracts import VoiceState
from brody.voice.ingress import VoiceIngressRuntime
from brody.voice.microphone import VirtualMicrophone
from brody.voice.runtime import ConversationVoiceRuntime
from brody.voice.stt import DeterministicSTT
from brody.voice.tts import LocalTTS, NativeWavSynthesizer
from brody.voice.turn_orchestrator import VoiceTurnOrchestrator
from brody.voice.wake import TranscriptWakeWordProvider, WakeInputRuntime


@pytest.fixture
def mock_memory_file(tmp_path: Path) -> Path:
    """Index mémoire synthétique pour valider l'appel réel au lecteur natif."""
    idx = tmp_path / "native_memory_test.jsonl"
    record = {
        "schema_version": "OBSIDIA_NATIVE_MEMORY_RECORD_V1",
        "native_id": "mem_kx108_inv_01",
        "title": "Gouvernance des invariants KX108",
        "normalized_source_path": "specs/kernel/kx108.md",
        "source_original_path": "specs/kernel/kx108.md",
        "source_ref": "obsidia://specs/kernel/kx108.md",
        "source_type": "OBSIDIA_NATIVE_MEMORY_V1",
        "tags": ["gouvernance", "noyau", "kx108", "invariants"],
        "score": 100,
        "text_excerpt": "Les 108 invariants formels sont inaltérables sans signature souveraine.",
        "readonly": True,
        "memory_authority": False,
        "memory_decision": False,
        "memory_write": False,
        "canonical_write": False,
        "auto_promotion": False,
        "kernel_mutation": False,
        "x108_mutation": False,
        "emits_act": False,
        "emits_verdict": False,
        "allowed_to_decide": False,
        "allowed_to_act": False,
        "decision_authority": "KX108_ONLY",
    }
    with idx.open("w", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return idx


def test_lot1_to_lot5_native_engines_real_execution(mock_memory_file: Path):
    pipeline = BrodyConversationalPipeline(memory_index_path=mock_memory_file)
    session = BrodyDialogueSession(session_id="exec_test_session")

    # 1. Vérification Lot 4 : Solveur Arithmétique Exact
    t1 = pipeline.process_turn("Calcule 15 * 8 + 30", session=session)
    assert t1.status == TURN_STATUS_SUCCESS
    assert "brody.reasoning.arithmetic_engine" in t1.native_modules_invoked
    assert t1.structured_payload.get("result") == 150
    assert "150" in t1.answer_text

    # 2. Vérification Lot 5 : Composition Studio E11
    t2 = pipeline.process_turn("Rédige un post linkedin pour expliquer les gains de l'IA", session=session)
    assert t2.status == TURN_STATUS_SUCCESS
    assert "brody.composition.engine" in t2.native_modules_invoked
    assert "brody.composition.envelope" in t2.native_modules_invoked
    assert "brody.composition.cleanup" in t2.native_modules_invoked
    assert "composition" in t2.structured_payload
    assert "consumption" in t2.structured_payload
    assert t2.structured_payload["consumption"]["publication_permitted"] is False

    # 3. Vérification Lot 2 & Lot 3 : Analyse SENS et Mémoire Native
    t3 = pipeline.process_turn("Quels sont les invariants du noyau KX108 ?", session=session)
    assert t3.status == TURN_STATUS_SUCCESS
    assert "brody.linguistic.sens" in t3.native_modules_invoked
    assert "brody.context.working_state_registry" in t3.native_modules_invoked

    # Vérification que le registre B6 (Lot 3) a conservé l'état des tours
    assert len(session.registry.list_entries()) >= 3


def test_lot6_voice_turn_orchestrator_integration():
    """Valide l'orchestration vocale complète raccordée au pipeline conversationnel."""
    pipeline = BrodyConversationalPipeline()
    session = BrodyDialogueSession(session_id="voice_integrated_session")

    mic = VirtualMicrophone(sample_rate=16000)
    stt = DeterministicSTT()
    wake_word = TranscriptWakeWordProvider(stt, phrase="hey brody")
    wake_input = WakeInputRuntime(mic, wake_word, stt)

    synth = NativeWavSynthesizer(sample_rate=16000, base_frequency=220.0)
    tts = LocalTTS(synth)
    conv = ConversationVoiceRuntime(stt, tts)
    ingress = VoiceIngressRuntime(wake_input, conv)

    # Fonction de cognition raccordée directement au pipeline unifié
    def unified_cognition(query: str):
        return pipeline.process_turn(query, session=session)

    orchestrator = VoiceTurnOrchestrator(
        ingress=ingress,
        conversation=conv,
        cognition_fn=unified_cognition,
    )

    audio_query = b"\x10\x20" * 8000
    mic.feed(audio_query)
    stt.register(audio_query, "hey brody combien font 25 * 4 ?")

    voice_res = orchestrator.run_once(duration_seconds=1.0)

    assert voice_res is not None
    assert voice_res.transcript == "hey brody combien font 25 * 4 ?"
    assert "100" in voice_res.response_text
    assert len(session.turns) == 1
    assert session.turns[0].structured_payload.get("result") == 100
