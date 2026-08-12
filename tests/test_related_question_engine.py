"""Tests for deterministic, lesson-bound follow-up question answers."""

import sys
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from knowledge_engine import get_structured_lesson
from related_question_engine import (
    APPLICATIONS,
    CAREERS,
    DEFINITION,
    EXAMPLE,
    EXPLANATION,
    FORMULA,
    MISCONCEPTION,
    NEXT_STEPS,
    answer_related_question,
    classify_related_question,
)


class RelatedQuestionEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        gravity = get_structured_lesson("gravity")
        momentum = get_structured_lesson("momentum")
        force = get_structured_lesson("force")
        assert gravity is not None
        assert momentum is not None
        assert force is not None
        self.gravity = gravity
        self.momentum = momentum
        self.force = force

    def test_classifies_bounded_follow_up_types(self) -> None:
        examples = {
            "What is it?": DEFINITION,
            "Why does this happen?": EXPLANATION,
            "How?": EXPLANATION,
            "What is the formula?": FORMULA,
            "Give me an example": EXAMPLE,
            "What are its real-world uses?": APPLICATIONS,
            "What is a common mistake?": MISCONCEPTION,
            "What careers use this?": CAREERS,
            "What should I learn next?": NEXT_STEPS,
        }
        for question, expected_type in examples.items():
            with self.subTest(question=question):
                self.assertEqual(classify_related_question(question), expected_type)

    def test_definition_uses_the_stored_simple_explanation(self) -> None:
        response = answer_related_question(self.gravity, "What is it?")
        assert response is not None
        self.assertEqual(response.question_type, DEFINITION)
        self.assertEqual(response.title, "SIMPLE EXPLANATION")
        self.assertEqual(response.text, "Gravity is the force that pulls objects toward Earth.")

    def test_why_question_uses_the_stored_detailed_explanation(self) -> None:
        response = answer_related_question(self.gravity, "Why do dropped things fall?")
        assert response is not None
        self.assertEqual(response.question_type, EXPLANATION)
        self.assertIn("Every object with mass", response.text)

    def test_formula_is_extracted_only_when_an_equation_exists_in_the_lesson(self) -> None:
        response = answer_related_question(self.momentum, "What is the formula?")
        assert response is not None
        self.assertEqual(response.question_type, FORMULA)
        self.assertEqual(response.text, "p = m x v")
        self.assertIsNone(answer_related_question(self.gravity, "What is the formula?"))

    def test_example_never_uses_unverified_local_context(self) -> None:
        response = answer_related_question(self.force, "Can you give an example?")
        assert response is not None
        self.assertEqual(response.question_type, EXAMPLE)
        self.assertIn("Pushing a door", response.text)
        self.assertNotIn("fishing net", response.text)

    def test_list_requests_use_existing_lesson_lists(self) -> None:
        cases = (
            ("What are the uses?", APPLICATIONS, "machines"),
            ("What is a common misconception?", MISCONCEPTION, "keep moving"),
            ("What careers use this?", CAREERS, "robotics"),
            ("What should I explore next?", NEXT_STEPS, "friction"),
        )
        for question, expected_type, expected_text in cases:
            with self.subTest(question=question):
                response = answer_related_question(self.force, question)
                assert response is not None
                self.assertEqual(response.question_type, expected_type)
                self.assertIn(expected_text, response.text)

    def test_unknown_or_missing_content_returns_none_without_guessing(self) -> None:
        self.assertIsNone(classify_related_question("Can you solve every question in my homework?"))
        self.assertIsNone(
            answer_related_question(self.gravity, "Can you solve every question in my homework?")
        )

    def test_unreviewed_language_falls_back_using_existing_language_rules(self) -> None:
        response = answer_related_question(self.gravity, "Give an example", "Malvani")
        assert response is not None
        self.assertEqual(response.language.resolved, "English")
        self.assertIn("Reviewed Malvani", response.language.notice or "")
        self.assertEqual(response.lesson_verification_status, "NEEDS_REVIEW")


if __name__ == "__main__":
    unittest.main()
