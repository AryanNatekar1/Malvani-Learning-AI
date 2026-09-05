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

    def test_keyboard_focus_reveals_home_start_button_at_minimum_window_size_when_display_is_available(
        self,
    ) -> None:
        """Tab/focus should never leave Home's primary action below the viewport."""
        try:
            from gui import LearningApp
            import tkinter as tk

            def is_visible_in_page(viewport: object, widget: object) -> bool:
                canvas = getattr(viewport, "canvas")
                body = getattr(viewport, "body")
                top = widget.winfo_rooty() - body.winfo_rooty()
                bottom = top + widget.winfo_height()
                visible_top = canvas.canvasy(0)
                visible_bottom = visible_top + canvas.winfo_height()
                return top >= visible_top and bottom <= visible_bottom

            app = LearningApp()
            app.geometry("800x600")
            app.show_screen("home")
            app.home_viewport.canvas.yview_moveto(0.0)
            app.update_idletasks()
            app.update()
            start_button = app.home_screen.start_button
            self.assertFalse(is_visible_in_page(app.home_viewport, start_button))

            start_button.focus_force()
            app.update_idletasks()
            app.update()
            self.assertIs(app.focus_get(), start_button)
            self.assertTrue(is_visible_in_page(app.home_viewport, start_button))
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

    def test_problem_solver_cart_visual_stays_gated_and_local_when_display_is_available(
        self,
    ) -> None:
        """The scenario visual should support, not bypass, the final comparison step."""
        try:
            from app_controller import AppController
            from gui import LearningApp
            from student_engine import ProfileStore
            from visual_learning import MomentumCartComparisonLab, PREDICTION_SAME
            import tkinter as tk

            with tempfile.TemporaryDirectory() as temporary_directory:
                controller = AppController(
                    profile_store=ProfileStore(Path(temporary_directory) / "profile.json")
                )
                app = LearningApp(controller=controller)
                app.geometry("900x700")
                app.home_screen.start_learning()
                app.learning_screen.question.set("Explain momentum")
                app.learning_screen.ask_question()
                app.learning_screen.start_problem_solver()
                app.update_idletasks()
                app.update()

                launch_button = app.learning_screen.problem_solver_visual_button
                self.assertTrue(bool(launch_button.grid_info()))
                locked_view = controller.problem_solver_visual_view()
                assert locked_view is not None
                self.assertIsNone(app.show_problem_solver_visual(locked_view))
                app.learning_screen.show_problem_solver_visual()
                self.assertIsNone(app._problem_solver_visual_window)
                self.assertIn(
                    "Complete the linked calculation step",
                    app.learning_screen.problem_solver_feedback.cget("text"),
                )

                for answer in ("6", "6 kg m/s"):
                    app.learning_screen.problem_solver_answer.set(answer)
                    app.learning_screen.submit_problem_solver_attempt()
                attempts_before_visual = controller.profile.problem_solver_attempts
                ready_view = controller.problem_solver_visual_view()
                assert ready_view is not None
                self.assertTrue(ready_view.is_unlocked)
                app.learning_screen.show_problem_solver_visual()
                app.update_idletasks()
                app.update()

                window = app._problem_solver_visual_window
                assert window is not None
                lab = getattr(window, "visual_lab")
                self.assertIsInstance(lab, MomentumCartComparisonLab)
                self.assertFalse(lab.result_revealed)
                self.assertIsNone(app.grab_current())
                pending = lab.accessible_description.get()
                self.assertIn("2 kg", pending)
                self.assertIn("3 m/s", pending)
                self.assertIn("3 kg", pending)
                self.assertIn("2 m/s", pending)
                self.assertNotIn("6 kg m/s", pending)
                self.assertIsNone(lab.test_prediction())
                self.assertFalse(lab.result_revealed)

                lab.prediction.set(PREDICTION_SAME)
                result = lab.test_prediction()
                assert result is not None
                self.assertTrue(result.supported)
                self.assertTrue(lab.result_revealed)
                self.assertIn("6 kg m/s", lab.accessible_description.get())
                active_view = controller.problem_solver_view()
                assert active_view is not None
                self.assertEqual(active_view.current_step_number, 3)
                self.assertEqual(controller.profile.problem_solver_attempts, attempts_before_visual)
                window.geometry("560x400")
                app.update_idletasks()
                app.update()
                dialog_viewport = getattr(window, "dialog_viewport")
                self.assertGreater(
                    dialog_viewport.body.winfo_height(),
                    dialog_viewport.canvas.winfo_height(),
                )
                dialog_viewport.canvas.yview_moveto(0.0)
                app.update_idletasks()
                close_button = lab.close_button
                assert close_button is not None
                close_button.focus_force()
                app.update_idletasks()
                app.update()
                self.assertIs(app.focus_get(), close_button)
                close_top = close_button.winfo_rooty() - dialog_viewport.body.winfo_rooty()
                close_bottom = close_top + close_button.winfo_height()
                visible_top = dialog_viewport.canvas.canvasy(0)
                visible_bottom = visible_top + dialog_viewport.canvas.winfo_height()
                self.assertGreaterEqual(close_top, visible_top)
                self.assertLessEqual(close_bottom, visible_bottom)
                self.assertAlmostEqual(dialog_viewport.canvas.yview()[1], 1.0, places=2)

                app.learning_screen.show_problem_solver_visual()
                self.assertIs(window, app._problem_solver_visual_window)
                window.event_generate("<Escape>")
                app.update_idletasks()
                app.update()
                self.assertIsNone(app._problem_solver_visual_window)

                app.learning_screen.show_problem_solver_visual()
                stale_window = app._problem_solver_visual_window
                assert stale_window is not None
                app.learning_screen.question.set("Explain force")
                app.learning_screen.ask_question()
                app.update_idletasks()
                self.assertIsNone(app._problem_solver_visual_window)
                self.assertFalse(bool(launch_button.grid_info()))
                self.assertIsNone(app.show_problem_solver_visual(ready_view))
                app.destroy()
        except tk.TclError:
            self.skipTest("Tk display is unavailable in this environment")

    def test_problem_solver_cart_visual_mirrors_valid_left_velocity_cues_when_display_is_available(
        self,
    ) -> None:
        """A valid left-moving model must never draw a contradictory right arrow."""
        try:
            import json
            import tkinter as tk

            from problem_scenario_engine import ProblemScenario, SCENARIOS_DIR
            from visual_learning import MomentumCartComparisonLab

            raw = json.loads(
                (SCENARIOS_DIR / "physics" / "momentum_cart_comparison.json").read_text(
                    encoding="utf-8"
                )
            )
            raw["visual_model"]["carts"][0]["velocity_m_per_s"] = -3
            raw["visual_model"]["carts"][1]["velocity_m_per_s"] = -2
            visual_model = ProblemScenario.from_mapping(raw).visual_model
            assert visual_model is not None

            root = tk.Tk()
            root.withdraw()
            lab = MomentumCartComparisonLab(root, visual_model)
            lab.pack(fill="both", expand=True)
            root.update_idletasks()
            root.update()
            arrow_coordinates = [
                lab.canvas.coords(item)
                for item in lab.canvas.find_withtag("velocity-arrow")
            ]
            self.assertEqual(len(arrow_coordinates), 2)
            self.assertTrue(all(coords[2] < coords[0] for coords in arrow_coordinates))
            root.destroy()
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
        """The model activity is topic-scoped and stays independently guided."""
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
                self.assertEqual(
                    app.learning_screen.research_entries["hypothesis"].cget("state"),
                    "normal",
                )
                self.assertEqual(
                    app.learning_screen.research_entries["analysis"].cget("state"),
                    "disabled",
                )
                app.deiconify()
                app.geometry("800x600")
                app.update_idletasks()
                app.update()
                self.assertGreater(
                    app.learning_viewport.body.winfo_height(),
                    app.learning_viewport.canvas.winfo_height(),
                )
                app.learning_viewport.canvas.yview_moveto(1.0)
                app.update_idletasks()
                self.assertAlmostEqual(app.learning_viewport.canvas.yview()[1], 1.0, places=2)
                hypothesis_entry = app.learning_screen.research_entries["hypothesis"]
                self.assertIsInstance(hypothesis_entry, tk.Text)
                self.assertFalse(getattr(hypothesis_entry, "_page_scroll_bound", False))
                self.assertTrue(getattr(hypothesis_entry, "_page_focus_bound", False))
                app.learning_screen.submit_research_stage("hypothesis")
                app.update_idletasks()
                blank_feedback = app.learning_screen.research_stage_feedback["hypothesis"]
                self.assertTrue(bool(blank_feedback.grid_info()))
                self.assertIn("Write your hypothesis", blank_feedback.cget("text"))
                feedback_top = (
                    blank_feedback.winfo_rooty()
                    - app.learning_viewport.body.winfo_rooty()
                )
                feedback_bottom = feedback_top + blank_feedback.winfo_height()
                visible_top = app.learning_viewport.canvas.canvasy(0)
                visible_bottom = visible_top + app.learning_viewport.canvas.winfo_height()
                self.assertGreaterEqual(feedback_top, visible_top)
                self.assertLessEqual(feedback_bottom, visible_bottom)
                self.assertIs(app.focus_get(), hypothesis_entry)
                hypothesis_entry.insert(
                    "1.0",
                    "If velocity increases while mass stays fixed,\nmomentum increases.",
                )
                app.learning_screen.submit_research_stage("hypothesis")
                self.assertEqual(hypothesis_entry.cget("state"), "disabled")
                self.assertIn(
                    "momentum increases.", hypothesis_entry.get("1.0", "end-1c")
                )
                self.assertEqual(
                    app.learning_screen.research_entries["analysis"].cget("state"),
                    "normal",
                )
                self.assertNotIn("If velocity increases", profile_path.read_text(encoding="utf-8"))

                app.learning_screen.question.set("Explain newton")
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
