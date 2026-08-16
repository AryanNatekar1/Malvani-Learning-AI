"""Small GUI smoke test; core behavior remains testable without a display."""

import sys
import tempfile
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))


class GuiSmokeTests(unittest.TestCase):
    def test_can_create_and_close_main_window_when_display_is_available(self) -> None:
        try:
            from gui import LearningApp
            import tkinter as tk

            app = LearningApp()
        except tk.TclError:
            self.skipTest("Tk display is unavailable in this environment")
        else:
            app.withdraw()
            app.update_idletasks()
            app.update()
            app.destroy()

    def test_home_learning_and_quiz_flow_when_display_is_available(self) -> None:
        try:
            from app_controller import AppController
            from gui import LearningApp
            from student_engine import ProfileStore
            import tkinter as tk

            with tempfile.TemporaryDirectory() as temporary_directory:
                controller = AppController(
                    profile_store=ProfileStore(Path(temporary_directory) / "profile.json")
                )
                app = LearningApp(controller=controller)
                app.withdraw()
                app.home_screen.language.set("English")
                app.home_screen.level.set("Class 9")
                app.home_screen.subject.set("Physics")
                app.home_screen.start_learning()
                app.learning_screen.question.set("What is momentum?")
                app.learning_screen.ask_question()
                self.assertIn("Momentum", app.learning_screen.lesson_cards.rendered_text())
                app.learning_screen.navigate("quiz")
                self.assertIn("momentum", app.quiz_screen.question_label.cget("text").lower())
                app.update()
                app.destroy()
        except tk.TclError:
            self.skipTest("Tk display is unavailable in this environment")

    def test_topic_and_subject_changes_clear_stale_challenge_ui_when_display_is_available(self) -> None:
        try:
            from app_controller import AppController
            from gui import LearningApp
            from student_engine import ProfileStore
            import tkinter as tk

            with tempfile.TemporaryDirectory() as temporary_directory:
                controller = AppController(
                    profile_store=ProfileStore(Path(temporary_directory) / "profile.json")
                )
                app = LearningApp(controller=controller)
                app.withdraw()
                app.home_screen.start_learning()
                app.learning_screen.question.set("What is gravity?")
                app.learning_screen.ask_question()
                app.learning_screen.show_action("challenge")
                app.update_idletasks()
                self.assertTrue(bool(app.learning_screen.challenge_frame.grid_info()))

                app.learning_screen.question.set("What is force?")
                app.learning_screen.ask_question()
                app.update_idletasks()
                self.assertFalse(bool(app.learning_screen.challenge_frame.grid_info()))

                app.home_screen.subject.set("Mathematics")
                app.home_screen.start_learning()
                self.assertIsNone(controller.current_topic)
                app.update()
                app.destroy()
        except tk.TclError:
            self.skipTest("Tk display is unavailable in this environment")

    def test_learning_keeps_a_related_question_and_tutor_answer_in_the_trail_when_display_is_available(self) -> None:
        try:
            from app_controller import AppController
            from gui import LearningApp
            from student_engine import ProfileStore
            import tkinter as tk

            with tempfile.TemporaryDirectory() as temporary_directory:
                controller = AppController(
                    profile_store=ProfileStore(Path(temporary_directory) / "profile.json")
                )
                app = LearningApp(controller=controller)
                app.withdraw()
                app.home_screen.start_learning()
                app.learning_screen.question.set("What is momentum?")
                app.learning_screen.ask_question()
                self.assertIn(
                    "What is the formula?", controller.related_question_suggestions()
                )

                app.learning_screen.ask_related_question("What is the formula?")
                trail = app.learning_screen.lesson_cards.rendered_text()
                self.assertIn("YOUR QUESTION", trail)
                self.assertIn("What is the formula?", trail)
                self.assertIn("p = m x v", trail)
                app.update()
                app.destroy()
        except tk.TclError:
            self.skipTest("Tk display is unavailable in this environment")

    def test_main_window_resizes_at_laptop_and_desktop_sizes_when_display_is_available(self) -> None:
        try:
            from gui import LearningApp
            import tkinter as tk

            app = LearningApp()
            app.withdraw()
            for size in ("800x600", "1366x768", "1920x1080"):
                with self.subTest(size=size):
                    app.geometry(size)
                    app.update_idletasks()
                    self.assertGreaterEqual(app.winfo_width(), 800)
                    self.assertGreaterEqual(app.winfo_height(), 600)
            app.update()
            app.destroy()
        except tk.TclError:
            self.skipTest("Tk display is unavailable in this environment")

    def test_navigation_compacts_before_the_learning_area_becomes_cramped_when_display_is_available(self) -> None:
        try:
            from gui import LearningApp
            import tkinter as tk
            from types import SimpleNamespace

            app = LearningApp()
            app.withdraw()
            app._adapt_navigation(SimpleNamespace(widget=app, width=800))
            self.assertTrue(app._compact_navigation)
            app._adapt_navigation(SimpleNamespace(widget=app, width=1180))
            self.assertFalse(app._compact_navigation)
            app.update_idletasks()
            app.update()
            app.destroy()
        except tk.TclError:
            self.skipTest("Tk display is unavailable in this environment")

    def test_returning_to_quiz_resumes_in_progress_session_when_display_is_available(self) -> None:
        try:
            from app_controller import AppController
            from gui import LearningApp
            from student_engine import ProfileStore
            import tkinter as tk

            with tempfile.TemporaryDirectory() as temporary_directory:
                controller = AppController(
                    profile_store=ProfileStore(Path(temporary_directory) / "profile.json")
                )
                app = LearningApp(controller=controller)
                app.withdraw()
                app.home_screen.start_learning()
                app.learning_screen.question.set("What is momentum?")
                app.learning_screen.ask_question()
                app._navigate_from_shell("quiz")
                app.quiz_screen.answer.set("12")
                app.quiz_screen.submit()
                app.quiz_screen.next_question()
                before = controller.quiz_view()
                assert before is not None
                self.assertEqual(before.position, 2)
                self.assertEqual(before.score, 1)

                app.show_screen("learning")
                app._navigate_from_shell("quiz")
                after = controller.quiz_view()
                assert after is not None
                self.assertEqual(after.position, 2)
                self.assertEqual(after.score, 1)
                app.update()
                app.destroy()
        except tk.TclError:
            self.skipTest("Tk display is unavailable in this environment")

    def test_home_and_learning_content_remain_reachable_at_minimum_window_size_when_display_is_available(self) -> None:
        try:
            from gui import LearningApp
            import tkinter as tk

            app = LearningApp()
            app.geometry("800x600")
            app.update_idletasks()
            app.update()

            app.show_screen("home")
            app.update_idletasks()
            self.assertGreater(
                app.home_viewport.body.winfo_height(),
                app.home_viewport.canvas.winfo_height(),
            )
            app.home_viewport.canvas.yview_moveto(1.0)
            app.update()
            self.assertAlmostEqual(app.home_viewport.canvas.yview()[1], 1.0, places=2)

            app.show_screen("learning")
            app.update_idletasks()
            self.assertGreaterEqual(app.learning_screen.lesson_cards.canvas.winfo_height(), 250)
            self.assertGreater(
                app.learning_viewport.body.winfo_height(),
                app.learning_viewport.canvas.winfo_height(),
            )
            app.learning_viewport.canvas.yview_moveto(1.0)
            app.update()
            self.assertAlmostEqual(app.learning_viewport.canvas.yview()[1], 1.0, places=2)
            app.destroy()
        except tk.TclError:
            self.skipTest("Tk display is unavailable in this environment")

    def test_momentum_visual_lab_updates_from_learner_controls_when_display_is_available(self) -> None:
        try:
            from gui import LearningApp
            from visual_learning import MomentumLab
            import tkinter as tk

            app = LearningApp()
            app.withdraw()
            window = app.show_diagram("momentum")
            assert window is not None
            lab = getattr(window, "visual_lab")
            self.assertIsInstance(lab, MomentumLab)
            lab.set_values(4, 3)
            app.update_idletasks()
            app.update()
            self.assertEqual(lab.current_state().momentum, 12)
            self.assertFalse(lab.result_revealed)
            self.assertIn("hidden", lab.momentum_text.get().lower())
            self.assertIn("Prediction pending", lab.accessible_description.get())
            lab.prediction.set("greater")
            result = lab.test_prediction()
            assert result is not None
            self.assertTrue(result.correct)
            self.assertIn("12 kg m/s right", lab.momentum_text.get())
            self.assertIn("4 kg cart", lab.accessible_description.get())
            self.assertGreaterEqual(window.winfo_height(), window.winfo_reqheight())
            window.destroy()
            app.destroy()
        except tk.TclError:
            self.skipTest("Tk display is unavailable in this environment")

    def test_manual_context_picker_is_optional_and_topic_scoped_when_display_is_available(self) -> None:
        try:
            from app_controller import AppController
            from context_engine import VERIFIED, ContextRecord, ContextRepository
            from gui import LearningApp
            from student_engine import ProfileStore
            import tkinter as tk

            context = ContextRecord(
                identifier="momentum-cart-model",
                title="Computer cart model",
                category="physics model",
                educational_prompt="Compare labelled carts in a reviewed classroom model.",
                topics=("momentum",),
                verification_status=VERIFIED,
                source="Teacher-reviewed classroom model",
            )
            with tempfile.TemporaryDirectory() as temporary_directory:
                profile_path = Path(temporary_directory) / "profile.json"
                controller = AppController(
                    profile_store=ProfileStore(profile_path),
                    context_repository=ContextRepository([context]),
                )
                app = LearningApp(controller=controller)
                app.withdraw()
                options = app.home_screen.manual_context_box.cget("values")
                label = next(value for value in options if "Computer cart model" in value)
                app.home_screen.manual_context.set(label)
                app.home_screen.start_learning()
                self.assertEqual(controller.selected_manual_context_id, "momentum-cart-model")

                app.learning_screen.question.set("Explain momentum")
                app.learning_screen.ask_question()
                trail = app.learning_screen.lesson_cards.rendered_text()
                self.assertIn("MANUAL LEARNING CONTEXT", trail)
                self.assertIn("did not use GPS", trail)
                self.assertNotIn("momentum-cart-model", profile_path.read_text(encoding="utf-8"))
                app.update_idletasks()
                app.update()
                app.destroy()
        except tk.TclError:
            self.skipTest("Tk display is unavailable in this environment")

    def test_problem_solver_and_go_deeper_flow_resets_stale_widgets_when_display_is_available(
        self,
    ) -> None:
        """The model activity is visible only for Momentum and stays independently guided."""
        try:
            from app_controller import AppController
            from gui import LearningApp
            from student_engine import ProfileStore
            import tkinter as tk

            with tempfile.TemporaryDirectory() as temporary_directory:
                profile_path = Path(temporary_directory) / "profile.json"
                controller = AppController(profile_store=ProfileStore(profile_path))
                app = LearningApp(controller=controller)
                app.withdraw()
                app.home_screen.start_learning()
                app.learning_screen.question.set("Explain momentum")
                app.learning_screen.ask_question()
                app.update_idletasks()
                self.assertTrue(bool(app.learning_screen.problem_solver_button.grid_info()))

                app.learning_screen.start_problem_solver()
                self.assertTrue(bool(app.learning_screen.problem_solver_frame.grid_info()))
                # Opening the same topic again starts a fresh controller lesson
                # state, so old interactive controls must disappear as well.
                app.learning_screen.question.set("Explain momentum")
                app.learning_screen.ask_question()
                self.assertFalse(bool(app.learning_screen.problem_solver_frame.grid_info()))

                app.learning_screen.start_problem_solver()
                for answer in ("6 kg m/s", "6", "equal"):
                    app.learning_screen.problem_solver_answer.set(answer)
                    app.learning_screen.submit_problem_solver_attempt()
                self.assertTrue(controller.can_go_deeper())
                app.learning_screen.start_go_deeper()
                app.update_idletasks()
                self.assertTrue(bool(app.learning_screen.research_frame.grid_info()))
                app.geometry("800x600")
                app.update_idletasks()
                self.assertGreater(
                    app.learning_viewport.body.winfo_height(),
                    app.learning_viewport.canvas.winfo_height(),
                )
                app.learning_viewport.canvas.yview_moveto(1.0)
                app.update_idletasks()
                self.assertAlmostEqual(app.learning_viewport.canvas.yview()[1], 1.0, places=2)
                hypothesis_entry = app.learning_screen.research_entries["hypothesis"]
                self.assertIsInstance(hypothesis_entry, tk.Text)
                hypothesis_entry.insert(
                    "1.0",
                    "If velocity increases while mass stays fixed,\nmomentum increases.",
                )
                app.learning_screen.submit_research_stage("hypothesis")
                self.assertEqual(hypothesis_entry.cget("state"), "disabled")
                self.assertIn(
                    "momentum increases.", hypothesis_entry.get("1.0", "end-1c")
                )
                self.assertNotIn("If velocity increases", profile_path.read_text(encoding="utf-8"))

                app.learning_screen.question.set("Explain force")
                app.learning_screen.ask_question()
                app.update_idletasks()
                self.assertFalse(bool(app.learning_screen.problem_solver_frame.grid_info()))
                self.assertFalse(bool(app.learning_screen.research_frame.grid_info()))
                self.assertFalse(bool(app.learning_screen.problem_solver_button.grid_info()))
                app.update()
                app.destroy()
        except tk.TclError:
            self.skipTest("Tk display is unavailable in this environment")

    def test_guided_inputs_scroll_into_view_and_receive_keyboard_focus_when_display_is_available(
        self,
    ) -> None:
        """A learner should reach the next input immediately on a compact laptop view."""
        try:
            from app_controller import AppController
            from gui import LearningApp
            from student_engine import ProfileStore
            import tkinter as tk

            def is_visible_in_page(viewport: object, widget: object) -> bool:
                canvas = getattr(viewport, "canvas")
                body = getattr(viewport, "body")
                top = widget.winfo_rooty() - body.winfo_rooty()
                bottom = top + widget.winfo_height()
                visible_top = canvas.canvasy(0)
                visible_bottom = visible_top + canvas.winfo_height()
                return top >= visible_top and bottom <= visible_bottom

            with tempfile.TemporaryDirectory() as temporary_directory:
                controller = AppController(
                    profile_store=ProfileStore(Path(temporary_directory) / "profile.json")
                )
                app = LearningApp(controller=controller)
                app.geometry("800x600")
                app.update_idletasks()
                app.update()
                app.home_screen.start_learning()
                app.learning_screen.question.set("Explain momentum")
                app.learning_screen.ask_question()
                app.learning_screen.start_problem_solver()
                app.update_idletasks()
                app.update()

                problem_entry = app.learning_screen.problem_solver_entry
                self.assertTrue(is_visible_in_page(app.learning_viewport, problem_entry))
                self.assertIs(app.focus_get(), problem_entry)

                for answer in ("6", "6", "equal"):
                    app.learning_screen.problem_solver_answer.set(answer)
                    app.learning_screen.submit_problem_solver_attempt()
                app.learning_screen.start_go_deeper()
                app.update_idletasks()
                app.update()

                hypothesis_entry = app.learning_screen.research_entries["hypothesis"]
                self.assertTrue(is_visible_in_page(app.learning_viewport, hypothesis_entry))
                self.assertIs(app.focus_get(), hypothesis_entry)
                app.destroy()
        except tk.TclError:
            self.skipTest("Tk display is unavailable in this environment")


if __name__ == "__main__":
    unittest.main()
