"""Tests for the promises the project makes in its own README.

Two kinds of claim get made in documentation and then quietly stop being true:
"it works without the internet", and "every lesson has a diagram". Both are
easy to break by adding a feature or a lesson, and neither failure is visible
from the outside. These tests hold them.
"""

import json
import re
import socket
import sys
import unittest
from contextlib import contextmanager
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

ROOT = Path(__file__).resolve().parent.parent
LESSON_DIR = ROOT / "data" / "lessons"
INDEX = ROOT / "index.html"


@contextmanager
def no_network():
    """Make every outbound connection fail, the way a rural signal drop does.

    Patching the socket constructor rather than a provider catches the case
    this is really guarding against: a new feature reaching the network from
    somewhere nobody thought to mock.
    """
    real_socket = socket.socket
    real_create = socket.create_connection

    def refuse(*args, **kwargs):
        raise OSError("network disabled for this test")

    socket.socket = refuse  # type: ignore[assignment]
    socket.create_connection = refuse  # type: ignore[assignment]
    try:
        yield
    finally:
        socket.socket = real_socket  # type: ignore[assignment]
        socket.create_connection = real_create  # type: ignore[assignment]


class OfflineTests(unittest.TestCase):
    """The headline promise: a learner on no connection loses nothing."""

    def test_lessons_and_places_load_with_no_network(self) -> None:
        from knowledge_engine import load_structured_lessons
        from place_engine import load_places

        with no_network():
            lessons = load_structured_lessons(LESSON_DIR)
            places = load_places(ROOT / "data" / "places")
        self.assertEqual(len(lessons), 19)
        self.assertTrue(places)

    def test_a_full_lesson_renders_with_no_network(self) -> None:
        from app_controller import AppController

        with no_network():
            controller = AppController()
            response = controller.answer_question("What is gravity?")
            self.assertTrue(response.is_structured)
            for action in ("simple", "example", "observe", "places", "think"):
                with self.subTest(action=action):
                    self.assertTrue(controller.lesson_action(action).text.strip())

    def test_a_quiz_can_be_taken_with_no_network(self) -> None:
        from app_controller import AppController

        with no_network():
            controller = AppController()
            controller.answer_question("What is gravity?")
            controller.start_quiz()
            self.assertIsNotNone(controller.quiz_view())

    def test_looking_up_a_topic_fails_gracefully_with_no_network(self) -> None:
        """The one networked action must degrade, not raise."""
        from app_controller import AppController

        with no_network():
            controller = AppController()
            controller.answer_question("Explain dispersion of light")
            response = controller.look_up_topic()
        self.assertIn("without the internet", response.text)

    def test_retrieval_returns_nothing_rather_than_raising(self) -> None:
        from wikipedia_retrieval import WikipediaRetrievalProvider

        with no_network():
            self.assertEqual(WikipediaRetrievalProvider().search("gravity"), ())


class DiagramPromiseTests(unittest.TestCase):
    """The README says every lesson opens with a diagram. Nothing checked it."""

    def setUp(self) -> None:
        self.html = INDEX.read_text(encoding="utf-8")
        start = self.html.index("const CONCEPT_VISUALS")
        self.visuals_block = self.html[start : self.html.index("\n};", start)]
        self.visual_keys = set(
            re.findall(r'^  "?([a-z][a-z ]*?)"?: \{', self.visuals_block, re.M)
        )
        self.topics = {
            json.loads(path.read_text(encoding="utf-8"))["topic"]
            for path in LESSON_DIR.rglob("*.json")
        }

    def test_every_lesson_has_a_diagram(self) -> None:
        missing = sorted(self.topics - self.visual_keys)
        self.assertEqual(missing, [], f"lessons with no diagram: {missing}")

    def test_no_diagram_points_at_a_lesson_that_does_not_exist(self) -> None:
        orphaned = sorted(self.visual_keys - self.topics)
        self.assertEqual(orphaned, [], f"diagrams with no lesson: {orphaned}")

    def test_every_diagram_carries_a_text_alternative(self) -> None:
        """Nothing in this app may be available only as a picture."""
        self.assertEqual(
            len(re.findall(r"\balt:", self.visuals_block)),
            len(self.visual_keys),
            "a diagram is missing its alt text",
        )

    def test_every_diagram_has_a_readout(self) -> None:
        self.assertEqual(
            len(re.findall(r"\bread:", self.visuals_block)), len(self.visual_keys)
        )


class LessonContentPromiseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.records = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(LESSON_DIR.rglob("*.json"))
        ]

    def test_every_lesson_has_a_quiz(self) -> None:
        for record in self.records:
            with self.subTest(topic=record["topic"]):
                self.assertTrue(record.get("quiz_questions"))

    def test_every_lesson_has_a_challenge(self) -> None:
        for record in self.records:
            with self.subTest(topic=record["topic"]):
                self.assertTrue(record.get("challenge"))

    def test_every_lesson_names_a_source(self) -> None:
        for record in self.records:
            with self.subTest(topic=record["topic"]):
                self.assertTrue(record.get("sources"))

    def test_no_lesson_claims_to_be_reviewed(self) -> None:
        """Nothing may say VERIFIED until a person has actually checked it."""
        for record in self.records:
            with self.subTest(topic=record["topic"]):
                self.assertEqual(record["verification_status"], "NEEDS_REVIEW")

    def test_every_quiz_answer_is_one_of_its_options(self) -> None:
        """A correct answer not among the options can never be chosen."""
        for record in self.records:
            for question in record.get("quiz_questions", []):
                options = question.get("options") or []
                if not options:
                    continue
                correct = question.get("correct_answers", [])
                with self.subTest(topic=record["topic"], question=question["id"]):
                    self.assertTrue(
                        any(answer in options for answer in correct),
                        f"no correct answer appears in the options",
                    )

    def test_quiz_options_are_not_duplicated(self) -> None:
        for record in self.records:
            for question in record.get("quiz_questions", []):
                options = question.get("options") or []
                with self.subTest(topic=record["topic"], question=question["id"]):
                    self.assertEqual(len(options), len(set(options)))


if __name__ == "__main__":
    unittest.main()
