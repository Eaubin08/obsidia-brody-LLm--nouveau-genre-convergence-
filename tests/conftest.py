"""Fixtures racine pytest pour la suite de tests Brody."""
import pytest
from pathlib import Path


@pytest.fixture
def repo_root() -> Path:
    """Retourne la racine du dépôt détectée par le module paths."""
    from brody.core.paths import BRODY_ROOT
    return BRODY_ROOT
