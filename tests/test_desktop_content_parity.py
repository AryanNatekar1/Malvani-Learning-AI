"""The desktop app must teach the same content the website does.

Both apps read the same JSON, which is only half of "one source of truth": the
desktop app parsed observations and places for a while without ever showing
them, so a student on the desktop app silently saw less. These tests pin the
two together at the level that matters — what reaches a learner.
"""

import sys
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from app_controller import AppController
from knowledge_engine import get_structured_lesson, load_structured_lessons
from teaching_engine import TeachingEngine

LESSON_DIR = Path(__file__).resolve().parent.parent / "data" / "lessons"
INDEX = Path(__file__).resolve().parent.parent / "index.html"


class DesktopContentParityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = TeachingEngine()

    def test_every_lesson_can_render_its_observation(self) -> None:
        for lesson in load_structured_lessons(LESSON_DIR):
            with self.subTest(topic=lesson.topic):
                response = self.engine.build_response(
                    lesson, "Class 9", "English", action="observe"
                )
                text = response.as_text()
                self.assertIn("LOOK AROUND YOU", text)
                assert lesson.observe_around_you is not None
                self.assertIn(lesson.observe_around_you.what_to_notice, text)

    def test_the_full_flow_includes_the_observation(self) -> None:
        """Not just on request: a learner reading the whole lesson should see it."""
        lesson = get_structured_lesson("waves")
        assert lesson is not None
        text = self.engine.build_response(lesson, "Class 9", "English").as_text()
        self.assertIn("LOOK AROUND YOU", text)

    def test_the_explanation_follows_the_instructions(self) -> None:
        """A learner who wants to look first must be able to stop reading."""
        lesson = get_structured_lesson("gravity")
        assert lesson is not None
        activity = lesson.observe_around_you
        assert activity is not None
        body = self.engine.build_response(
            lesson, "Class 9", "English", action="observe"
        ).sections[0].body
        self.assertLess(
            body.index(activity.what_to_do),
            body.index(activity.concept_link),
            "the answer appears before the instruction to go and watch",
        )

    def test_places_reach_the_desktop_app(self) -> None:
        text = self.engine.build_response(
            get_structured_lesson("waves"), "Class 9", "English", action="places"
        ).as_text()
        self.assertIn("PLACES NEAR YOU", text)
        self.assertIn("coastline of Sindhudurg", text)
        self.assertIn("draft records", text)

    def test_a_topic_with_no_place_says_so_instead_of_failing(self) -> None:
        text = self.engine.build_response(
            get_structured_lesson("algorithms"), "Class 9", "English", action="places"
        ).as_text()
        self.assertIn("No place record connects to this lesson yet", text)

    def test_the_controller_exposes_both_actions(self) -> None:
        controller = AppController()
        controller.answer_question("Explain waves")
        for action, expected in (("observe", "LOOK AROUND YOU"), ("places", "PLACES NEAR YOU")):
            with self.subTest(action=action):
                self.assertIn(expected, controller.lesson_action(action).text)

    def test_both_apps_offer_the_observation(self) -> None:
        """Guard against the web app and desktop app drifting apart again."""
        html = INDEX.read_text(encoding="utf-8")
        self.assertIn("Look around you", html)
        self.assertIn("function buildObserve(", html)


if __name__ == "__main__":
    unittest.main()
