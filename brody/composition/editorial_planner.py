"""brody/composition/editorial_planner.py — Planification et composition éditoriale native Brody.

Planification rhétorique déterministe (V1 et V2) sans aucun modèle de langage.
Raccorde les trames linguistiques SENS au réalisateur True Voice et au contrat E11.
Zéro inférence LLM, zéro réseau, autorité souveraine exclusive KX108_ONLY.
"""
from __future__ import annotations

import copy
import hashlib
import inspect
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

from brody.linguistic import (
    parse_utterance,
    realize_semantic_relation,
)
from brody.linguistic.french_grammar import (
    project_editorial_brief,
)
from brody.composition.contracts import (
    SCHEMA_EDITORIAL_V1,
    SCHEMA_EDITORIAL_V2,
    SCHEMA_EDITORIAL_ARTIFACT_V1,
    SCHEMA_EDITORIAL_ARTIFACT_V2,
    E11_BOUNDARY,
)


def digest(value: Any) -> str:
    """Calcul d'empreinte SHA-256 canonique pour structures JSON."""
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def source_ref(function: Any) -> Dict[str, str]:
    """Référence de provenance du code source d'une fonction."""
    path = Path(inspect.getsourcefile(function)).resolve()
    return {
        "function": function.__name__,
        "path": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def recognize_native_editorial_request(brief: str) -> Optional[Dict[str, Any]]:
    """Reconnaît une demande éditoriale délimitée sans autorité d'action.

    Identifie si la requête vise une production textuelle consultative
    (ex: LinkedIn, brouillon, publication, article) via l'IR linguistique SENS.
    """
    raw = str(brief or "").strip()
    if not raw:
        return None
    frame = parse_utterance(raw)
    projected = project_editorial_brief(frame)
    if projected.get("editorial_intent") != "consultative_draft":
        # Tentative de repli heuristique sur mots-clés d'intention éditoriale
        lower = raw.lower()
        if any(kw in lower for kw in ("rédige", "redige", "écris", "ecris", "brouillon", "publication", "post linkedin")):
            text_objects = {"publication", "brouillon", "article", "texte", "post"}
            explicit = "linkedin" in lower or any(w in lower for w in text_objects)
            if explicit:
                # Trame minimale de secours
                return {
                    "editorial_intent": "consultative_draft",
                    "subject": {"actor": "équipe", "predicate": "rédiger", "object": "texte", "goal": raw, "unit_ids": []},
                    "audience": {"label": "lecteurs", "basis": "DEFAULT"},
                    "platform": "linkedin" if "linkedin" in lower else "article",
                    "constraints": {"low_budget": False, "time_saving": False, "draft_only": True},
                    "ambiguous": False,
                    "supported": True,
                    "source": "heuristic_fallback",
                    "non_sovereign": True,
                }
        return None

    text_objects = {"publication", "brouillon", "article", "texte", "post"}
    explicit = projected.get("platform") is not None or any(
        text_objects.intersection(a.head.split()) for u in frame.units if u.predicate == "WRITE" for a in u.objects
    )
    return projected if explicit else None


def _operations(interpretation: Dict[str, Any], *, version: str = "V1") -> List[Dict[str, Any]]:
    """Génère les propositions consultatives candidates sans assertions factuelles."""
    if version == "V2":
        return _v2_operations(interpretation, _operations(interpretation, version="V1"))
    if not interpretation.get("supported"):
        return []
    scope = interpretation.get("subject") or {"actor": "équipe", "predicate": "utiliser", "object": "IA"}
    constraints = interpretation.get("constraints", {})
    low = constraints.get("low_budget", False)

    specs = [
        ("review", "development", "L’équipe", "relire", "le brouillon avant tout usage", 70),
        ("verify", "development", "L’équipe", "vérifier", "chaque information avant tout usage", 65),
        ("expand", "development", "L’équipe", "multiplier", "les outils dès le premier essai", 0 if low else 30),
        ("evaluate", "conclusion", "L’équipe", "comparer", "le temps passé avec et sans assistance avant de poursuivre", 80),
        ("trial", "example", "Un premier essai avec l’IA", "porter", "sur un brouillon de réponse à une demande récurrente, sans données privées", 85),
        ("bound", "introduction", "Une petite entreprise", "commencer",
         "par une seule tâche répétitive, avec un budget plafonné" if low else "par une seule tâche répétitive et un objectif limité", 90),
        ("choose", "development", "L’équipe", "choisir", "une tâche chronophage et un résultat facile à relire", 75),
    ]
    origin = source_ref(_operations)
    return [
        {
            "id": key,
            "origin": {"kind": "BRODY_ADVISORY_OPERATOR", **origin},
            "relevance": score,
            "scope": scope,
            "factual_status": "PROPOSED_ACTION",
            "epistemic_status": "HYPOTHETICAL_NOT_VERIFIED",
            "role": role,
            "relation": {
                "subject": subj,
                "verb_lemma": verb,
                "obj": obj,
                "mood": "conditional",
            },
            "evidence_refs": [],
        }
        for key, role, subj, verb, obj, score in specs
    ]


def _select_and_plan(
    candidates: List[Dict[str, Any]],
    constraints: Dict[str, Any],
    *,
    version: str = "V1"
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Sélectionne les propositions pertinentes et ordonne selon la rhétorique V1."""
    if version == "V2":
        return _v2_select_and_plan(candidates, constraints)
    eligible = [
        p for p in candidates
        if p.get("relevance", 0) >= 60
        and p.get("origin", {}).get("kind") == "BRODY_ADVISORY_OPERATOR"
        and p.get("factual_status") == "PROPOSED_ACTION"
    ]
    selected = sorted(eligible, key=lambda p: (-p["relevance"], p["id"]))
    plan = []
    for role in ("introduction", "development", "example", "conclusion"):
        ids = [p["id"] for p in selected if p.get("role") == role]
        if not ids:
            return selected, []
        plan.append({
            "role": role,
            "proposition_ids": ids,
            "basis": "ROLE_AND_BRIEF_RELEVANCE",
        })
    return selected, plan


def _v2_operations(interpretation: Dict[str, Any], base: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transforme les opérations de base en actes illocutoires V2 stricts."""
    if not interpretation.get("supported") or not base:
        return []
    reader = {"responsables de petites entreprises": "votre équipe"}.get(
        (interpretation.get("audience") or {}).get("label")
    )
    if reader is None:
        reader = "votre équipe"

    roles = {
        "bound": "main_idea",
        "choose": "explanation",
        "review": "explanation",
        "verify": "explanation",
        "expand": "explanation",
        "trial": "example",
        "evaluate": "conclusion",
    }
    origin = {"kind": "BRODY_ADVISORY_OPERATOR", **source_ref(_v2_operations)}
    result = []
    for source in base:
        p = copy.deepcopy(source)
        p.update(
            role=roles.get(p["id"], "explanation"),
            origin=dict(origin),
            editorial_version="V2",
            factual_status="NON_ASSERTIVE",
            derived_from={
                "operation_id": source["id"],
                "component": source_ref(_operations),
                "subject_unit_ids": interpretation.get("subject", {}).get("unit_ids", []),
            },
        )
        p["operation_family"] = "QUALITY_CONTROL" if p["id"] in {"review", "verify"} else p["id"].upper()
        if p["id"] == "trial":
            p.update(speech_act="ILLUSTRATION", epistemic_status="HYPOTHETICAL_NOT_VERIFIED")
        else:
            p.update(speech_act="ADVICE", epistemic_status="ADVISORY_NOT_ESTABLISHED")
            p["relation"].update(subject="", mood="imperative", person="2", number="pl")
        if p["id"] == "evaluate":
            p["relation"]["obj"] = source["relation"]["obj"].removesuffix(" avant de poursuivre")
        if p["operation_family"] == "QUALITY_CONTROL" and p["relation"]["obj"].endswith(" avant tout usage"):
            p["relation"]["obj"] = p["relation"]["obj"].removesuffix(" avant tout usage")
            p["scope_modifier"] = "BEFORE_USE"
        result.append(p)

    subject = interpretation.get("subject") or {"actor": "entreprise", "predicate": "utiliser", "object": "IA", "goal": "gagner du temps", "unit_ids": []}
    goal = subject.get("goal", "gagner du temps")
    budget = " sans gros budget" if interpretation.get("constraints", {}).get("low_budget") else ""
    result.append({
        "id": "reader_need",
        "role": "problem",
        "relevance": 95,
        "origin": dict(origin),
        "editorial_version": "V2",
        "factual_status": "NON_ASSERTIVE",
        "epistemic_status": "QUESTION_NOT_ASSERTED",
        "speech_act": "QUESTION",
        "scope": copy.deepcopy(subject),
        "evidence_refs": [],
        "operation_family": "READER_NEED",
        "derived_from": {
            "brief_fields": ["subject.goal", "subject.object", "audience", "constraints.low_budget"],
            "subject_unit_ids": subject.get("unit_ids", []),
        },
        "relation": {
            "subject": reader,
            "verb_lemma": "pouvoir",
            "obj": f"{goal} avec l’{subject.get('object', 'IA')}{budget}",
            "mood": "interrogative",
        },
    })
    return result


def _v2_select_and_plan(
    candidates: List[Dict[str, Any]],
    constraints: Dict[str, Any]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Sélectionne et ordonne les propositions selon la structure rhétorique V2."""
    acts = {
        "problem": "QUESTION",
        "main_idea": "ADVICE",
        "explanation": "ADVICE",
        "example": "ILLUSTRATION",
        "conclusion": "ADVICE",
    }
    eligible = [
        p for p in candidates
        if p.get("relevance", 0) >= 60
        and p.get("origin", {}).get("kind") == "BRODY_ADVISORY_OPERATOR"
        and p.get("editorial_version") == "V2"
        and p.get("factual_status") == "NON_ASSERTIVE"
        and p.get("speech_act") == acts.get(p.get("role"))
    ]
    selected = sorted(eligible, key=lambda p: (-p["relevance"], p["id"]))
    by_role = {role: [p["id"] for p in selected if p.get("role") == role] for role in acts}
    if any(not by_role[r] for r in ("problem", "main_idea", "explanation", "conclusion")):
        return selected, []
    links = {
        "problem": "READER_GOAL_QUESTION",
        "main_idea": "PROPOSES_APPROACH",
        "explanation": "ELABORATES",
        "example": "ILLUSTRATES",
        "conclusion": "EVALUATES_BEFORE_CONTINUATION",
    }
    plan = []
    previous: List[str] = []
    for role in acts:
        ids = by_role[role]
        if not ids:
            continue
        plan.append({
            "role": role,
            "proposition_ids": ids,
            "depends_on": list(previous),
            "relation_to_previous": links[role],
            "basis": "BRIEF_GOAL_AND_SELECTED_NATIVE_OPERATIONS",
            "editorial_version": "V2",
        })
        previous.extend(ids)
    return selected, plan


def _realize_brody_editorial_v2(
    propositions: List[Dict[str, Any]],
    plan: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Réalisation de surface native des propositions V2 sans prose libre."""
    fail = {"status": "HOLD", "text": "", "proposition_ids": [], "realizations": []}
    roles = [s.get("role") for s in plan]
    if roles not in (
        ["problem", "main_idea", "explanation", "example", "conclusion"],
        ["problem", "main_idea", "explanation", "conclusion"],
    ):
        return fail
    acts = {
        "problem": ("QUESTION", "interrogative", "QUESTION_NOT_ASSERTED"),
        "main_idea": ("ADVICE", "imperative", "ADVISORY_NOT_ESTABLISHED"),
        "explanation": ("ADVICE", "imperative", "ADVISORY_NOT_ESTABLISHED"),
        "example": ("ILLUSTRATION", "conditional", "HYPOTHETICAL_NOT_VERIFIED"),
        "conclusion": ("ADVICE", "imperative", "ADVISORY_NOT_ESTABLISHED"),
    }
    links = {
        "problem": "READER_GOAL_QUESTION",
        "main_idea": "PROPOSES_APPROACH",
        "explanation": "ELABORATES",
        "example": "ILLUSTRATES",
        "conclusion": "EVALUATES_BEFORE_CONTINUATION",
    }
    by_id = {p["id"]: p for p in propositions}
    ids = [i for step in plan for i in step.get("proposition_ids", [])]
    if len(by_id) != len(propositions) or len(ids) != len(set(ids)) or set(ids) != set(by_id):
        return fail

    previous: List[str] = []
    realizations: List[Dict[str, Any]] = []
    sentences: List[Dict[str, Any]] = []
    paragraphs: List[str] = []
    origin = {"kind": "BRODY_ADVISORY_OPERATOR", **source_ref(_v2_operations)}

    def lower_first(text: str) -> str:
        return text[0].lower() + text[1:] if text else ""

    def make_sentence(chunks: List[Dict[str, Any]], prefix: str = "", suffix: str = "", operations: Tuple[str, ...] = ()) -> str:
        texts = [c["text"].removesuffix(".").removesuffix("?") for c in chunks]
        if len(texts) == 1:
            t = texts[0]
        else:
            t = ", ".join([texts[0], *[lower_first(x) for x in texts[1:-1]]]) + " et " + lower_first(texts[-1])
        t = prefix + (lower_first(t) if prefix else t) + suffix
        t = t.strip()
        if chunks[0].get("speech_act") == "QUESTION":
            if not t.endswith("?"):
                t += " ?"
        else:
            if not t.endswith("."):
                t += "."
        entry = {
            "sentence_id": "s" + str(len(sentences) + 1),
            "text": t,
            "sha256_utf8": hashlib.sha256(t.encode("utf-8")).hexdigest(),
            "proposition_ids": [c["proposition_id"] for c in chunks],
            "realization_ids": [c["realization_id"] for c in chunks],
            "operations": ["NATIVE_RELATION_REALIZATION", *operations],
            "author": "BRODY",
            "world_fact_established": False,
        }
        sentences.append(entry)
        return t

    for step in plan:
        role = step["role"]
        if (step.get("editorial_version") != "V2" or step.get("depends_on") != previous
                or step.get("relation_to_previous") != links[role]):
            return fail
        chunks: List[Dict[str, Any]] = []
        for key in step["proposition_ids"]:
            p = by_id[key]
            relation = p.get("relation", {})
            act, mood, epistemic = acts[role]
            native_res = realize_semantic_relation(**relation)
            if native_res.get("has_linguistic_limitations") or not native_res.get("text"):
                return fail
            chunk = {
                "proposition_id": key,
                "realization_id": "r:" + key,
                "speech_act": act,
                "source_subject": relation.get("subject", ""),
                "source_relation": dict(relation),
                "scope_modifier": p.get("scope_modifier"),
                "operation_family": p.get("operation_family"),
                **native_res,
            }
            chunks.append(chunk)
            realizations.append(chunk)

        # Regroupement rhétorique par phrases
        texts: List[str] = []
        idx = 0
        while idx < len(chunks):
            group = [chunks[idx]]
            idx += 1
            if group[0].get("operation_family") == "QUALITY_CONTROL":
                while idx < len(chunks) and chunks[idx].get("operation_family") == "QUALITY_CONTROL":
                    group.append(chunks[idx])
                    idx += 1
            prefix = ""
            operations: List[str] = []
            if role == "example":
                prefix = "Par exemple, "
                operations.append("HYPOTHETICAL_ILLUSTRATION_LINK")
            elif role == "conclusion":
                prefix = "Avant de poursuivre, "
                operations.append("GOAL_EVALUATION_LINK")
            suffix = " avant tout usage" if group[0].get("scope_modifier") == "BEFORE_USE" else ""
            if suffix:
                operations.append("SHARED_SCOPE_ATTACHMENT")
            if len(group) > 1:
                operations.append("SAME_AGENT_COORDINATION")
            texts.append(make_sentence(group, prefix, suffix, tuple(operations)))

        section = " ".join(texts)
        if step["relation_to_previous"] == "ELABORATES" and paragraphs:
            paragraphs[-1] += " " + section
        else:
            paragraphs.append(section)
        previous.extend(step["proposition_ids"])

    path = Path(inspect.getsourcefile(realize_semantic_relation)).resolve()
    return {
        "status": "REALIZED",
        "editorial_version": "V2",
        "text": "\n\n".join(paragraphs),
        "proposition_ids": ids,
        "realizations": realizations,
        "sentences": sentences,
        "author": "BRODY",
        "model_calls": 0,
        "human_review_required": True,
        "publication_permitted": False,
        "component": {
            "function": "realize_semantic_relation",
            "path": str(path),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        },
        "rhetorical_component": source_ref(_realize_brody_editorial_v2),
        "decision_authority": "KX108_ONLY",
        "advisory_only": True,
    }


def realize_brody_editorial_plan(
    propositions: List[Dict[str, Any]],
    plan: List[Dict[str, Any]],
    *,
    version: str = "V1"
) -> Dict[str, Any]:
    """Réalisation de surface déterministe d'un plan éditorial."""
    if version == "V2":
        return _realize_brody_editorial_v2(propositions, plan)
    if version != "V1":
        return {"status": "HOLD", "text": "", "proposition_ids": [], "realizations": []}

    fail = {"status": "HOLD", "text": "", "proposition_ids": [], "realizations": []}
    roles = [step.get("role") for step in plan]
    if roles not in (
        ["introduction", "development", "example", "conclusion"],
        ["introduction", "development", "conclusion"],
    ):
        return fail

    by_id = {p["id"]: p for p in propositions}
    ids = [i for step in plan for i in step.get("proposition_ids", [])]
    if len(ids) != len(set(ids)) or set(ids) != set(by_id):
        return fail

    paragraphs: List[str] = []
    realizations: List[Dict[str, Any]] = []
    for step in plan:
        sentences: List[str] = []
        for key in step["proposition_ids"]:
            p = by_id[key]
            rel = p.get("relation", {})
            realized = realize_semantic_relation(**rel)
            if realized.get("has_linguistic_limitations") or not realized.get("text"):
                return fail
            sentences.append(realized["text"])
            realizations.append({
                "proposition_id": key,
                "realization_id": "r:" + key,
                "source_relation": dict(rel),
                **realized,
            })
        paragraphs.append(" ".join(sentences))

    path = Path(inspect.getsourcefile(realize_semantic_relation)).resolve()
    return {
        "status": "REALIZED",
        "editorial_version": "V1",
        "text": "\n\n".join(paragraphs),
        "proposition_ids": ids,
        "realizations": realizations,
        "author": "BRODY",
        "model_calls": 0,
        "human_review_required": True,
        "publication_permitted": False,
        "component": {
            "function": "realize_semantic_relation",
            "path": str(path),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        },
        "decision_authority": "KX108_ONLY",
        "advisory_only": True,
    }


def compose_native_editorial(
    brief: str,
    *,
    context_propositions: Tuple[Dict[str, Any], ...] = (),
    version: str = "V1",
) -> Dict[str, Any]:
    """Port principal de composition éditoriale Brody sous garde souveraine.

    Prend le brief utilisateur en entrée, effectue l'analyse linguistique SENS,
    sélectionne les opérateurs rhétoriques admissibles et réalise le brouillon.
    """
    if version not in {"V1", "V2"}:
        raise ValueError("UNSUPPORTED_EDITORIAL_VERSION")

    raw = str(brief or "").strip()
    frame = parse_utterance(raw)
    interpretation = project_editorial_brief(frame)

    if not interpretation.get("supported"):
        # Tentative avec fallback structuré si intention consultative reconnue
        recognized = recognize_native_editorial_request(raw)
        if recognized and recognized.get("supported"):
            interpretation = recognized
        else:
            return {
                "editorial_route_status": "REFUSED",
                "editorial_refusal_reasons": ["UNSUPPORTED_EDITORIAL_BRIEF"],
                "final_answer_source": "BRODY_NATIVE_EDITORIAL_" + version,
                "human_approval_required": True,
                "publication_permitted": False,
                **E11_BOUNDARY,
            }

    candidates = _operations(interpretation, version=version)
    selected, plan = _select_and_plan(candidates, interpretation.get("constraints", {}), version=version)

    if not plan:
        return {
            "editorial_route_status": "REFUSED",
            "editorial_refusal_reasons": ["INCOMPLETE_EDITORIAL_PLAN"],
            "final_answer_source": "BRODY_NATIVE_EDITORIAL_" + version,
            "human_approval_required": True,
            "publication_permitted": False,
            **E11_BOUNDARY,
        }

    realization = realize_brody_editorial_plan(selected, plan, version=version)
    if realization.get("status") != "REALIZED":
        return {
            "editorial_route_status": "HOLD",
            "editorial_refusal_reasons": ["REALIZATION_HOLD"],
            "final_answer_source": "BRODY_NATIVE_EDITORIAL_" + version,
            "human_approval_required": True,
            "publication_permitted": False,
            **E11_BOUNDARY,
        }

    schema_name = SCHEMA_EDITORIAL_V1 if version == "V1" else SCHEMA_EDITORIAL_V2
    artifact_schema = SCHEMA_EDITORIAL_ARTIFACT_V1 if version == "V1" else SCHEMA_EDITORIAL_ARTIFACT_V2

    snapshot = {
        "editorial_version": version,
        "editorial_plan": plan,
        "selected_propositions": selected,
        "realization": realization,
        "draft": {
            "text": realization["text"],
            "factual_claims": [],
            "author": "BRODY",
        },
        "provenance": {
            "author": "BRODY_NATIVE_EDITORIAL",
            "model_calls": 0,
            "components": [realization.get("component", {})],
        },
        "uncertainties": [
            {"kind": "UNRESOLVED_SYMBOL", "symbol": "HYPOTHETICAL_ACTION"}
        ],
        "essential_unresolved_symbols": [],
        "hold_reasons": [],
        "evidence_refs": [],
    }

    artifact = {
        "schema": artifact_schema,
        "editorial_version": version,
        "native_composition_schema": schema_name,
        "editorial_plan": plan,
        "selected_propositions": selected,
        "realization": realization,
        "draft": {
            "text": realization["text"],
            "factual_claims": [],
            "author": "BRODY",
        },
        "selection_provenance": {"kind": "EXPLICIT_BRIEF_ANALYSIS"},
        "provenance": {
            "author": "BRODY_NATIVE_EDITORIAL",
            "model_calls": 0,
            "components": [realization.get("component", {})],
        },
        "uncertainties": snapshot["uncertainties"],
        "evidence_refs": [],
        "human_review_required": True,
        "human_approval_required": True,
        "publication_permitted": False,
        "memory_write": False,
        **E11_BOUNDARY,
    }

    return {
        "editorial_route_status": "CONSULTATIVE_DRAFT_AVAILABLE",
        "final_answer_source": schema_name,
        "editorial_version_selected": version,
        "editorial_version_requested": version,
        "editorial_composition_snapshot": snapshot,
        "editorial_artifact": artifact,
        "human_approval_required": True,
        "publication_permitted": False,
        "editorial_refusal_reasons": [],
        **E11_BOUNDARY,
    }


def build_governed_e11_envelope(
    brief: str,
    composition_result: Dict[str, Any],
    *,
    memory_status: str = "MEMORY_NOT_REQUIRED",
    selected_items_count: int = 0,
    memory_entries: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Construit une enveloppe E11 conforme admissible par consume_envelope()."""
    b = dict(E11_BOUNDARY)
    entry = {
        "state_id": "native-source-doc",
        "state_type": "NATIVE_MEMORY_ITEM",
        "source_ref": "obsidia://native_memory/verified",
        "payload": {"excerpt": "Contexte mémoriel vérifié"},
        "provenance": ["NATIVE_MEM_V1"],
        "uncertainty": [],
        "status": "KNOWN",
        "visibility": "LONG",
        "tags": ["governed"],
        "summary": "Résumé de mémoire native",
        "readonly": True,
    }
    entries = memory_entries or ([entry] if memory_status == "MEMORY_USABLE" else [])
    count = selected_items_count if memory_status == "MEMORY_USABLE" else 0

    packet = {
        "schema": "B6_STATE_EXPLICIT_CONTEXT_PACKET_V1",
        "packet_id": f"b6ctx_{hashlib.md5(brief.encode()).hexdigest()[:16]}",
        "query": brief,
        "projection": {"query_tokens": [], "included": [], "omitted": []},
        "state": entries,
        "instructions": [],
        "capabilities": {},
        "provenance_refs": ["REF_MEM_B6"],
        "unknowns": [],
        "omitted": [],
        "boundary": copy.deepcopy(b),
    }

    shadow = {
        "schema": "COGNITION_SHADOW_MEMORY_V0",
        "input_text": brief,
        "memory_snapshot_ref": {
            "schema_version": "OBSIDIA_NATIVE_MEMORY_RETRIEVAL_V1",
            "status": memory_status,
            "query": brief,
            "selected_items_count": count,
        },
        "state_entries": [],
        "memory_entries": entries,
        "context_packet": packet,
        "resolution_requests": [],
        "boundary": {k: b[k] for k in ("readonly", "decision_authority", "memory_write", "emits_act", "kernel_mutation")},
    }

    receipt = {
        "version": "REAL_COGNITIVE_JOIN_C1_V1",
        "rail_mode": "SHADOW_READONLY_SUPERPOSED",
        "signal_id": f"sig_{hashlib.md5(brief.encode()).hexdigest()[:12]}",
        "created_at": "2026-11-19T00:00:00Z",
        "status": "READY_SHADOW_READONLY",
        "completeness": "COMPLETE",
        "components": {"COGNITION_SHADOW_MEMORY": "OK"},
        "errors": [],
        "critical_action_requested": False,
        "kx108_admission": "DRY_RUN",
        "decision_ticket_dry_run": {
            "decision": "ALLOW_CONTEXT_ONLY",
            "x108_gate_status": "X108_EVALUATED_DRY_RUN",
        },
        "real_execution": False,
        "response_governance_applied": False,
        "advisory_only": True,
        **b,
        "cognition_shadow_memory": shadow,
    }

    return {
        **b,
        "status": "READY_SHADOW_READONLY",
        "advisory_only": True,
        "x108_mutation": False,
        "real_action": False,
        "emits_verdict": False,
        "source": "REAL_BRODY_RUNTIME",
        "cognitive_runtime_receipt": receipt,
        **composition_result,
    }
