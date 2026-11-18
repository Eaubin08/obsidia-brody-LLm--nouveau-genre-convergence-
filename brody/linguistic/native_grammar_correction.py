"""Source-bound, consultative FR/EN grammar correction proposals.

This module never rewrites user text. It consumes the current native structural
analysis and only proposes a replacement when an existing incompatibility and
an attested target form can be tied to exact source offsets.
"""
from __future__ import annotations

import hashlib
from typing import Any

from brody.linguistic.french_grammar import parse_utterance
from brody.linguistic.lexical_corpus import lookup_surface_form, realize_inflection
from brody.linguistic.english_grammar import _BE, _CONTRACTIONS, _DO, _HAVE

SCHEMA = "BRODY_NATIVE_GRAMMAR_CORRECTION_ADVISORY_V0"
SUPPORTED_LANGUAGES = {"fr", "en"}


def _source_bound_proposal(
    *, original_text: str, span: list[int], replacement: str, rule_id: str,
    analysis_refs: list[str], lexical_refs: list[dict[str, Any]],
    rule_provenance: list[dict[str, Any]], conditions: list[str],
    uncertainties: list[str],
) -> dict[str, Any]:
    """Create a proposal only if its half-open Unicode code-point span is exact."""
    if (not isinstance(span, (list, tuple)) or len(span) != 2
            or not all(isinstance(value, int) for value in span)):
        raise ValueError("invalid source span")
    start, end = span
    if start < 0 or end < start or end > len(original_text):
        raise ValueError("source span outside original text")
    fragment = original_text[start:end]
    if not fragment or not replacement or not rule_id or not analysis_refs or not rule_provenance:
        raise ValueError("incomplete source-bound proposal")
    if fragment.isupper():
        replacement = replacement.upper()
    elif fragment[:1].isupper():
        replacement = replacement[:1].upper() + replacement[1:]
    return {
        "span": [start, end], "original_fragment": fragment,
        "replacement": replacement, "rule_id": rule_id,
        "analysis_refs": list(dict.fromkeys(analysis_refs)),
        "lexical_refs": lexical_refs, "rule_provenance": rule_provenance,
        "conditions": conditions, "uncertainties": uncertainties,
    }


def _token_by_ref(analysis: dict[str, Any], token_ref: str | None) -> dict[str, Any] | None:
    if not token_ref:
        return None
    return next((token for token in analysis.get("tokens", []) if token.get("id") == token_ref), None)


def _analyses(token: dict[str, Any] | None, *, lang: str, pos: str = "verb") -> list[dict[str, Any]]:
    if not token:
        return []
    return [row for row in token.get("nature_analyses", [])
            if row.get("lang") == lang and row.get("pos", "").lower() == pos]


def _lexical_refs(rows: list[dict[str, Any]], corpus_identity: Any) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        source_id = row.get("source_id")
        if source_id:
            result.append({"source_id": source_id, "lemma": row.get("lemma"),
                           "surface_form": row.get("surface_form"),
                           "corpus_identity": corpus_identity})
    return result


def _target_rows(surface: str, *, lang: str, lemma: str, mood: str,
                 tense: str | None = None, person: str | None = None,
                 number: str | None = None, gender: str | None = None) -> list[dict[str, Any]]:
    rows = [row.to_dict() for row in lookup_surface_form(surface, lang=lang)]
    return [row for row in rows if row.get("lemma") == lemma and row.get("pos", "").lower() == "verb"
            and row.get("mood", "").lower() == mood
            and (tense is None or row.get("tense", "").lower() == tense)
            and (person is None or not row.get("person") or row.get("person") == person)
            and (number is None or not row.get("number") or row.get("number") == number)
            and (gender is None or not row.get("gender") or row.get("gender") == gender)]


def _case_like(fragment: str, replacement: str) -> str:
    if fragment.isupper():
        return replacement.upper()
    if fragment[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def _french_proposals(original: str, analysis: dict[str, Any], identity: Any) -> tuple[list, list]:
    proposals, unresolved = [], []
    tokens = {row.get("id"): row for row in analysis.get("tokens", [])}
    for index, agreement in enumerate(analysis.get("agreements", [])):
        if agreement.get("status") != "INCOMPATIBLE":
            continue
        kind = agreement.get("kind")
        source_rule = agreement.get("source_rule") or agreement.get("evidence")
        candidate_specs: list[tuple[dict[str, Any], str, str, str, str, str]] = []
        if kind == "SUBJECT_PARTICIPLE" and source_rule == "existing_etre_participle_corpus_agreement":
            refs = agreement.get("evidence_refs") or {}
            token = tokens.get(refs.get("participle_token"))
            target_gender, target_number = agreement.get("expected_gender"), agreement.get("expected_number")
            if token and target_gender in {"fem", "masc"} and target_number in {"sg", "pl"}:
                for row in _analyses(token, lang="fr"):
                    if row.get("mood") == "participle" and row.get("tense") == "past" and row.get("source_id"):
                        candidate_specs.append((row, "participle", "past", "", target_number, target_gender))
        elif kind == "ANTECEDENT_PARTICIPLE" and source_rule == "existing_avoir_preposed_object_participle_agreement":
            refs = agreement.get("evidence_refs") or {}
            token = tokens.get(refs.get("participle_token"))
            target_gender, target_number = agreement.get("expected_gender"), agreement.get("expected_number")
            if token and target_gender in {"fem", "masc"} and target_number in {"sg", "pl"}:
                for row in _analyses(token, lang="fr"):
                    if row.get("mood") == "participle" and row.get("tense") == "past" and row.get("source_id"):
                        candidate_specs.append((row, "participle", "past", "", target_number, target_gender))
        elif kind == "SUBJECT_VERB" and source_rule == "written_subject_or_determiner_and_corpus_alternatives":
            surface = agreement.get("finite_form_surface")
            target_person, target_number = agreement.get("expected_person"), agreement.get("expected_number")
            dependent = next((group for group in analysis.get("groups", [])
                              if group.get("id") == agreement.get("dependent")), None)
            dependent_span = dependent.get("span") if dependent else None
            token_matches = [t for t in analysis.get("tokens", [])
                             if t.get("raw") == surface and t.get("span")
                             and (not dependent_span or
                                  dependent_span[0] <= t["span"][0] <= t["span"][1] <= dependent_span[1])]
            token = token_matches[0] if len(token_matches) == 1 else None
            if token and target_person in {"1", "2", "3"} and target_number in {"sg", "pl"}:
                for row in _analyses(token, lang="fr"):
                    if row.get("mood") == "indicative" and row.get("tense") and row.get("person") and row.get("number"):
                        candidate_specs.append((row, row["mood"], row["tense"], target_person, target_number, ""))
        else:
            unresolved.append({"kind": kind or "AGREEMENT", "reason": "NO_SUPPORTED_CORRECTION_RULE",
                               "analysis_ref": f"agreement:{index}"})
            continue

        supported = False
        for row, mood, tense, person, number, gender in candidate_specs:
            lemma = row.get("lemma")
            if not lemma:
                continue
            replacement = realize_inflection(lemma, pos="verb", mood=mood, tense=tense,
                person=person, number=number, gender=gender, lang="fr")
            if not replacement:
                continue
            target = _target_rows(replacement, lang="fr", lemma=lemma, mood=mood,
                tense=tense, person=person or None, number=number or None, gender=gender or None)
            if not target:
                continue
            refs = agreement.get("evidence_refs") or {}
            target_token_ref = refs.get("participle_token") if kind == "ANTECEDENT_PARTICIPLE" else None
            span = (tokens.get(target_token_ref, {}).get("span") if target_token_ref else
                    next((t.get("span") for t in analysis.get("tokens", [])
                          if t.get("raw") == row.get("surface_form")), None))
            if not span:
                continue
            try:
                proposal = _source_bound_proposal(original_text=original, span=span,
                    replacement=_case_like(original[span[0]:span[1]], replacement),
                    rule_id=("fr.subject_participle_agreement.etre" if kind == "SUBJECT_PARTICIPLE"
                             else ("fr.preposed_cod_participle_agreement.avoir" if kind == "ANTECEDENT_PARTICIPLE"
                                   else "fr.subject_verb_agreement.corpus")),
                    analysis_refs=[f"agreement:{index}", row.get("source_id", "")],
                    lexical_refs=_lexical_refs([row] + target, identity),
                    rule_provenance=[{"source_rule": source_rule, "analysis_evidence": agreement.get("evidence"),
                                      "corpus_identity": identity}],
                    conditions=["native_parser_status=INCOMPATIBLE", f"target_form_attested={replacement}"],
                    uncertainties=[])
            except ValueError:
                continue
            if proposal not in proposals:
                proposals.append(proposal)
                supported = True
        if not supported:
            unresolved.append({"kind": kind, "reason": "NO_UNIQUE_ATTESTED_TARGET_FORM",
                               "analysis_ref": f"agreement:{index}"})
    return proposals, unresolved


def _english_aux_target(observed: str, person: str, number: str) -> tuple[str, str] | None:
    contracted = _CONTRACTIONS.get(observed.lower())
    if contracted:
        family, finite, negative = contracted
    else:
        finite = observed.lower()
        family = "be" if finite in _BE else "have" if finite in _HAVE else "do" if finite in _DO else ""
        negative = False
    paradigms = {"be": _BE, "have": _HAVE, "do": _DO}
    forms = paradigms.get(family, {})
    if family == "be":
        tense_forms = {"am", "is", "are"} if finite in {"am", "is", "are"} else {"was", "were"}
    elif family == "have":
        tense_forms = {"had"} if finite == "had" else {"have", "has"}
    elif family == "do":
        tense_forms = {"did"} if finite == "did" else {"do", "does"}
    else:
        return None
    candidates = sorted(form for form, cells in forms.items()
                        if form in tense_forms and (person, number) in cells)
    if len(candidates) != 1:
        return None
    target = candidates[0]
    if negative:
        contractions = sorted(surface for surface, mapping in _CONTRACTIONS.items()
                              if mapping == (family, target, True))
        if len(contractions) != 1:
            return None
        target = contractions[0]
    return target, family


def _english_proposals(original: str, analysis: dict[str, Any], identity: Any) -> tuple[list, list]:
    proposals, unresolved = [], []
    chain = analysis.get("verbal_chain") or {}
    for index, agreement in enumerate(analysis.get("agreements", [])):
        if agreement.get("status") != "INCOMPATIBLE":
            continue
        kind = agreement.get("kind")
        if kind == "AUXILIARY_COMPLEMENT" and agreement.get("expected_form") == "BASE":
            part = chain.get("lexical_part") or {}
            span = part.get("span")
            lemmas = part.get("lemma_candidates") or ([part.get("lemma")] if part.get("lemma") else [])
            if not span or not lemmas:
                unresolved.append({"kind": kind, "reason": "LEXICAL_LEMMA_UNAVAILABLE",
                                   "analysis_ref": f"agreement:{index}"})
                continue
            admitted = 0
            for lemma in dict.fromkeys(lemmas):
                # The corpus exposes base forms as surface rows; reverse realization has
                # incomplete infinitive coverage, so require the forward-attested lemma form.
                targets = [row.to_dict() for row in lookup_surface_form(lemma, lang="en")
                           if row.lemma == lemma and row.pos.lower() == "verb"
                           and row.mood.lower() == "infinitive" and row.surface_form.lower() == lemma.lower()]
                if not targets:
                    continue
                try:
                    proposal = _source_bound_proposal(original_text=original, span=span,
                        replacement=_case_like(original[span[0]:span[1]], lemma),
                        rule_id="en.base_form_after_do_or_modal",
                        analysis_refs=[f"agreement:{index}", "verbal_chain:lexical_part", f"lemma:{lemma}"],
                        lexical_refs=_lexical_refs(targets, identity),
                        rule_provenance=[{"source_rule": agreement.get("evidence"), "corpus_identity": identity}],
                        conditions=["native_parser_status=INCOMPATIBLE", "required_form=BASE",
                                    f"candidate_lemma={lemma}"],
                        uncertainties=["Multiple attested lemmas remain; no correction candidate is selected."]
                                     if len(set(lemmas)) > 1 else [])
                except ValueError:
                    unresolved.append({"kind": kind, "reason": "SOURCE_SPAN_INVALID",
                                       "analysis_ref": f"agreement:{index}"})
                    continue
                if proposal not in proposals:
                    proposals.append(proposal)
                admitted += 1
            if not admitted:
                unresolved.append({"kind": kind, "reason": "BASE_FORM_NOT_ATTESTED",
                                   "analysis_ref": f"agreement:{index}"})
        elif kind == "SUBJECT_AUXILIARY" and agreement.get("evidence") == "closed_english_auxiliary_paradigm":
            aux = chain.get("finite_auxiliary") or {}
            span = aux.get("span")
            target = _english_aux_target(agreement.get("observed_auxiliary", ""),
                str(agreement.get("expected_person", "")), str(agreement.get("expected_number", "")))
            if not span or not target:
                unresolved.append({"kind": kind, "reason": "AUXILIARY_TARGET_NOT_UNIQUE",
                                   "analysis_ref": f"agreement:{index}"})
                continue
            replacement, family = target
            target_rows = [row.to_dict() for row in lookup_surface_form(replacement, lang="en")]
            target_rows = [row for row in target_rows if row.get("source_id")]
            # Some closed-paradigm cells (notably 3pl "are") are absent in lexical data.
            # The parser's explicit closed paradigm remains the grammatical evidence.
            try:
                proposals.append(_source_bound_proposal(original_text=original, span=span,
                    replacement=_case_like(original[span[0]:span[1]], replacement),
                    rule_id="en.subject_auxiliary_agreement.closed_paradigm",
                    analysis_refs=[f"agreement:{index}", "verbal_chain:finite_auxiliary"],
                    lexical_refs=_lexical_refs(target_rows, identity),
                    rule_provenance=[{"source_rule": agreement.get("evidence"),
                        "register_scope": agreement.get("register_scope", "STANDARD_ENGLISH"),
                        "dialectal_impossibility_claimed": agreement.get("dialectal_impossibility_claimed", False),
                        "paradigm_family": family, "corpus_identity": identity}],
                    conditions=["native_parser_status=INCOMPATIBLE", "target_cell_unique_in_existing_paradigm"],
                    uncertainties=["Applies to the parser's standard-English scope; dialectal variants are not declared impossible."
                                   ] if agreement.get("register_scope") == "STANDARD_ENGLISH" else []))
            except ValueError:
                unresolved.append({"kind": kind, "reason": "SOURCE_SPAN_INVALID", "analysis_ref": f"agreement:{index}"})
        else:
            unresolved.append({"kind": kind or "AGREEMENT", "reason": "NO_SUPPORTED_CORRECTION_RULE",
                               "analysis_ref": f"agreement:{index}"})
    return proposals, unresolved


def build_grammar_correction_advisory(original_text: str, *, language: str) -> dict[str, Any]:
    """Analyze explicitly selected FR/EN input and return source-bound proposals only."""
    original = original_text if isinstance(original_text, str) else str(original_text)
    lang = str(language or "").lower()
    digest = hashlib.sha256(original.encode("utf-8")).hexdigest()
    base: dict[str, Any] = {
        "schema": SCHEMA, "language": lang, "original_text": original,
        "original_sha256": digest, "position_unit": "unicode_code_points",
        "analysis_status": "NOT_RUN", "disagreements": [], "proposals": [],
        "alternatives": [], "uncertainties": [], "analysis_provenance": {},
        "authority": "KX108_ONLY", "applied": False,
        "boundary": {"consultative": True, "applied": False,
            "decision_authority": "KX108_ONLY", "memory_write": False, "emits_action": False},
    }
    if lang not in SUPPORTED_LANGUAGES:
        base.update(status="UNSUPPORTED_LANGUAGE", uncertainties=["LANGUAGE_NOT_SUPPORTED"])
        return base
    try:
        frame = parse_utterance(original, language=lang)
        analysis = frame.structural_analysis
    except Exception as exc:  # fail closed; keep bounded diagnostic only
        base.update(status="ANALYSIS_UNAVAILABLE", uncertainties=[type(exc).__name__])
        return base
    provenance = analysis.get("provenance") or {}
    source_digest = provenance.get("source_sha256")
    if analysis.get("original") != original or analysis.get("language") != lang or source_digest != digest:
        base.update(status="ANALYSIS_INVALID", analysis_status=analysis.get("status", "UNKNOWN"),
                    uncertainties=["ANALYSIS_SOURCE_OR_PROVENANCE_MISMATCH"],
                    analysis_provenance=provenance)
        return base
    base["analysis_status"] = analysis.get("status", "UNKNOWN")
    base["analysis_provenance"] = provenance
    base["disagreements"] = [dict(row) for row in analysis.get("agreements", [])
                              if row.get("status") == "INCOMPATIBLE"]
    base["alternatives"] = [dict(row) for row in analysis.get("alternatives", [])]
    unresolved: list[dict[str, Any]] = list(analysis.get("unresolved", []))
    if lang == "fr":
        proposals, correction_unresolved = _french_proposals(original, analysis,
            provenance.get("corpus"))
    else:
        identity = provenance.get("corpus_identity")
        proposals, correction_unresolved = _english_proposals(original, analysis, identity)
    base["proposals"] = proposals
    unresolved.extend(correction_unresolved)
    if analysis.get("alternatives"):
        unresolved.extend({"kind": row.get("kind", "ALTERNATIVE"), "reason": "UNRESOLVED_ALTERNATIVE",
                           "selected": row.get("selected")}
                          for row in analysis.get("alternatives", []) if row.get("selected") is None)
    base["uncertainties"] = unresolved
    if proposals:
        base["status"] = "PROPOSALS_AVAILABLE"
    elif unresolved or base["analysis_status"] != "STRUCTURALLY_ANALYZED":
        base["status"] = "UNRESOLVED"
    else:
        base["status"] = "NO_CHANGE"
    return base
