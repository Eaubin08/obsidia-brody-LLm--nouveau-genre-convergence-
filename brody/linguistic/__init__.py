"""brody/linguistic — Moteurs linguistiques natifs de Brody V1.

Ce package rassemble les analyseurs grammaticaux déterministes français et anglais,
le gestionnaire lexical SQLite unifié, le générateur morphosyntaxique et les modules
d'advisory grammatical (F8) et de décodage phonétique (F9).

Zéro modèle de langage externe. Zéro réseau. Décrit, ne décide jamais.
"""
from __future__ import annotations

import sys

from brody.linguistic import (
    lexical_corpus,
    primitives,
    lexicon,
    french_grammar,
    english_grammar,
    structural_deciphering,
    language_flow_projection,
    native_realization,
    native_grammar_correction,
    native_phonetics_f9,
    freedict_phonetics,
)

# Export des points d'entrée canoniques
from brody.linguistic.lexical_corpus import (
    corpus_identity,
    lookup_surface_form,
    realize_inflection,
    get_verb_paradigm,
    get_senses_and_synonyms,
    is_known_lexical_item,
    LinguisticAnalysis,
)
from brody.linguistic.primitives import (
    UtteranceFrame,
    PredicateUnit,
    Argument,
    RelationKind,
)
from brody.linguistic.french_grammar import (
    parse_utterance,
)
from brody.linguistic.english_grammar import (
    parse_english_utterance,
)
from brody.linguistic.structural_deciphering import (
    decipher_frame,
    decipher_dialogue,
)
from brody.linguistic.language_flow_projection import (
    project_ordered_flows,
)
from brody.linguistic.native_realization import (
    realize_semantic_relation,
)
from brody.linguistic.native_grammar_correction import (
    build_grammar_correction_advisory,
)
from brody.linguistic.native_phonetics_f9 import (
    text_to_phonemes,
)

# Rétrocompatibilité transparente pour les suites de tests existantes
_self = sys.modules[__name__]
sys.modules.setdefault("app.semantic.lattice", _self)
sys.modules.setdefault("brody.linguistic.lexical_corpus", lexical_corpus)
sys.modules.setdefault("brody.linguistic.lexical_corpus", lexical_corpus)
sys.modules.setdefault("brody.linguistic.french_grammar", french_grammar)
sys.modules.setdefault("brody.linguistic.english_grammar", english_grammar)
sys.modules.setdefault("brody.linguistic.primitives", primitives)
sys.modules.setdefault("brody.linguistic.lexicon", lexicon)
sys.modules.setdefault("brody.linguistic.structural_deciphering", structural_deciphering)
sys.modules.setdefault("brody.linguistic.language_flow_projection", language_flow_projection)
sys.modules.setdefault("brody.linguistic.native_realization", native_realization)
sys.modules.setdefault("brody.linguistic.native_grammar_correction", native_grammar_correction)
sys.modules.setdefault("brody.linguistic.native_phonetics_f9", native_phonetics_f9)
sys.modules.setdefault("brody.linguistic.freedict_phonetics", freedict_phonetics)

__all__ = [
    "parse_utterance",
    "parse_english_utterance",
    "lookup_surface_form",
    "realize_inflection",
    "get_verb_paradigm",
    "get_senses_and_synonyms",
    "is_known_lexical_item",
    "LinguisticAnalysis",
    "UtteranceFrame",
    "PredicateUnit",
    "Argument",
    "RelationKind",
    "decipher_frame",
    "decipher_dialogue",
    "project_ordered_flows",
    "realize_semantic_relation",
    "build_grammar_correction_advisory",
    "text_to_phonemes",
    "corpus_identity",
]
