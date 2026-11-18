"""brody/core/exceptions.py — Hiérarchie formelle des exceptions Brody."""
from __future__ import annotations


class BrodyError(Exception):
    """Exception de base pour toutes les erreurs du domaine Brody."""
    pass


class CorpusNotFoundError(BrodyError, FileNotFoundError):
    """Levée lorsque la base lexicale requise est introuvable."""
    pass


class GovernanceViolationError(BrodyError):
    """Levée en cas de tentative d'outrepassement d'autorité ou d'écriture non autorisée."""
    pass


class InvariantViolationError(BrodyError):
    """Levée lors de la violation d'un invariant formel de sécurité ou de logique."""
    pass
