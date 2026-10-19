"""Tests for looking a topic up from the desktop app.

Everything else in this app runs on the learner's own machine. This one action
sends what they typed to Wikipedia, so the tests cover the boundary as much as
the feature: it must be opt-in, it must say what it does, and it must never
fire on its own.
"""

import sys
import unittest
from pathlib import Path
from unittest import mock

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))

from app_controller import AppController
from grounded_answer import Passage

DISPERSION = Passage(
    text=(
        "Dispersion is the phenomenon in which white light separates into its "
        "constituent colours, because each colour is refracted by a different "
        "amount when it passes through a prism."
    ),
    title="Dispersion (optics)",
    url="https://en.wikipedia.org/wiki/Dispersion_(optics)",
)


class UnknownTopicTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = AppController()

    def test_an_unknown_topic_offers_a_look_up_instead_of_a_dead_end(self) -> None:
        response = self.controller.answer_question("Explain dispersion of light")
        self.assertFalse(response.is_structured)
        self.assertIn("not going to guess", response.text)
        self.assertIn("Look it up online", response.text)

    def test_the_offer_says_the_question_leaves_the_machine(self) -> None:
        """A learner should know before they press it, not after."""
        response = self.controller.answer_question("Explain dispersion of light")
        self.assertIn("sends what you typed", response.text)

    def test_the_question_is_remembered_so_it_need_not_be_retyped(self) -> None:
        self.controller.answer_question("Explain dispersion of light")
        self.assertIn("dispersion", self.controller.last_unanswered_question.lower())

    def test_a_question_that_is_answered_leaves_nothing_pending(self) -> None:
        """Otherwise the look-up offer lingers after an answered question."""
        self.controller.answer_question("Explain dispersion of light")
        self.assertTrue(self.controller.last_unanswered_question)
        self.controller.answer_question("What is gravity?")
        self.assertEqual(self.controller.last_unanswered_question, "")


class LookUpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = AppController()

    def test_nothing_is_searched_until_the_action_is_taken(self) -> None:
        """Asking a question must not reach the network by itself."""
        with mock.patch("app_controller.WikipediaRetrievalProvider") as provider:
            self.controller.answer_question("Explain dispersion of light")
            provider.assert_not_called()

    def test_a_successful_look_up_cites_every_sentence(self) -> None:
        self.controller.answer_question("Explain dispersion of light")
        with mock.patch("app_controller.WikipediaRetrievalProvider") as provider:
            provider.return_value.search.return_value = (DISPERSION,)
            response = self.controller.look_up_topic()
        self.assertIn("[1]", response.text)
        self.assertIn(DISPERSION.url, response.text)
        self.assertIn("not written by a teacher", response.text)

    def test_the_result_is_labelled_as_unreviewed(self) -> None:
        self.controller.answer_question("Explain dispersion of light")
        with mock.patch("app_controller.WikipediaRetrievalProvider") as provider:
            provider.return_value.search.return_value = (DISPERSION,)
            response = self.controller.look_up_topic()
        self.assertIn("NOT A REVIEWED LESSON", [s.title for s in response.sections])
        self.assertFalse(response.is_structured)

    def test_no_connection_points_back_at_the_offline_lessons(self) -> None:
        self.controller.answer_question("Explain dispersion of light")
        with mock.patch("app_controller.WikipediaRetrievalProvider") as provider:
            provider.return_value.search.return_value = ()
            response = self.controller.look_up_topic()
        self.assertIn("without the internet", response.text)

    def test_unsupported_claims_produce_a_refusal_not_a_guess(self) -> None:
        self.controller.answer_question("Explain dispersion of light")
        unrelated = Passage(
            text=(
                "The mango is a tropical stone fruit grown widely across the "
                "Konkan coast and harvested in the dry months before the rains."
            ),
            title="Mango",
            url="https://en.wikipedia.org/wiki/Mango",
        )
        with mock.patch("app_controller.WikipediaRetrievalProvider") as provider:
            provider.return_value.search.return_value = (unrelated,)
            response = self.controller.look_up_topic()
        self.assertIn("not going to guess", response.text)

    def test_looking_up_with_nothing_pending_asks_for_a_question(self) -> None:
        response = AppController().look_up_topic()
        self.assertIn("Ask a question first", response.text)

    def test_the_search_follows_the_chosen_language(self) -> None:
        self.controller.answer_question("Explain dispersion of light")
        with mock.patch("app_controller.WikipediaRetrievalProvider") as provider:
            provider.return_value.search.return_value = (DISPERSION,)
            self.controller.look_up_topic()
        provider.assert_called_once()
        self.assertEqual(
            provider.call_args.kwargs.get("language"),
            self.controller.preferences().language,
        )


class LearningScreenLayoutTests(unittest.TestCase):
    """One button was stacked invisibly on another for two commits."""

    def test_no_two_action_buttons_share_a_grid_cell(self) -> None:
        try:
            import gui
        except Exception as error:  # pragma: no cover - headless CI without Tk
            self.skipTest(f"Tk unavailable: {error}")
        try:
            app = gui.LearningApp()
        except Exception as error:  # pragma: no cover
            self.skipTest(f"no display: {error}")
        try:
            app.update_idletasks()
            occupied: dict[tuple, str] = {}
            for widget in self._walk(app):
                try:
                    info = widget.grid_info()
                    label = str(widget.cget("text"))
                except Exception:
                    continue
                if not info or not label:
                    continue
                cell = (str(widget.master), info.get("row"), info.get("column"))
                if cell in occupied:
                    self.fail(
                        f"'{label}' is stacked on '{occupied[cell]}' at {cell}; "
                        "one of them cannot be used"
                    )
                occupied[cell] = label
        finally:
            app.destroy()

    @staticmethod
    def _walk(widget):
        for child in widget.winfo_children():
            yield child
            yield from LearningScreenLayoutTests._walk(child)


if __name__ == "__main__":
    unittest.main()
