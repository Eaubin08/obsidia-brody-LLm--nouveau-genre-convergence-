"""Targeted native FR/EN grammar analysis contracts with UTF-8 source text."""

import hashlib

import pytest

from brody.linguistic.french_grammar import parse_utterance


def _groups(frame, function):
    return [group for group in frame.structural_analysis["groups"] if group["function"] == function]


def _subject_verb_status(frame):
    return [item["status"] for item in frame.structural_analysis["agreements"]
            if item["kind"] == "SUBJECT_VERB"]


@pytest.mark.parametrize(
    ("text", "digest"),
    [
        ("Nous est prêts.", "fbd4f23c0231c32fb323b0093a85a1e9665ea14ee13146cd7c56aa78227544e1"),
        ("Elle sont partie.", "6852c43e8bb9944bd5e9fbb52c1f7a6d1019b58c3086fa50b44be3d1f70d7a40"),
        ("Je suis prêt.", "521b47db0c86f4fb2317ad33f7897422985901e4a862f0b0c5bfb2f9de42b74c"),
        ("Nous avons été prêts.", "ab1561db5b89763b01696f8278eafa1ca6a3054f07450ce0dabe43e34cf5dfa2"),
    ],
)
def test_french_unicode_transport_and_source_preservation(text, digest):
    assert hashlib.sha256(text.encode("utf-8")).hexdigest() == digest
    frame = parse_utterance(text)
    assert frame.raw == text
    assert "\ufffd" not in frame.raw
    assert "?" not in frame.raw


def test_french_copula_agreement_detects_written_mismatch_and_accepts_match():
    mismatch = parse_utterance("Nous est prêts.")
    compatible = parse_utterance("Je suis prêt.")

    assert _groups(mismatch, "COPULAR_CONSTRUCTION")
    assert "INCOMPATIBLE" in _subject_verb_status(mismatch)
    assert _groups(compatible, "COPULAR_CONSTRUCTION")
    assert "COMPATIBLE" in _subject_verb_status(compatible)
    assert mismatch.units == ()  # structural agreement is not a semantic proposition
    assert compatible.units == ()


def test_french_compound_checks_finite_auxiliary_not_participle_agreement():
    mismatch = parse_utterance("Elle sont partie.")
    compatible = parse_utterance("Elles sont parties.")

    assert "INCOMPATIBLE" in _subject_verb_status(mismatch)
    assert "COMPATIBLE" in _subject_verb_status(compatible)


def test_french_compound_etre_exposes_auxiliary_chain_without_semantic_invention():
    frame = parse_utterance("Nous avons été prêts.")
    chain_groups = [g for g in frame.structural_analysis["groups"] if g.get("verbal_chain")]

    assert chain_groups
    chain = chain_groups[0]["verbal_chain"]
    assert chain["finite_auxiliary"]["surface"] == "avons"
    assert chain["finite_auxiliary"]["lemma"] == "avoir"
    assert chain["lexical_part"]["surface"] == "été"
    assert chain["lexical_part"]["lemma"] == "être"
    assert chain["tense_aspect"] == "COMPOUND_PAST"
    assert chain["verified_fact"] is False


@pytest.mark.parametrize(
    ("text", "expected_status", "expected_subject", "expected_auxiliary", "negative"),
    [
        ("They is not ready.", "INCOMPATIBLE", "they", "be", True),
        ("He don't know.", "INCOMPATIBLE", "he", "do", True),
        ("She is ready.", "COMPATIBLE", "she", "be", False),
        ("We have been working.", "COMPATIBLE", "we", "have", False),
    ],
)
def test_english_explicit_language_analysis(text, expected_status, expected_subject, expected_auxiliary, negative):
    frame = parse_utterance(text, language="en")
    analysis = frame.structural_analysis

    assert analysis["language"] == "en"
    assert analysis["status"] == "STRUCTURALLY_ANALYZED"
    assert analysis["agreements"][0]["status"] == expected_status
    assert analysis["verbal_chain"]["subject"] == expected_subject
    assert analysis["verbal_chain"]["finite_auxiliary"]["lemma"] == expected_auxiliary
    assert analysis["verbal_chain"]["negative"] is negative
    assert analysis["provenance"]["language_selection"] == "explicit_caller_argument"
    assert analysis["authority"] == "KX108_ONLY"
    assert analysis["verified_fact"] is False
    assert frame.units == ()


@pytest.mark.parametrize("text", ["They are ready.", "I am ready.", "He doesn't know.", "She has been working."])
def test_english_generalization_uses_requested_language_and_preserves_structure(text):
    frame = parse_utterance(text, language="en")

    assert frame.structural_analysis["language"] == "en"
    assert frame.structural_analysis["status"] == "STRUCTURALLY_ANALYZED"
    assert frame.structural_analysis["verbal_chain"]["language"] == "en"
    assert frame.structural_analysis["verbal_chain"]["source_text"] == text
    assert frame.structural_analysis["verified_fact"] is False


def test_unsupported_language_fails_closed():
    with pytest.raises(ValueError, match="unsupported language"):
        parse_utterance("She is ready.", language="de")


@pytest.mark.parametrize(
    ("text", "expected_status"),
    [("They are not ready.", "COMPATIBLE"), ("He doesn't know.", "COMPATIBLE")],
)
def test_english_correct_finite_auxiliaries_preserve_negation(text, expected_status):
    frame = parse_utterance(text, language="en")
    analysis = frame.structural_analysis

    assert analysis["verbal_chain"]["agreement"] == expected_status
    assert analysis["verbal_chain"]["negative"] is True
    assert analysis["agreements"][0]["status"] == expected_status


def test_explicit_english_never_promotes_french_lexical_rows():
    frame = parse_utterance("We have been working.", language="en")
    rows = [row for token in frame.structural_analysis["tokens"]
            for row in token["nature_analyses"]]

    assert rows
    assert {row["lang"] for row in rows} == {"en"}
    assert all(row["lemma"] not in {"haver", "eissir"} for row in rows)
    assert frame.structural_analysis["verbal_chain"]["lexical_part"]["lemma_candidates"] == ["work", "worke"]
    assert frame.structural_analysis["verbal_chain"]["selected_referent"] is None
    by_surface = {token["normalized"]: token for token in frame.structural_analysis["tokens"]}
    assert by_surface["have"]["selected_nature"] == "AUXILIARY"
    assert by_surface["been"]["selected_nature"] == "AUXILIARY"
    assert by_surface["working"]["selected_nature"] == "VERB"
    assert "LEXICAL_PARTICIPLE" in by_surface["working"]["functions"]
