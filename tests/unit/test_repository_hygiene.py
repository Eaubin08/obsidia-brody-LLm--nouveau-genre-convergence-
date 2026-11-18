"""tests/unit/test_repository_hygiene.py — Contrôles de salubrité et sécurité pré-push."""
import ast
import os
import re
from pathlib import Path

from brody.core.paths import BRODY_ROOT

# Motifs de détection de secrets
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}", re.IGNORECASE),
    re.compile(r"AIza[0-9A-Za-z-_]{35}", re.IGNORECASE),
    re.compile(r"-----BEGIN (RSA|EC|DSA|OPENSSH|PRIVATE) KEY-----"),
    re.compile(r"ghp_[A-Za-z0-9]{36}"),
]

# Extensions de fichiers interdites dans Git
FORBIDDEN_EXTENSIONS = {".env", ".key", ".pem", ".p12", ".sqlite", ".sqlite3", ".db-wal", ".db-journal"}


def test_no_forbidden_files_staged():
    """Vérifie qu'aucun fichier sensible ou interdit n'est présent dans le dépôt."""
    for root, dirs, files in os.walk(BRODY_ROOT):
        # Ignorer .git et caches pytest
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", ".pytest_cache"}]
        for f in files:
            p = Path(root) / f
            assert p.suffix.lower() not in FORBIDDEN_EXTENSIONS, f"Fichier interdit détecté : {p}"
            # Bloquer les fichiers .db à l'exception éventuelle d'un mock explicite < 1Mo dans fixtures
            if p.suffix.lower() == ".db":
                pytest.fail(f"Base de données .db détectée dans le dépôt : {p}")


def test_file_size_limits():
    """Vérifie qu'aucun fichier ne dépasse la limite préventive de 10 Mo."""
    MAX_BYTES = 10 * 1024 * 1024  # 10 Mo
    for root, dirs, files in os.walk(BRODY_ROOT):
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", ".pytest_cache"}]
        for f in files:
            p = Path(root) / f
            size = p.stat().st_size
            assert size < MAX_BYTES, f"Fichier trop lourd détecté ({size / 1024 / 1024:.2f} Mo) : {p}"


def test_no_hardcoded_user_paths_in_code():
    """Vérifie l'absence de chaînes codées en dur avec le chemin utilisateur du développeur."""
    FORBIDDEN_PATH_PATTERN = re.compile(r"C:[\\/]Users[\\/]Aubin", re.IGNORECASE)
    
    text_extensions = {".py", ".toml", ".txt", ".json", ".md", ".yml", ".yaml"}
    for root, dirs, files in os.walk(BRODY_ROOT):
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", ".pytest_cache"}]
        for f in files:
            p = Path(root) / f
            if p.suffix.lower() in text_extensions and p.name != "README.md":
                content = p.read_text(encoding="utf-8", errors="ignore")
                match = FORBIDDEN_PATH_PATTERN.search(content)
                assert match is None, f"Chemin utilisateur en dur détecté dans {p} : {match.group(0)}"


def test_python_syntax_validity():
    """Vérifie que tous les fichiers Python ont une syntaxe valide (ast.parse)."""
    for root, dirs, files in os.walk(BRODY_ROOT):
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", ".pytest_cache"}]
        for f in files:
            p = Path(root) / f
            if p.suffix.lower() == ".py":
                content = p.read_text(encoding="utf-8", errors="ignore")
                try:
                    ast.parse(content, filename=str(p))
                except SyntaxError as e:
                    pytest.fail(f"Erreur de syntaxe Python dans {p}: {e}")
