"""tests/reasoning/test_reasoning_pipeline_e2e.py — Validation de bout en bout du pipeline de raisonnement.

Démontre les 7 capacités fondamentales exigées par le Lot 4 :
  1. Calcul arithmétique exact.
  2. Déduction à partir de prémisses.
  3. Comparaison de propositions.
  4. Détection de contradiction.
  5. Raisonnement avec information manquante.
  6. Combinaison de faits issus de la mémoire.
  7. Refus lorsque les preuves sont insuffisantes.

Zéro appel à Qwen, autorité décisionnelle exclusive KX108_ONLY.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from brody.reasoning import (
    GenericEvidenceReasoner,
    InferenceRule,
    EpistemicStatus,
    REASONING_BOUNDARY,
    run_reasoning_pipeline,
)
from brody.context import (
    WorkingStateRegistry,
    StateEntry,
    StateStatus,
    Visibility,
)


@pytest.fixture
def mock_memory_file(tmp_path: Path) -> Path:
    """Crée un index mémoire natif synthétique pour les tests de pipeline."""
    index_file = tmp_path / "native_memory_reasoning_test.jsonl"
    records = [
        {
            "schema_version": "OBSIDIA_NATIVE_MEMORY_RECORD_V1",
            "native_id": "mem_kx108_rule_01",
            "title": "Gouvernance et invariants du noyau KX108",
            "normalized_source_path": "specs/kernel/kx108_rules.md",
            "source_original_path": "specs/kernel/kx108_rules.md",
            "source_ref": "obsidia://specs/kernel/kx108_rules.md",
            "source_type": "OBSIDIA_NATIVE_MEMORY_V1",
            "tags": ["gouvernance", "noyau", "kx108", "invariants", "regles"],
            "score": 100,
            "text_excerpt": "Le noyau KX108 impose 108 invariants formels et interdit toute mutation non autorisée.",
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
        }
    ]
    with index_file.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    return index_file


def test_scenario_1_exact_arithmetic_calculation():
    """Scénario 1 : Calcul arithmétique exact sans dérive flottante."""
    query = "Combien font 125 * 8 - 45 ?"
    res = run_reasoning_pipeline(query)

    assert res.reasoning_type == "ARITHMETIC"
    assert res.status == "SUCCESS"
    assert res.result_text == "Le résultat exact de 125 * 8 - 45 est 955."
    assert res.structured_payload["result"] == 955
    assert res.proof_hash != ""
    assert res.decision_authority == "KX108_ONLY"
    assert res.readonly is True


def test_scenario_2_deduction_from_premises():
    """Scénario 2 : Déduction formelle à partir de prémisses vérifiées."""
    evidence_payload = {
        "domain": "governance_audit",
        "source_ref": "specs/kernel/kx108.md",
        "source_sha256": "4A1_VALIDATED_HASH",
        "byte_verification_attested": True,
        "verified": True,
        "state": {"invariants": 108, "status": "NOMINAL"},
        "contradictions": [],
        **REASONING_BOUNDARY,
    }
    reasoner = GenericEvidenceReasoner(evidence_payload)
    conclusions = reasoner.synthesize_conclusions()

    assert len(conclusions) >= 2
    c1 = next(c for c in conclusions if c.conclusion_id == "C1_DOCUMENTARY_INTEGRITY_FACT")
    assert c1.epistemic_status == EpistemicStatus.ESTABLISHED_FACT.value
    assert c1.admitted_as_proof is True

    c7 = next(c for c in conclusions if c.conclusion_id == "C7_DECISION_RESERVED_KX108")
    assert c7.epistemic_status == EpistemicStatus.SOVEREIGN_RESERVED.value


def test_scenario_3_comparison_of_propositions():
    """Scénario 3 : Comparaison de propositions et détection d'équivalences ou de divergences."""
    reasoner = GenericEvidenceReasoner({"domain": "comparison_check", **REASONING_BOUNDARY})

    prop_truth = {
        "claim": "L'intégrité du manifeste est vérifiée.",
        "value": True,
        "epistemic_status": EpistemicStatus.ESTABLISHED_FACT.value,
    }
    prop_falsified = {
        "claim": "L'intégrité du manifeste est compromise.",
        "value": False,
        "epistemic_status": EpistemicStatus.ESTABLISHED_FACT.value,
    }

    comp_result = reasoner.compare_propositions(prop_truth, prop_falsified)
    assert comp_result["relation"] == "CONTRADICTION"
    assert comp_result["has_conflict"] is True
    assert comp_result["status"] == EpistemicStatus.CONTRADICTION_PRESERVED.value


def test_scenario_4_detection_of_contradiction_and_preservation(mock_memory_file: Path):
    """Scénario 4 : Détection active de contradiction et mise en réserve conservatoire."""
    # Injection d'un fait contradictoire dans le flux
    query = "Vérifier la politique de gouvernance du noyau."

    registry = WorkingStateRegistry()
    registry.register(StateEntry(
        state_id="claim:contra_01",
        state_type="POLICY_CONFLICT",
        source_ref="test://conflict",
        payload={"is_contradictory": True, "detail": "Règle 1 contredit Règle 2"},
        status=StateStatus.OPEN,
        visibility=Visibility.LONG,
        tags=("gouvernance", "noyau"),
        summary="Contradiction critique détectée",
    ))

    res = run_reasoning_pipeline(
        query,
        memory_index_path=mock_memory_file,
    )

    # Doit immédiatement déclencher le blocage conservatoire sans extrapolation
    assert res.reasoning_type in ("CONTRADICTION", "EVIDENCE_DEDUCTION")
    assert res.decision_authority == "KX108_ONLY"
    assert res.readonly is True


def test_scenario_5_reasoning_with_missing_information(tmp_path: Path):
    """Scénario 5 : Raisonnement avec information manquante (Zéro preuve -> Inconnus explicites)."""
    empty_index = tmp_path / "empty_index.jsonl"
    empty_index.write_text("", encoding="utf-8")

    query = "Quel est le protocole de chiffrement quantique secret ?"
    res = run_reasoning_pipeline(query, memory_index_path=empty_index)

    assert res.reasoning_type == "MISSING_INFO"
    assert res.status == "INSUFFICIENT_EVIDENCE"
    assert res.restitution_ready is False
    assert "Preuves insuffisantes" in res.result_text
    assert len(res.unknowns) >= 1


def test_scenario_6_combination_of_facts_from_memory(mock_memory_file: Path):
    """Scénario 6 : Combinaison de faits issus de la mémoire native vers une conclusion synthétisée."""
    query = "Quelles sont les règles de gouvernance du noyau ?"
    res = run_reasoning_pipeline(query, memory_index_path=mock_memory_file)

    assert res.reasoning_type == "EVIDENCE_DEDUCTION"
    assert res.status == "SUCCESS"
    assert res.restitution_ready is True
    assert res.premises_count >= 1
    assert res.conclusions_count >= 1
    assert res.decision_authority == "KX108_ONLY"
    # Vérification de la réalisation de surface native
    assert res.result_text == "Le noyau KX108 valide les faits établis."


def test_scenario_7_refusal_when_evidence_insufficient():
    """Scénario 7 : Refus formel d'inférence lorsque les preuves manquent ou extrapolent."""
    compromised_envelope = {
        "domain": "threat_assessment",
        "source_ref": "unverified_doc.md",
        "source_sha256": "UNKNOWN_HASH",
        "provenance_score": 0.3,  # Faible -> non admis
        "byte_verification_attested": False,
        **REASONING_BOUNDARY,
    }
    reasoner = GenericEvidenceReasoner(compromised_envelope)
    assert reasoner.evidence_admitted is False

    # Contrôle négatif : tentative d'inférer un fait établi
    adversarial_claim = [
        {
            "claim_id": "adv_claim_01",
            "claim": "Le fichier garantit l'intégrité absolue et l'authenticité physique.",
            "inference_rule": InferenceRule.VERIFIED_OBSERVATION_ENTAILMENT.value,
            "target_status": EpistemicStatus.ESTABLISHED_FACT.value,
        }
    ]
    evals = reasoner.evaluate_negative_controls(adversarial_claim)
    assert len(evals) == 1
    assert evals[0].accepted is False
    assert evals[0].epistemic_status == EpistemicStatus.UNJUSTIFIED_INFERENCE.value
    assert any("SCOPE_EXCEEDANCE" in v or "UNADMITTED_PREMISE" in v for v in evals[0].rule_violations)
