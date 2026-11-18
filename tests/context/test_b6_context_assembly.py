"""B6 context assembly: conditional instructions, tiered capability disclosure, replayable packet."""
from __future__ import annotations

import json

from brody.context.capabilities import DisclosureLevel, disclose
from brody.context.context_assembly import assemble_context
from brody.context.contracts import StateEntry
from brody.context.instructions import DEFAULT_INSTRUCTIONS, select_instructions
from brody.context.registry import WorkingStateRegistry
from brody.context.sens_adapter import sens_state_entries

_MATRIX = {
    "categories": ["PURE_RESPONSE", "MEMORY_READ"],
    "matrix": {
        "PURE_RESPONSE": {"brody_may": ["repondre"], "brody_must_not": ["decider"], "response_mode": "FULL"},
        "MEMORY_READ": {"brody_may": ["lire_memoire"], "brody_must_not": ["ecrire_memoire"],
                        "requires_memory_gate": True},
    },
}

_D4 = "Si le script qui teste P " + chr(0xE9) + "choue, lance R."


def _registry(text="Lance P."):
    r = WorkingStateRegistry()
    for e in sens_state_entries(text):
        r.register(e)
    return r


def test_instructions_are_conditional():
    always = {i.instruction_id for i in DEFAULT_INSTRUCTIONS if i.always}
    plain = {i.instruction_id for i in select_instructions(frozenset())}
    assert plain == always
    opened = {i.instruction_id for i in select_instructions(frozenset({"status:open"}))}
    assert opened > plain


def test_capability_disclosure_is_not_permission():
    for level in DisclosureLevel:
        d = disclose(_MATRIX, level)
        assert d["disclosure_is_permission"] is False and d["execution_authority"] == "KX108_ONLY"
    assert "categories" not in disclose(_MATRIX, DisclosureLevel.SUMMARY)
    assert disclose(_MATRIX, DisclosureLevel.CATEGORY)["categories"] == ["MEMORY_READ", "PURE_RESPONSE"]
    exact = disclose(_MATRIX, DisclosureLevel.EXACT, categories=("MEMORY_READ",))
    assert exact["capabilities"]["MEMORY_READ"]["brody_may"] == ["lire_memoire"]
    assert set(exact["capabilities"]) == {"MEMORY_READ"}


def test_packet_is_replayable_serializable_and_bounded():
    a = assemble_context("Lance P.", _registry(), capability_matrix=_MATRIX)
    b = assemble_context("Lance P.", _registry(), capability_matrix=_MATRIX)
    assert a.to_dict() == b.to_dict() and a.packet_id == b.packet_id
    d = json.loads(a.to_json())
    assert d["boundary"]["decision_authority"] == "KX108_ONLY" and d["boundary"]["emits_act"] is False
    assert {"query", "projection", "instructions", "capabilities", "provenance_refs", "unknowns",
            "omitted"} <= set(d)


def test_d4_context_preserves_conditional_input_without_open_status():
    p = assemble_context(_D4, _registry(_D4), capability_matrix=_MATRIX)
    packet = p.to_dict()
    instructions = {i["instruction_id"] for i in packet["instructions"]}
    state = next(s for s in packet["state"] if s["state_id"] == "sens:frame")

    # D4's meaning is structurally resolved. The epistemic conditional remains verbatim in
    # the query/payload preview; the context makes no truth claim and authorizes no action.
    assert packet["query"] == _D4 and _D4 in state["payload_preview"]
    assert state["status"] == "KNOWN" and state["uncertainty"] == []
    assert "sens_open_meaning" not in instructions
    assert "requested_action_not_authorized" in instructions
    assert state["source_ref"] in packet["provenance_refs"]
    assert state["visibility_is_permission"] is False
    assert packet["unknowns"] == []
    assert packet["boundary"]["decision_authority"] == "KX108_ONLY"
    assert packet["boundary"]["memory_write"] is False
    assert packet["boundary"]["emits_act"] is False


def test_memory_entries_are_projected_without_entering_the_registry():
    r = _registry()
    mem = StateEntry(state_id="mem:1", state_type="NATIVE_MEMORY_ITEM", source_ref="native:1", payload={},
                     tags=("lance",))
    p = assemble_context("Lance P.", r, capability_matrix=_MATRIX, memory_entries=(mem,))
    assert "mem:1" in [i["state_id"] for i in p.projection["included"]]
    assert "mem:1" not in [e.state_id for e in r.list_entries()]
