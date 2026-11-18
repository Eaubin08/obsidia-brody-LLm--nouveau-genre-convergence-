"""tests/composition/test_editorial_intent.py — Tests de l'intention éditoriale."""
from __future__ import annotations

import unittest
from brody.composition import explanatory_editorial_request


class EditorialIntentTests(unittest.TestCase):
    def test_request_contains_readonly_explanatory_question(self):
        text = explanatory_editorial_request(
            "Pourquoi une IA doit comprendre avant d'agir ?", "LinkedIn"
        )
        self.assertIn("Rédige une publication LinkedIn expliquant", text)
        self.assertTrue(text.endswith("Pourquoi une IA doit comprendre avant d'agir ?"))
        self.assertNotIn("ALLOW", text)

    def test_non_question_topic_is_made_explicit(self):
        text = explanatory_editorial_request("La gouvernance cognitive", "LinkedIn")
        self.assertTrue(text.endswith("La gouvernance cognitive"))
        self.assertNotIn("Pourquoi La gouvernance", text)

    def test_preserves_existing_writing_directive(self):
        text = explanatory_editorial_request("Rédige un post sur la mémoire", "LinkedIn")
        self.assertEqual(text, "Rédige un post sur la mémoire")

    def test_appends_source_context_safely(self):
        text = explanatory_editorial_request("Sujet", "LinkedIn", source_text="Faits établis ici.")
        self.assertIn("Contexte fourni :\nFaits établis ici.", text)

    def test_no_subject_raises(self):
        with self.assertRaises(ValueError):
            explanatory_editorial_request("  ")


if __name__ == "__main__":
    unittest.main()
