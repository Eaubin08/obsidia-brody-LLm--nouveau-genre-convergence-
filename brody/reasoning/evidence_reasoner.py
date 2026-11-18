"""brody/reasoning/evidence_reasoner.py — Moteur d'inférence épistémique déductif générique.

Version décorrélée et autonome de GenericEvidenceReasonerV2, capable de raisonner
sur des preuves issues de n'importe quel domaine, de la mémoire native ou du contexte B6.
Garantit la non-extrapolation, la préservation des contradictions et la séparation de souveraineté.
"""
from __future__ import annotations

import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple

from brody.reasoning.contracts import (
    ActionCandidate,
    EpistemicStatus,
    EvidenceConclusion,
    EvidencePremise,
    EvidenceRelation,
    InferenceRule,
    NegativeControlEvaluation,
    PeripheralSignalPacket,
    REASONING_BOUNDARY,
    TypedInferenceRule,
    run_provenance_gate,
)

# ---------------------------------------------------------------------------
# Règles d'inférence typées canoniques d'Obsidia (F4H / Contrat B)
# ---------------------------------------------------------------------------
TYPED_INFERENCE_RULES: Dict[InferenceRule, TypedInferenceRule] = {
    InferenceRule.VERIFIED_OBSERVATION_ENTAILMENT: TypedInferenceRule(
        rule_id=InferenceRule.VERIFIED_OBSERVATION_ENTAILMENT,
        name="Verified Observation Entailment",
        required_premise_ids=("P1_MANIFEST_INTEGRITY", "P4_DECODED_STATE_MEASUREMENTS"),
        allowed_epistemic_statuses=(
            EpistemicStatus.ESTABLISHED_FACT.value,
            EpistemicStatus.OPEN_HYPOTHESIS_UNPROVEN.value,
            EpistemicStatus.UNVERIFIED_INTEGRITY_COMPROMISED.value,
        ),
        established_scope="Intégrité documentaire du fichier enregistré et décodage de ses mesures payload.",
        prohibited_scopes=(
            "authenticité physique", "physical authenticity",
            "source en direct", "live emitter", "présence réelle",
            "batterie", "battery", "décollage", "clairance de vol", "météo", "weather",
            "certification", "homologation", "causalité", "cause", "sabotage", "spoofing",
        ),
        permitted_claim_keywords=(
            "intégrité", "integrity", "manifeste", "manifest", "hash", "sha256", "empreinte",
            "documentaire", "documentary", "fichier", "file", "mesures", "mesure", "décodage", "octets"
        ),
    ),
    InferenceRule.BOUNDED_REPRODUCIBILITY_ENTAILMENT: TypedInferenceRule(
        rule_id=InferenceRule.BOUNDED_REPRODUCIBILITY_ENTAILMENT,
        name="Bounded Reproducibility Limitation",
        required_premise_ids=("P2_INDEPENDENT_AUDIT_DETERMINISM",),
        allowed_epistemic_statuses=(
            EpistemicStatus.REPRODUCIBLE_OBSERVATION.value,
            EpistemicStatus.OPEN_HYPOTHESIS_UNPROVEN.value,
            EpistemicStatus.UNJUSTIFIED_INFERENCE.value,
        ),
        established_scope="Mesures d'écart empirique et bornage de la reproductibilité sous rejeu d'audit.",
        prohibited_scopes=(
            "déterminisme algorithmique", "déterminisme absolu", "authenticité physique"
        ),
        permitted_claim_keywords=(
            "reproductibilité", "reproducibility", "écart", "delta", "audit", "rejeu"
        ),
    ),
    InferenceRule.DETERMINISTIC_REPRODUCIBILITY_ENTAILMENT: TypedInferenceRule(
        rule_id=InferenceRule.DETERMINISTIC_REPRODUCIBILITY_ENTAILMENT,
        name="Bounded Empirical Reproducibility Entailment",
        required_premise_ids=("P2_INDEPENDENT_AUDIT_DETERMINISM",),
        allowed_epistemic_statuses=(
            EpistemicStatus.REPRODUCIBLE_OBSERVATION.value,
            EpistemicStatus.OPEN_HYPOTHESIS_UNPROVEN.value,
            EpistemicStatus.UNJUSTIFIED_INFERENCE.value,
        ),
        established_scope="Écarts spatiaux et métriques de variance mesurées lors des rejeux d'audit.",
        prohibited_scopes=(
            "authenticité physique", "physical authenticity",
            "déterminisme absolu", "déterminisme algorithmique",
            "seuil choisi a posteriori", "décision", "action",
        ),
        permitted_claim_keywords=(
            "audit", "reproductibilité", "reproducibility", "écart", "delta", "distance",
            "métrique", "metric", "rejeu", "replay", "contrôle"
        ),
    ),
    InferenceRule.NEGATIVE_PREMISE_NON_ENTAILMENT: TypedInferenceRule(
        rule_id=InferenceRule.NEGATIVE_PREMISE_NON_ENTAILMENT,
        name="Historical Capture Temporal Limitation",
        required_premise_ids=("P3_HISTORICAL_CAPTURE_RECORD",),
        allowed_epistemic_statuses=(
            EpistemicStatus.OPEN_HYPOTHESIS_UNPROVEN.value,
        ),
        established_scope="Métadonnées d'enregistrement temporel et qualification en signal historique enregistré.",
        prohibited_scopes=(
            "preuve de l'absence", "proof of absence", "signal en direct",
            "authenticité temps réel", "présence physique actuelle",
        ),
        permitted_claim_keywords=(
            "capture", "enregistrement", "recorded", "historique", "historical",
            "horodatage", "timestamp", "métadonnée", "metadata", "signal"
        ),
    ),
    InferenceRule.CAUSAL_CORRELATION_SEPARATION: TypedInferenceRule(
        rule_id=InferenceRule.CAUSAL_CORRELATION_SEPARATION,
        name="Epistemic Disjunction of Correlation and Causation",
        required_premise_ids=("P4_DECODED_STATE_MEASUREMENTS", "P5_CAUSAL_STATUS_UNKNOWN"),
        allowed_epistemic_statuses=(
            EpistemicStatus.OPEN_HYPOTHESIS_UNPROVEN.value,
        ),
        established_scope="Corrélation observationnelle sans attribution causale interventionnelle.",
        prohibited_scopes=(
            "prouve la cause", "lien de causalité", "est causé par", "imputation causale",
            "mécanisme causal prouvé",
        ),
        permitted_claim_keywords=(
            "cause", "causal", "causality", "corrélation", "correlation", "non démontrée", "inconnue"
        ),
    ),
    InferenceRule.SECURITY_CLAIM_VALIDATION_BOUNDARY: TypedInferenceRule(
        rule_id=InferenceRule.SECURITY_CLAIM_VALIDATION_BOUNDARY,
        name="Security and Adversarial Testing Boundary Enforcement",
        required_premise_ids=("P6_ADVERSARIAL_RESISTANCE_STATUS",),
        allowed_epistemic_statuses=(
            EpistemicStatus.OPEN_HYPOTHESIS_UNPROVEN.value,
        ),
        established_scope="Couverture des suites de tests adversariaux et qualification de résistance non démontrée.",
        prohibited_scopes=(
            "immunité prouvée", "invulnérable", "résistance garantie au leurre",
            "absence d'attaque démontrée", "spoofing impossible",
        ),
        permitted_claim_keywords=(
            "sécurité", "security", "adversarial", "leurre", "spoofing", "robustesse", "robustness", "menace", "threat"
        ),
    ),
    InferenceRule.CONTRADICTION_PRESERVATION: TypedInferenceRule(
        rule_id=InferenceRule.CONTRADICTION_PRESERVATION,
        name="Dialectical Contradiction Preservation Hold",
        required_premise_ids=("P7_ACTIVE_CONTRADICTIONS",),
        allowed_epistemic_statuses=(
            EpistemicStatus.CONTRADICTION_PRESERVED.value,
        ),
        established_scope="Préservation dialectique des contradictions observées sans résolution arbitraire.",
        prohibited_scopes=(
            "résolution sans preuve", "contradiction éliminée", "lissage",
        ),
        permitted_claim_keywords=(
            "contradiction", "divergence", "incohérence", "préservation", "fail-closed"
        ),
    ),
    InferenceRule.SOVEREIGN_AUTHORITY_SEPARATION: TypedInferenceRule(
        rule_id=InferenceRule.SOVEREIGN_AUTHORITY_SEPARATION,
        name="Jurisdictional Sovereignty Separation Lock",
        required_premise_ids=("P8_NON_SOVEREIGN_AUTHORITY_LOCK",),
        allowed_epistemic_statuses=(
            EpistemicStatus.SOVEREIGN_RESERVED.value,
        ),
        established_scope="Réservation juridictionnelle stricte de toute décision opérationnelle ou verdict à KX108.",
        prohibited_scopes=(
            "ordonne", "action immédiate", "manœuvre", "déclenche", "déploiement",
            "autorise le vol", "décision souveraine", "verdict",
        ),
        permitted_claim_keywords=(
            "autorité", "authority", "décision", "decision", "souverain", "sovereign", "kx108", "readonly"
        ),
    ),
}


class GenericEvidenceReasoner:
    """Moteur d'inférence épistémique autonome et déterministe."""

    def __init__(
        self,
        evidence_data: Dict[str, Any],
        trusted_verifier: Optional[Any] = None,
    ):
        self.trusted_verifier = trusted_verifier
        self.envelope = dict(evidence_data.get("sigma_envelope") or evidence_data)

        # Vérification stricte des invariants souverains
        for key in (
            "allowed_to_decide", "allowed_to_act", "emits_act",
            "emits_verdict", "memory_write", "kernel_mutation", "x108_mutation"
        ):
            if self.envelope.get(key) is not False and key in self.envelope:
                raise ValueError(f"SOVEREIGN_BOUNDARY_VIOLATION:{key}")

        if "decision_authority" in self.envelope and self.envelope.get("decision_authority") != "KX108_ONLY":
            raise ValueError("AUTHORITY_VIOLATION:decision_authority_must_be_KX108_ONLY")

        self.domain = str(self.envelope.get("domain", "generic_domain"))
        self.premises: List[EvidencePremise] = []
        self.relations: List[EvidenceRelation] = []
        self.conclusions: List[EvidenceConclusion] = []
        self._extracted = False

        # Admission consultative préalable
        prov_payload = dict(self.envelope.get("provenance_payload") or {})
        if "provenance_score" not in prov_payload:
            prov_payload["provenance_score"] = float(self.envelope.get("provenance_score", 1.0))
        if "fake_provenance_detected" not in prov_payload:
            prov_payload["fake_provenance_detected"] = bool(
                self.envelope.get("fake_provenance_detected", False)
                or self.envelope.get("provenance_untrusted", False)
            )
        if "mimetic_risk" not in prov_payload:
            prov_payload["mimetic_risk"] = float(self.envelope.get("mimetic_risk", 0.0))

        prov_action = ActionCandidate(
            action_id=f"prov_{uuid.uuid4().hex[:8]}",
            domain=self.domain,
            actor_id="generic_evidence_reasoner",
            intent="evidence_provenance_admission",
            action_type="ADMISSION_CHECK",
            irreversible=False,
            timestamp_plan="",
            payload=prov_payload,
        )
        self.provenance_packet: PeripheralSignalPacket = run_provenance_gate(prov_action)
        self.consultative_risk_admitted: bool = (
            self.provenance_packet.recommended_gate == "NONE"
            and "FAKE_PROVENANCE" not in self.provenance_packet.contradictions
            and "PROVENANCE_WEAK" not in self.provenance_packet.unknowns
        )
        self.evidence_admitted: bool = self.consultative_risk_admitted

    def extract_premises(self) -> List[EvidencePremise]:
        """Extrait les prémisses de l'enveloppe de manière normalisée et traçable."""
        if self._extracted:
            return self.premises

        env = self.envelope
        src_ref = str(env.get("source_ref", ""))
        src_hash = str(env.get("source_sha256", env.get("source_hash", "")))
        manifest_files = env.get("manifest_files", env.get("artifacts", []))

        # P1: Manifest / Intégrité cryptographique
        p1_verified = bool(env.get("byte_verification_attested", False)) or bool(
            src_ref and src_hash and env.get("verified", False)
        )
        p1_admitted = bool(self.consultative_risk_admitted and p1_verified)
        self.premises.append(EvidencePremise(
            premise_id="P1_MANIFEST_INTEGRITY",
            category="CRYPTOGRAPHIC_PROVENANCE",
            concept="manifest_file_binding",
            value={"source_ref": src_ref, "declared_hash": src_hash},
            source_ref=src_ref,
            source_hash=src_hash,
            verification_status="VERIFIED" if p1_verified else "UNVERIFIED",
            verification_method="RECEIPT_AND_SHA256_BINDING" if p1_verified else "UNATTESTED",
            admitted_as_proof=p1_admitted,
        ))

        # P2: Reproductibilité d'audit
        p2_verified = bool(env.get("audit_verified", True))
        self.premises.append(EvidencePremise(
            premise_id="P2_INDEPENDENT_AUDIT_DETERMINISM",
            category="EMPIRICAL_AUDIT",
            concept="independent_audit_comparison",
            value={
                "checks": env.get("audit_checks", 0),
                "failures": env.get("audit_failures", 0),
                "controlled_replication_proven": env.get("controlled_replication_proven", False),
            },
            source_ref="audit://independent",
            verification_status="VERIFIED" if p2_verified else "UNVERIFIED",
            admitted_as_proof=p2_verified and self.evidence_admitted,
        ))

        # P3: Enregistrement historique
        self.premises.append(EvidencePremise(
            premise_id="P3_HISTORICAL_CAPTURE_RECORD",
            category="TEMPORAL_GROUNDING",
            concept="historical_capture_record",
            value={"captured_at": env.get("observed_at", "")},
            source_ref=src_ref,
            verification_status="VERIFIED" if src_ref else "UNVERIFIED",
            admitted_as_proof=bool(src_ref and self.evidence_admitted),
        ))

        # P4: Mesures et télémétrie décodées
        telemetry = env.get("state") or env.get("telemetry") or env.get("payload") or {}
        self.premises.append(EvidencePremise(
            premise_id="P4_DECODED_STATE_MEASUREMENTS",
            category="EMPIRICAL_MEASUREMENTS",
            concept="decoded_state_measurements",
            value=telemetry,
            source_ref=src_ref,
            verification_status="VERIFIED" if telemetry else "UNVERIFIED",
            admitted_as_proof=bool(telemetry and self.evidence_admitted),
        ))

        # P5: Statut causal
        has_causality = bool(env.get("controlled_intervention_proven", False))
        self.premises.append(EvidencePremise(
            premise_id="P5_CAUSAL_STATUS_UNKNOWN",
            category="EPISTEMIC_BOUND",
            concept="causal_mechanism_status",
            value={"causality_proven": has_causality},
            source_ref="epistemic://causal_boundary",
            verification_status="VERIFIED",
            admitted_as_proof=True,
        ))

        # P6: Résistance adversariale
        has_sec = bool(env.get("adversarial_suite_passed", False))
        self.premises.append(EvidencePremise(
            premise_id="P6_ADVERSARIAL_RESISTANCE_STATUS",
            category="SECURITY_TESTING",
            concept="adversarial_test_coverage",
            value={"adversarial_tested": has_sec},
            source_ref="security://test_suite",
            verification_status="VERIFIED",
            admitted_as_proof=True,
        ))

        # P7: Contradictions actives
        contras = list(env.get("contradictions", []))
        self.premises.append(EvidencePremise(
            premise_id="P7_ACTIVE_CONTRADICTIONS",
            category="DIALECTICAL_STATE",
            concept="active_contradictions",
            value={"contradictions": contras, "count": len(contras)},
            source_ref="runtime://contradictions",
            verification_status="VERIFIED",
            admitted_as_proof=True,
        ))

        # P8: Verrou souverain non négociable
        self.premises.append(EvidencePremise(
            premise_id="P8_NON_SOVEREIGN_AUTHORITY_LOCK",
            category="JURISDICTIONAL_INVARIANT",
            concept="kx108_exclusive_sovereignty",
            value={"authority": "KX108_ONLY", "readonly": True},
            source_ref="kernel://x108",
            verification_status="VERIFIED",
            admitted_as_proof=True,
        ))

        self._extracted = True
        return self.premises

    def synthesize_conclusions(self) -> List[EvidenceConclusion]:
        """Déduit et synthétise les conclusions selon les règles d'inférence typées."""
        self.extract_premises()
        self.conclusions.clear()

        p_map = {p.premise_id: p for p in self.premises}
        p1 = p_map["P1_MANIFEST_INTEGRITY"]
        p4 = p_map["P4_DECODED_STATE_MEASUREMENTS"]
        p7 = p_map["P7_ACTIVE_CONTRADICTIONS"]

        # C1 : Intégrité documentaire
        rule_c1 = TYPED_INFERENCE_RULES[InferenceRule.VERIFIED_OBSERVATION_ENTAILMENT]
        if not self.evidence_admitted:
            c1_status = EpistemicStatus.UNVERIFIED_INTEGRITY_COMPROMISED.value
            c1_claim = "L'intégrité documentaire ne peut être établie : provenance rejetée."
            c1_admitted = False
        elif p1.verification_status == "VERIFIED" and p1.admitted_as_proof:
            c1_status = EpistemicStatus.ESTABLISHED_FACT.value
            c1_claim = f"L'intégrité documentaire du fichier source ({p1.source_ref}) est un fait établi vérifié."
            c1_admitted = True
        else:
            c1_status = EpistemicStatus.OPEN_HYPOTHESIS_UNPROVEN.value
            c1_claim = f"L'intégrité documentaire du fichier ({p1.source_ref}) demeure non vérifiée."
            c1_admitted = False

        self.conclusions.append(EvidenceConclusion(
            conclusion_id="C1_DOCUMENTARY_INTEGRITY_FACT",
            claim=c1_claim,
            epistemic_status=c1_status,
            inference_rule=rule_c1.rule_id.value,
            premises=[p1.to_dict(), p4.to_dict()],
            references=[p1.source_ref],
            limits="Certifie l'intégrité documentaire du fichier ; ne démontre pas l'authenticité physique.",
            established_scope=rule_c1.established_scope,
            admitted_as_proof=c1_admitted,
        ))

        # C6 : Préservation des contradictions
        rule_c6 = TYPED_INFERENCE_RULES[InferenceRule.CONTRADICTION_PRESERVATION]
        has_contras = bool(p7.value.get("count", 0) > 0)
        c6_claim = (
            f"Contradictions actives ({p7.value.get('count')} détectées) préservées sans lissage sous politique fail-closed."
            if has_contras else "Aucune contradiction active observée dans les faits vérifiés."
        )
        self.conclusions.append(EvidenceConclusion(
            conclusion_id="C6_CONTRADICTIONS_PRESERVED",
            claim=c6_claim,
            epistemic_status=EpistemicStatus.CONTRADICTION_PRESERVED.value if has_contras else EpistemicStatus.ESTABLISHED_FACT.value,
            inference_rule=rule_c6.rule_id.value,
            premises=[p7.to_dict()],
            references=["runtime://contradictions"],
            limits="Les contradictions ne sont jamais résolues sans preuve formelle.",
            established_scope=rule_c6.established_scope,
            admitted_as_proof=True,
        ))

        # C7 : Autorité souveraine exclusive KX108
        rule_c7 = TYPED_INFERENCE_RULES[InferenceRule.SOVEREIGN_AUTHORITY_SEPARATION]
        self.conclusions.append(EvidenceConclusion(
            conclusion_id="C7_DECISION_RESERVED_KX108",
            claim="Toute décision opérationnelle ou verdict souverain demeure exclusivement réservé au noyau KX108.",
            epistemic_status=EpistemicStatus.SOVEREIGN_RESERVED.value,
            inference_rule=rule_c7.rule_id.value,
            premises=[p_map["P8_NON_SOVEREIGN_AUTHORITY_LOCK"].to_dict()],
            references=["kernel://x108"],
            limits="L'environnement de raisonnement est strictement consultatif et en lecture seule.",
            established_scope=rule_c7.established_scope,
            admitted_as_proof=True,
        ))

        return self.conclusions

    def evaluate_negative_controls(
        self,
        candidate_claims: List[Dict[str, Any]],
    ) -> List[NegativeControlEvaluation]:
        """Évalue et rejette formellement toute affirmation candidate extrapolée ou non démontrée."""
        self.extract_premises()
        self.synthesize_conclusions()
        results: List[NegativeControlEvaluation] = []

        for c_obj in candidate_claims:
            cid = str(c_obj.get("claim_id", uuid.uuid4().hex[:8]))
            text = str(c_obj.get("claim", ""))
            rule_key = c_obj.get("inference_rule")
            target_status = str(c_obj.get("target_status", EpistemicStatus.ESTABLISHED_FACT.value))

            rule = TYPED_INFERENCE_RULES.get(InferenceRule(rule_key)) if rule_key in InferenceRule._value2member_map_ else None
            if rule is None:
                results.append(NegativeControlEvaluation(
                    claim_id=cid,
                    candidate_claim=text,
                    accepted=False,
                    epistemic_status=EpistemicStatus.UNJUSTIFIED_INFERENCE.value,
                    rule_violations=["UNKNOWN_INFERENCE_RULE"],
                    reasoning="Règle d'inférence non reconnue par le contrat.",
                ))
                continue

            violations: List[str] = []
            text_lower = text.lower()

            # 1. Vérification des scopes prohibés
            for prohibited in rule.prohibited_scopes:
                if prohibited.lower() in text_lower:
                    violations.append(
                        f"SCOPE_EXCEEDANCE_IN_RULE: Règle {rule.rule_id.value} interdit '{prohibited}'. "
                        f"Périmètre restreint à : {rule.established_scope}"
                    )

            # 2. Vérification des prémisses requises
            available = {p.premise_id: p for p in self.premises}
            for req in rule.required_premise_ids:
                if req not in available:
                    violations.append(f"MISSING_REQUIRED_PREMISE:{req}")
                elif not available[req].admitted_as_proof:
                    violations.append(f"UNADMITTED_PREMISE_IN_RULE:{req}")

            # 3. Vérification du statut autorisé
            if target_status not in rule.allowed_epistemic_statuses:
                violations.append(f"UNAUTHORIZED_EPISTEMIC_STATUS:{target_status}")

            accepted = len(violations) == 0
            epistemic_status = target_status if accepted else EpistemicStatus.UNJUSTIFIED_INFERENCE.value
            results.append(NegativeControlEvaluation(
                claim_id=cid,
                candidate_claim=text,
                accepted=accepted,
                epistemic_status=epistemic_status,
                rule_violations=violations,
                reasoning="Affirmation conforme au périmètre établi." if accepted else "; ".join(violations),
            ))

        return results

    def compare_propositions(
        self,
        prop_a: Dict[str, Any],
        prop_b: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compare deux propositions et détecte concordance, contradiction ou écart de preuve."""
        claim_a = str(prop_a.get("claim", "")).strip()
        claim_b = str(prop_b.get("claim", "")).strip()
        status_a = prop_a.get("epistemic_status", EpistemicStatus.OPEN_HYPOTHESIS_UNPROVEN.value)
        status_b = prop_b.get("epistemic_status", EpistemicStatus.OPEN_HYPOTHESIS_UNPROVEN.value)

        # Détection de contradiction directe sur les valeurs
        val_a = prop_a.get("value")
        val_b = prop_b.get("value")
        has_direct_conflict = (val_a is not None and val_b is not None and val_a != val_b)

        if has_direct_conflict:
            relation = "CONTRADICTION"
            status = EpistemicStatus.CONTRADICTION_PRESERVED.value
            summary = f"Contradiction formelle entre la proposition A ({val_a}) et la proposition B ({val_b})."
        elif claim_a == claim_b and status_a == status_b:
            relation = "EQUIVALENCE"
            status = status_a
            summary = "Propositions identiques en affirmation et en statut épistémique."
        elif status_a != status_b:
            relation = "EPISTEMIC_GAP"
            status = EpistemicStatus.OPEN_HYPOTHESIS_UNPROVEN.value
            summary = f"Écart épistémique : proposition A ({status_a}) vs proposition B ({status_b})."
        else:
            relation = "DISTINCT"
            status = EpistemicStatus.OPEN_HYPOTHESIS_UNPROVEN.value
            summary = "Propositions distinctes sans contradiction formelle identifiée."

        return {
            "relation": relation,
            "status": status,
            "summary": summary,
            "has_conflict": has_direct_conflict,
            "prop_a": prop_a,
            "prop_b": prop_b,
            **REASONING_BOUNDARY,
        }
