"""Tests for misconceptions asked as questions rather than printed as a list.

A list headed "these are not true" treats every learner identically and learns
nothing about any of them. Asked first, the same sentence tells the app which
misconception this particular learner holds — which matters because two
learners wrong about photosynthesis may be wrong in different ways, one
thinking the food comes from the soil and the other that it comes from the air.
"""

import json
import re
import sys
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from knowledge_engine import load_structured_lessons
from lesson_models import LessonFormatError, Misconception

ROOT = Path(__file__).resolve().parent.parent
LESSON_DIR = ROOT / "data" / "lessons"
INDEX = ROOT / "index.html"


class MisconceptionModelTests(unittest.TestCase):
    def test_a_plain_sentence_is_still_valid(self) -> None:
        """Lessons were authored as strings and must not need rewriting."""
        parsed = Misconception.from_value("Heavier objects fall faster.")
        self.assertEqual(parsed.statement, "Heavier objects fall faster.")
        self.assertEqual(parsed.correction, "")

    def test_a_statement_can_carry_its_correction(self) -> None:
        parsed = Misconception.from_value(
            {"statement": "Heavier objects fall faster.", "correction": "They land together."}
        )
        self.assertEqual(parsed.correction, "They land together.")

    def test_a_misconception_without_a_statement_is_rejected(self) -> None:
        for bad in ({"correction": "only a correction"}, {"statement": "   "}, 7, None):
            with self.subTest(value=bad):
                with self.assertRaises(LessonFormatError):
                    Misconception.from_value(bad)


class MisconceptionContentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.lessons = load_structured_lessons(LESSON_DIR)

    def test_every_misconception_has_a_correction(self) -> None:
        """Being told you are wrong without being told what is right is useless."""
        for lesson in self.lessons:
            for item in lesson.common_misconceptions:
                with self.subTest(topic=lesson.topic, statement=item.statement[:40]):
                    self.assertTrue(
                        item.correction.strip(),
                        f"{lesson.topic}: no correction for {item.statement!r}",
                    )

    def test_a_correction_does_not_merely_repeat_the_statement(self) -> None:
        for lesson in self.lessons:
            for item in lesson.common_misconceptions:
                with self.subTest(topic=lesson.topic):
                    self.assertNotEqual(
                        item.correction.strip().lower(), item.statement.strip().lower()
                    )

    def test_a_statement_asks_about_exactly_one_belief(self) -> None:
        """A compound statement cannot be answered true or false honestly.

        No test can decide whether a sentence is true, and a denial is not the
        giveaway — "an object standing still cannot have any energy" is a
        belief learners really hold. What a test can check is shape. Two claims
        joined by a semicolon leave a learner who agrees with one and not the
        other no way to answer, and that shape is also how the old mistakes
        looked: a denial followed by the correction in the same breath.
        """
        for lesson in self.lessons:
            for item in lesson.common_misconceptions:
                with self.subTest(topic=lesson.topic, statement=item.statement[:40]):
                    self.assertNotIn(
                        ";",
                        item.statement,
                        "two claims in one statement: a learner may agree with "
                        "one half and not the other",
                    )
                    self.assertLessEqual(
                        len(item.statement),
                        190,
                        "too long to answer true or false to at a glance",
                    )

    def test_a_correction_actually_says_something_more(self) -> None:
        """A learner who ticks wrongly needs what to believe instead."""
        for lesson in self.lessons:
            for item in lesson.common_misconceptions:
                with self.subTest(topic=lesson.topic):
                    self.assertGreaterEqual(len(item.correction.split()), 8)

    def test_every_lesson_still_has_misconceptions(self) -> None:
        without = [l.topic for l in self.lessons if not l.common_misconceptions]
        self.assertEqual(without, [], f"lessons with none: {without}")

    def test_the_stored_shape_is_the_one_the_browser_reads(self) -> None:
        raw = json.loads(
            (LESSON_DIR / "physics" / "gravity.json").read_text(encoding="utf-8")
        )
        entry = raw["common_misconceptions"][0]
        self.assertIsInstance(entry, dict)
        self.assertIn("statement", entry)
        self.assertIn("correction", entry)


class BrowserBehaviourTests(unittest.TestCase):
    """The change that matters is in the lesson screen, not the data."""

    def setUp(self) -> None:
        self.html = INDEX.read_text(encoding="utf-8")

    def test_the_browser_asks_before_it_corrects(self) -> None:
        block = re.search(r"function mythBlock\(.*?\n\}", self.html, re.S)
        self.assertIsNotNone(block, "index.html has no mythBlock()")
        assert block is not None
        body = block.group(0)
        self.assertIn("true or false", body.lower())
        self.assertIn('data-say="true"', body)
        self.assertIn('data-say="false"', body)

    def test_the_old_list_of_falsehoods_is_gone(self) -> None:
        self.assertNotIn("these are <em", self.html)
        self.assertNotIn("Common mistakes —", self.html)

    def test_a_plain_string_misconception_still_renders(self) -> None:
        """Older data must not break the screen."""
        self.assertIn("function normaliseMyth(", self.html)
        normalise = re.search(r"function normaliseMyth\(.*?\n\}", self.html, re.S)
        assert normalise is not None
        self.assertIn('typeof entry === "string"', normalise.group(0))

    def test_what_a_learner_believed_is_kept_only_on_their_device(self) -> None:
        """It is a note back to the learner, never a score and never sent."""
        record = re.search(r"function recordMyth\(.*?\n\}", self.html, re.S)
        self.assertIsNotNone(record)
        assert record is not None
        self.assertIn("state.progress.myths", record.group(0))
        self.assertIn("saveProgress", record.group(0))
        # Progress is localStorage only; nothing here may post it anywhere.
        self.assertNotIn("fetch(", record.group(0))

    def test_clearing_progress_clears_the_answers_too(self) -> None:
        reset = re.search(r"state\.progress = \{[^}]*\}", self.html)
        self.assertIsNotNone(reset)
        assert reset is not None
        self.assertIn("myths", reset.group(0))

    def test_what_was_collected_is_given_back_to_the_learner(self) -> None:
        """Asking and then doing nothing with the answers is worse than not asking.

        It spends a learner's time and returns nothing. The answers have to
        reappear somewhere they can act on.
        """
        block = re.search(r"function revisitBlock\(.*?\n\}", self.html, re.S)
        self.assertIsNotNone(block, "nothing uses the answers that were collected")
        assert block is not None
        body = block.group(0)
        self.assertIn("state.progress.myths", body)
        # It must name the belief and link back, not report a score.
        self.assertIn("myth-claim", body)
        self.assertIn("#/lesson/", body)
        self.assertIn("revisitBlock()", self.html)

    def test_a_renamed_or_removed_lesson_does_not_break_the_page(self) -> None:
        """Saved answers outlive content changes, so stale keys must be skipped."""
        block = re.search(r"function revisitBlock\(.*?\n\}", self.html, re.S)
        assert block is not None
        self.assertIn("if(!lesson || !entry) continue", block.group(0))

    def test_a_returning_learner_is_not_asked_again(self) -> None:
        block = re.search(r"function mythBlock\(.*?\n\}", self.html, re.S)
        assert block is not None
        self.assertIn("state.progress.myths", block.group(0))


if __name__ == "__main__":
    unittest.main()
