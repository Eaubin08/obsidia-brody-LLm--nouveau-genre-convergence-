"""Targeted native FR/EN conjugation and realization contract cases."""

import pytest

from brody.linguistic.native_realization import realize_semantic_relation


@pytest.mark.parametrize(
    ("case", "kwargs", "expected"),
    [
        (
            "fr_present_copula_plural",
            {"subject": "Nous", "verb_lemma": "être", "obj": "prêts", "person": "1", "number": "pl", "gender": "masc", "lang": "fr"},
            "Nous sommes prêts.",
        ),
        (
            "fr_compound_partir_agreement",
            {"subject": "Elles", "verb_lemma": "partir", "tense": "compound_past", "person": "3", "number": "pl", "gender": "fem", "lang": "fr"},
            "Elles sont parties.",
        ),
        (
            "fr_present_copula_singular",
            {"subject": "Je", "verb_lemma": "être", "obj": "prêt", "person": "1", "number": "sg", "gender": "masc", "lang": "fr"},
            "Je suis prêt.",
        ),
        (
            "fr_compound_etre",
            {"subject": "Nous", "verb_lemma": "être", "obj": "prêts", "tense": "compound_past", "person": "1", "number": "pl", "gender": "masc", "lang": "fr"},
            "Nous avons été prêts.",
        ),
        (
            "en_be_plural_negation",
            {"subject": "They", "verb_lemma": "be", "obj": "ready", "person": "3", "number": "pl", "polarity": "negative", "lang": "en"},
            "They are not ready.",
        ),
        (
            "en_do_support_negation",
            {"subject": "He", "verb_lemma": "know", "person": "3", "number": "sg", "polarity": "negative", "lang": "en"},
            "He does not know.",
        ),
        (
            "en_be_singular",
            {"subject": "She", "verb_lemma": "be", "obj": "ready", "person": "3", "number": "sg", "lang": "en"},
            "She is ready.",
        ),
        (
            "en_perfect_progressive",
            {"subject": "We", "verb_lemma": "work", "person": "1", "number": "pl", "aspect": "perfect_progressive", "tense": "present", "lang": "en"},
            "We have been working.",
        ),
    ],
)
def test_native_realization_produces_expected_fr_en_grammar(case, kwargs, expected):
    result = realize_semantic_relation(**kwargs)

    assert result["text"] == expected, case
    assert result["has_linguistic_limitations"] is False, case
    assert result["decision_authority"] == "KX108_ONLY", case
    assert result["is_world_fact_established"] is False, case
