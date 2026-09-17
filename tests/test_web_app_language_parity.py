"""The web app's language gate must match the Python one.

The browser app reimplements resolve_lesson_language() in JavaScript, because
it cannot import Python. That duplication is the risk: if one side drifts, an
unreviewed translation reaches a student on the website while the desktop app
correctly hides it. These tests read index.html as text and check the parts
that must agree.
"""

import json
import re
import sys
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from language_engine import SUPPORTED_LANGUAGES

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
LESSON_DIR = ROOT / "data" / "lessons"


class WebAppLanguageParityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.html = INDEX.read_text(encoding="utf-8")

    def test_web_app_offers_the_same_languages(self) -> None:
        match = re.search(r"const LANGUAGES = \[(.*?)\];", self.html, re.S)
        self.assertIsNotNone(match, "index.html has no LANGUAGES list")
        assert match is not None
        listed = tuple(re.findall(r'"([^"]+)"', match.group(1)))
        self.assertEqual(listed, SUPPORTED_LANGUAGES)

    def test_web_app_requires_verified_and_a_source(self) -> None:
        """Both conditions must appear, or a draft could render to a student."""
        match = re.search(
            r"function resolveLessonLanguage\(.*?\n\}", self.html, re.S
        )
        self.assertIsNotNone(match, "index.html has no resolveLessonLanguage()")
        assert match is not None
        body = match.group(0)
        self.assertIn('verification_status === "VERIFIED"', body)
        self.assertIn("meta.source", body)
        self.assertIn('requested === "English"', body)

    def test_no_lesson_would_render_a_draft_translation(self) -> None:
        """Right now every non-English variant is a draft, so none may show.

        This also guards the reverse mistake: marking a translation VERIFIED
        while leaving its source empty.
        """
        for path in sorted(LESSON_DIR.rglob("*.json")):
            record = json.loads(path.read_text(encoding="utf-8"))
            for language, meta in record.get("language_metadata", {}).items():
                if language == "English":
                    continue
                with self.subTest(lesson=path.stem, language=language):
                    if meta.get("verification_status") == "VERIFIED":
                        self.assertTrue(
                            meta.get("source"),
                            "a verified translation must name who checked it",
                        )

    def test_the_marathi_waves_draft_exists_and_stays_hidden(self) -> None:
        """The review workflow only works if the draft is present but gated."""
        record = json.loads(
            (LESSON_DIR / "physics" / "waves.json").read_text(encoding="utf-8")
        )
        self.assertIn("Marathi", record["content"])
        marathi = record["content"]["Marathi"]
        for field in ("simple_explanation", "detailed_explanation", "everyday_example"):
            self.assertTrue(marathi.get(field, "").strip(), f"Marathi {field} is empty")
        meta = record["language_metadata"]["Marathi"]
        self.assertEqual(meta["verification_status"], "NEEDS_REVIEW")
        self.assertIsNone(meta["source"])

    def test_paragraph_breaks_are_preserved_in_lesson_prose(self) -> None:
        self.assertIn("function escPara(", self.html)
        self.assertIn("escPara(en.detailed_explanation)", self.html)


if __name__ == "__main__":
    unittest.main()
