"""F6 English grammar analysis on the real native parser and pinned corpus."""

import hashlib

import pytest

from brody.linguistic.french_grammar import parse_utterance


CASES = [
    ("He knows.", "SUPPORTED_CORRECT"),
    ("He know.", "SUPPORTED_MISMATCH"),
    ("She walks to school.", "SUPPORTED_CORRECT"),
    ("She walk to school.", "SUPPORTED_MISMATCH"),
    ("They are ready.", "SUPPORTED_CORRECT"),
    ("They is ready.", "SUPPORTED_MISMATCH"),
    ("He doesn't know.", "SUPPORTED_CORRECT"),
    ("He don't know.", "SUPPORTED_MISMATCH"),
    ("She has eaten.", "SUPPORTED_CORRECT"),
    ("She have eaten.", "SUPPORTED_MISMATCH"),
    ("We have been working.", "AMBIGUOUS"),
    ("Did he go?", "SUPPORTED_CORRECT"),
    ("Did he went?", "SUPPORTED_MISMATCH"),
    ("He can swim.", "SUPPORTED_CORRECT"),
    ("He can swims.", "SUPPORTED_MISMATCH"),
    ("She isn't ready.", "SUPPORTED_CORRECT"),
    ("You read it.", "AMBIGUOUS"),
    ("The letter was written.", "AMBIGUOUS"),
]


def _frame(text):
    return parse_utterance(text, language="en")


def _classification(analysis):
    if analysis["status"] != "STRUCTURALLY_ANALYZED" or analysis.get("verbal_chain") is None:
        return "UNSUPPORTED"
    if analysis.get("alternatives"):
        return "AMBIGUOUS"
    chain = analysis["verbal_chain"]
    if len(chain.get("lexical_part", {}).get("lemma_candidates", [])) > 1:
        return "AMBIGUOUS"
    statuses = {row["status"] for row in analysis.get("agreements", [])}
    if "INCOMPATIBLE" in statuses:
        return "SUPPORTED_MISMATCH"
    return "SUPPORTED_CORRECT"


@pytest.mark.parametrize(("text", "expected"), CASES)
def test_f6_corpus_classification(text, expected):
    frame = _frame(text)
    analysis = frame.structural_analysis
    assert _classification(analysis) == expected
    assert frame.raw == text
    assert analysis["original"] == text
    assert analysis["language"] == "en"
    assert analysis["provenance"]["source_sha256"] == hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert analysis["authority"] == "KX108_ONLY"
    assert analysis["verified_fact"] is False
    assert frame.units == ()
    for token in analysis["tokens"]:
        start, end = token["span"]
        assert text[start:end] == token["raw"]
        assert all(row["lang"] == "en" for row in token["nature_analyses"])


@pytest.mark.parametrize(
    ("text", "auxiliary", "tense", "negative", "agreement"),
    [
        ("They are ready.", "be", "PRESENT", False, "COMPATIBLE"),
        ("They is ready.", "be", "PRESENT", False, "INCOMPATIBLE"),
        ("He doesn't know.", "do", "PRESENT", True, "COMPATIBLE"),
        ("He don't know.", "do", "PRESENT", True, "INCOMPATIBLE"),
        ("She has eaten.", "have", "PRESENT", False, "COMPATIBLE"),
        ("She have eaten.", "have", "PRESENT", False, "INCOMPATIBLE"),
        ("Did he go?", "do", "PAST", False, "COMPATIBLE"),
        ("Did he went?", "do", "PAST", False, "COMPATIBLE"),
        ("He can swim.", "can", "MODAL", False, "COMPATIBLE"),
        ("He can swims.", "can", "MODAL", False, "COMPATIBLE"),
        ("She isn't ready.", "be", "PRESENT", True, "COMPATIBLE"),
    ],
)
def test_f6_auxiliary_contract(text, auxiliary, tense, negative, agreement):
    analysis = _frame(text).structural_analysis
    chain = analysis["verbal_chain"]
    finite = chain.get("finite_auxiliary") or chain.get("finite_verb")
    assert finite["lemma"] == auxiliary
    assert chain["tense"] == tense
    assert chain["negative"] is negative
    assert chain["agreement"] == agreement


def test_f6_do_and_modal_complements_preserve_non_base_forms_as_mismatches():
    for text in ("Did he went?", "He can swims."):
        analysis = _frame(text).structural_analysis
        complement = next(row for row in analysis["agreements"]
                          if row["kind"] == "AUXILIARY_COMPLEMENT")
        assert complement["status"] == "INCOMPATIBLE"
        assert complement["verified_fact"] is False


def test_f6_inverted_do_question_preserves_source_spans_and_auxiliary_role():
    analysis = _frame("Did he go?").structural_analysis
    assert analysis["surface_act"] == "interrogative"
    did = next(token for token in analysis["tokens"] if token["raw"] == "Did")
    assert did["selected_nature"] == "AUXILIARY"
    assert did["functions"] == ["FINITE_AUXILIARY"]
    start, end = did["span"]
    assert "Did he go?"[start:end] == did["raw"]


def test_f6_read_preserves_present_past_ambiguity_without_selection():
    analysis = _frame("You read it.").structural_analysis
    chain = analysis["verbal_chain"]
    assert chain["tense"] == "AMBIGUOUS"
    assert set(chain["tense_candidates"]) == {"PRESENT", "PAST"}
    assert analysis["alternatives"][0]["selected"] is None


def test_f6_standard_register_mismatch_does_not_claim_dialectal_impossibility():
    analysis = _frame("He don't know.").structural_analysis
    auxiliary = next(row for row in analysis["agreements"] if row["kind"] == "SUBJECT_AUXILIARY")
    assert auxiliary["status"] == "INCOMPATIBLE"
    assert auxiliary["register_scope"] == "STANDARD_ENGLISH"
    assert auxiliary["dialectal_impossibility_claimed"] is False


def test_f6_multiple_auxiliaries_keep_the_existing_lemma_candidates():
    analysis = _frame("We have been working.").structural_analysis
    chain = analysis["verbal_chain"]
    assert chain["aspect"] == "PERFECT_PROGRESSIVE"
    assert chain["middle_auxiliary"]["lemma"] == "be"
    assert chain["lexical_part"]["lemma"] is None
    assert len(chain["lexical_part"]["lemma_candidates"]) > 1
