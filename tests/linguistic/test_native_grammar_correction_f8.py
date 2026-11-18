"""F8 consultative grammar-correction contract tests."""

from __future__ import annotations

import hashlib
from types import SimpleNamespace

import pytest

from brody.linguistic.native_grammar_correction import (
    build_grammar_correction_advisory,
)


@pytest.mark.parametrize(
    ("text", "language", "replacement"),
    [
        ("Elle est parti.", "fr", "partie"),
        ("Elles sont arriv\u00e9.", "fr", "arriv\u00e9es"),
        ("Les portes sont ouvert.", "fr", "ouvertes"),
        ("Nous mange.", "fr", "mangeons"),
        ("She don't know.", "en", "doesn't"),
        ("They is ready.", "en", "are"),
        ("Did he went?", "en", "go"),
        ("He can swims.", "en", "swim"),
        ("She have eaten.", "en", "has"),
    ],
)
def test_demonstrated_mismatch_produces_source_bound_advisory(text, language, replacement):
    receipt = build_grammar_correction_advisory(text, language=language)
    assert receipt["schema"] == "BRODY_NATIVE_GRAMMAR_CORRECTION_ADVISORY_V0"
    assert receipt["original_text"] == text
    assert receipt["original_sha256"] == hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert receipt["authority"] == "KX108_ONLY"
    assert receipt["applied"] is False
    assert receipt["status"] == "PROPOSALS_AVAILABLE"
    assert any(row["replacement"] == replacement for row in receipt["proposals"])
    for proposal in receipt["proposals"]:
        start, end = proposal["span"]
        assert text[start:end] == proposal["original_fragment"]
        assert proposal["rule_id"]
        assert proposal["analysis_refs"]
        assert proposal["rule_provenance"]


@pytest.mark.parametrize(
    ("text", "language"),
    [
        ("Elle est partie.", "fr"),
        ("Les portes sont ouvertes.", "fr"),
        ("La porte est ouverte.", "fr"),
        ("Les lettres qu'elle a \u00e9crites.", "fr"),
        ("Elles se sont parl\u00e9.", "fr"),
        ("She doesn't know.", "en"),
        ("They are ready.", "en"),
        ("Did he go?", "en"),
        ("He can swim.", "en"),
    ],
)
def test_no_demonstrated_mismatch_means_no_correction(text, language):
    receipt = build_grammar_correction_advisory(text, language=language)
    assert receipt["proposals"] == []
    assert receipt["applied"] is False
    assert receipt["original_text"] == text


def test_ambiguous_english_reading_is_not_rewritten():
    receipt = build_grammar_correction_advisory("You read it.", language="en")
    assert receipt["proposals"] == []
    assert receipt["status"] == "UNRESOLVED"
    assert receipt["uncertainties"]


def test_unsupported_language_is_refused_without_rewrite():
    receipt = build_grammar_correction_advisory("Elle est parti.", language="de")
    assert receipt["status"] == "UNSUPPORTED_LANGUAGE"
    assert receipt["proposals"] == []
    assert receipt["original_text"] == "Elle est parti."


def test_unicode_offsets_are_code_points_and_preserve_apostrophes():
    text = "She don't know about caf\u00e9."
    receipt = build_grammar_correction_advisory(text, language="en")
    proposal = next(row for row in receipt["proposals"] if row["original_fragment"] == "don't")
    start, end = proposal["span"]
    assert text[start:end] == "don't"
    assert receipt["position_unit"] == "unicode_code_points"


def test_bad_source_span_is_rejected_not_rebased():
    from brody.linguistic.native_grammar_correction import _source_bound_proposal

    with pytest.raises(ValueError):
        _source_bound_proposal(
            original_text="She don't know.", span=[99, 104], replacement="doesn't",
            rule_id="test", analysis_refs=["a1"], lexical_refs=[], rule_provenance=[],
            conditions=[], uncertainties=[],
        )


def test_original_parser_provenance_and_authority_are_retained():
    receipt = build_grammar_correction_advisory("Elle est parti.", language="fr")
    assert receipt["analysis_provenance"]["source_sha256"] == receipt["original_sha256"]
    assert receipt["authority"] == "KX108_ONLY"
    assert receipt["boundary"] == {
        "consultative": True, "applied": False, "decision_authority": "KX108_ONLY",
        "memory_write": False, "emits_action": False,
    }


def test_unattested_target_form_stays_unresolved(monkeypatch):
    import brody.linguistic.native_grammar_correction as correction

    text = "He can swims."
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    analysis = {
        "schema": "BRODY_STRUCTURAL_LANGUAGE_ANALYSIS_V1", "original": text,
        "language": "en", "status": "STRUCTURALLY_ANALYZED",
        "provenance": {"source_sha256": digest, "corpus_identity": {"status": "READY"}},
        "agreements": [{"kind": "AUXILIARY_COMPLEMENT", "status": "INCOMPATIBLE",
                        "expected_form": "BASE", "evidence": "english_base_form_after_do_or_modal"}],
        "alternatives": [], "unresolved": [],
        "verbal_chain": {"lexical_part": {"surface": "swims", "lemma_candidates": ["not-in-corpus"],
                                             "span": [7, 12], "form": "non_base_after_operator"}},
    }
    monkeypatch.setattr(correction, "parse_utterance",
                        lambda raw, language: SimpleNamespace(structural_analysis=analysis))
    receipt = correction.build_grammar_correction_advisory(text, language="en")
    assert receipt["proposals"] == []
    assert receipt["status"] == "UNRESOLVED"


def test_multiple_attested_lexical_readings_remain_separate_proposals(monkeypatch):
    import brody.linguistic.native_grammar_correction as correction

    text = "He can swims."
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    analysis = {
        "schema": "BRODY_STRUCTURAL_LANGUAGE_ANALYSIS_V1", "original": text,
        "language": "en", "status": "STRUCTURALLY_ANALYZED",
        "provenance": {"source_sha256": digest, "corpus_identity": {"status": "READY"}},
        "agreements": [{"kind": "AUXILIARY_COMPLEMENT", "status": "INCOMPATIBLE",
                        "expected_form": "BASE", "evidence": "english_base_form_after_do_or_modal"}],
        "alternatives": [{"kind": "LEXICAL_AMBIGUITY", "selected": None,
                          "candidates": ["go", "swim"]}], "unresolved": [],
        "verbal_chain": {"lexical_part": {"surface": "swims", "lemma_candidates": ["go", "swim"],
                                             "span": [7, 12], "form": "non_base_after_operator"}},
    }
    monkeypatch.setattr(correction, "parse_utterance",
                        lambda raw, language: SimpleNamespace(structural_analysis=analysis))
    receipt = correction.build_grammar_correction_advisory(text, language="en")
    assert {row["replacement"] for row in receipt["proposals"]} == {"go", "swim"}
    assert all(row["uncertainties"] for row in receipt["proposals"])
    assert receipt["alternatives"][0]["selected"] is None
    assert receipt["uncertainties"]
