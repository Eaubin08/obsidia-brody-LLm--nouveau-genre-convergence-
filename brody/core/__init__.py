"""Sous-module core de Brody — Chemins, exceptions et invariants."""

from brody.core.paths import (
    BRODY_ROOT,
    BRODY_DATA_DIR,
    BRODY_CORPUS_DIR,
    BRODY_LEXICON_PATH,
    BRODY_CONFIG_DIR,
    check_corpus_available,
    require_lexicon_path,
)
from brody.core.exceptions import (
    BrodyError,
    CorpusNotFoundError,
    GovernanceViolationError,
    InvariantViolationError,
)

__all__ = [
    "BRODY_ROOT",
    "BRODY_DATA_DIR",
    "BRODY_CORPUS_DIR",
    "BRODY_LEXICON_PATH",
    "BRODY_CONFIG_DIR",
    "check_corpus_available",
    "require_lexicon_path",
    "BrodyError",
    "CorpusNotFoundError",
    "GovernanceViolationError",
    "InvariantViolationError",
]
