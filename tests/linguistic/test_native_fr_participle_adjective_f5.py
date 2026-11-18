"""Bounded F5 checks for French participial chains and copular alternatives."""

from brody.linguistic.french_grammar import parse_utterance


def _analysis(text):
    return parse_utterance(text, language="fr").structural_analysis


def _pp_agreements(analysis):
    return [item for item in analysis["agreements"] if item["kind"] == "SUBJECT_PARTICIPLE"]


def _participial_alternatives(analysis):
    return [item for item in analysis["alternatives"]
            if item.get("kind") == "PARTICIPIAL_PREDICATION_OR_ATTRIBUTE"]


def test_etre_compounds_expose_participle_agreement_from_attested_features():
    cases = [
        ("Elle est partie.", "fem", "sg"),
        ("Elles sont arriv\u00e9es.", "fem", "pl"),
        ("La porte est ouverte.", "fem", "sg"),
        ("Les portes sont ouvertes.", "fem", "pl"),
    ]
    for text, gender, number in cases:
        analysis = _analysis(text)
        agreements = _pp_agreements(analysis)
        assert len(agreements) == 1, (text, analysis["agreements"])
        assert agreements[0]["status"] == "COMPATIBLE"
        assert agreements[0]["expected_gender"] == gender
        assert agreements[0]["expected_number"] == number
        assert agreements[0]["verified_fact"] is False


def test_mismatched_etre_participle_is_reported_without_rewriting_source():
    for text in ("Elle est parti.", "Elles sont arriv\u00e9e."):
        frame = parse_utterance(text, language="fr")
        agreements = _pp_agreements(frame.structural_analysis)
        assert len(agreements) == 1
        assert agreements[0]["status"] == "INCOMPATIBLE"
        assert frame.raw == text


def test_participial_attribute_ambiguity_remains_unselected():
    analysis = _analysis("La porte est ouverte.")
    alternatives = _participial_alternatives(analysis)
    assert len(alternatives) == 1
    assert alternatives[0]["selected"] is None
    assert {item["kind"] for item in alternatives[0]["interpretations"]} == {
        "NATIVE_PARTICIPIAL_PREDICATION", "COPULAR_ATTRIBUTE_CANDIDATE"
    }
    assert analysis["boundary"]["decision_authority"] == "KX108_ONLY"
    assert analysis["boundary"]["semantic_resolution"] is False
    agreement = _pp_agreements(analysis)[0]
    assert agreement["evidence_refs"]["subject_token"]
    assert agreement["evidence_refs"]["participle_token"]
    assert agreement["source_rule"] == "existing_etre_participle_corpus_agreement"
    assert analysis["provenance"]["corpus"]["status"] == "READY"
    assert len(analysis["provenance"]["corpus"]["database_sha256"]) == 64
    token_map = {token["id"]: token for token in analysis["tokens"]}
    for token_ref in agreement["evidence_refs"].values():
        assert any(reading.get("source_id") for reading in token_map[token_ref]["nature_analyses"])


def test_adjective_attribute_is_not_promoted_to_a_participle_or_event():
    frame = parse_utterance("Elle est pr\u00eate.", language="fr")
    analysis = frame.structural_analysis
    assert any(group["function"] == "SUBJECT_ATTRIBUTE" for group in analysis["groups"])
    assert not _pp_agreements(analysis)
    assert not frame.units
    assert frame.raw == "Elle est pr\u00eate."


def test_avoir_compound_does_not_get_subject_participle_agreement():
    analysis = _analysis("Il a mang\u00e9.")
    assert not _pp_agreements(analysis)
    chain = next(group["verbal_chain"] for group in analysis["groups"] if "verbal_chain" in group)
    assert chain["finite_auxiliary"]["lemma"] == "avoir"
    assert chain["lexical_part"]["form"] == "PARTICIPLE"


def test_cod_preposed_and_reflexive_indirect_cases_remain_explicitly_unresolved():
    cod_frame = parse_utterance("Les lettres qu'elle a \u00e9crites.", language="fr")
    cod_analysis = cod_frame.structural_analysis
    reflexive_analysis = _analysis("Elles se sont parl\u00e9.")
    written_participle = next(unit for unit in cod_frame.units if unit.lemma == "\u00e9crire")
    assert not any(dependency.get("relation") == "DIRECT_OBJECT"
                   and dependency.get("predicate_ref") == written_participle.id
                   for dependency in cod_analysis["dependencies"])
    assert not any(unit.lemma == "lettrer" for unit in cod_frame.units)
    assert not _pp_agreements(cod_analysis)  # HAVE/COD attachment is not established.
    assert not _pp_agreements(reflexive_analysis)
    assert reflexive_analysis["boundary"]["decision_authority"] == "KX108_ONLY"


def test_all_f5_source_text_is_preserved_and_non_authoritative():
    texts = [
        "Elle est partie.", "Elles sont arriv\u00e9es.", "La porte est ouverte.",
        "Les portes sont ouvertes.", "Il a mang\u00e9.",
        "Les lettres qu'elle a \u00e9crites.", "Elles se sont parl\u00e9.", "Elle est pr\u00eate.",
    ]
    for text in texts:
        frame = parse_utterance(text, language="fr")
        assert frame.raw == text
        assert frame.structural_analysis["original"] == text
        assert frame.structural_analysis["boundary"]["decision_authority"] == "KX108_ONLY"
        assert frame.structural_analysis["boundary"]["semantic_resolution"] is False
        assert frame.structural_analysis["boundary"]["verified_fact"] is False
