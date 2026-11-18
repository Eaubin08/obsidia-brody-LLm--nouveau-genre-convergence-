"""brody/composition/editorial_cleanup.py — Nettoyage conservateur d'affichage de brouillon éditorial.

Supprime les bavardages périphériques et normalise les retours à la ligne
sans jamais altérer ni réécrire les faits ou le contenu rédigé par l'utilisateur.
"""
from __future__ import annotations

import re

_INTRO = re.compile(
    r"^(?:voici|je vous propose|je te propose)\s+(?:une\s+)?"
    r"(?:courte\s+)?(?:publication|proposition|version|texte|post)\b[^\n:]{0,200}:\s*",
    re.I,
)
_OUTRO = re.compile(
    r"\s+(?:cette publication|ce post|ce texte)\s+"
    r"(?:respecte|couvre|est adapté|est concis|est une proposition)\b.*$",
    re.I | re.S,
)


def clean_editorial_draft(text: str) -> str:
    """Nettoie l'affichage d'un brouillon éditorial sans inventer ni reformuler."""
    if not isinstance(text, str):
        raise TypeError("draft must be a string")
    clean = text.strip()
    # Remplacement des sauts de ligne littéraux échappés
    clean = clean.replace("\\r\\n", "\\n").replace("\\n", "\n")
    clean = clean.strip()
    intro = _INTRO.match(clean)
    if intro:
        body = clean[intro.end():].strip()
        if body.startswith(('"', "«")):
            closer = '"' if body[0] == '"' else "»"
            end = body.rfind(closer)
            if end > 0 and (end == len(body) - 1 or _OUTRO.fullmatch(body[end + 1:])):
                clean = body[1:end].strip()
            else:
                clean = body
        else:
            clean = body
            clean = _OUTRO.sub("", clean).strip()
    clean = re.sub(
        r"\s+N[’']invente aucun fait ou chiffre\.?\s*$",
        "", clean, flags=re.I,
    ).strip()
    if len(clean) >= 2 and (
        (clean.startswith('"') and clean.endswith('"'))
        or (clean.startswith("«") and clean.endswith("»"))
    ):
        clean = clean[1:-1].strip()
    return clean.strip()
