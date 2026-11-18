"""F7b: reproducible cell-level completeness and provenance checks."""

from collections import Counter

import pytest

from brody.linguistic.lexical_corpus import (
    get_verb_paradigm,
    lookup_surface_form,
    realize_inflection,
)


def _has_cell(form, lang, lemma, mood, tense, person="", number="", gender=""):
    return any(
        row.pos == "verb"
        and row.lemma == lemma
        and row.mood == mood
        and row.tense == tense
        and row.person == person
        and row.number == number
        and row.gender == gender
        and bool(row.source_id)
        for row in lookup_surface_form(form, lang=lang)
    )


def test_f7b_french_applicable_cells_and_pouvoir_imperative_scope():
    # This is a deliberately bounded cell set, not an exhaustive paradigm score.
    cells = [
        ("venir", "indicative", "present", "1", "sg", "viens"),
        ("venir", "indicative", "present", "1", "pl", "venons"),
        ("venir", "indicative", "future", "3", "sg", "viendra"),
        ("venir", "indicative", "future", "3", "pl", "viendront"),
        ("aller", "indicative", "present", "1", "sg", "vais"),
        ("aller", "indicative", "present", "1", "pl", "allons"),
        ("aller", "indicative", "future", "1", "sg", "irai"),
        ("faire", "indicative", "present", "1", "sg", "fais"),
        ("faire", "indicative", "present", "3", "sg", "fait"),
        ("faire", "indicative", "future", "1", "pl", "ferons"),
        ("prendre", "indicative", "present", "1", "sg", "prends"),
        ("prendre", "indicative", "present", "1", "pl", "prenons"),
        ("prendre", "participle", "past", "", "inv", "pris", "masc"),
        ("pouvoir", "indicative", "present", "1", "sg", "puis"),
        ("pouvoir", "indicative", "present", "2", "sg", "peux"),
        ("pouvoir", "indicative", "present", "1", "pl", "pouvons"),
        ("pouvoir", "indicative", "present", "3", "pl", "peuvent"),
        ("etre", "indicative", "present", "1", "sg", "suis"),
        ("etre", "indicative", "present", "3", "sg", "est"),
        ("etre", "indicative", "present", "2", "pl", "\u00eates"),
        ("etre", "indicative", "imperfect", "1", "pl", "\u00e9tions"),
        ("etre", "participle", "past", "", "inv", "\u00e9t\u00e9"),
        ("avoir", "indicative", "present", "1", "sg", "ai"),
        ("avoir", "indicative", "present", "1", "pl", "avons"),
        ("avoir", "indicative", "present", "3", "sg", "a"),
        ("avoir", "indicative", "imperfect", "3", "sg", "avait"),
        ("avoir", "participle", "past", "", "sg", "eu", "masc"),
    ]
    assert len(cells) == 27
    for lemma, mood, tense, person, number, form, *gender in cells:
        assert _has_cell(form, "fr", "\u00eatre" if lemma == "etre" else lemma,
                         mood, tense, person, number, gender[0] if gender else "")

    # French pouvoir has no standard imperative paradigm; exclude the cell from
    # missing-cell counts instead of calling it a corpus/parser defect.
    imperative = get_verb_paradigm("pouvoir", "fr").get("imperative_present", [])
    assert not imperative
    assert realize_inflection(
        "pouvoir", lang="fr", mood="imperative", tense="present", person="2", number="sg"
    ) is None


def test_f7b_english_form_inventory_classifies_attestation_rule_and_gaps():
    # Each row is one requested lemma Ã— feature cell Ã— expected surface.
    cells = [
        ("play", "infinitive", "", "", "", "play", "ATTESTED"),
        ("play", "indicative", "present", "3", "sg", "plays", "UNATTESTED"),
        ("play", "indicative", "past", "", "", "played", "RULE_VALIDATED"),
        ("play", "participle", "past", "", "", "played", "UNATTESTED"),
        ("play", "participle", "present", "", "", "playing", "UNATTESTED"),
        ("talk", "infinitive", "", "", "", "talk", "ATTESTED"),
        ("talk", "indicative", "present", "3", "sg", "talks", "UNATTESTED"),
        ("talk", "indicative", "past", "", "", "talked", "RULE_VALIDATED"),
        ("talk", "participle", "past", "", "", "talked", "UNATTESTED"),
        ("talk", "participle", "present", "", "", "talking", "UNATTESTED"),
        ("walk", "infinitive", "", "", "", "walk", "ATTESTED"),
        ("walk", "indicative", "present", "3", "sg", "walks", "ATTESTED"),
        ("walk", "indicative", "past", "", "", "walked", "ATTESTED"),
        ("walk", "participle", "past", "", "", "walked", "ATTESTED"),
        ("walk", "participle", "present", "", "", "walking", "ATTESTED"),
        ("run", "infinitive", "", "", "", "run", "ATTESTED"),
        ("run", "indicative", "past", "", "", "ran", "ATTESTED"),
        ("run", "participle", "past", "", "", "run", "UNATTESTED"),
        ("run", "participle", "present", "", "", "running", "ATTESTED"),
        ("write", "infinitive", "", "", "", "write", "ATTESTED"),
        ("write", "indicative", "past", "", "", "wrote", "ATTESTED"),
        ("write", "participle", "past", "", "", "written", "ATTESTED"),
        ("write", "participle", "present", "", "", "writing", "ATTESTED"),
        ("go", "infinitive", "", "", "", "go", "ATTESTED"),
        ("go", "indicative", "past", "", "", "went", "ATTESTED"),
        ("go", "participle", "past", "", "", "gone", "ATTESTED"),
        ("go", "participle", "present", "", "", "going", "ATTESTED"),
        ("read", "infinitive", "", "", "", "read", "ATTESTED"),
        ("read", "indicative", "past", "", "", "read", "ATTESTED"),
        ("read", "participle", "past", "", "", "read", "ATTESTED"),
        ("read", "participle", "present", "", "", "reading", "ATTESTED"),
    ]
    counts = Counter(status for *_, status in cells)
    assert len(cells) == 31
    assert counts == Counter(ATTESTED=22, RULE_VALIDATED=2, UNATTESTED=7)

    for lemma, mood, tense, person, number, form, status in cells:
        if status == "ATTESTED":
            assert _has_cell(form, "en", lemma, mood, tense, person, number)
        elif status == "RULE_VALIDATED":
            # The existing English regular-past rule is the evidence class here;
            # it is tested across multiple lemmas and does not cover participles.
            assert realize_inflection(
                lemma, lang="en", mood=mood, tense=tense,
                person=person or "3", number=number or "sg",
            ) == form
        else:
            assert not _has_cell(form, "en", lemma, mood, tense, person, number)
            assert realize_inflection(
                lemma, lang="en", mood=mood, tense=tense,
                person=person or "3", number=number or "sg",
            ) is None


@pytest.mark.parametrize("lemma", ["play", "talk"])
def test_f7b_source_lemma_mismatch_is_not_promoted_to_attestation(lemma):
    source_lemma = lemma + "e"
    expected_form = lemma + ("ed" if lemma.endswith("y") else "ed")
    rows = lookup_surface_form(expected_form, lang="en")
    assert any(row.pos == "verb" and row.lemma == source_lemma and row.source_id == "unimorph_eng"
               for row in rows)
    assert not any(row.pos == "verb" and row.lemma == lemma and row.source_id == "unimorph_eng"
                   for row in rows)


def test_f7b_run_irregular_and_ambiguous_source_rows_are_not_collapsed():
    ran = lookup_surface_form("ran", lang="en")
    assert any(row.lemma == "run" and row.source_id == "wordnet_exc" for row in ran)
    assert any(row.lemma == "rin" and row.source_id == "unimorph_eng" for row in ran)
    assert realize_inflection("run", lang="en", mood="participle", tense="past") is None


def test_f7b_french_ambiguous_forms_keep_feature_and_lemma_alternatives():
    viens = lookup_surface_form("viens", lang="fr")
    assert {row.lemma for row in viens if row.pos == "verb"} >= {"venir"}
    assert {(row.mood, row.tense, row.person, row.number) for row in viens
            if row.lemma == "venir" and row.pos == "verb"} >= {
                ("indicative", "present", "1", "sg"),
                ("indicative", "present", "2", "sg"),
                ("imperative", "present", "2", "sg"),
            }
    suis = lookup_surface_form("suis", lang="fr")
    assert {row.lemma for row in suis if row.pos == "verb"} >= {"\u00eatre", "suivre"}


def test_f7b_full_requested_french_cell_counts_exclude_non_applicable_imperative():
    lemmas = "parler finir vendre marcher choisir".split() + ["\u00eatre"] + \
        "avoir aller faire venir prendre pouvoir vouloir devoir".split()
    groups = [
        ("indicative_present", 84),
        ("indicative_imperfect", 84),
        ("indicative_future", 84),
        ("conditional_present", 84),
        ("subjunctive_present", 83),
    ]
    observed = {}
    for group, expected in groups:
        cells = {
            (lemma, row["person"], row["number"])
            for lemma in lemmas
            for row in get_verb_paradigm(lemma, "fr").get(group, [])
            if row["source_id"] and row["person"] in {"1", "2", "3"}
            and row["number"] in {"sg", "pl"}
        }
        observed[group] = len(cells)
        assert len(cells) == expected

    imperative_lemmas = [lemma for lemma in lemmas if lemma != "pouvoir"]
    imperative_cells = {
        (lemma, row["person"], row["number"])
        for lemma in imperative_lemmas
        for row in get_verb_paradigm(lemma, "fr").get("imperative_present", [])
        if row["source_id"] and (row["person"], row["number"]) in {
            ("2", "sg"), ("1", "pl"), ("2", "pl")
        }
    }
    assert len(imperative_cells) == 39
    assert len(get_verb_paradigm("pouvoir", "fr").get("imperative_present", [])) == 0

    participle_counts = {
        group: sum(bool(get_verb_paradigm(lemma, "fr").get(group)) for lemma in lemmas)
        for group in ("participle_present", "participle_past")
    }
    assert participle_counts == {"participle_present": 14, "participle_past": 14}

    # The surface puisses exists, but the corpus tags it as 3sg. Do not relabel
    # that row as the missing 2sg cell; it remains insufficient evidence here.
    puisses = [row for row in lookup_surface_form("puisses", lang="fr")
               if row.lemma == "pouvoir" and row.pos == "verb"
               and row.mood == "subjunctive" and row.tense == "present"]
    assert puisses and all(row.person == "3" and row.number == "sg" for row in puisses)
    assert not _has_cell("puisses", "fr", "pouvoir", "subjunctive", "present", "2", "sg")
    assert observed["subjunctive_present"] == 83


def test_f7b_requested_english_paradigm_group_counts_are_source_backed():
    lemmas = "walk play work talk open be have do go come eat write know read run".split()
    expected = {
        "indicative_present": (12, 15),
        "indicative_past": (13, 15),
        "participle_present": (12, 15),
        "participle_past": (12, 15),
    }
    for group, (count, denominator) in expected.items():
        present = sum(bool(get_verb_paradigm(lemma, "en").get(group)) for lemma in lemmas)
        assert (present, len(lemmas)) == (count, denominator)


def test_f7b_ambiguity_counts_are_preserved_in_the_bounded_surface_sets():
    french_forms = [
        "viens", "venons", "viendra", "viendront", "vais", "allons", "irai",
        "fais", "fait", "ferons", "prends", "prenons", "pris", "peux", "puis",
        "pouvons", "peuvent", "suis", "est", "\u00eates", "\u00e9tions",
        "\u00e9t\u00e9", "ai", "avons", "a", "avait", "eu",
    ]
    english_forms = [
        "play", "plays", "played", "playing", "talk", "talks", "talked", "talking",
        "walk", "walks", "walked", "walking", "run", "ran", "running", "write",
        "wrote", "written", "writing", "go", "went", "gone", "going", "read", "reading",
    ]

    def ambiguous_forms(forms, lang):
        result = set()
        for form in forms:
            signatures = {
                (row.lemma, row.mood, row.tense, row.person, row.number, row.gender, row.source_id)
                for row in lookup_surface_form(form, lang=lang) if row.pos == "verb"
            }
            if len(signatures) > 1:
                result.add(form)
        return result

    assert len(french_forms) == 27
    assert len(ambiguous_forms(french_forms, "fr")) == 16
    assert len(english_forms) == 25
    assert len(ambiguous_forms(english_forms, "en")) == 8

