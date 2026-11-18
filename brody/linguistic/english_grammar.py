"""Bounded English structural grammar analysis using English-only evidence.

This module is the English branch of the existing native language parser. The
current French parser has French-specific segmentation and lexical assumptions;
dispatch is explicit so English rows can never be treated as French readings.
This subset describes syntax and morphology only, not world facts or decisions.
"""
from __future__ import annotations

import hashlib
import re

from brody.linguistic.primitives import UtteranceFrame

_TOKEN = re.compile(r"[^\W\d_]+n't|[^\W_]+'|[^\W_]+|[?!.,;:]", re.UNICODE)
_SUBJECTS = {
    "i": ("1", "sg"), "we": ("1", "pl"), "you": ("2", None),
    "he": ("3", "sg"), "she": ("3", "sg"), "it": ("3", "sg"),
    "they": ("3", "pl"),
}
_BE = {
    "am": {("1", "sg")}, "is": {("3", "sg")},
    "are": {("2", "sg"), ("1", "pl"), ("2", "pl"), ("3", "pl")},
    "was": {("1", "sg"), ("3", "sg")},
    "were": {("2", "sg"), ("1", "pl"), ("2", "pl"), ("3", "pl")},
}
_HAVE = {
    "have": {("1", "sg"), ("2", "sg"), ("1", "pl"), ("2", "pl"), ("3", "pl")},
    "has": {("3", "sg")},
}
_DO = {
    "do": {("1", "sg"), ("2", "sg"), ("1", "pl"), ("2", "pl"), ("3", "pl")},
    "does": {("3", "sg")},
}
_ALL_PERSON_NUMBER = {(person, number) for person in ("1", "2", "3") for number in ("sg", "pl")}
_MODALS = {"can", "could", "will", "would", "shall", "should", "may", "might", "must"}
_DETERMINERS = {"the", "a", "an", "this", "that", "these", "those"}
_PREPOSITIONS = {"to", "in", "on", "at", "by", "for", "from", "with", "of", "into", "under", "over"}
_NEGATORS = {"not", "never", "don't", "doesn't", "didn't", "isn't", "aren't",
             "wasn't", "weren't", "haven't", "hasn't", "hadn't"}
_CONTRACTIONS = {
    "don't": ("do", "do", True), "doesn't": ("do", "does", True),
    "didn't": ("do", "did", True), "isn't": ("be", "is", True),
    "aren't": ("be", "are", True), "wasn't": ("be", "was", True),
    "weren't": ("be", "were", True), "haven't": ("have", "have", True),
    "hasn't": ("have", "has", True), "hadn't": ("have", "had", True),
}


def _lookup(word: str, language: str):
    from brody.linguistic.lexical_corpus import lookup_surface_form
    return lookup_surface_form(word, lang=language)


def parse_english_utterance(raw: str) -> UtteranceFrame:
    from brody.linguistic.lexical_corpus import corpus_identity

    identity = corpus_identity()
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    if identity.get("status") != "READY":
        return UtteranceFrame(raw=raw, normalized=raw,
            missing=("english_lexical_corpus_unavailable",),
            structural_analysis={"schema": "BRODY_STRUCTURAL_LANGUAGE_ANALYSIS_V1",
                "original": raw, "language": "en", "status": "HOLD", "tokens": [],
                "groups": [], "dependencies": [], "agreements": [],
                "unresolved": [{"kind": "RESOURCE_UNAVAILABLE", "resource": "english_lexical_corpus"}],
                "provenance": {"language_selection": "explicit_caller_argument",
                    "source_sha256": digest, "corpus_identity": identity},
                "authority": "KX108_ONLY", "verified_fact": False})

    lowered = "".join("'" if c in "’‘ʼ`´" else c.lower() for c in raw)
    matches = list(_TOKEN.finditer(lowered))
    words = [m.group() for m in matches]
    rows_by_word = {word: _lookup(word, "en") for word in set(words)}
    tokens = []
    for i, (match, word) in enumerate(zip(matches, words), 1):
        rows = rows_by_word[word]
        positions = {r.pos.lower() for r in rows}
        if word in _SUBJECTS:
            positions.add("pronoun")
        if word in _DETERMINERS:
            positions.add("determiner")
        if word in _CONTRACTIONS or word in _BE or word in _HAVE or word in _DO \
                or word in _MODALS or word in {"did", "had"}:
            positions.add("auxiliary")
        if word == "not":
            positions.add("negation")
        selected = ("PRONOUN" if word in _SUBJECTS else
                    "AUXILIARY" if "auxiliary" in positions else
                    "DETERMINER" if "determiner" in positions else
                    "NEGATION" if word == "not" else
                    "ADJECTIVE" if "adj" in positions else "UNKNOWN")
        tokens.append({"id": f"t{i}", "raw": raw[match.start():match.end()],
            "normalized": word, "span": [match.start(), match.end()],
            "nature_candidates": sorted(positions or {"UNKNOWN"}), "selected_nature": selected,
            "functions": [], "lexical_status": "ATTESTED" if rows else
                "CLOSED_CLASS" if word in (set(_SUBJECTS) | {"not", ".", "!", "?", ","}) else "UNATTESTED",
            "nature_analyses": [r.to_dict() | {"verified_fact": False} for r in rows],
            "morphological_alternatives": [{"lemma": r.lemma, "pos": r.pos,
                "mood": r.mood, "tense": r.tense, "person": r.person,
                "number": r.number, "source_id": r.source_id} for r in rows]})

    punctuation = {".", "!", "?", ",", ";", ":"}
    content_indices = [i for i, word in enumerate(words) if word not in punctuation]
    def nominal_extent(start):
        if start >= len(words):
            return None
        head_i = start + 1 if words[start] in _DETERMINERS else start
        if head_i >= len(words):
            return None
        noun_rows = [row for row in rows_by_word.get(words[head_i], ())
                     if row.pos.lower() in {"noun", "n"}]
        numbers = {row.number for row in noun_rows if row.number in {"sg", "pl"}}
        if not noun_rows or len(numbers) != 1:
            return None
        start_span = matches[start].start()
        end_span = matches[head_i].end()
        return {"start_i": start, "head_i": head_i, "end_i": head_i + 1,
                "text": raw[start_span:end_span], "span": [start_span, end_span],
                "head": words[head_i], "number": next(iter(numbers)),
                "head_token_ref": f"t{head_i + 1}",
                "morphological_analyses": [row.to_dict() for row in noun_rows]}

    def nominal_descriptor(extent):
        return {key: extent[key] for key in ("text", "span", "head", "number",
                                               "head_token_ref", "morphological_analyses")}

    def noun_phrase_after(start):
        extent = nominal_extent(start)
        if extent is None:
            return None
        if any(word not in punctuation for word in words[extent["end_i"]:]):
            return None
        return extent

    def past_participle_rows(word):
        return [row for row in _lookup(word, "en") if row.pos.lower() == "verb"
                and row.mood == "participle" and row.tense == "past"]

    def agent_after_by():
        by_i = next((i for i in range(subj_i + 1, len(words)) if words[i] == "by"), None)
        if by_i is None:
            return None
        return noun_phrase_after(by_i + 1)

    subj_i = next((i for i in content_indices if words[i] in _SUBJECTS), None)
    nominal_subject = None
    if subj_i is None:
        for start in content_indices:
            candidate = nominal_extent(start)
            if candidate is None:
                continue
            has_following_predicate = any(
                word in (set(_BE) | set(_HAVE) | set(_DO) | _MODALS | {"did", "had"})
                or any(row.pos.lower() == "verb" for row in rows_by_word.get(word, ()))
                for word in words[candidate["end_i"]:] if word not in punctuation)
            if has_following_predicate:
                nominal_subject = candidate
                subj_i = candidate["head_i"]
                break
    if subj_i is None:
        return UtteranceFrame(raw=raw, normalized=" ".join(words),
            missing=("english_subject_not_recognized",),
            structural_analysis={"schema": "BRODY_STRUCTURAL_LANGUAGE_ANALYSIS_V1",
                "original": raw, "language": "en", "status": "PARTIAL", "tokens": tokens,
                "groups": [], "dependencies": [], "agreements": [],
                "unresolved": [{"kind": "SUBJECT_UNRESOLVED"}],
                "provenance": {"language_selection": "explicit_caller_argument",
                    "source_sha256": digest, "corpus_identity": identity},
                "authority": "KX108_ONLY", "verified_fact": False})

    subject = words[subj_i] if nominal_subject is None else nominal_subject["text"]
    expected = _SUBJECTS.get(subject, ("3", nominal_subject["number"] if nominal_subject else None))
    subject_descriptor = (nominal_descriptor(nominal_subject) if nominal_subject else {
        "text": raw[matches[subj_i].start():matches[subj_i].end()],
        "span": [matches[subj_i].start(), matches[subj_i].end()], "head": subject,
        "number": expected[1], "head_token_ref": f"t{subj_i + 1}"})
    auxiliary_words = set(_BE) | set(_HAVE) | set(_DO) | set(_CONTRACTIONS) | _MODALS | {"did", "had"}
    leading_aux_i = next((i for i in range(subj_i) if words[i] in auxiliary_words), None)
    following_aux_i = next((i for i in range(subj_i + 1, len(words))
                            if words[i] in auxiliary_words), None)
    aux_word_i = leading_aux_i if leading_aux_i is not None else following_aux_i
    chain = None
    agreements = []
    alternatives = []
    negative = False
    subject_agreement = "UNKNOWN"
    active_predicate_i = None
    if aux_word_i is not None:
        surface = words[aux_word_i]
        contracted = _CONTRACTIONS.get(surface)
        if contracted:
            family, finite_surface, negative = contracted
        elif surface in _MODALS:
            family, finite_surface = "modal", surface
        else:
            family = ("be" if surface in _BE else "have" if surface in _HAVE or surface == "had"
                      else "do" if surface in _DO or surface == "did" else "")
            finite_surface = surface
        if leading_aux_i is not None:
            remainder = words[subj_i + 1:]
        else:
            remainder = words[aux_word_i + 1:]
        negative = negative or any(word in _NEGATORS or word == "not" for word in remainder)
        aux_span = tokens[aux_word_i]["span"]
        paradigms = {"be": _BE, "have": _HAVE, "do": _DO}
        observed = paradigms.get(family, {}).get(finite_surface, set())
        if finite_surface in {"did", "had"}:
            observed = _ALL_PERSON_NUMBER
        if family == "modal":
            subject_agreement = "COMPATIBLE"  # closed invariant modal in this target set
        elif expected[1] is not None and observed:
            subject_agreement = "COMPATIBLE" if expected in observed else "INCOMPATIBLE"
        if family:
            aux_lemma = surface if family == "modal" else family
            agreements.append({"kind": "SUBJECT_AUXILIARY", "subject": subject,
                "expected_person": expected[0], "expected_number": expected[1],
                "observed_auxiliary": surface, "status": subject_agreement,
                "evidence": "closed_english_auxiliary_paradigm" if family != "modal"
                            else "closed_english_invariant_modal_paradigm",
                "verified_fact": False})
            if surface == "don't":
                agreements[-1].update(register_scope="STANDARD_ENGLISH",
                                      dialectal_impossibility_claimed=False)
        else:
            aux_lemma = surface
        remainder = [word for word in remainder if word not in punctuation]
        if family == "be":
            lexical_indices = [i for i in range(aux_word_i + 1, len(words))
                               if words[i] not in punctuation and words[i] not in _NEGATORS]
            being_i = next((i for i in lexical_indices if words[i] == "being"), None)
            passive_i = (next((i for i in lexical_indices if i > being_i and past_participle_rows(words[i])), None)
                         if being_i is not None else
                         next((i for i in lexical_indices if past_participle_rows(words[i])), None))
            agent = agent_after_by() if any(words[i] == "by" for i in lexical_indices) else None
            agent_marker = next((i for i in lexical_indices if words[i] == "by"), None)
            has_passive_support = (being_i is not None or agent is not None or
                                   finite_surface in {"was", "were"})
            if passive_i is not None and has_passive_support:
                lexical = words[passive_i]
                pp_rows = past_participle_rows(lexical)
                lexical_span = [matches[passive_i].start(), matches[passive_i].end()]
                ambiguous_state = agent is None and any(row.pos.lower() in {"adj", "adjective"}
                                                        for row in _lookup(lexical, "en"))
                voice = "AMBIGUOUS" if ambiguous_state else "PASSIVE"
                chain = {"finite_auxiliary": {"surface": surface, "lemma": "be", "span": aux_span},
                    "lexical_part": {"surface": lexical,
                        "lemma": next(iter(sorted({row.lemma for row in pp_rows}))) if len({row.lemma for row in pp_rows}) == 1 else None,
                        "lemma_candidates": sorted({row.lemma for row in pp_rows}),
                        "form": "past_participle", "span": lexical_span,
                        "morphological_analyses": [row.to_dict() for row in pp_rows]},
                    "voice": voice,
                    "aspect": "PROGRESSIVE_PASSIVE" if being_i is not None else
                              "AMBIGUOUS" if ambiguous_state else "SIMPLE_PASSIVE",
                    "tense": "PAST" if finite_surface in {"was", "were"} else "PRESENT",
                    "agent": {"text": agent["text"], "span": agent["span"],
                              "head": agent["head"], "head_token_ref": agent["head_token_ref"],
                              "status": "SOURCE_BOUND"} if agent else None,
                    "patient": None if ambiguous_state else subject_descriptor,
                    "by_token_span": ([matches[agent_marker].start(), matches[agent_marker].end()]
                                      if agent_marker is not None else None)}
                if being_i is not None:
                    chain["middle_auxiliary"] = {"surface": "being", "lemma": "be", "form": "present_participle",
                        "span": [matches[being_i].start(), matches[being_i].end()]}
                if ambiguous_state:
                    alternatives.append({"kind": "PASSIVE_EVENT_OR_RESULT_STATE",
                        "span": lexical_span, "selected": None,
                        "candidates": [{"voice": "PASSIVE", "patient_candidate": subject_descriptor,
                                        "agent": None},
                                       {"voice": "COPULAR", "attribute": lexical}],
                        "verified_fact": False})
            else:
                attr = next((word for word in reversed(remainder) if word not in _NEGATORS), None)
                attr_rows = _lookup(attr, "en") if attr else ()
                participle_rows = [row for row in attr_rows if row.pos.lower() == "verb"
                                   and row.mood == "participle" and row.tense == "present"]
                adjective_rows = [row for row in attr_rows
                                  if row.pos.lower() in {"adj", "adjective"}]
                pp_rows = past_participle_rows(attr) if attr else ()
                past_verb_lemmas = {row.lemma for row in attr_rows
                                    if row.pos.lower() == "verb" and row.tense == "past"}
                pp_lemmas = {row.lemma for row in pp_rows}
                if (attr and pp_rows and adjective_rows and len(pp_lemmas) == 1
                        and past_verb_lemmas == pp_lemmas):
                    lexical_span = next((token["span"] for token in tokens
                                         if token["normalized"] == attr), None)
                    pp_lemmas = sorted(pp_lemmas)
                    adjective_lemmas = sorted({row.lemma for row in adjective_rows})
                    token_ref = next((token["id"] for token in tokens
                                      if token["span"] == lexical_span), None)
                    chain = {"finite_auxiliary": {"surface": surface, "lemma": "be", "span": aux_span},
                        "lexical_part": {"surface": attr,
                            "lemma": pp_lemmas[0] if len(pp_lemmas) == 1 else None,
                            "lemma_candidates": pp_lemmas, "form": "past_participle_or_adjective",
                            "span": lexical_span,
                            "morphological_analyses": [row.to_dict() for row in pp_rows + adjective_rows]},
                        "aspect": "AMBIGUOUS",
                        "tense": "PAST" if finite_surface in {"was", "were"} else "PRESENT",
                        "voice": "AMBIGUOUS", "agent": None, "patient": None}
                    alternatives.append({"kind": "PASSIVE_EVENT_OR_RESULT_STATE",
                        "token_ref": token_ref, "span": lexical_span, "selected": None,
                        "candidates": [{"voice": "PASSIVE", "patient_candidate": subject_descriptor,
                                        "agent": None},
                                       {"voice": "COPULAR", "attribute": attr,
                                        "lemma_candidates": adjective_lemmas}],
                        "verified_fact": False})
                elif attr and participle_rows:
                    lexical_span = next((token["span"] for token in tokens
                                         if token["normalized"] == attr), None)
                    lexical_lemmas = sorted({row.lemma for row in participle_rows})
                    chain = {"finite_auxiliary": {"surface": surface, "lemma": "be", "span": aux_span},
                        "lexical_part": {"surface": attr,
                            "lemma": lexical_lemmas[0] if len(lexical_lemmas) == 1 else None,
                            "lemma_candidates": lexical_lemmas, "form": "present_participle",
                            "span": lexical_span,
                            "morphological_analyses": [row.to_dict() for row in participle_rows]},
                        "aspect": "PROGRESSIVE",
                        "tense": "PAST" if finite_surface in {"was", "were"} else "PRESENT",
                        "voice": "ACTIVE", "agent": None, "patient": None}
                    if adjective_rows:
                        token_ref = next((token["id"] for token in tokens
                                          if token["span"] == lexical_span), None)
                        alternatives.append({"kind": "PROGRESSIVE_OR_ADJECTIVAL_PREDICATION",
                            "token_ref": token_ref, "span": lexical_span, "selected": None,
                            "candidates": [
                                {"aspect": "PROGRESSIVE", "form": "present_participle",
                                 "lemma_candidates": lexical_lemmas},
                                {"aspect": "COPULAR", "form": "adjective",
                                 "lemma_candidates": sorted({row.lemma for row in adjective_rows})}],
                            "verified_fact": False})
                elif attr and adjective_rows:
                    chain = {"finite_auxiliary": {"surface": surface, "lemma": "be", "span": aux_span},
                        "lexical_part": {"surface": attr, "lemma": attr, "form": "adjective"},
                        "aspect": "COPULAR", "tense": "PAST" if finite_surface in {"was", "were"} else "PRESENT",
                        "voice": "COPULAR", "agent": None, "patient": None}
        elif family in {"do", "modal"}:
            lexical = next((word for word in remainder if word not in _NEGATORS), None)
            lexical_rows = _lookup(lexical, "en") if lexical else ()
            verb_rows = [row for row in lexical_rows if row.pos.lower() == "verb"]
            base_rows = [row for row in verb_rows if row.mood == "infinitive"]
            if lexical and verb_rows:
                complement_status = "COMPATIBLE" if base_rows else "INCOMPATIBLE"
                lexical_lemmas = sorted({row.lemma for row in (base_rows or verb_rows)})
                lexical_span = next((token["span"] for token in tokens
                                     if token["normalized"] == lexical), None)
                chain = {"finite_auxiliary": {"surface": surface, "lemma": aux_lemma, "span": aux_span},
                    "lexical_part": {"surface": lexical,
                        "lemma": lexical_lemmas[0] if len(lexical_lemmas) == 1 else None,
                        "lemma_candidates": lexical_lemmas, "form": "base" if base_rows else "non_base_after_operator",
                        "span": lexical_span, "morphological_analyses": [row.to_dict() for row in verb_rows]},
                    "aspect": "MODAL" if family == "modal" else "SIMPLE",
                    "tense": "MODAL" if family == "modal" else "PAST" if finite_surface == "did" else "PRESENT"}
                agreements.append({"kind": "AUXILIARY_COMPLEMENT", "auxiliary": surface,
                    "complement": lexical, "status": complement_status,
                    "expected_form": "BASE", "observed_forms": sorted({row.mood for row in verb_rows}),
                    "evidence": "english_base_form_after_do_or_modal", "verified_fact": False})
        elif family == "have":
            if remainder[:1] == ["been"] and len(remainder) > 1 and past_participle_rows(remainder[1]):
                lexical = remainder[1]
                pp_rows = past_participle_rows(lexical)
                lexical_index = next((i for i in range(aux_word_i + 1, len(words))
                                      if words[i] == lexical), None)
                agent = agent_after_by()
                adjective_rows = [row for row in _lookup(lexical, "en")
                                  if row.pos.lower() in {"adj", "adjective"}]
                ambiguous_state = agent is None and bool(adjective_rows)
                lexical_span = ([matches[lexical_index].start(), matches[lexical_index].end()]
                                if lexical_index is not None else None)
                by_marker_i = next((i for i in range(aux_word_i + 1, len(words))
                                    if words[i] == "by"), None)
                chain = {"finite_auxiliary": {"surface": surface, "lemma": "have", "span": aux_span},
                    "middle_auxiliary": {"surface": "been", "lemma": "be", "form": "past_participle",
                        "span": [matches[aux_word_i + 1].start(), matches[aux_word_i + 1].end()]},
                    "lexical_part": {"surface": lexical,
                        "lemma": next(iter(sorted({row.lemma for row in pp_rows}))) if len({row.lemma for row in pp_rows}) == 1 else None,
                        "lemma_candidates": sorted({row.lemma for row in pp_rows}),
                        "form": "past_participle", "span": lexical_span,
                        "morphological_analyses": [row.to_dict() for row in pp_rows]},
                    "voice": "AMBIGUOUS" if ambiguous_state else "PASSIVE",
                    "aspect": "AMBIGUOUS" if ambiguous_state else "PERFECT_PASSIVE",
                    "tense": "PAST" if finite_surface == "had" else "PRESENT",
                    "agent": {"text": agent["text"], "span": agent["span"],
                              "head": agent["head"], "head_token_ref": agent["head_token_ref"],
                              "status": "SOURCE_BOUND"} if agent else None,
                    "patient": None if ambiguous_state else subject_descriptor,
                    "by_token_span": ([matches[by_marker_i].start(), matches[by_marker_i].end()]
                                      if by_marker_i is not None else None)}
                if ambiguous_state:
                    alternatives.append({"kind": "PASSIVE_EVENT_OR_RESULT_STATE",
                        "span": lexical_span, "selected": None,
                        "candidates": [{"voice": "PASSIVE", "patient_candidate": subject_descriptor,
                                        "agent": None},
                                       {"voice": "COPULAR", "attribute": lexical}],
                        "verified_fact": False})
            elif remainder[:1] == ["been"] and len(remainder) > 1:
                lexical = remainder[1]
                lexical_rows = _lookup(lexical, "en")
                lemmas = {row.lemma for row in lexical_rows if row.pos.lower() == "verb"
                          and row.mood == "participle" and row.tense == "present"}
                if lemmas:
                    chain = {"finite_auxiliary": {"surface": surface, "lemma": "have", "span": aux_span},
                        "middle_auxiliary": {"surface": "been", "lemma": "be", "form": "past_participle"},
                        "lexical_part": {"surface": lexical, "lemma": next(iter(lemmas)) if len(lemmas) == 1 else None,
                                         "lemma_candidates": sorted(lemmas), "form": "present_participle"},
                        "aspect": "PERFECT_PROGRESSIVE", "tense": "PRESENT"}
            else:
                lexical = next((word for word in remainder if word not in _NEGATORS), None)
                lexical_rows = _lookup(lexical, "en") if lexical else ()
                participles = [row for row in lexical_rows if row.pos.lower() == "verb"
                               and row.mood == "participle" and row.tense == "past"]
                if lexical and participles:
                    lemmas = sorted({row.lemma for row in participles})
                    lexical_span = next((token["span"] for token in tokens
                                         if token["normalized"] == lexical), None)
                    chain = {"finite_auxiliary": {"surface": surface, "lemma": "have", "span": aux_span},
                        "lexical_part": {"surface": lexical,
                            "lemma": lemmas[0] if len(lemmas) == 1 else None,
                            "lemma_candidates": lemmas, "form": "past_participle", "span": lexical_span,
                            "morphological_analyses": [row.to_dict() for row in participles]},
                        "aspect": "PERFECT", "tense": "PAST" if finite_surface == "had" else "PRESENT"}

    if chain is None and aux_word_i is None:
        candidate_i = next((i for i in range(subj_i + 1, len(words))
            if any(row.pos.lower() == "verb" and row.mood in {"indicative", "infinitive"}
                   for row in rows_by_word.get(words[i], ()))), None)
        if candidate_i is not None:
            lexical = words[candidate_i]
            lexical_rows = [row for row in rows_by_word.get(lexical, ()) if row.pos.lower() == "verb"]
            present_rows = [row for row in lexical_rows if row.mood == "indicative" and row.tense == "present"]
            past_rows = [row for row in lexical_rows if row.mood == "indicative" and row.tense == "past"]
            base_rows = [row for row in lexical_rows if row.mood == "infinitive"]
            finite_rows = present_rows or past_rows
            lexical_span = tokens[candidate_i]["span"]
            lemmas = sorted({row.lemma for row in (finite_rows or base_rows or lexical_rows)})
            tense_candidates = []
            if present_rows:
                tense_candidates = ["PRESENT"]
                pairs = {(row.person, row.number) for row in present_rows if row.person and row.number}
                status = ("COMPATIBLE" if expected in pairs else "INCOMPATIBLE") if pairs else "UNKNOWN"
            elif past_rows and base_rows:
                tense_candidates = ["PAST", "PRESENT"] if expected[0] != "3" or expected[1] != "sg" else ["PAST"]
                status = "COMPATIBLE" if len(tense_candidates) > 1 else "UNKNOWN"
            elif past_rows:
                tense_candidates = ["PAST"]
                status = "COMPATIBLE"  # English simple past is invariant for person/number.
            elif base_rows:
                tense_candidates = ["PRESENT"]
                status = "INCOMPATIBLE" if expected == ("3", "sg") else "COMPATIBLE"
            else:
                status = "UNKNOWN"
            if lexical_rows:
                chain = {"finite_verb": {"surface": lexical, "lemma": lemmas[0] if len(lemmas) == 1 else None,
                                         "lemma_candidates": lemmas, "span": lexical_span},
                    "lexical_part": {"surface": lexical, "lemma": lemmas[0] if len(lemmas) == 1 else None,
                                     "form": "FINITE" if finite_rows else "BASE_FORM",
                                     "span": lexical_span,
                                     "morphological_analyses": [row.to_dict() for row in lexical_rows]},
                    "aspect": "SIMPLE", "tense": tense_candidates[0] if len(tense_candidates) == 1 else "AMBIGUOUS"}
                active_predicate_i = candidate_i
                if len(tense_candidates) > 1:
                    chain["tense_candidates"] = tense_candidates
                    alternatives.append({"kind": "TENSE_AMBIGUITY", "span": lexical_span,
                        "token_ref": f"t{candidate_i + 1}", "selected": None,
                        "candidates": tense_candidates, "verified_fact": False})
                agreements.append({"kind": "SUBJECT_VERB", "subject": subject,
                    "expected_person": expected[0], "expected_number": expected[1],
                    "observed_verb": lexical, "status": status,
                    "evidence": "english_corpus_finite_or_base_form_and_closed_subject_agreement",
                    "verified_fact": False})

    if chain is not None and aux_word_i is None and active_predicate_i is not None:
        object_extent = noun_phrase_after(active_predicate_i + 1)
        if object_extent is not None:
            chain["voice"] = "ACTIVE"
            chain["patient"] = nominal_descriptor(object_extent)
            chain["direct_object"] = nominal_descriptor(object_extent)
            chain["agent"] = subject_descriptor
    unresolved = []
    if chain is not None and active_predicate_i is not None:
        tail = [word for word in words[active_predicate_i + 1:] if word not in punctuation]
        if tail and tail[0] not in _PREPOSITIONS and chain.get("patient") is None:
            unresolved.append({"kind": "NOMINAL_ARGUMENT_UNRESOLVED",
                               "source_span": [matches[active_predicate_i + 1].start(),
                                               matches[-1].end()]})

    if chain is not None:
        unselected_token_refs = {row.get("token_ref") for row in alternatives
                                 if row.get("selected") is None and row.get("token_ref")}
        chain.setdefault("voice", "ACTIVE")
        chain.setdefault("agent", None)
        chain.setdefault("patient", None)
        chain.update(language="en", subject=subject, grammatical_subject=subject_descriptor, negative=negative,
            agreement=subject_agreement if chain.get("finite_auxiliary") else
                      next((row["status"] for row in agreements if row["kind"] == "SUBJECT_VERB"), "UNKNOWN"),
            source_text=raw, verified_fact=False, authority="KX108_ONLY", selected_referent=None)
        if chain.get("finite_auxiliary"):
            aux_surface = chain["finite_auxiliary"]["surface"]
            aux_span = chain["finite_auxiliary"]["span"]
            for token in tokens:
                if token["span"] == aux_span:
                    token["selected_nature"] = "AUXILIARY"
                    token["functions"].append("FINITE_AUXILIARY")
        if chain.get("finite_verb"):
            finite_span = chain["finite_verb"]["span"]
            for token in tokens:
                if token["span"] == finite_span:
                    token["selected_nature"] = "VERB"
                    token["functions"].append("FINITE_PREDICATE")
        if chain.get("middle_auxiliary"):
            for token in tokens:
                if token["normalized"] == chain["middle_auxiliary"]["surface"]:
                    token["selected_nature"] = "AUXILIARY"
                    token["functions"].append("AUXILIARY_PARTICIPLE")
        for token in tokens:
            if chain.get("lexical_part", {}).get("span") == token["span"] or (
                    chain.get("lexical_part", {}).get("span") is None
                    and token["normalized"] == chain["lexical_part"]["surface"]):
                if token["id"] in unselected_token_refs:
                    token["selected_nature"] = "UNKNOWN"
                    continue
                part_form = chain["lexical_part"]["form"]
                if part_form not in {"adjective"}:
                    token["selected_nature"] = "VERB"
                    token["functions"].append("LEXICAL_PARTICIPLE" if "participle" in part_form
                                               else "LEXICAL_PREDICATE")
            if token["normalized"] in _NEGATORS:
                token["functions"].append("NEGATION")
    if chain is None:
        status = "PARTIAL"
        groups = [{"id": "g1", "kind": "UTTERANCE", "span": [0, len(raw)],
                   "raw": raw, "function": "UTTERANCE", "status": "GROUNDED_IN_SOURCE"}]
        dependencies = []
        unresolved = [{"kind": "VERBAL_CHAIN_UNRESOLVED", "source_span": [0, len(raw)]}]
    else:
        status = "PARTIAL" if unresolved else "STRUCTURALLY_ANALYZED"
        start = (matches[leading_aux_i].start() if leading_aux_i is not None else
                 matches[nominal_subject["start_i"]].start() if nominal_subject else matches[subj_i].start())
        end = len(raw.rstrip(".!?;:"))
        groups = [{"id": "g1", "kind": "UTTERANCE", "span": [0, len(raw)], "raw": raw,
                   "function": "UTTERANCE", "status": "GROUNDED_IN_SOURCE"},
                  {"id": "g2", "kind": "CLAUSE", "span": [start, end], "raw": raw[start:end],
                   "function": "CLAUSE", "parent": "g1", "status": status},
                  {"id": "g3", "kind": "VERBAL_CHAIN", "span": [start, end], "raw": raw[start:end],
                   "function": "VERBAL_CHAIN", "parent": "g2", "status": status,
                   "verbal_chain": chain}]
        if nominal_subject:
            subject_group = {"id": "g4", "kind": "NP", "span": subject_descriptor["span"],
                "raw": subject_descriptor["text"], "head": subject_descriptor["head"],
                "head_token_ref": subject_descriptor["head_token_ref"],
                "function": "GRAMMATICAL_SUBJECT", "parent": "g2", "children": [],
                "predicate_ref": None, "status": "SOURCE_BOUND", "verified_fact": False}
            groups.append(subject_group)
            dependencies = [{"relation": "SUBJECT", "head": "g3", "dependent": subject_group["id"],
                             "source_rule": "english_written_nominal_subject"}]
            head_index = nominal_subject["head_i"]
            tokens[head_index]["selected_nature"] = "NOUN"
            tokens[head_index]["functions"].append("NOMINAL_HEAD")
            if nominal_subject["start_i"] != head_index:
                det_token = tokens[nominal_subject["start_i"]]
                det_token["selected_nature"] = "DETERMINER"
                det_token["functions"].append("NOMINAL_DETERMINER")
        else:
            dependencies = [{"relation": "SUBJECT", "head": "g3", "dependent": f"t{subj_i + 1}",
                             "source_rule": "english_written_subject_pronoun"}]
            subject_group = None
        role_groups = {}
        if chain.get("voice") == "PASSIVE" and chain.get("patient"):
            role_groups["patient"] = subject_group["id"] if subject_group else f"t{subj_i + 1}"
            dependencies.append({"relation": "PATIENT", "head": "g3", "dependent": role_groups["patient"],
                                 "source_rule": "english_be_past_participle_passive"})
        if chain.get("voice") == "ACTIVE" and chain.get("agent") and chain.get("patient"):
            role_groups["agent"] = subject_group["id"] if subject_group else f"t{subj_i + 1}"
            dependencies.append({"relation": "AGENT", "head": "g3", "dependent": role_groups["agent"],
                                 "source_rule": "english_active_subject_agent"})
        if chain.get("agent") and chain.get("voice") == "PASSIVE":
            agent_desc = chain["agent"]
            agent_group = {"id": "g" + str(len(groups) + 1), "kind": "NP", "span": agent_desc["span"],
                "raw": agent_desc["text"], "head": agent_desc["head"],
                "head_token_ref": agent_desc["head_token_ref"], "function": "AGENT", "parent": "g2",
                "children": [], "predicate_ref": None, "status": "SOURCE_BOUND", "verified_fact": False}
            groups.append(agent_group)
            dependencies.append({"relation": "AGENT", "head": "g3", "dependent": agent_group["id"],
                                 "source_rule": "english_by_phrase_agent"})
            agent_index = int(agent_desc["head_token_ref"][1:]) - 1
            tokens[agent_index]["selected_nature"] = "NOUN"
            tokens[agent_index]["functions"].append("NOMINAL_HEAD")
            by_span = chain.get("by_token_span")
            if by_span:
                by_token = next((token for token in tokens if token["span"] == by_span), None)
                if by_token:
                    by_token["selected_nature"] = "PREPOSITION"
                    by_token["functions"].append("AGENT_MARKER")
        if chain.get("voice") == "ACTIVE" and chain.get("patient"):
            patient_desc = chain["patient"]
            patient_group = {"id": "g" + str(len(groups) + 1), "kind": "NP", "span": patient_desc["span"],
                "raw": patient_desc["text"], "head": patient_desc["head"],
                "head_token_ref": patient_desc["head_token_ref"], "function": "DIRECT_OBJECT", "parent": "g2",
                "children": [], "predicate_ref": None, "status": "SOURCE_BOUND", "verified_fact": False}
            groups.append(patient_group)
            dependencies.append({"relation": "DIRECT_OBJECT", "head": "g3", "dependent": patient_group["id"],
                                 "source_rule": "english_active_object_np"})
            dependencies.append({"relation": "PATIENT", "head": "g3", "dependent": patient_group["id"],
                                 "source_rule": "english_active_direct_object_patient"})
            object_index = int(patient_desc["head_token_ref"][1:]) - 1
            tokens[object_index]["selected_nature"] = "NOUN"
            tokens[object_index]["functions"].append("NOMINAL_HEAD")
    return UtteranceFrame(raw=raw, normalized=" ".join(words),
        missing=tuple(item["kind"] for item in unresolved),
        structural_analysis={"schema": "BRODY_STRUCTURAL_LANGUAGE_ANALYSIS_V1",
            "original": raw, "language": "en", "status": status, "tokens": tokens,
            "groups": groups, "dependencies": dependencies, "agreements": agreements,
            "unresolved": unresolved, "verbal_chain": chain, "alternatives": alternatives,
            "surface_act": "interrogative" if raw.rstrip().endswith("?") else "declarative",
            "provenance": {"language_selection": "explicit_caller_argument",
                "source_sha256": digest, "corpus_identity": identity,
                "analysis_sources": "english_only_corpus_rows_and_closed_auxiliary_paradigm"},
            "authority": "KX108_ONLY", "verified_fact": False,
            "boundary": {"readonly": True, "decision_authority": "KX108_ONLY",
                "memory_write": False, "emits_act": False}})
