"""Fixtures racine pytest pour la suite de tests Brody."""
from __future__ import annotations

import sys
from pathlib import Path
import pytest

# Garantir que la racine du dépôt est dans sys.path
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Enregistrement des alias de rétrocompatibilité pour les suites de tests
import brody.linguistic as linguistic
import brody.linguistic.lexical_corpus as lexical_corpus

sys.modules.setdefault("app.semantic.lattice", linguistic)
sys.modules.setdefault("periphery.language.lexical_corpus", lexical_corpus)


@pytest.fixture
def repo_root() -> Path:
    """Retourne la racine du dépôt détectée par le module paths."""
    from brody.core.paths import BRODY_ROOT
    return BRODY_ROOT
