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


if __name__ == "__main__":
    unittest.main()
