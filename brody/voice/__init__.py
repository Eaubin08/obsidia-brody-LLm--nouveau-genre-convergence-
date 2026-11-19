"""brody/voice — Sous-système vocal natif de Brody (reconnaissance, activation, synthèse et orchestration).

Ce package rassemble les briques vocales souveraines :
- Contrats et protocoles : VoiceState, SpeechToTextProvider, TextToSpeechProvider, WakeWordProvider
- Ingress et détection de mot d'activation : WakeInputRuntime, TranscriptWakeWordProvider, OpenWakeWordProvider
- Gestionnaire de conversation : ConversationVoiceRuntime (transitions, barge-in, follow-up)
- Reconnaissance vocale (STT) : FasterWhisperSTT (CPU int8), DeterministicSTT
- Synthèse vocale (TTS) : LocalTTS, NativeWavSynthesizer (CPU sans modèle lourd), KokoroEngine
- Capture audio : VirtualMicrophone, SoundDeviceMicrophone
- Orchestration de bout en bout : VoiceTurnOrchestrator (raccordé au pipeline de raisonnement Brody)

Zéro appel réseau non vérifié, Qwen désactivé, autorité souveraine exclusive KX108_ONLY.
"""
from __future__ import annotations

import sys

from brody.voice import (
    contracts,
    runtime,
    wake,
    ingress,
    stt,
    tts,
    microphone,
    turn_orchestrator,
    governed_audio,
)

from brody.voice.contracts import (
    MicrophoneProvider,
    SpeechEngine,
    SpeechHandle,
    SpeechToTextProvider,
    TextToSpeechProvider,
    VoiceState,
    VoiceTurnResult,
    WakeInputResult,
    WakeWordProvider,
    VOICE_BOUNDARY,
)
from brody.voice.runtime import (
    ConversationVoiceRuntime,
)
from brody.voice.wake import (
    OpenWakeWordProvider,
    TranscriptWakeWordProvider,
    WakeInputRuntime,
)
from brody.voice.ingress import (
    StreamingVoiceIngress,
    VoiceIngressRuntime,
)
from brody.voice.stt import (
    DeterministicSTT,
    FasterWhisperSTT,
)
from brody.voice.tts import (
    KokoroEngine,
    LocalSpeechHandle,
    LocalTTS,
    NativeWavSynthesizer,
)
from brody.voice.microphone import (
    SoundDeviceMicrophone,
    VirtualMicrophone,
)
from brody.voice.turn_orchestrator import (
    VoiceTurnOrchestrator,
    default_brody_cognition,
)
from brody.voice.governed_audio import (
    GovernedAudioCommandHandler,
)

# Alias de modules pour rétrocompatibilité des tests Jarjar/Jarvis existants
_self = sys.modules[__name__]
sys.modules.setdefault("jarvis.voice_runtime", runtime)
sys.modules.setdefault("jarvis.wake_input_runtime", wake)
sys.modules.setdefault("jarvis.voice_ingress_runtime", ingress)
sys.modules.setdefault("jarvis.streaming_voice_ingress", ingress)
sys.modules.setdefault("jarvis.voice_turn_runtime", turn_orchestrator)
sys.modules.setdefault("jarvis.contracts", contracts)

__all__ = [
    "VoiceState",
    "MicrophoneProvider",
    "WakeWordProvider",
    "SpeechToTextProvider",
    "TextToSpeechProvider",
    "SpeechHandle",
    "SpeechEngine",
    "WakeInputResult",
    "VoiceTurnResult",
    "VOICE_BOUNDARY",
    "ConversationVoiceRuntime",
    "WakeInputRuntime",
    "TranscriptWakeWordProvider",
    "OpenWakeWordProvider",
    "VoiceIngressRuntime",
    "StreamingVoiceIngress",
    "DeterministicSTT",
    "FasterWhisperSTT",
    "LocalSpeechHandle",
    "LocalTTS",
    "KokoroEngine",
    "NativeWavSynthesizer",
    "VirtualMicrophone",
    "SoundDeviceMicrophone",
    "VoiceTurnOrchestrator",
    "default_brody_cognition",
    "GovernedAudioCommandHandler",
]
