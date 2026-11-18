"""F9 adapter tests using the locally pinned FreeDict TEI as the real producer."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from brody.core.paths import BRODY_CORPUS_DIR, BRODY_ROOT
from brody.linguistic.freedict_phonetics import extract_freedict_pronunciations
from brody.linguistic.native_phonetics_f9 import (
    phonemes_to_candidates,
    text_to_phonemes,
)

ROOT = BRODY_ROOT
TEI = BRODY_ROOT / "docs/evidence/p6_e_local_20261105/source/freedict_fra_eng.tei"
if not TEI.is_file():
    _alt = BRODY_ROOT.parent / "obsidia-brody" / "docs/evidence/p6_e_local_20261105/source/freedict_fra_eng.tei"
    if _alt.is_file():
        TEI = _alt


@pytest.fixture(scope="module")
def extraction():
    manifest = json.loads((BRODY_CORPUS_DIR / "DOWNLOAD_MANIFEST.json").read_text(encoding="utf-8"))
    source = next(row for row in manifest if row.get("id") == "freedict_fra_eng")
    return extract_freedict_pronunciations(TEI, source)


def test_text_to_phonemes_keeps_french_homophone_records_separate(extraction):
    expected = {"ver", "vers", "verre", "vert"}
    records = []
    for spelling in sorted(expected):
        result = text_to_phonemes(extraction, original_text=spelling, language="fr")
        assert result["original_text"] == spelling
        assert result["original_sha256"] == hashlib.sha256(spelling.encode("utf-8")).hexdigest()
        assert result["status"] == "SOURCE_ATTESTED_NOTATION_UNVALIDATED"
        assert result["boundary"]["text_modified"] is False
        assert result["authority"] == "KX108_ONLY"
        assert len(result["candidates"]) >= 1
        for candidate in result["candidates"]:
            records.append(candidate)
            assert candidate["pronunciation_record"]["lemma"] == spelling
            assert candidate["provenance"]["source_sha256"] == extraction["source"]["sha256_observed"]
            assert candidate["decoded_candidate"]["status"] == "DECODED_CANDIDATE"
            assert "HISTORICAL_RECORD_CONFORMANCE_NOT_INDEPENDENTLY_VERIFIED" in candidate["decoded_candidate"]["uncertainty"]
            assert candidate["notation_qualification"]["source_notation_status"] == "SOURCE_NOTATION_ATTESTED"
            assert candidate["notation_qualification"]["ipa_decoding_status"] == "IPA_DECODED_CONDITIONAL"
            assert candidate["notation_qualification"]["ipa_validation_status"] == "NOT_VALIDATED"
            assert candidate["notation_qualification"]["ipa_validated"] is False
    sequences = {tuple(row["decoded_candidate"]["decoded_phonemes"][i]["symbol"]
                       for i in range(len(row["decoded_candidate"]["decoded_phonemes"])))
                 for row in records}
    assert len(sequences) == 1
    assert len({row["provenance"]["variant_ref"] for row in records}) >= 5


def test_source_bound_phoneme_candidate_returns_all_exact_spelling_matches(extraction):
    forward = text_to_phonemes(extraction, original_text="ver", language="fr")
    query = forward["candidates"][0]
    result = phonemes_to_candidates(extraction, phonetic_candidate=query, language="fr")
    spellings = {row["lemma"] for row in result["candidates"]}
    assert result["status"] == "CONDITIONAL_EXACT_SEQUENCE_MATCHES"
    assert {"ver", "vers", "verre", "vert"} <= spellings
    assert result["boundary"]["selected_candidate"] is None
    assert result["authority"] == "KX108_ONLY"
    assert all(row["provenance"]["source_sha256"] == extraction["source"]["sha256_observed"]
               for row in result["candidates"])
    assert all(row["notation_qualification"]["ipa_validation_status"] == "NOT_VALIDATED"
               for row in result["candidates"])


def test_real_multiple_pronunciations_for_one_spelling_are_kept_separate(extraction):
    result = text_to_phonemes(extraction, original_text="s'occuper", language="fr")
    assert {row["raw_notation"] for row in result["candidates"]} == {"sokype", "sɔkype"}
    assert len({row["provenance"]["variant_ref"] for row in result["candidates"]}) == 2
    assert all(row["status"] == "SOURCE_SHA256_VERIFIED_NOTATION_UNVALIDATED"
               for row in result["candidates"])


def test_real_partial_transcription_is_source_attested_but_not_promoted_to_ipa(extraction):
    result = text_to_phonemes(extraction, original_text="J\u00e9sus-Christ", language="fr")
    assert len(result["candidates"]) == 1
    candidate = result["candidates"][0]
    assert candidate["raw_notation"] == "\u0292ezyk\u0280i(st)"
    assert candidate["decoded_candidate"]["status"] == "PARTIAL"
    assert candidate["notation_qualification"]["source_notation_status"] == "SOURCE_NOTATION_ATTESTED"
    assert candidate["notation_qualification"]["ipa_decoding_status"] == "IPA_DECODED_PARTIAL"
    assert candidate["notation_qualification"]["ipa_validation_status"] == "NOT_VALIDATED"
    assert candidate["notation_qualification"]["ipa_validated"] is False


def test_english_source_is_reported_unavailable_not_inferred(extraction):
    for spelling in ("right", "write", "read"):
        result = text_to_phonemes(extraction, original_text=spelling, language="en")
        assert result["status"] == "PHONETIC_SOURCE_UNAVAILABLE"
        assert result["candidates"] == []


def test_unknown_french_form_and_language_are_not_guessed(extraction):
    missing = text_to_phonemes(extraction, original_text="not-a-source-entry", language="fr")
    unsupported = text_to_phonemes(extraction, original_text="ver", language="de")
    assert missing["status"] == "PHONETIC_UNRESOLVED"
    assert missing["candidates"] == []
    assert unsupported["status"] == "UNSUPPORTED_LANGUAGE"
    assert unsupported["candidates"] == []


def test_inverse_rejects_modified_decoding_and_unpinned_extraction(extraction):
    query = text_to_phonemes(extraction, original_text="ver", language="fr")["candidates"][0]
    tampered = dict(query)
    tampered["decoded_candidate"] = dict(query["decoded_candidate"])
    tampered["decoded_candidate"]["decoded_phonemes"] = []
    bad_query = phonemes_to_candidates(extraction, phonetic_candidate=tampered, language="fr")
    assert bad_query["status"] == "HOLD_QUERY_DECODE_MISMATCH"
    missing_ref = dict(query)
    missing_ref["pronunciation_record"] = dict(query["pronunciation_record"], variant_ref="missing:variant")
    missing_result = phonemes_to_candidates(extraction, phonetic_candidate=missing_ref, language="fr")
    assert missing_result["status"] == "HOLD_QUERY_PROVENANCE_INVALID"
    altered_extraction = dict(extraction)
    altered_extraction["source"] = dict(extraction["source"], sha256_observed="0" * 64)
    bad_source = phonemes_to_candidates(altered_extraction, phonetic_candidate=query, language="fr")
    assert bad_source["status"] == "HOLD_SOURCE_PROVENANCE_INVALID"


def test_invalid_reverse_input_and_audio_claim_are_refused(extraction):
    result = phonemes_to_candidates(extraction, phonetic_candidate={"raw": "vɛʀ"}, language="fr")
    assert result["status"] == "HOLD_QUERY_NOT_SOURCE_BOUND"
    assert result["boundary"]["audio_input"] is False
