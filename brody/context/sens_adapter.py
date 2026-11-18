"""B6 SENS -> working state: one SENS_FRAME entry per utterance, open meaning kept open.

Uses the canonical SENS APIs only (parse_utterance, governable_summary, semantic_closure);
app/semantic/lattice is never modified. SENS CLOSED does not mean every utterance is closed:
missing content, ambiguities, unresolved references, contradictions and closure reasons
(including the frozen D1-D5 limits) are copied as uncertainty, never resolved. A requested
world action is described, never authorized.

R1: payload["semantic_frame"] is an exhaustive, deterministic serialization of EVERY canonical
dataclass field of the frame (walked dynamically, so a field SENS adds later is never dropped by
this adapter). Values are converted without reinterpretation (dataclass -> mapping of all its
fields, Enum -> value, tuple -> list); a value that cannot be converted strictly makes the whole
entry an explicit ERROR, never a silent omission.
"""
from __future__ import annotations

import dataclasses
from enum import Enum
from typing import Any

from brody.context.contracts import StateEntry, StateStatus, Visibility, error_entry
from brody.linguistic.french_grammar import parse_utterance
from brody.linguistic.ir_projection import governable_summary
from brody.linguistic.semantic_closure import semantic_closure


def serialize_frame(value: Any) -> Any:
    """Exhaustive strict conversion of a SENS value (no field selection, no interpretation)."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: serialize_frame(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, Enum):
        return serialize_frame(value.value)
    if isinstance(value, (list, tuple)):
        return [serialize_frame(v) for v in value]
    if isinstance(value, dict):
        if not all(isinstance(k, str) for k in value):
            raise ValueError("non-string key in a SENS mapping")
        return {k: serialize_frame(v) for k, v in value.items()}
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    raise ValueError(f"unserializable SENS value of type {type(value).__name__}")


def _source_bound_ambiguity_markers(raw: str, semantic_frame: dict[str, Any]) -> tuple[str, ...]:
    """Project only P1's validated, unselected source-bound ambiguities for B7.

    This is an information-preservation bridge, not reference resolution. Any absent,
    malformed, or provenance-inconsistent evidence yields no marker; it never guesses.
    P1's digest is an internal source-consistency check, not a cryptographic authority proof.
    """
    try:
        from brody.linguistic.communication import digest

        communication = semantic_frame.get("structural_analysis", {}).get("communication")
        if not isinstance(communication, dict):
            return ()
        expected_digest = digest(raw)
        provenance = communication.get("provenance")
        if (communication.get("schema") != "BRODY_COMMUNICATION_STRUCTURE_V0"
                or communication.get("original_expression") != raw
                or not isinstance(provenance, dict)
                or provenance.get("source") != "EXISTING_P1_STRUCTURAL_ANALYSIS"
                or provenance.get("raw_sha256") != expected_digest):
            return ()

        mentions_list = communication.get("mentions")
        references = communication.get("references")
        units_list = semantic_frame.get("units")
        if not isinstance(mentions_list, list) or not isinstance(references, list) or not isinstance(units_list, list):
            return ()
        mentions = {m.get("id"): m for m in mentions_list if isinstance(m, dict)}
        if len(mentions) != len(mentions_list):
            return ()
        units = {u.get("id"): u for u in units_list if isinstance(u, dict)}
        if len(units) != len(units_list):
            return ()

        markers: list[str] = []
        for ref in references:
            if not isinstance(ref, dict):
                continue
            mention = mentions.get(ref.get("mention_ref"))
            if not isinstance(mention, dict) or mention.get("function") != "SUBJECT":
                continue
            binding = ref.get("reference_binding")
            if not isinstance(binding, dict):
                continue
            # Already-bound and merely unresolved references are not ambiguities.
            if binding.get("status") != "AMBIGUOUS":
                continue

            span = mention.get("span")
            predicate_ref = mention.get("predicate_ref")
            unit = units.get(predicate_ref)
            binding_provenance = binding.get("provenance")
            if (not isinstance(span, list) or len(span) != 2
                    or any(type(n) is not int for n in span)
                    or span[0] < 0 or span[0] >= span[1] or span[1] > len(raw)
                    or raw[span[0]:span[1]] != mention.get("text")
                    or ref.get("scope_ref") != mention.get("scope_ref")
                    or ref.get("deictic_scope_ref") != binding.get("deictic_scope_ref")
                    or binding.get("scope_ref") != ref.get("scope_ref")
                    or not isinstance(unit, dict)
                    or str(unit.get("subject", "")).casefold() != str(mention.get("text", "")).casefold()
                    or unit.get("subject_ref") is not None
                    or not isinstance(binding_provenance, dict)
                    or binding_provenance.get("raw_sha256") != expected_digest
                    or binding.get("schema") != "BRODY_SOURCE_BOUND_REFERENCE_V0"
                    or binding.get("referents") != []
                    or binding.get("semantic_resolution") is not False
                    or binding.get("verified_fact") is not False
                    or binding.get("identity_authenticated") is not False
                    or binding.get("original_reference_unchanged") is not True
                    or ref.get("status") != "OPEN_CANDIDATES"
                    or ref.get("selected_ref") is not None
                    or ref.get("semantic_resolution") is not False
                    or ref.get("verified_fact") is not False
                    or ref.get("original_reference_unchanged") is not True):
                continue

            candidate_ids = ref.get("candidate_refs")
            if (not isinstance(candidate_ids, list) or len(candidate_ids) < 2
                    or any(not isinstance(candidate, str) or not candidate for candidate in candidate_ids)
                    or len(set(candidate_ids)) != len(candidate_ids)):
                continue
            candidate_mentions = [mentions.get(candidate) for candidate in candidate_ids]
            if any(not isinstance(candidate, dict)
                   or candidate.get("scope_ref") != mention.get("scope_ref")
                   or not candidate.get("group_ref")
                   or not isinstance(candidate.get("span"), list)
                   or len(candidate["span"]) != 2
                   or any(type(n) is not int for n in candidate["span"])
                   or candidate["span"][0] < 0
                   or candidate["span"][0] >= candidate["span"][1]
                   or candidate["span"][1] > len(raw)
                   or raw[candidate["span"][0]:candidate["span"][1]] != candidate.get("text")
                   or candidate["span"][1] > span[0]
                   for candidate in candidate_mentions):
                continue

            markers.append(
                f"ambiguous_antecedent:{predicate_ref}:{mention['text']}:" + ",".join(candidate_ids)
            )
        return tuple(dict.fromkeys(markers))
    except (AttributeError, KeyError, TypeError, ValueError, IndexError):
        return ()


def sens_state_entries(text: str, state_id: str = "sens:frame", *, context=None, previous_contextual=None,
                       language: str = "fr") -> tuple[StateEntry, ...]:
    source_ref = "brody.linguistic.french_grammar.parse_utterance"
    try:
        frame = parse_utterance(text, language=language)
        summary = governable_summary(frame)
        closure = semantic_closure(frame)
    except Exception as exc:          # a failed parse stays visible, never silent
        return (error_entry(state_id, source_ref, exc, state_type="SENS_FRAME_ERROR"),)
    is_open = not closure.closed or not frame.closure
    try:
        semantic_frame = serialize_frame(frame)
    except ValueError as exc:
        return (error_entry(state_id, source_ref, exc, state_type="SENS_FRAME_ERROR"),)
    reference_ambiguities = _source_bound_ambiguity_markers(frame.raw, semantic_frame)
    canonical_ambiguities = tuple(dict.fromkeys([*frame.ambiguities, *reference_ambiguities]))
    open_items = [*frame.missing, *canonical_ambiguities, *frame.unresolved_references,
                  *frame.contradictions, *closure.reasons]
    payload = {
        "semantic_frame": semantic_frame,
        "raw": frame.raw,
        "units": summary["units"],
        "relations": summary["relations"],
        "coordinations": summary["coordinations"],
        "requested_world_actions": summary["requested_world_actions"],
        "requested_is_authorized": False,
        "missing": list(frame.missing),
        "ambiguities": list(canonical_ambiguities),
        "unresolved_references": list(frame.unresolved_references),
        "contradictions": list(frame.contradictions),
        "frame_closure": frame.closure,
        "semantic_closure": {"closed": closure.closed, "reasons": list(closure.reasons)},
    }
    tags = {"sens", *(u.lemma for u in frame.units if u.lemma)}
    if is_open:
        tags.add("sens_open")
    if summary["requested_world_actions"]:
        tags.add("requested_action")
    try:
        entry = StateEntry(state_id=state_id, state_type="SENS_FRAME", source_ref=source_ref, payload=payload,
                       provenance=(source_ref, "brody.linguistic.semantic_closure"),
                       uncertainty=tuple(dict.fromkeys(open_items)),
                       status=StateStatus.OPEN if is_open else StateStatus.KNOWN,
                       visibility=Visibility.LONG, tags=tuple(sorted(tags)),
                       summary=f"SENS frame: {len(frame.units)} unit(s), "
                               f"{'open' if is_open else 'closed'}")
    except ValueError as exc:          # over-bound or non-strict content: explicit error, never dropped
        return (error_entry(state_id, source_ref, exc, state_type="SENS_FRAME_ERROR"),)
    if context is not None or previous_contextual is not None:
        return (entry,contextual_sens_entry(frame,context=context,previous=previous_contextual,state_id=state_id+':contextual'))
    return (entry,)


def contextual_sens_entry(frame, *, context=None, previous=None, state_id='sens:contextual'):
    """A separate OPEN interpretation entry: never trusted B7 or world truth.

    Accepting an already parsed frame avoids a second parse or any retrieval.
    Bounds/errors stay in the existing StateEntry contract.
    """
    source_ref='brody.linguistic.review_join_v1.contextualize_review'
    try:
        from brody.linguistic.review_join_v1 import contextualize_review
        view=contextualize_review(frame,context=context,previous=previous).to_dict()
        snap=view['snapshot']
        uncertainty=tuple(dict.fromkeys([*snap['original_closure_blockers'],
            *snap['original_semantic_reasons'],'EXPLORATORY_CONTEXT_NOT_WORLD_PROOF']))
        return StateEntry(state_id=state_id,state_type='SENS_CONTEXTUAL_VIEW',source_ref=source_ref,
            payload=view,provenance=(source_ref,),uncertainty=uncertainty,status=StateStatus.OPEN,
            visibility=Visibility.LONG,tags=('sens','sens_open','contextual_meaning'),
            summary='Situated readings; local selection is neither truth nor authority')
    except (ValueError,TypeError,KeyError,OverflowError) as exc:
        return error_entry(state_id,source_ref,exc,state_type='SENS_CONTEXTUAL_VIEW_ERROR')
