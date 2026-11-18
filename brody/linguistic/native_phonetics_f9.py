"""Thin F9 adapter over the verified P6-E/P6-F FreeDict producer.

The historical TEI edition does not declare its notation. Returned decoded
segments therefore remain conditional IPA candidates, never verified speech.
This module performs no grapheme-to-phoneme inference and no audio recognition.
"""
from __future__ import annotations

import hashlib
from typing import Any

from brody.linguistic.freedict_phonetics import (
    PINNED_SHA256,
    SCHEMA as FREEDICT_SCHEMA,
    decode_freedict_pronunciation,
    lookup_freedict_pronunciations,
)

F9_SCHEMA = "BRODY_P6_NATIVE_PHONETICS_F9_V1"
IPA_DECODE_SCHEMA = "BRODY_P6_F_IPA_DECODING_V1"


def _valid_extraction(extraction: Any) -> bool:
    return bool(
        isinstance(extraction, dict)
        and extraction.get("schema") == FREEDICT_SCHEMA
        and extraction.get("integrity_status") == "SOURCE_SHA256_VERIFIED"
        and extraction.get("source", {}).get("sha256_observed") == PINNED_SHA256
    )


def _signature(decoded: dict[str, Any]) -> tuple:
    segments = decoded.get("decoded_phonemes")
    if not isinstance(segments, list) or not segments:
        return ()
    segment_signature = tuple(
        (row.get("symbol"), tuple(row.get("modifiers", [])))
        for row in segments
    )
    stress_signature = tuple(
        (row.get("symbol"), row.get("before_segment_index"))
        for row in decoded.get("stress_markers", [])
    )
    return segment_signature, stress_signature


def _notation_qualification(record: dict[str, Any], decoded: dict[str, Any]) -> dict[str, Any]:
    """Keep source attestation, conditional decoding, and validation distinct."""
    source_attested = (
        record.get("verification_status") == "SOURCE_SHA256_VERIFIED_NOTATION_UNVALIDATED"
        and record.get("source_sha256") == PINNED_SHA256
        and isinstance(record.get("raw_pronunciation"), str)
        and bool(record.get("raw_pronunciation"))
    )
    decode_status = decoded.get("status")
    if decode_status == "DECODED_CANDIDATE":
        ipa_status = "IPA_DECODED_CONDITIONAL"
    elif decode_status == "PARTIAL":
        ipa_status = "IPA_DECODED_PARTIAL"
    else:
        ipa_status = "IPA_DECODE_UNRESOLVED"
    return {
        "source_notation_status": "SOURCE_NOTATION_ATTESTED" if source_attested else "SOURCE_NOTATION_UNVERIFIED",
        "ipa_decoding_status": ipa_status,
        "ipa_validation_status": "NOT_VALIDATED",
        "declared_notation": record.get("notation"),
        "ipa_validated": False,
    }


def text_to_phonemes(
    extraction: dict[str, Any], *, original_text: str, language: str
) -> dict[str, Any]:
    """Return exact French FreeDict records and P6 conditional IPA candidates."""
    text = original_text if isinstance(original_text, str) else str(original_text)
    lang = str(language or "").lower()
    result: dict[str, Any] = {
        "schema": F9_SCHEMA, "direction": "TEXT_TO_PHONEMES",
        "language": lang, "original_text": text,
        "original_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "notation": "IPA_CANDIDATE", "status": "UNRESOLVED",
        "candidates": [], "uncertainties": [], "authority": "KX108_ONLY",
        "boundary": {"consultative": True, "text_modified": False,
                     "decision_authority": "KX108_ONLY", "memory_write": False,
                     "emits_action": False, "audio_input": False},
    }
    if lang not in {"fr", "en"}:
        result["status"] = "UNSUPPORTED_LANGUAGE"
        result["uncertainties"].append("LANGUAGE_NOT_SUPPORTED")
        return result
    if not _valid_extraction(extraction):
        result["status"] = "HOLD_SOURCE_PROVENANCE_INVALID"
        result["uncertainties"].append("PINNED_FREEDICT_EXTRACTION_REQUIRED")
        return result
    result["source"] = {
        "id": extraction["source"].get("id"),
        "version": extraction["source"].get("version"),
        "date": extraction["source"].get("date"),
        "license": extraction["source"].get("license"),
        "sha256": extraction["source"].get("sha256_observed"),
        "url": extraction["source"].get("url"),
        "notation_policy": extraction["source"].get("notation_policy"),
    }
    if lang != "fr":
        result["status"] = "PHONETIC_SOURCE_UNAVAILABLE"
        result["uncertainties"].append("PINNED_FREEDICT_SOURCE_CONTAINS_FRENCH_RECORDS_ONLY")
        return result
    records = lookup_freedict_pronunciations(extraction, text)
    for record in records:
        decoded = decode_freedict_pronunciation(record)
        result["candidates"].append({
            "lemma": record.get("lemma"),
            "lemma_candidates": list(record.get("lemma_candidates", [])),
            "raw_notation": record.get("raw_pronunciation"),
            "pronunciation_record": dict(record),
            "decoded_candidate": decoded,
            "status": record.get("verification_status"),
            "notation_qualification": _notation_qualification(record, decoded),
            "provenance": {key: record.get(key) for key in (
                "source_id", "source_version", "source_date", "source_sha256",
                "source_url", "license", "entry_ref", "form_ref", "variant_ref", "sense_refs",
            )},
        })
    if not records:
        result["status"] = "PHONETIC_UNRESOLVED"
        result["uncertainties"].append("NO_EXACT_CASE_SOURCE_PRONUNCIATION")
    else:
        result["status"] = "SOURCE_ATTESTED_NOTATION_UNVALIDATED"
        result["uncertainties"].extend([
            "HISTORICAL_RECORD_CONFORMANCE_NOT_INDEPENDENTLY_VERIFIED",
            "P6_DECODED_SYMBOLS_ARE_CONDITIONAL_CANDIDATES_NOT_AUDIO_VERIFIED",
        ])
    return result


def phonemes_to_candidates(
    extraction: dict[str, Any], *, phonetic_candidate: dict[str, Any], language: str
) -> dict[str, Any]:
    """Find exact decoded-sequence matches for a source-bound P6 candidate.

    The query must be a candidate returned by this adapter so its notation and
    origin can be revalidated against the pinned TEI before reverse matching.
    """
    lang = str(language or "").lower()
    result: dict[str, Any] = {
        "schema": F9_SCHEMA, "direction": "PHONEMES_TO_CANDIDATES",
        "language": lang, "notation": "IPA_CANDIDATE",
        "status": "UNRESOLVED", "candidates": [], "records_examined": 0,
        "authority": "KX108_ONLY",
        "boundary": {"consultative": True, "selected_candidate": None,
                     "decision_authority": "KX108_ONLY", "memory_write": False,
                     "emits_action": False, "audio_input": False},
        "uncertainties": [],
    }
    if lang not in {"fr", "en"}:
        result["status"] = "UNSUPPORTED_LANGUAGE"
        result["uncertainties"].append("LANGUAGE_NOT_SUPPORTED")
        return result
    if not _valid_extraction(extraction):
        result["status"] = "HOLD_SOURCE_PROVENANCE_INVALID"
        result["uncertainties"].append("PINNED_FREEDICT_EXTRACTION_REQUIRED")
        return result
    if lang != "fr":
        result["status"] = "PHONETIC_SOURCE_UNAVAILABLE"
        result["uncertainties"].append("PINNED_FREEDICT_SOURCE_CONTAINS_FRENCH_RECORDS_ONLY")
        return result
    if not isinstance(phonetic_candidate, dict):
        result["status"] = "HOLD_QUERY_NOT_SOURCE_BOUND"
        result["uncertainties"].append("A_VERIFIED_P6_PHONETIC_CANDIDATE_IS_REQUIRED")
        return result

    query_record = phonetic_candidate.get("pronunciation_record")
    query_decoded = phonetic_candidate.get("decoded_candidate")
    if not isinstance(query_record, dict) or not isinstance(query_decoded, dict):
        result["status"] = "HOLD_QUERY_NOT_SOURCE_BOUND"
        result["uncertainties"].append("A_VERIFIED_P6_PHONETIC_CANDIDATE_IS_REQUIRED")
        return result
    variant_ref = query_record.get("variant_ref")
    pinned_record = next((row for row in extraction.get("records", [])
                          if row.get("variant_ref") == variant_ref), None)
    if (not pinned_record or pinned_record != query_record
            or query_decoded.get("schema") != IPA_DECODE_SCHEMA
            or query_decoded.get("status") != "DECODED_CANDIDATE"
            or query_decoded.get("provenance", {}).get("variant_ref") != variant_ref):
        result["status"] = "HOLD_QUERY_PROVENANCE_INVALID"
        result["uncertainties"].append("QUERY_DOES_NOT_MATCH_PINNED_DECODED_RECORD")
        return result
    redecoded = decode_freedict_pronunciation(pinned_record)
    signature = _signature(redecoded)
    if not signature or signature != _signature(query_decoded):
        result["status"] = "HOLD_QUERY_DECODE_MISMATCH"
        result["uncertainties"].append("QUERY_PHONEME_SEQUENCE_DIFFERS_FROM_PINNED_RECORD")
        return result

    for record in extraction.get("records", []):
        result["records_examined"] += 1
        decoded = decode_freedict_pronunciation(record)
        if decoded.get("status") != "DECODED_CANDIDATE" or _signature(decoded) != signature:
            continue
        result["candidates"].append({
            "lemma": record.get("lemma"),
            "lemma_candidates": list(record.get("lemma_candidates", [])),
            "raw_notation": record.get("raw_pronunciation"),
            "provenance": {key: record.get(key) for key in (
                "source_id", "source_version", "source_date", "source_sha256",
                "source_url", "license", "entry_ref", "form_ref", "variant_ref", "sense_refs",
            )},
            "notation_status": record.get("verification_status"),
            "notation_qualification": _notation_qualification(record, decoded),
        })
    result["status"] = "CONDITIONAL_EXACT_SEQUENCE_MATCHES" if result["candidates"] else "NO_COMPATIBLE_CANDIDATE"
    result["uncertainties"].extend([
        "HISTORICAL_RECORD_CONFORMANCE_NOT_INDEPENDENTLY_VERIFIED",
        "MATCHES_ARE_CONDITIONAL_IPA_CANDIDATES_NOT_VERIFIED_PRONUNCIATIONS",
        "NO_CANDIDATE_IS_SELECTED",
    ])
    return result
