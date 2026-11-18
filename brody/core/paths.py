"""brody/core/paths.py — Résolution dynamique et portable des chemins racine.

Garantit le découplage complet de l'environnement machine.
Aucun chemin absolu en dur n'est autorisé.
"""
from __future__ import annotations

import os
from pathlib import Path

from brody.core.exceptions import CorpusNotFoundError


# 1. Détermination de la racine du dépôt (relatif à ce fichier : brody/core/paths.py -> parents[2])
_DEFAULT_ROOT = Path(__file__).resolve().parents[2]
BRODY_ROOT = Path(os.getenv("BRODY_ROOT", str(_DEFAULT_ROOT)))

# 2. Emplacements configurables des données et des corpus
BRODY_DATA_DIR = Path(os.getenv("BRODY_DATA_DIR", str(BRODY_ROOT / "data")))
BRODY_CORPUS_DIR = Path(os.getenv("BRODY_CORPUS_DIR", str(BRODY_DATA_DIR / "linguistic_corpus")))
BRODY_LEXICON_PATH = Path(os.getenv("BRODY_LEXICON_PATH", str(BRODY_CORPUS_DIR / "lexicon.db")))
BRODY_CONFIG_DIR = Path(os.getenv("BRODY_CONFIG_DIR", str(BRODY_ROOT / "config")))


def check_corpus_available() -> bool:
    """Vérifie si la base lexicale est présente localement sans bloquer ni lever d'erreur."""
    try:
        return BRODY_LEXICON_PATH.is_file() and BRODY_LEXICON_PATH.stat().st_size > 1024 * 1024
    except (OSError, PermissionError):
        return False


def require_lexicon_path() -> Path:
    """Retourne le chemin du lexique ou lève une exception descriptive en cas d'absence."""
    if not check_corpus_available():
        raise CorpusNotFoundError(
            f"Base lexicale introuvable à l'emplacement : {BRODY_LEXICON_PATH}\n"
            "Conformément au statut LEXICON_PUBLICATION_HOLD, la base SQLite n'est pas distribuée dans Git.\n"
            "Pour la générer localement de manière déterministe, exécutez :\n"
            "  python scripts/download_linguistic_corpora.py\n"
            "  python scripts/build_linguistic_corpus.py"
        )
    return BRODY_LEXICON_PATH
