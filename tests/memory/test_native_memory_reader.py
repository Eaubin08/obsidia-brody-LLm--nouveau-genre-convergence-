"""tests/memory/test_native_memory_reader.py — Tests unitaires du lecteur de mémoire native.

Vérifie la conformité de lecture, le filtrage déterministe, le score lexical
et le respect absolu de la frontière 4A1 (lecture seule, autorité KX108_ONLY).
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from brody.memory.native_reader import (
    NATIVE_MEMORY_BOUNDARY,
    _validate_record,
    build_native_memory_retrieval_snapshot,
    load_native_memory_index,
    query_native_memory,
)


@pytest.fixture
def sample_records(tmp_path: Path) -> Path:
    """Crée un index mémoire natif synthétique pour les tests unitaires isolés."""
    index_file = tmp_path / "test_native_memory.jsonl"
    records = [
        {
            "schema_version": "OBSIDIA_NATIVE_MEMORY_RECORD_V1",
            "native_id": "rec_001",
            "title": "Kernel Governance and X108 Invariant",
            "normalized_source_path": "docs/kernel/x108.md",
            "source_original_path": "docs/kernel/x108.md",
            "source_ref": "obsidia://kernel/x108",
            "source_type": "OBSIDIA_NATIVE_MEMORY_V1",
            "tags": ["kernel", "x108", "governance"],
            "score": 100,
            "text_excerpt": "Le noyau KX108 est la seule autorité décisionnelle souveraine.",
            "readonly": True,
            "memory_authority": False,
            "memory_decision": False,
            "memory_write": False,
            "canonical_write": False,
            "auto_promotion": False,
            "kernel_mutation": False,
            "x108_mutation": False,
            "emits_act": False,
            "emits_verdict": False,
            "allowed_to_decide": False,
            "allowed_to_act": False,
            "decision_authority": "KX108_ONLY",
        },
        {
            "schema_version": "OBSIDIA_NATIVE_MEMORY_RECORD_V1",
            "native_id": "rec_002",
            "title": "Hexaflux Pipeline and State Continuum",
            "normalized_source_path": "docs/continuum/hexaflux.md",
            "source_original_path": "docs/continuum/hexaflux.md",
            "source_ref": "obsidia://continuum/hexaflux",
            "source_type": "OBSIDIA_NATIVE_MEMORY_V1",
            "tags": ["continuum", "hexaflux", "timeline"],
            "score": 85,
            "text_excerpt": "L'architecture Hexaflux garantit la traçabilité temporelle des états.",
            "readonly": True,
            "memory_authority": False,
            "memory_decision": False,
            "memory_write": False,
            "canonical_write": False,
            "auto_promotion": False,
            "kernel_mutation": False,
            "x108_mutation": False,
            "emits_act": False,
            "emits_verdict": False,
            "allowed_to_decide": False,
            "allowed_to_act": False,
            "decision_authority": "KX108_ONLY",
        },
        {
            "schema_version": "OBSIDIA_NATIVE_MEMORY_RECORD_V1",
            "native_id": "rec_003",
            "title": "Agentic Boundary and Readonly Policy",
            "normalized_source_path": "docs/security/boundary.md",
            "source_original_path": "docs/security/boundary.md",
            "source_ref": "obsidia://security/boundary",
            "source_type": "OBSIDIA_NATIVE_MEMORY_V1",
            "tags": ["agent", "security", "readonly"],
            "score": 70,
            "text_excerpt": "Les agents périphériques ne possèdent aucun droit d'écriture automatique.",
            "readonly": True,
            "memory_authority": False,
            "memory_decision": False,
            "memory_write": False,
            "canonical_write": False,
            "auto_promotion": False,
            "kernel_mutation": False,
            "x108_mutation": False,
            "emits_act": False,
            "emits_verdict": False,
            "allowed_to_decide": False,
            "allowed_to_act": False,
            "decision_authority": "KX108_ONLY",
        },
    ]
    with index_file.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    return index_file


def test_boundary_constants():
    """Valide les constantes de la clôture de gouvernance 4A1."""
    assert NATIVE_MEMORY_BOUNDARY["readonly"] is True
    assert NATIVE_MEMORY_BOUNDARY["memory_write"] is False
    assert NATIVE_MEMORY_BOUNDARY["canonical_write"] is False
    assert NATIVE_MEMORY_BOUNDARY["allowed_to_decide"] is False
    assert NATIVE_MEMORY_BOUNDARY["decision_authority"] == "KX108_ONLY"


def test_load_native_memory_index(sample_records: Path):
    """Valide le chargement d'un index mémoire conforme."""
    records = load_native_memory_index(sample_records)
    assert len(records) == 3
    assert records[0]["native_id"] == "rec_001"
    assert records[1]["native_id"] == "rec_002"
    assert records[2]["native_id"] == "rec_003"


def test_query_native_memory(sample_records: Path):
    """Valide la recherche par mot-clé et le classement par pertinence."""
    records = load_native_memory_index(sample_records)
    results = query_native_memory("x108 kernel", records, limit=2)
    assert len(results) >= 1
    assert results[0]["id"] == "rec_001"
    assert "x108" in results[0]["tags"]


def test_build_retrieval_snapshot(sample_records: Path):
    """Valide la construction d'un snapshot de restitution conforme."""
    snapshot = build_native_memory_retrieval_snapshot(
        "continuum hexaflux",
        memory_required=True,
        limit=5,
        index_path=sample_records,
    )
    assert snapshot["schema_version"] == "OBSIDIA_NATIVE_MEMORY_RETRIEVAL_V1"
    assert snapshot["status"] == "MEMORY_USABLE"
    assert snapshot["memory_required"] is True
    assert snapshot["selected_items_count"] >= 1
    assert snapshot["selected_items"][0]["id"] == "rec_002"
    assert snapshot["decision_authority"] == "KX108_ONLY"
    assert snapshot["memory_write"] is False


def test_fail_closed_on_authority_violation():
    """Valide le rejet immédiat de tout enregistrement n'ayant pas KX108_ONLY."""
    bad_record = {
        "schema_version": "OBSIDIA_NATIVE_MEMORY_RECORD_V1",
        "id": "rec_bad",
        "readonly": True,
        "memory_write": False,
        "decision_authority": "BRODY_LOCAL",  # Interdit
    }
    with pytest.raises(ValueError) as exc:
        _validate_record(bad_record, ordinal=1)
    assert "NATIVE_MEMORY_AUTHORITY_VIOLATION" in str(exc.value)


def test_fail_closed_on_write_flag():
    """Valide le rejet immédiat de tout enregistrement autorisant l'écriture."""
    bad_record = {
        "schema_version": "OBSIDIA_NATIVE_MEMORY_RECORD_V1",
        "id": "rec_bad",
        "readonly": True,
        "memory_write": True,  # Interdit (clôture 4A1)
        "decision_authority": "KX108_ONLY",
    }
    with pytest.raises(ValueError) as exc:
        _validate_record(bad_record, ordinal=1)
    assert "NATIVE_MEMORY_WRITE_NOT_FALSE" in str(exc.value)
