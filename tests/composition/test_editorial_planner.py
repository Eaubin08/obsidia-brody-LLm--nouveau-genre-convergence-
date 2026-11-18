"""tests/composition/test_editorial_planner.py — Tests du planificateur et réalisateur rhétorique natif."""
from __future__ import annotations

import pytest

from brody.composition import (
    recognize_native_editorial_request,
    compose_native_editorial,
    realize_brody_editorial_plan,
    SCHEMA_EDITORIAL_V1,
    SCHEMA_EDITORIAL_V2,
)
from brody.composition.editorial_planner import (
    _operations,
    _select_and_plan,
    _v2_operations,
    _v2_select_and_plan,
)


SAMPLE_BRIEF = (
    "Rédige une publication LinkedIn expliquant comment une petite entreprise peut utiliser l’IA pour gagner du temps."
)


def test_recognize_native_editorial_request():
    req = recognize_native_editorial_request(SAMPLE_BRIEF)
    assert req is not None
    assert req.get("editorial_intent") == "consultative_draft"
    assert req.get("platform") == "linkedin"
    assert req.get("supported") is True


def test_v1_operations_and_planning():
    req = recognize_native_editorial_request(SAMPLE_BRIEF)
    ops = _operations(req, version="V1")
    assert len(ops) >= 6
    selected, plan = _select_and_plan(ops, req["constraints"], version="V1")
    assert len(plan) == 4
    roles = [step["role"] for step in plan]
    assert roles == ["introduction", "development", "example", "conclusion"]


def test_v2_operations_and_planning():
    req = recognize_native_editorial_request(SAMPLE_BRIEF)
    ops_v1 = _operations(req, version="V1")
    ops_v2 = _v2_operations(req, ops_v1)
    assert any(p["id"] == "reader_need" for p in ops_v2)
    selected, plan = _v2_select_and_plan(ops_v2, req["constraints"])
    assert len(plan) == 5
    roles = [step["role"] for step in plan]
    assert roles == ["problem", "main_idea", "explanation", "example", "conclusion"]


def test_compose_native_editorial_v1():
    res = compose_native_editorial(SAMPLE_BRIEF, version="V1")
    assert res["editorial_route_status"] == "CONSULTATIVE_DRAFT_AVAILABLE"
    assert res["final_answer_source"] == SCHEMA_EDITORIAL_V1
    assert res["editorial_version_selected"] == "V1"
    draft = res["editorial_artifact"]["draft"]["text"]
    assert len(draft) > 100
    assert "Une petite entreprise commencerait" in draft
    assert res["human_approval_required"] is True
    assert res["publication_permitted"] is False
    assert res["editorial_artifact"]["provenance"]["model_calls"] == 0


def test_compose_native_editorial_v2():
    res = compose_native_editorial(SAMPLE_BRIEF, version="V2")
    assert res["editorial_route_status"] == "CONSULTATIVE_DRAFT_AVAILABLE"
    assert res["final_answer_source"] == SCHEMA_EDITORIAL_V2
    assert res["editorial_version_selected"] == "V2"
    draft = res["editorial_artifact"]["draft"]["text"]
    assert "Est-ce que votre équipe peut gagner du temps avec l’IA" in draft
    assert "Commencez par une seule tâche répétitive" in draft
    assert "Par exemple, un premier essai" in draft
    assert "Avant de poursuivre, comparez le temps passé" in draft
    assert res["human_approval_required"] is True
    assert res["publication_permitted"] is False
    assert res["editorial_artifact"]["provenance"]["model_calls"] == 0


def test_unsupported_brief_routes_to_refused():
    res = compose_native_editorial("Bonjour comment ça va ?")
    assert res["editorial_route_status"] == "REFUSED"
    assert res["human_approval_required"] is True
    assert res["publication_permitted"] is False
