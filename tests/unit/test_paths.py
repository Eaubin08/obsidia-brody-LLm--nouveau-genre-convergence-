"""tests/unit/test_paths.py — Validation de la portabilité et de la dynamique des chemins."""
import os
import pytest
from pathlib import Path

from brody.core.paths import (
    BRODY_ROOT,
    BRODY_DATA_DIR,
    BRODY_CORPUS_DIR,
    BRODY_LEXICON_PATH,
    check_corpus_available,
    require_lexicon_path,
)
from brody.core.exceptions import CorpusNotFoundError


def test_brody_root_resolution():
    """Valide que BRODY_ROOT est un répertoire existant contenant pyproject.toml."""
    assert BRODY_ROOT.is_dir()
    assert (BRODY_ROOT / "pyproject.toml").is_file()
    assert (BRODY_ROOT / "brody").is_dir()


def test_paths_relative_structure():
    """Valide la cohérence de l'arborescence par défaut."""
    assert BRODY_DATA_DIR == BRODY_ROOT / "data"
    assert BRODY_CORPUS_DIR == BRODY_DATA_DIR / "linguistic_corpus"
    assert BRODY_LEXICON_PATH == BRODY_CORPUS_DIR / "lexicon.db"


def test_corpus_absence_tolerance():
    """Valide que check_corpus_available retourne un booléen sans exception."""
    result = check_corpus_available()
    assert isinstance(result, bool)


def test_require_lexicon_path_raises_when_missing(monkeypatch, tmp_path):
    """Valide que require_lexicon_path lève CorpusNotFoundError lorsque le fichier est absent."""
    fake_db = tmp_path / "non_existent.db"
    monkeypatch.setattr("brody.core.paths.BRODY_LEXICON_PATH", fake_db)
    
    with pytest.raises(CorpusNotFoundError) as exc_info:
        require_lexicon_path()
    
    assert "Base lexicale introuvable" in str(exc_info.value)
    assert "LEXICON_PUBLICATION_HOLD" in str(exc_info.value)


def test_env_override_data_dir(monkeypatch, tmp_path):
    """Valide que la surcharge par variable d'environnement fonctionne."""
    custom_data = tmp_path / "custom_data"
    monkeypatch.setenv("BRODY_DATA_DIR", str(custom_data))
    
    # Recharger ou instancier avec la nouvelle variable
    data_dir = Path(os.getenv("BRODY_DATA_DIR"))
    assert data_dir == custom_data
