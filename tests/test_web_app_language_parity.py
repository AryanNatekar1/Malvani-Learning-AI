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

    def test_every_lesson_on_disk_is_registered_in_both_manifests(self) -> None:
        """A lesson the website never lists is a lesson nobody can open.

        The web app fetches an explicit list rather than scanning a directory,
        and the service worker precaches another, so adding a file is three
        edits. Forgetting one fails silently: the lesson simply never appears,
        or appears but is missing offline.
        """
        on_disk = {
            path.relative_to(ROOT).as_posix() for path in LESSON_DIR.rglob("*.json")
        }
        self.assertTrue(on_disk, "no lesson files found")

        listed = set(
            re.findall(
                r'"(data/lessons/[^"]+)"',
                re.search(r"const LESSON_FILES = \[(.*?)\];", self.html, re.S).group(1),
            )
        )
        self.assertEqual(
            on_disk - listed, set(), "lesson files missing from LESSON_FILES"
        )
        self.assertEqual(
            listed - on_disk, set(), "LESSON_FILES names a file that does not exist"
        )

        service_worker = (ROOT / "sw.js").read_text(encoding="utf-8")
        precached = {
            url.lstrip("./")
            for url in re.findall(r'"(\./data/lessons/[^"]+)"', service_worker)
        }
        self.assertEqual(
            on_disk - precached, set(), "lesson files missing from the sw.js precache"
        )

    def test_browser_lookup_keeps_the_same_grounding_rules(self) -> None:
        """A static page reimplements retrieval in JS; the rules must survive.

        These are the properties that make the Python pipeline safe. If the
        browser copy quietly drops one, a student gets an uncited claim on
        the one version most of them actually use.
        """
        lookup = re.search(r"async function renderLookup\(.*?\n\}", self.html, re.S)
        self.assertIsNotNone(lookup, "index.html has no renderLookup()")
        assert lookup is not None
        body = lookup.group(0)
        # Every displayed sentence carries a citation link.
        self.assertIn('class="cite"', body)
        # A failed search refuses rather than guessing.
        self.assertIn("not going to guess", body)
        # The reader is told this is not reviewed lesson content.
        self.assertIn("checked by a teacher", body)
        # Losing the network degrades to a message, not an exception.
        self.assertIn("catch", body)

    def test_browser_retrieval_rejects_passages_with_no_source(self) -> None:
        search = re.search(r"async function wikiSearch\(.*?\n\}", self.html, re.S)
        self.assertIsNotNone(search)
        assert search is not None
        self.assertIn("p.url && p.title", search.group(0))

    def test_browser_selection_matches_the_python_scoring(self) -> None:
        """Same three corrections, or the two produce different answers."""
        select = re.search(r"function wikiSelect\(.*?\n\}", self.html, re.S)
        self.assertIsNotNone(select)
        assert select is not None
        body = select.group(0)
        self.assertIn("1.5", body)   # lead-sentence bonus
        self.assertIn("0.6", body)   # search-rank decay
        self.assertIn("0.25", body)  # mild length penalty
        self.assertIn("0.7", body)   # near-duplicate threshold

        import extractive_answer as extractive

        self.assertEqual(extractive.LEAD_SENTENCE_BONUS, 1.5)
        self.assertEqual(extractive.RANK_DECAY, 0.6)
        self.assertEqual(extractive.MINIMUM_SENTENCE_CHARACTERS, 40)
        self.assertEqual(extractive.MAXIMUM_SENTENCE_CHARACTERS, 320)
        splitter = re.search(r"function wikiSentences\(.*?\n\}", self.html, re.S)
        self.assertIsNotNone(splitter)
        assert splitter is not None
        self.assertIn("40", splitter.group(0))
        self.assertIn("320", splitter.group(0))

    def test_lookup_is_not_precached_as_if_it_worked_offline(self) -> None:
        """The offline promise covers lessons, and must not appear to cover this."""
        service_worker = (ROOT / "sw.js").read_text(encoding="utf-8")
        self.assertNotIn("wikipedia.org", service_worker)

    def test_lesson_tabs_are_addressable_and_fall_back_safely(self) -> None:
        """A teacher can link straight to a tab; a bad one must not blank the page."""
        self.assertIn("function renderLesson(topic, tab)", self.html)
        self.assertIn('tab = tab || "understand"', self.html)
        self.assertIn('if(!panels[name]) name = "understand"', self.html)
        # replaceState, not pushState: Back should leave the lesson rather than
        # walking the student back through every tab they opened.
        self.assertIn("history.replaceState", self.html)
        self.assertNotIn("history.pushState", self.html)


if __name__ == "__main__":
    unittest.main()
