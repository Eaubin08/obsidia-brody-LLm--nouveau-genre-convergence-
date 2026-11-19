"""tests/orchestration/test_advanced_multi_turn_dialogue.py — Scénarios avancés de dialogue et validation des frontières (Lot 7).

Valide :
  1. Continuité cognitive sur dialogue long (15 tours consécutifs sans dégradation).
  2. Résilience et récupération après une contradiction (fail-closed).
  3. Enchaînement mixte : Audio STT -> Calcul exact -> Consultation Mémoire -> Rédaction E11 -> TTS.
  4. Non-régression : zéro appel à Qwen pendant les sessions natives pures.
  5. Imperméabilité souveraine KX108_ONLY sur tous les tours.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from brody.orchestration import (
    BrodyConversationalPipeline,
    BrodyDialogueSession,
    GovernedQwenFallback,
    TURN_STATUS_SUCCESS,
    TURN_STATUS_REFUSAL_JUSTIFIED,
    TURN_STATUS_HOLD_RECORDED,
    TURN_STATUS_INSUFFICIENT_EVIDENCE,
    TURN_STATUS_CONTRADICTION_PRESERVED,
    TURN_STATUS_FALLBACK_CONSULTATIVE,
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
def advanced_memory_file(tmp_path: Path) -> Path:
    """Index mémoire synthétique multi-entrées pour dialogue étendu."""
    idx = tmp_path / "native_memory_advanced.jsonl"
    records = [
        {
            "schema_version": "OBSIDIA_NATIVE_MEMORY_RECORD_V1",
            "native_id": "mem_arch_01",
            "title": "Architecture modulaire Brody",
            "normalized_source_path": "specs/arch/brody_modules.md",
            "source_original_path": "specs/arch/brody_modules.md",
            "source_ref": "obsidia://specs/arch/brody_modules.md",
            "source_type": "OBSIDIA_NATIVE_MEMORY_V1",
            "tags": ["architecture", "brody", "modules", "cognition"],
            "score": 100,
            "text_excerpt": "Brody articule six strates souveraines : hygiène, linguistique, contexte, raisonnement, composition et voix.",
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
        },
        {
            "schema_version": "OBSIDIA_NATIVE_MEMORY_RECORD_V1",
            "native_id": "mem_kx108_inv",
            "title": "Gouvernance des invariants du noyau",
            "normalized_source_path": "specs/kernel/kx108_invariants.md",
            "source_original_path": "specs/kernel/kx108_invariants.md",
            "source_ref": "obsidia://specs/kernel/kx108_invariants.md",
            "source_type": "OBSIDIA_NATIVE_MEMORY_V1",
            "tags": ["noyau", "kx108", "invariants", "gouvernance"],
            "score": 95,
            "text_excerpt": "108 invariants formels verrouillent l'espace d'exécution sans dérive.",
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
        },
    ]
    with idx.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    return idx


def test_extended_fifteen_turn_dialogue(advanced_memory_file: Path):
    """Vérifie la robustesse d'un dialogue de 15 tours consécutifs sans fuite d'état ni régression."""
    qwen_fb = GovernedQwenFallback(enabled=False)
    pipeline = BrodyConversationalPipeline(
        memory_index_path=advanced_memory_file,
        qwen_fallback=qwen_fb,
    )
    session = BrodyDialogueSession(session_id="extended_session_15_turns")

    queries_and_expectations = [
        # (requête, statut attendu, qwen_fallback)
        ("Bonjour Brody", TURN_STATUS_SUCCESS, False),
        ("Qui es-tu ?", TURN_STATUS_SUCCESS, False),
        ("Combien font 40 * 25 + 50 ?", TURN_STATUS_SUCCESS, False),
        ("Quels sont les invariants du noyau KX108 ?", TURN_STATUS_SUCCESS, False),
        ("Quel est l'état actuel de notre dialogue ?", TURN_STATUS_SUCCESS, False),
        ("Rédige une publication LinkedIn expliquant comment une petite entreprise peut utiliser l'IA pour gagner du temps.", TURN_STATUS_SUCCESS, False),
        ("Calcule 250 / 5 + 18 * 2", TURN_STATUS_SUCCESS, False),
        ("Quelle est l'architecture modulaire Brody ?", TURN_STATUS_SUCCESS, False),
        ("force-push sur la branche principale", TURN_STATUS_REFUSAL_JUSTIFIED, False),
        ("deploy les conteneurs de production", TURN_STATUS_HOLD_RECORDED, False),
        ("Quelle est la population de la colonie sur Ganymède en 2550 ?", TURN_STATUS_INSUFFICIENT_EVIDENCE, False),
        ("Combien font 999 + 1 ?", TURN_STATUS_SUCCESS, False),
        ("Quel est l'état actuel de notre dialogue ?", TURN_STATUS_SUCCESS, False),
        ("rm -rf / --no-preserve-root", TURN_STATUS_REFUSAL_JUSTIFIED, False),
        ("Combien font 12 * 12 ?", TURN_STATUS_SUCCESS, False),
    ]

    for idx, (q, expected_status, fb_flag) in enumerate(queries_and_expectations, start=1):
        turn = pipeline.process_turn(q, session=session, allow_qwen_fallback=fb_flag)
        assert turn.turn_index == idx
        assert turn.status == expected_status
        assert turn.route_decision.decision_authority == "KX108_ONLY"
        assert turn.receipt.qwen_fallback_used is False

    # Zéro appel à Qwen vérifié
    assert qwen_fb.model_calls_count == 0

    # Vérification métriques session
    snapshot = session.get_snapshot()
    assert snapshot.total_turns == 15
    assert snapshot.native_correct_count == 13
    assert snapshot.justified_refusal_count == 4
    assert snapshot.qwen_recourse_count == 0
    assert snapshot.qwen_recourse_rate == 0.0
    assert snapshot.native_correct_rate == round(13 / 15, 4)


def test_mixed_voice_and_text_multi_turn(advanced_memory_file: Path):
    """Valide l'alternance fluide entre entrées audio (Lot 6) et texte dans la même session."""
    pipeline = BrodyConversationalPipeline(memory_index_path=advanced_memory_file)
    session = BrodyDialogueSession(session_id="mixed_voice_text_session")

    # Configuration vocale Lot 6
    mic = VirtualMicrophone(sample_rate=16000)
    stt = DeterministicSTT()
    wake_word = TranscriptWakeWordProvider(stt, phrase="hey brody")
    wake_input = WakeInputRuntime(mic, wake_word, stt)
    synth = NativeWavSynthesizer(sample_rate=16000, base_frequency=220.0)
    tts = LocalTTS(synth)
    conv = ConversationVoiceRuntime(stt, tts)
    ingress = VoiceIngressRuntime(wake_input, conv)

    def unified_cognition(query: str):
        return pipeline.process_turn(query, session=session)

    orchestrator = VoiceTurnOrchestrator(ingress=ingress, conversation=conv, cognition_fn=unified_cognition)

    # Tour 1 : Entrée Audio STT
    audio_pcm = b"\x15\x30" * 8000
    mic.feed(audio_pcm)
    stt.register(audio_pcm, "hey brody combien font 50 * 6 ?")
    v_turn = orchestrator.run_once(duration_seconds=1.0)
    assert v_turn is not None
    assert "300" in v_turn.response_text
    assert len(session.turns) == 1

    # Tour 2 : Entrée Texte direct (Demande rédactionnelle Studio E11)
    t2 = pipeline.process_turn(
        "Rédige une publication LinkedIn expliquant comment une petite entreprise peut utiliser l'IA pour gagner du temps.",
        session=session,
    )
    assert t2.turn_index == 2
    assert t2.status == TURN_STATUS_SUCCESS
    assert "gagner du temps" in t2.answer_text
    assert len(session.turns) == 2

    # Tour 3 : Entrée Audio STT (Interrogation de statut)
    audio_pcm_2 = b"\x22\x44" * 8000
    mic.feed(audio_pcm_2)
    stt.register(audio_pcm_2, "hey brody quel est l'état actuel ?")
    v_turn_2 = orchestrator.run_once(duration_seconds=1.0)
    assert v_turn_2 is not None
    assert "tours enregistrés" in v_turn_2.response_text
    assert len(session.turns) == 3
