"""F7 corpus-backed FR/EN morphology and safe inflection realization."""

import hashlib
import sqlite3
from pathlib import Path

import pytest

from brody.linguistic import lexical_corpus as app_corpus
from brody.linguistic.french_grammar import parse_utterance
from brody.linguistic import lexical_corpus as pinned_corpus
from brody.linguistic.lexical_corpus import _find_lexicon_db

DB_PATH = _find_lexicon_db()
PINNED_DB_SHA256 = "a9583d24334169b518521394efb72f1524267b5b4a79c17fb27ce67cd38e04dd"


@pytest.fixture(scope="module", autouse=True)
def readonly_corpus_connection():
    """Give the real app lexical API a pinned, immutable SQLite connection."""
    previous = getattr(app_corpus._local, "conn", None)
    if hasattr(app_corpus._local, "conn"):
        del app_corpus._local.conn
    conn = sqlite3.connect(DB_PATH.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    app_corpus._local.conn = conn
    for function in (app_corpus.lookup_surface_form, app_corpus.realize_inflection,
                     app_corpus.get_verb_paradigm, app_corpus.is_known_lexical_item):
        function.cache_clear()
    yield conn
    for function in (app_corpus.lookup_surface_form, app_corpus.realize_inflection,
                     app_corpus.get_verb_paradigm, app_corpus.is_known_lexical_item):
        function.cache_clear()
    conn.close()
    if previous is not None:
        app_corpus._local.conn = previous
    elif hasattr(app_corpus._local, "conn"):
        del app_corpus._local.conn


def test_f7_pinned_corpus_identity_and_database_are_read_only(readonly_corpus_connection):
    identity = pinned_corpus.corpus_identity()
    digest = hashlib.sha256()
    with DB_PATH.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    assert identity["status"] == "READY"
    assert identity["database_sha256"] == PINNED_DB_SHA256
    assert digest.hexdigest() == PINNED_DB_SHA256
    assert readonly_corpus_connection.execute("PRAGMA query_only").fetchone()[0] == 1
    assert readonly_corpus_connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"


def test_f7_measured_french_paradigm_group_coverage_is_reproducible():
    lemmas = "parler finir vendre marcher choisir \u00eatre avoir aller faire venir prendre pouvoir vouloir devoir".split()
    paradigms = {lemma: app_corpus.get_verb_paradigm(lemma, "fr") for lemma in lemmas}
    expected = {
        "indicative_present": 14,
        "indicative_imperfect": 14,
        "indicative_future": 14,
        "conditional_present": 14,
        "subjunctive_present": 14,
        "imperative_present": 13,
        "participle_present": 14,
        "participle_past": 14,
    }
    for group, count in expected.items():
        assert sum(bool(paradigm.get(group)) for paradigm in paradigms.values()) == count


def test_f7_measured_english_paradigm_group_coverage_is_reproducible():
    lemmas = "walk play work talk open be have do go come eat write know read run".split()
    paradigms = {lemma: app_corpus.get_verb_paradigm(lemma, "en") for lemma in lemmas}
    expected = {
        "indicative_present": 12,
        "indicative_past": 13,
        "participle_present": 12,
        "participle_past": 12,
    }
    for group, count in expected.items():
        assert sum(bool(paradigm.get(group)) for paradigm in paradigms.values()) == count
    assert not paradigms["play"].get("indicative_past")
    assert not paradigms["talk"].get("indicative_past")
    assert not paradigms["run"].get("participle_past")


def test_f7_app_lexical_connection_is_strictly_read_only():
    injected = app_corpus._local.conn
    del app_corpus._local.conn
    opened = app_corpus._get_connection()
    try:
        assert opened is not None
        assert opened.execute("PRAGMA query_only").fetchone()[0] == 1
    finally:
        if opened is not None:
            opened.close()
        app_corpus._local.conn = injected


@pytest.mark.parametrize(
    ("lemma", "lang", "mood", "tense", "person", "number", "gender", "expected"),
    [
        ("parler", "fr", "indicative", "present", "1", "sg", "", "parle"),
        ("finir", "fr", "indicative", "present", "1", "sg", "", "finis"),
        ("vendre", "fr", "indicative", "future", "1", "pl", "", "vendrons"),
        ("\u00eatre", "fr", "indicative", "imperfect", "1", "pl", "", "\u00e9tions"),
        ("avoir", "fr", "subjunctive", "present", "1", "sg", "", "aie"),
        ("faire", "fr", "participle", "past", "3", "sg", "fem", "faite"),
        ("venir", "fr", "participle", "past", "3", "pl", "fem", "venues"),
        ("walk", "en", "indicative", "past", "3", "sg", "", "walked"),
        ("go", "en", "indicative", "past", "3", "sg", "", "went"),
        ("go", "en", "participle", "past", "3", "sg", "", "gone"),
        ("write", "en", "indicative", "past", "3", "sg", "", "wrote"),
        ("write", "en", "participle", "past", "3", "sg", "", "written"),
        ("eat", "en", "indicative", "past", "3", "sg", "", "ate"),
        ("eat", "en", "participle", "past", "3", "sg", "", "eaten"),
    ],
)
def test_f7_attested_inflections_are_realized_without_losing_language(
    lemma, lang, mood, tense, person, number, gender, expected
):
    assert app_corpus.realize_inflection(
        lemma, pos="verb", mood=mood, tense=tense, person=person,
        number=number, gender=gender, lang=lang,
    ) == expected


def test_f7_irregular_past_participle_is_not_derived_from_regular_suffix():
    # The pinned corpus has indicative past "ran" but no past participle cell for run.
    assert app_corpus.realize_inflection(
        "run", pos="verb", mood="participle", tense="past", lang="en"
    ) is None


@pytest.mark.parametrize("lemma", ["play", "talk"])
def test_f7_unattested_regular_past_participle_is_not_invented(lemma):
    assert app_corpus.realize_inflection(
        lemma, pos="verb", mood="participle", tense="past", lang="en"
    ) is None


def test_f7_irregular_verb_missing_requested_person_is_not_regularized():
    # The corpus identifies be as irregular, but does not encode the singular you cell.
    assert app_corpus.realize_inflection(
        "be", pos="verb", mood="indicative", tense="past",
        person="2", number="sg", lang="en",
    ) is None


def test_f7_attested_irregular_lemma_is_not_regularized_for_missing_person_cell():
    # The corpus gives be's past paradigm but not the 2nd-person singular cell.
    assert app_corpus.realize_inflection(
        "be", pos="verb", mood="indicative", tense="past",
        person="2", number="sg", lang="en",
    ) is None


def test_f7_french_homographs_keep_all_attested_analyses():
    suis = app_corpus.lookup_surface_form("suis", lang="fr")
    parle = app_corpus.lookup_surface_form("parle", lang="fr")
    assert {row.lemma for row in suis} >= {"\u00eatre", "suivre"}
    assert {row.lemma for row in parle} == {"parler"}
    assert {row.mood for row in parle} >= {"indicative", "subjunctive", "imperative"}


def test_f7_english_homograph_read_keeps_base_past_and_participle():
    rows = app_corpus.lookup_surface_form("read", lang="en")
    assert {row.mood for row in rows} >= {"infinitive", "indicative", "participle"}
    assert {row.tense for row in rows if row.mood == "indicative"} >= {"past"}


def test_f7_corpus_attested_future_venir_is_attached_to_written_subject():
    frame = parse_utterance("Ils viendront.", language="fr")
    analysis = frame.structural_analysis
    assert len(frame.units) == 1
    assert frame.units[0].lemma == "venir"
    assert frame.units[0].tense_aspect == "FUTURE"
    agreement = next(row for row in analysis["agreements"] if row["kind"] == "SUBJECT_VERB")
    assert agreement["status"] == "COMPATIBLE"
    assert agreement["expected_person"] == "3"
    assert agreement["expected_number"] == "pl"
    assert agreement["observed_person_number"] == [["3", "pl"]]
    assert analysis["boundary"]["decision_authority"] == "KX108_ONLY"
    assert analysis["boundary"]["verified_fact"] is False
    assert analysis["boundary"]["execution_authorized"] is False


@pytest.mark.parametrize(
    ("text", "tense", "lemma"),
    [("She is walking.", "PRESENT", "walk"), ("They were working.", "PAST", "work")],
)
def test_f7_be_ing_projects_progressive_without_discarding_adjective_reading(text, tense, lemma):
    frame = parse_utterance(text, language="en")
    analysis = frame.structural_analysis
    chain = analysis["verbal_chain"]
    assert chain["aspect"] == "PROGRESSIVE"
    assert chain["tense"] == tense
    assert chain["lexical_part"]["form"] == "present_participle"
    assert lemma in chain["lexical_part"]["lemma_candidates"]
    alternatives = [row for row in analysis["alternatives"]
                    if row["kind"] == "PROGRESSIVE_OR_ADJECTIVAL_PREDICATION"]
    assert alternatives and alternatives[0]["selected"] is None
    lexical_token = next(row for row in analysis["tokens"] if row["normalized"] in {"walking", "working"})
    assert lexical_token["selected_nature"] == "UNKNOWN"
    assert frame.units == ()


@pytest.mark.parametrize(
    ("text", "lang", "expected_lemma"),
    [
        ("Vous finissez.", "fr", "finir"),
        ("She wrote.", "en", "write"),
        ("They went.", "en", "go"),
        ("They have written.", "en", "write"),
    ],
)
def test_f7_held_out_sentences_use_real_parser_and_keep_source(text, lang, expected_lemma):
    frame = parse_utterance(text, language=lang)
    analysis = frame.structural_analysis
    assert frame.raw == text
    assert analysis["original"] == text
    assert analysis["language"] == lang
    boundary = analysis.get("boundary", analysis)
    assert boundary.get("decision_authority", boundary.get("authority")) == "KX108_ONLY"
    assert boundary.get("verified_fact", analysis.get("verified_fact")) is False
    if lang == "en":
        assert frame.units == ()
    else:
        assert boundary["readonly"] is True
        assert boundary["memory_write"] is False
        assert boundary["execution_authorized"] is False
        assert analysis["semantic_status"] == "NOT_EVALUATED"
    serialized = str(analysis)
    assert expected_lemma in serialized


def test_f7_unrecognized_lemma_stays_unavailable():
    assert app_corpus.realize_inflection(
        "florb", pos="verb", mood="indicative", tense="past", lang="en"
    ) is None
