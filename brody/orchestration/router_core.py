"""brody/orchestration/router_core.py — Routeur sémantique et gardes déterministes.

Intègre la normalisation UTF-8 mojibake, la compilation d'IR unifié, l'évaluation
des gardes (DENY / HOLD / CLARIFY / ALLOW), la cartographie des sujets canoniques
et la sélection du niveau d'inférence.

Frontière gouvernée : 100% CPU, non-souverain, KX108_ONLY.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any, Mapping, Optional

from brody.orchestration.contracts import (
    DECISION_AUTHORITY,
    LEVEL_0_NO_MODEL,
    LEVEL_1_BRODY_NATIVE,
    LEVEL_2_MEMORY_LOOKUP,
    LEVEL_3_GOVERNED_FALLBACK,
    GATE_ALLOW,
    GATE_DENY,
    GATE_HOLD,
    GATE_CLARIFY,
    ROUTE_STACK_NATIVE,
    ROUTE_LLM_LANGUAGE,
    ROUTE_LLM_REASONING,
    ROUTE_HUMAN_AUTHORITY,
    ROUTE_UNKNOWN,
    RouteDecision,
)


# ── Réparation mojibake UTF-8 canonique ────────────────────────────────────
_MOJIBAKE_FIXES: dict[str, str] = {
    "mÃ©moire": "mémoire",
    "crÃ©ation": "création",
    "crÃ©ateur": "créateur",
    "crÃ©e": "crée",
    "rÃ©ponse": "réponse",
    "rÃ©ponds": "réponds",
    "rÃ´le": "rôle",
    "prÃ©cÃ©dent": "précédent",
    "dÃ©cision": "décision",
    "dÃ©passe": "dépasse",
    "rÃ©el": "réel",
    "dÃ©jÃ ": "déjà",
    "systÃ¨me": "système",
    "Ã©tat": "état",
    "actuel": "actuel",
}


def normalize_utf8_mojibake(text: str) -> str:
    """Répare les déformations d'encodage fréquentes avant analyse."""
    res = str(text or "")
    for garbled, fix in _MOJIBAKE_FIXES.items():
        res = res.replace(garbled, fix)
    return res


def fold_accents(text: str) -> str:
    """Normalise la casse et retire les accents pour correspondances robustes."""
    folded = unicodedata.normalize("NFKD", text)
    folded = "".join(c for c in folded if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", folded.lower()).strip()


# ── Mots-clés de garde (Gates) ─────────────────────────────────────────────
# Mots-clés provoquant un refus immédiat (DENY)
DENY_KEYWORDS: list[str] = [
    "force-push", "force push", "rm -rf", "drop database", "format c",
    "disable gates", "bypass gates", "skip invariants", "ignore invariants",
    "override kx108", "bypass kx108", "takeover",
]

# Mots-clés entraînant une mise en réserve de commande (HOLD)
HOLD_KEYWORDS: list[str] = [
    "push", "commit", "deploy", "deploie", "delete", "supprime",
    "execute", "run", "lance", "install", "installe", "act", "autorise",
    "authorize",
]


def _key_match(key: str, normalized: str) -> bool:
    """Correspondance avec frontière de mot pour éviter les faux positifs (ex: 'act' dans 'actuel')."""
    if " " in key:
        return key in normalized
    return re.search(rf"(?<![a-z0-9]){re.escape(key)}(?![a-z0-9])", normalized) is not None


def evaluate_gates(ir: dict[str, Any]) -> dict[str, Any]:
    """Évalue les gardes de sécurité de manière déterministe avant toute inférence."""
    normalized = ir.get("normalized", "")

    for kw in DENY_KEYWORDS:
        if _key_match(kw, normalized):
            return {
                "verdict": GATE_DENY,
                "matched": kw,
                "invariants": ["no_auto_act", "invariants_preserved"],
                "reason": f"Mot-clé interdit '{kw}' : tentative hors cadre souverain.",
            }

    for kw in HOLD_KEYWORDS:
        if _key_match(kw, normalized):
            return {
                "verdict": GATE_HOLD,
                "matched": kw,
                "invariants": ["no_auto_act", "no_auto_commit", "no_auto_push"],
                "reason": f"Action système '{kw}' : requiert confirmation humaine explicite (commandes seules).",
            }

    if ir.get("intent_type") == "unknown" or "intent" in ir.get("missing", []):
        return {
            "verdict": GATE_CLARIFY,
            "matched": None,
            "invariants": ["bounded_output"],
            "reason": "Intention non résolue de manière déterministe : clarification requise.",
        }

    return {
        "verdict": GATE_ALLOW,
        "matched": None,
        "invariants": ["bounded_output"],
        "reason": "Requête dans le cadre souverain autorisé.",
    }


# ── Mots-clés de l'IR unifié ───────────────────────────────────────────────
_STATUS_WORDS = {"status", "statut", "etat", "state", "health", "sante", "ping", "version"}
_ACTION_WORDS = {"execute", "run", "lance", "push", "commit", "deploy", "deploie", "delete", "supprime", "rm", "install", "installe", "format", "drop", "autorise", "authorize", "act"}
_CODE_WORDS = {"code", "coder", "patch", "implemente", "implement", "fix", "corrige", "refactor", "script", "fonction", "function", "write", "ecris"}
_PLAN_WORDS = {"plan", "roadmap", "etapes", "steps", "organise", "planifie", "suite", "continue", "reprendre"}
_AUDIT_WORDS = {"audit", "verifie", "verify", "check", "inspecte", "inspect", "review", "diagnostique", "diagnose", "coherence", "contradiction"}
_QUESTION_WORDS = {"explique", "explain", "pourquoi", "why", "comment", "how", "quoi", "what", "contexte", "context", "resume", "summarize", "definis", "define", "who", "qui", "quel", "quelle", "quels", "quelles"}
_REASONING_WORDS = {"prouve", "prove", "demontre", "raisonne", "analyse", "analyze", "compare", "calcule", "compute", "combien", "deduis", "deduction"}
_EDITORIAL_WORDS = {"redige", "rediger", "draft", "publication", "article", "post", "editorial", "linkedin", "e11"}

_LAYER_KEYWORDS: list[tuple[str, set[str]]] = [
    ("obsidure", {"obsidure"}),
    ("domain", {"bank", "trading", "virement", "bancaire", "gps", "altitude"}),
    ("proof", {"preuve", "proof", "lean", "tla", "merkle", "theoreme", "invariant"}),
    ("memory", {"memoire", "memory", "corpus", "souviens", "remember", "retenir", "rappel"}),
    ("composition", {"redige", "rediger", "draft", "publication", "article", "post", "linkedin", "e11"}),
    ("arithmetic", {"calcule", "calculer", "combien", "+", "-", "*", "/", "="}),
    ("brody", {"brody", "qui es tu", "qui es-tu", "ton role", "ton statut", "qui t'a cree", "createur"}),
    ("system", {"status", "statut", "etat", "state", "version"}),
    ("world", {"push", "commit", "deploy", "delete", "supprime", "install", "execute"}),
]


def _words(normalized: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", normalized))


def _detect_layer(words: set[str], raw: str) -> str:
    for layer, kws in _LAYER_KEYWORDS:
        if words & kws:
            return layer
        for kw in kws:
            if kw in raw.lower():
                return layer
    return "unknown"


def build_ir(raw_query: str) -> dict[str, Any]:
    """Construit l'IR unifié décrivant l'intention et le niveau de risque."""
    repaired = normalize_utf8_mojibake(raw_query)
    normalized = fold_accents(repaired)
    w_set = _words(normalized)
    target_layer = _detect_layer(w_set, normalized)

    is_action = bool(w_set & _ACTION_WORDS)
    is_status = bool(w_set & _STATUS_WORDS)
    is_code = bool(w_set & _CODE_WORDS)
    is_plan = bool(w_set & _PLAN_WORDS)
    is_audit = bool(w_set & _AUDIT_WORDS)
    is_question = bool(w_set & _QUESTION_WORDS)
    is_reasoning = bool(w_set & _REASONING_WORDS)
    is_editorial = bool(w_set & _EDITORIAL_WORDS)

    if is_action:
        intent_type, action_type, risk_level = "world_action", "act_request", "high"
        target_layer = "world"
    elif is_editorial:
        intent_type, action_type, risk_level = "editorial_request", "compose", "low"
        target_layer = "composition"
    elif is_status:
        intent_type, action_type, risk_level = "status", "read_status", "low"
    elif is_code:
        intent_type, action_type, risk_level = "code_request", "commands", "medium"
    elif is_audit:
        intent_type, action_type, risk_level = "audit", "read", "medium"
    elif is_plan:
        intent_type, action_type, risk_level = "plan", "guide", "low"
    elif is_reasoning:
        intent_type, action_type, risk_level = "reasoning", "deduce", "low"
    elif is_question:
        intent_type, action_type, risk_level = "question", "answer", "low"
        if target_layer == "unknown":
            target_layer = "brody"
    else:
        # Détection heuristique additionnelle pour questions conversationnelles courantes
        if any(g in normalized for g in ["bonjour", "salut", "hello", "coucou", "qui es-tu", "qui es tu", "qui t'a", "merci"]):
            intent_type, action_type, risk_level = "greeting_or_identity", "answer", "low"
            target_layer = "brody"
        elif any(c in raw_query for c in ["+", "-", "*", "/"]) and any(d.isdigit() for d in raw_query):
            intent_type, action_type, risk_level = "reasoning", "calculate", "low"
            target_layer = "arithmetic"
        else:
            intent_type, action_type, risk_level = "unknown", "guide", "low"

    missing: list[str] = []
    if intent_type == "unknown":
        missing.append("intent")

    return {
        "raw": raw_query,
        "repaired": repaired,
        "normalized": normalized,
        "intent_type": intent_type,
        "target_layer": target_layer,
        "action_type": action_type,
        "risk_level": risk_level,
        "missing": missing,
        "words": list(w_set),
    }


# ── Cartographie canonique des sujets (Sémantique Brody) ───────────────────
_TOPIC_ROUTES: list[tuple[list[str], str, str, str]] = [
    # (triggers, topic, semantic_query, canonical_role)
    (
        ["x108", "kx108", "noyau", "invariants kx108", "decision_authority"],
        "X108",
        "X108 kernel décision gouvernance",
        "GOVERNANCE",
    ),
    (
        ["34 arbres", "34_arbres", "arbres obsidia", "tree policy"],
        "34_ARBRES",
        "34 arbres tree policy safe blocked",
        "TREE_POLICY",
    ),
    (
        ["bonjour", "salut", "hello", "qui es-tu", "qui es tu", "ton role", "ton statut", "qui est brody", "projet obsidia", "obsidia brody"],
        "OBSIDIA_BRODY_ROLE",
        "Obsidia Brody X108 mémoire gouvernance",
        "IDENTITY",
    ),
    (
        ["createur", "créateur", "qui t'a cree", "qui t'a créé", "inventeur"],
        "CREATOR_CONTEXT",
        "Brody créateur cadre X108",
        "CREATOR",
    ),
    (
        ["memoire", "mémoire", "souviens", "registre", "rappel", "corpus"],
        "MEMORY_QUERY",
        "Brody mémoire candidate pipeline",
        "MEMORY",
    ),
    (
        ["etat actuel", "état actuel", "statut actuel", "ou on en est", "où on en est", "recap"],
        "CURRENT_STATE",
        "Brody Obsidia etat actuel",
        "STATUS",
    ),
]


def match_canonical_topic(normalized: str) -> Optional[tuple[str, str, str]]:
    """Identifie un sujet canonique couvert par le corpus natif sans inférence LLM."""
    for triggers, topic, sem_query, role in _TOPIC_ROUTES:
        for trig in triggers:
            trig_fold = fold_accents(trig)
            if trig_fold in normalized:
                return topic, sem_query, role
    return None


class SemanticRouter:
    """Routeur conversationnel Brody unifié et déterministe."""

    def __init__(self, *, allow_fallback: bool = False) -> None:
        self.allow_fallback = allow_fallback

    def decide_route(
        self,
        raw_query: str,
        *,
        memory_index: Optional[dict[str, Any]] = None,
    ) -> RouteDecision:
        """Détermine le niveau d'inférence et la route optimale pour une requête."""
        raw = str(raw_query or "").strip()
        ir = build_ir(raw)
        gate = evaluate_gates(ir)
        topic_match = match_canonical_topic(ir["normalized"])
        topic_name = topic_match[0] if topic_match else None

        route_id = f"route_{hashlib.md5(raw.encode('utf-8')).hexdigest()[:10]}"

        # 1. Traitement des gardes strictes (DENY / HOLD) -> Niveau 0
        if gate["verdict"] == GATE_DENY:
            proof = hashlib.sha256(f"DENY:{raw}".encode("utf-8")).hexdigest()
            return RouteDecision(
                route_id=route_id,
                raw_query=raw,
                normalized_query=ir["normalized"],
                intent_type=ir["intent_type"],
                target_layer=ir["target_layer"],
                gate_verdict=GATE_DENY,
                gate_reason=gate["reason"],
                inference_level=LEVEL_0_NO_MODEL,
                route_class=ROUTE_HUMAN_AUTHORITY,
                canonical_topic=topic_name,
                decision_authority=DECISION_AUTHORITY,
                proof_hash=proof,
            )

        if gate["verdict"] == GATE_HOLD:
            proof = hashlib.sha256(f"HOLD:{raw}".encode("utf-8")).hexdigest()
            return RouteDecision(
                route_id=route_id,
                raw_query=raw,
                normalized_query=ir["normalized"],
                intent_type=ir["intent_type"],
                target_layer=ir["target_layer"],
                gate_verdict=GATE_HOLD,
                gate_reason=gate["reason"],
                inference_level=LEVEL_0_NO_MODEL,
                route_class=ROUTE_HUMAN_AUTHORITY,
                canonical_topic=topic_name,
                decision_authority=DECISION_AUTHORITY,
                proof_hash=proof,
            )

        # 2. Détection de solveurs locaux fermés (Arithmétique exacte, Lot 4) -> Niveau 1
        from brody.reasoning.arithmetic_engine import extract_arithmetic_expression
        arith_expr = extract_arithmetic_expression(raw)
        if arith_expr:
            proof = hashlib.sha256(f"SOLVER_ARITH:{arith_expr}".encode("utf-8")).hexdigest()
            return RouteDecision(
                route_id=route_id,
                raw_query=raw,
                normalized_query=ir["normalized"],
                intent_type="reasoning",
                target_layer="arithmetic",
                gate_verdict=GATE_ALLOW,
                gate_reason="Calcul arithmétique résolu par solveur déterministe local.",
                inference_level=LEVEL_1_BRODY_NATIVE,
                route_class=ROUTE_STACK_NATIVE,
                canonical_topic="ARITHMETIC",
                solver_hit="DeterministicArithmeticEngine",
                decision_authority=DECISION_AUTHORITY,
                proof_hash=proof,
            )

        # 3. Détection de rédaction éditoriale Studio E11 (Lot 5) -> Niveau 1
        from brody.composition import recognize_native_editorial_request
        editorial_intent = recognize_native_editorial_request(raw)
        if editorial_intent:
            proof = hashlib.sha256(f"EDITORIAL:{raw}".encode("utf-8")).hexdigest()
            return RouteDecision(
                route_id=route_id,
                raw_query=raw,
                normalized_query=ir["normalized"],
                intent_type="editorial_request",
                target_layer="composition",
                gate_verdict=GATE_ALLOW,
                gate_reason="Intention éditoriale reconnue : composition native Studio E11.",
                inference_level=LEVEL_1_BRODY_NATIVE,
                route_class=ROUTE_STACK_NATIVE,
                canonical_topic="EDITORIAL_STUDIO_E11",
                solver_hit="StudioEditorialEngine",
                decision_authority=DECISION_AUTHORITY,
                proof_hash=proof,
            )

        # 4. Clarification si intention ambiguë et pas de sujet canonique
        if gate["verdict"] == GATE_CLARIFY:
            if topic_name:
                # Le sujet canonique résout l'ambiguïté sans inférence
                proof = hashlib.sha256(f"CANONICAL_RESOLVED:{topic_name}".encode("utf-8")).hexdigest()
                return RouteDecision(
                    route_id=route_id,
                    raw_query=raw,
                    normalized_query=ir["normalized"],
                    intent_type="question",
                    target_layer="memory",
                    gate_verdict=GATE_ALLOW,
                    gate_reason=f"Ambiguïté résolue par le sujet canonique '{topic_name}'.",
                    inference_level=LEVEL_2_MEMORY_LOOKUP,
                    route_class=ROUTE_STACK_NATIVE,
                    canonical_topic=topic_name,
                    decision_authority=DECISION_AUTHORITY,
                    proof_hash=proof,
                )
            proof = hashlib.sha256(f"CLARIFY:{raw}".encode("utf-8")).hexdigest()
            return RouteDecision(
                route_id=route_id,
                raw_query=raw,
                normalized_query=ir["normalized"],
                intent_type=ir["intent_type"],
                target_layer=ir["target_layer"],
                gate_verdict=GATE_CLARIFY,
                gate_reason=gate["reason"],
                inference_level=LEVEL_0_NO_MODEL,
                route_class=ROUTE_UNKNOWN,
                canonical_topic=None,
                decision_authority=DECISION_AUTHORITY,
                proof_hash=proof,
            )

        # 5. Sujets canoniques de statut ou mémoire -> Niveau 1 ou 2
        if topic_name in ("OBSIDIA_BRODY_ROLE", "CREATOR_CONTEXT", "CURRENT_STATE", "X108"):
            proof = hashlib.sha256(f"CANONICAL_TOPIC:{topic_name}".encode("utf-8")).hexdigest()
            return RouteDecision(
                route_id=route_id,
                raw_query=raw,
                normalized_query=ir["normalized"],
                intent_type=ir["intent_type"],
                target_layer="brody",
                gate_verdict=GATE_ALLOW,
                gate_reason=f"Sujet canonique '{topic_name}' traité par la mémoire et le registre local.",
                inference_level=LEVEL_1_BRODY_NATIVE,
                route_class=ROUTE_STACK_NATIVE,
                canonical_topic=topic_name,
                decision_authority=DECISION_AUTHORITY,
                proof_hash=proof,
            )

        # 6. Requêtes conversationnelles générales
        # Si le fallback est permis et que la requête exige un modèle externe non couvert
        if self.allow_fallback and ir["target_layer"] == "world_remote":
            proof = hashlib.sha256(f"FALLBACK_QWEN:{raw}".encode("utf-8")).hexdigest()
            return RouteDecision(
                route_id=route_id,
                raw_query=raw,
                normalized_query=ir["normalized"],
                intent_type=ir["intent_type"],
                target_layer=ir["target_layer"],
                gate_verdict=GATE_ALLOW,
                gate_reason="Escalade consultative gouvernée autorisée vers modèle local.",
                inference_level=LEVEL_3_GOVERNED_FALLBACK,
                route_class=ROUTE_LLM_LANGUAGE,
                canonical_topic=topic_name,
                selected_model="qwen_local_consultative",
                decision_authority=DECISION_AUTHORITY,
                proof_hash=proof,
            )

        # Route par défaut : moteur natif Brody (Niveau 1)
        proof = hashlib.sha256(f"NATIVE_PIPELINE:{raw}".encode("utf-8")).hexdigest()
        return RouteDecision(
            route_id=route_id,
            raw_query=raw,
            normalized_query=ir["normalized"],
            intent_type=ir["intent_type"],
            target_layer=ir["target_layer"],
            gate_verdict=GATE_ALLOW,
            gate_reason="Traitement par le pipeline cognitif natif Brody.",
            inference_level=LEVEL_1_BRODY_NATIVE,
            route_class=ROUTE_STACK_NATIVE,
            canonical_topic=topic_name,
            decision_authority=DECISION_AUTHORITY,
            proof_hash=proof,
        )
