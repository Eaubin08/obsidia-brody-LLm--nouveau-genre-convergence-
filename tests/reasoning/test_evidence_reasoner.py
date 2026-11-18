"""tests/reasoning/test_evidence_reasoner.py — Tests unitaires du moteur d'inférence déductive.

Vérifie la déduction rigoureuse à partir de prémisses, le contrôle négatif d'extrapolations,
la comparaison de propositions, la détection de contradiction et le refus pour preuves insuffisantes.
"""
from __future__ import annotations

import pytest

from brody.reasoning.contracts import (
    EpistemicStatus,
    InferenceRule,
    REASONING_BOUNDARY,
)
from brody.reasoning.evidence_reasoner import (
    GenericEvidenceReasoner,
    TYPED_INFERENCE_RULES,
)


@pytest.fixture
def sample_verified_evidence():
    return {
        "domain": "governance_spec",
        "source_ref": "specs/kernel/kx108.md",
        "source_sha256": "E4D3B2A10987654321FEDCBA0987654321FEDCBA0987654321FEDCBA09876543",
        "byte_verification_attested": True,
        "verified": True,
        "state": {
            "kernel_version": "0.9.3",
            "invariants_checked": 108,
            "status": "NOMINAL",
        },
        "audit_checks": 12,
        "audit_failures": 0,
        "controlled_replication_proven": True,
        "observed_at": "2026-11-18T22:00:00Z",
        "contradictions": [],
        **REASONING_BOUNDARY,
    }


def test_deduction_from_verified_premises(sample_verified_evidence):
    """Valide la déduction de conclusions conformes à partir de prémisses vérifiées."""
    reasoner = GenericEvidenceReasoner(sample_verified_evidence)
    premises = reasoner.extract_premises()
    assert len(premises) == 8

    p1 = next(p for p in premises if p.premise_id == "P1_MANIFEST_INTEGRITY")
    assert p1.verification_status == "VERIFIED"
    assert p1.admitted_as_proof is True

    conclusions = reasoner.synthesize_conclusions()
    assert len(conclusions) >= 3

    # C1 : Intégrité documentaire établie
    c1 = next(c for c in conclusions if c.conclusion_id == "C1_DOCUMENTARY_INTEGRITY_FACT")
    assert c1.epistemic_status == EpistemicStatus.ESTABLISHED_FACT.value
    assert c1.admitted_as_proof is True
    assert "specs/kernel/kx108.md" in c1.claim

    # C7 : Séparation juridictionnelle souveraine
    c7 = next(c for c in conclusions if c.conclusion_id == "C7_DECISION_RESERVED_KX108")
    assert c7.epistemic_status == EpistemicStatus.SOVEREIGN_RESERVED.value


def test_rejection_of_scope_exceedance_negative_control(sample_verified_evidence):
    """Valide le rejet formel de toute affirmation prétendant à un périmètre prohibé."""
    reasoner = GenericEvidenceReasoner(sample_verified_evidence)

    adversarial_claims = [
        {
            "claim_id": "adv_01",
            "claim": "Le fichier prouve l'authenticité physique et la présence en direct de la source.",
            "inference_rule": InferenceRule.VERIFIED_OBSERVATION_ENTAILMENT.value,
            "target_status": EpistemicStatus.ESTABLISHED_FACT.value,
        },
        {
            "claim_id": "adv_02",
            "claim": "L'audit établit le déterminisme absolu du système.",
            "inference_rule": InferenceRule.DETERMINISTIC_REPRODUCIBILITY_ENTAILMENT.value,
            "target_status": EpistemicStatus.ESTABLISHED_FACT.value,
        },
    ]

    evaluations = reasoner.evaluate_negative_controls(adversarial_claims)
    assert len(evaluations) == 2

    # adv_01 doit être formellement rejeté pour tentative d'authenticité physique
    assert evaluations[0].accepted is False
    assert evaluations[0].epistemic_status == EpistemicStatus.UNJUSTIFIED_INFERENCE.value
    assert any("SCOPE_EXCEEDANCE" in v for v in evaluations[0].rule_violations)

    # adv_02 doit être rejeté pour prétention à un déterminisme absolu
    assert evaluations[1].accepted is False
    assert any("SCOPE_EXCEEDANCE" in v for v in evaluations[1].rule_violations)


def test_refusal_when_evidence_is_unadmitted_or_unverified():
    """Valide le refus strict lorsque la provenance est compromise ou non vérifiée."""
    compromised_data = {
        "domain": "untrusted_domain",
        "source_ref": "docs/unverified.md",
        "source_sha256": "BAD_HASH",
        "provenance_score": 0.2,  # Score insuffisant -> PROVENANCE_WEAK
        "fake_provenance_detected": True,
        **REASONING_BOUNDARY,
    }

    reasoner = GenericEvidenceReasoner(compromised_data)
    assert reasoner.evidence_admitted is False

    conclusions = reasoner.synthesize_conclusions()
    c1 = next(c for c in conclusions if c.conclusion_id == "C1_DOCUMENTARY_INTEGRITY_FACT")
    assert c1.epistemic_status == EpistemicStatus.UNVERIFIED_INTEGRITY_COMPROMISED.value
    assert c1.admitted_as_proof is False


def test_contradiction_detection_and_dialectical_preservation():
    """Valide la détection et la préservation dialectique d'une contradiction."""
    contradictory_evidence = {
        "domain": "security_policy",
        "source_ref": "specs/policy.md",
        "source_sha256": "A1B2C3D4",
        "verified": True,
        "contradictions": ["RULE_A_CONTRADICTS_RULE_B"],
        **REASONING_BOUNDARY,
    }

    reasoner = GenericEvidenceReasoner(contradictory_evidence)
    conclusions = reasoner.synthesize_conclusions()

    c6 = next(c for c in conclusions if c.conclusion_id == "C6_CONTRADICTIONS_PRESERVED")
    assert c6.epistemic_status == EpistemicStatus.CONTRADICTION_PRESERVED.value
    assert "1 détectées" in c6.claim


def test_comparison_of_propositions():
    """Valide la comparaison déterministe entre deux propositions."""
    reasoner = GenericEvidenceReasoner({"domain": "comparison_test", **REASONING_BOUNDARY})

    prop_a = {"claim": "Le noyau est stable.", "value": "STABLE", "epistemic_status": EpistemicStatus.ESTABLISHED_FACT.value}
    prop_b = {"claim": "Le noyau est instable.", "value": "UNSTABLE", "epistemic_status": EpistemicStatus.ESTABLISHED_FACT.value}
    prop_c = {"claim": "Le noyau est stable.", "value": "STABLE", "epistemic_status": EpistemicStatus.ESTABLISHED_FACT.value}

    # Comparaison contradictoire
    res_conflict = reasoner.compare_propositions(prop_a, prop_b)
    assert res_conflict["relation"] == "CONTRADICTION"
    assert res_conflict["has_conflict"] is True
    assert res_conflict["status"] == EpistemicStatus.CONTRADICTION_PRESERVED.value

    # Comparaison équivalente
    res_equiv = reasoner.compare_propositions(prop_a, prop_c)
    assert res_equiv["relation"] == "EQUIVALENCE"
    assert res_equiv["has_conflict"] is False
    assert res_equiv["status"] == EpistemicStatus.ESTABLISHED_FACT.value


def test_fail_closed_on_authority_boundary_violation():
    """Valide le rejet immédiat si une enveloppe tente de s'arroger des droits décisionnels."""
    illegal_envelope = {
        "domain": "rogue_domain",
        "allowed_to_decide": True,  # Violation formelle
        "decision_authority": "BRODY_LOCAL",
    }
    with pytest.raises(ValueError) as exc:
        GenericEvidenceReasoner(illegal_envelope)
    assert "SOVEREIGN_BOUNDARY_VIOLATION" in str(exc.value) or "AUTHORITY_VIOLATION" in str(exc.value)
