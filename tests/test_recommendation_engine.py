"""Tests for transparent recommendations based only on local evidence."""

import sys
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from knowledge_engine import load_structured_lessons
from recommendation_engine import build_recommendation
from student_engine import StudentProfile


class RecommendationEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.lessons = load_structured_lessons()
        self.momentum = next(lesson for lesson in self.lessons if lesson.topic == "momentum")

    def test_no_activity_recommends_a_first_lesson_without_inventing_personalization(self) -> None:
        recommendation = build_recommendation(StudentProfile(), self.lessons)
        self.assertEqual(recommendation.kind, "start")
        self.assertIsNone(recommendation.topic)
        self.assertIn("No local learning activity", recommendation.reason)

    def test_low_quiz_accuracy_recommends_review_with_visible_evidence(self) -> None:
        profile = StudentProfile()
        profile.record_question("momentum", False)
        profile.record_question("momentum", True)
        profile.record_question("momentum", False)
        recommendation = build_recommendation(profile, self.lessons, self.momentum)
        self.assertEqual(recommendation.kind, "review")
        self.assertEqual(recommendation.topic, "momentum")
        self.assertIn("1 of 3", recommendation.reason)
        self.assertIn("33%", recommendation.reason)

    def test_authored_installed_next_topic_is_offered_after_no_low_score(self) -> None:
        profile = StudentProfile()
        profile.record_question("momentum", True)
        recommendation = build_recommendation(profile, self.lessons, self.momentum)
        self.assertEqual(recommendation.kind, "explore")
        self.assertEqual(recommendation.topic, "force")
        self.assertIn("authored next-step topics", recommendation.reason)

    def test_uninstalled_authored_next_topic_is_not_presented_as_openable(self) -> None:
        gravity = next(lesson for lesson in self.lessons if lesson.topic == "gravity")
        profile = StudentProfile()
        profile.record_lesson("gravity")
        recommendation = build_recommendation(profile, self.lessons, gravity)
        self.assertNotEqual(recommendation.topic, "mass and weight")
        self.assertEqual(recommendation.kind, "continue")


if __name__ == "__main__":
    unittest.main()
