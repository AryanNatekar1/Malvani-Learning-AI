"""Tests for the drafting command and the wall around what it writes.

The safety property matters more than the command: a machine-assembled draft
must be unreachable by the app no matter what it contains. If a draft could be
loaded as a lesson, every rule about reviewed content would have a way around
it.
"""

import contextlib
import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))
sys.path.insert(0, str(PROJECT_DIR / "scripts"))

from grounded_answer import Passage
from knowledge_engine import load_structured_lessons

DRAFT_DIR = PROJECT_DIR / "data" / "lesson_drafts"
LESSON_DIR = PROJECT_DIR / "data" / "lessons"

REFRACTION = Passage(
    text=(
        "Refraction is the change in direction of a wave as it passes from one "
        "medium to another. Optical prisms and lenses use refraction to "
        "redirect light, as does the human eye."
    ),
    title="Refraction",
    url="https://en.wikipedia.org/wiki/Refraction",
)


class DraftIsolationTests(unittest.TestCase):
    """A draft must be invisible to the app that teaches students."""

    def test_drafts_live_outside_the_lesson_folder(self) -> None:
        self.assertFalse(
            str(DRAFT_DIR).startswith(str(LESSON_DIR)),
            "drafts are inside the folder the lesson loader reads",
        )

    def test_the_lesson_loader_does_not_pick_up_drafts(self) -> None:
        loaded = {lesson.topic for lesson in load_structured_lessons(LESSON_DIR)}
        for path in DRAFT_DIR.glob("*.json"):
            record = json.loads(path.read_text(encoding="utf-8"))
            with self.subTest(draft=path.name):
                self.assertNotIn(record["topic"], loaded)

    def test_every_draft_on_disk_is_marked_unreviewed(self) -> None:
        for path in DRAFT_DIR.glob("*.json"):
            record = json.loads(path.read_text(encoding="utf-8"))
            with self.subTest(draft=path.name):
                self.assertEqual(record["verification_status"], "NEEDS_REVIEW")
                self.assertIn("generated", record)
                self.assertTrue(record["sources"])

    def test_no_draft_invents_a_quiz_or_challenge(self) -> None:
        for path in DRAFT_DIR.glob("*.json"):
            record = json.loads(path.read_text(encoding="utf-8"))
            for absent in ("quiz_questions", "challenge", "reasoning_guide"):
                with self.subTest(draft=path.name, field=absent):
                    self.assertNotIn(absent, record)

    def test_the_folder_explains_itself(self) -> None:
        readme = (DRAFT_DIR / "README.md").read_text(encoding="utf-8")
        # Collapse wrapping before matching: the sentence is real, it just
        # spans a line break, and a test should not pin the line width.
        flattened = " ".join(readme.split())
        self.assertIn("Nothing in this folder reaches a student", flattened)
        self.assertIn("data/lessons/", flattened)


class DraftCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        import draft_lesson

        self.module = draft_lesson
        # The command is built to report to a person at a terminal. Let it,
        # into a buffer, so a passing suite stays readable.
        # stderr too: argparse prints its usage there when it rejects a bad
        # choice, and two of these tests exist to prove it does.
        for redirect in (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            redirect.__enter__()
            self.addCleanup(redirect.__exit__, None, None, None)

    def _with_results(self, passages):
        return mock.patch.object(
            self.module,
            "WikipediaRetrievalProvider",
            return_value=mock.Mock(search=mock.Mock(return_value=tuple(passages))),
        )

    def test_a_dry_run_writes_nothing(self) -> None:
        with self._with_results([REFRACTION]):
            with mock.patch.object(self.module, "draft_lesson") as drafter:
                code = self.module.main(["refraction", "--dry-run"])
        self.assertEqual(code, 0)
        drafter.return_value.write.assert_not_called()

    def test_writing_produces_a_loadable_draft(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            with self._with_results([REFRACTION]):
                code = self.module.main(["refraction", "--out", directory])
            self.assertEqual(code, 0)
            written = list(Path(directory).glob("*.json"))
            self.assertEqual(len(written), 1)
            record = json.loads(written[0].read_text(encoding="utf-8"))
            self.assertEqual(record["verification_status"], "NEEDS_REVIEW")
            self.assertTrue(record["sources"])

    def test_no_search_results_is_an_error_not_an_empty_draft(self) -> None:
        with self._with_results([]):
            self.assertEqual(self.module.main(["refraction"]), 1)

    def test_nothing_supported_is_an_error_not_a_guess(self) -> None:
        unrelated = Passage(
            text=(
                "The mango is a tropical stone fruit grown widely across the "
                "Konkan coast and harvested before the rains arrive."
            ),
            title="Mango",
            url="https://en.wikipedia.org/wiki/Mango",
        )
        with self._with_results([unrelated]):
            self.assertEqual(self.module.main(["refraction of light"]), 1)

    def test_the_subject_must_be_one_the_app_teaches(self) -> None:
        with self.assertRaises(SystemExit):
            self.module.main(["refraction", "--subject", "Astrology"])

    def test_the_language_must_be_one_with_an_edition(self) -> None:
        with self.assertRaises(SystemExit):
            self.module.main(["refraction", "--language", "Klingon"])


if __name__ == "__main__":
    unittest.main()
