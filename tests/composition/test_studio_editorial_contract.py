"""tests/composition/test_studio_editorial_contract.py — Tests du contrat éditorial déterministe Studio."""
from __future__ import annotations

import unittest
from brody.composition import build_readonly_draft


class StudioEditorialContractTests(unittest.TestCase):
    def test_template_never_claims_cognitive_synthesis(self):
        r = build_readonly_draft("Mémoire cognitive", "", "LinkedIn")
        self.assertIn("[Ce qui a réellement été réalisé", r["text"])
        self.assertEqual(r["provenance"]["source"], "STUDIO_DETERMINISTIC_TEMPLATE")
        self.assertFalse(r["provenance"]["publication_permitted"])
        self.assertFalse(r["provenance"]["brody_post_model_synthesis_proven"])
        self.assertEqual(r["provenance"]["cognitive_gate"], "NOT_CALLED")
        self.assertTrue(r["provenance"]["human_approval_required"])

    def test_source_is_preserved(self):
        r = build_readonly_draft("titre", "  Texte précis fourni.  ", "LinkedIn")
        self.assertEqual(r["text"], "Texte précis fourni.")
        self.assertEqual(r["provenance"]["source"], "USER_SOURCE_TEXT_ONLY")
        self.assertIn("Vérification humaine requise", r["warning"])

    def test_empty_input_refused(self):
        with self.assertRaises(ValueError):
            build_readonly_draft("  ", "  ", "LinkedIn")


if __name__ == "__main__":
    unittest.main()
