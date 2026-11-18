"""brody/composition/editorial_intent.py — Construction délimitée d'une demande éditoriale.

Formule une requête éditoriale explicative bornée sans introduire de boilerplate
lexical parasite dans le routeur sémantique.
"""
from __future__ import annotations


def explanatory_editorial_request(subject: str, network: str = "LinkedIn", source_text: str = "") -> str:
    """Construit une requête éditoriale explicative délimitée."""
    subj = str(subject or "").strip()
    if not subj:
        raise ValueError("Sujet éditorial requis")
    if subj.casefold().startswith(("rédige ", "redige ", "écris ", "ecris ")):
        prompt = subj
    else:
        prompt = f"Rédige une publication {network} expliquant " + subj
    if source_text and str(source_text).strip():
        prompt += "\n\nContexte fourni :\n" + str(source_text).strip()[:6000]
    return prompt
