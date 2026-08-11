"""Tkinter desktop interface for the offline Malvani Learning AI prototype."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from app_controller import AppController, LearningPreferences, QuizView
from language_engine import SUPPORTED_LANGUAGES, interface_text
from media_engine import get_visual
from voice_engine import DisabledVoiceProvider


LEVELS = ("Beginner", "Class 8", "Class 9", "Class 10", "Class 11/12")


class ScrollableLessonCards(ttk.Frame):
    """A responsive scrollable stack of focused lesson sections."""

    def __init__(self, parent: ttk.Frame) -> None:
        super().__init__(parent)
        self.canvas = tk.Canvas(self, highlightthickness=0, background="#F7FAFC")
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.content = ttk.Frame(self, padding=(8, 4))
        self._content_window = self.canvas.create_window(
            (0, 0), window=self.content, anchor="nw"
        )
        self.content.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._resize_content)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self._rendered_text = ""

    def _update_scroll_region(self, _event: tk.Event[tk.Misc]) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_content(self, event: tk.Event[tk.Misc]) -> None:
        self.canvas.itemconfigure(self._content_window, width=event.width)

    def _on_mousewheel(self, event: tk.Event[tk.Misc]) -> None:
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def render(
        self,
        title: str,
        text: str,
        sections: tuple[object, ...] = (),
        append: bool = False,
    ) -> None:
        """Render structured sections as cards or a single honest information card."""
        if not append:
            for widget in self.content.winfo_children():
                widget.destroy()
            self._rendered_text = ""

        if title:
            ttk.Label(self.content, text=title, style="Section.TLabel").pack(
                fill="x", padx=6, pady=(8, 4)
            )
            self._rendered_text += f"{title}\n\n"

        if sections:
            for section in sections:
                section_title = getattr(section, "title", "Lesson")
                section_body = getattr(section, "body", "")
                self._add_card(section_title, section_body)
                self._rendered_text += f"{section_title}\n{section_body}\n\n"
        else:
            self._add_card("LEARNING NOTE", text)
            self._rendered_text += f"{text}\n\n"
        self.canvas.yview_moveto(1.0 if append else 0.0)

    def _add_card(self, title: str, body: str) -> None:
        card = ttk.LabelFrame(self.content, text=title, padding=(14, 10))
        card.pack(fill="x", padx=6, pady=5)
        ttk.Label(
            card,
            text=body,
            justify="left",
            wraplength=760,
            font=("Segoe UI", 10),
        ).pack(fill="x")

    def rendered_text(self) -> str:
        """Expose displayed text for lightweight GUI tests."""
        return self._rendered_text


class LearningApp(tk.Tk):
    """One window with navigable screens for local learning activities."""

    def __init__(self, controller: AppController | None = None) -> None:
        super().__init__()
        self.title("Malvani Learning AI")
        self.geometry("1000x700")
        self.minsize(800, 600)
        self.controller = controller or AppController()
        self._configure_style()

        container = ttk.Frame(self, padding=12)
        container.pack(fill="both", expand=True)
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        self.home_screen = HomeScreen(container, self)
        self.learning_screen = LearningScreen(container, self)
        self.quiz_screen = QuizScreen(container, self)
        self.progress_screen = ProgressScreen(container, self)
        self.library_screen = LibraryScreen(container, self)
        self.settings_screen = SettingsScreen(container, self)
        self.screens = {
            "home": self.home_screen,
            "learning": self.learning_screen,
            "quiz": self.quiz_screen,
            "progress": self.progress_screen,
            "library": self.library_screen,
            "settings": self.settings_screen,
        }
        for screen in self.screens.values():
            screen.grid(row=0, column=0, sticky="nsew")

        self.show_screen("home")

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("Segoe UI", 24, "bold"), foreground="#0B4F6C")
        style.configure("Subtitle.TLabel", font=("Segoe UI", 11), foreground="#34515E")
        style.configure("Section.TLabel", font=("Segoe UI", 15, "bold"), foreground="#0B4F6C")
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))

    def show_screen(self, name: str) -> None:
        """Raise a screen and let it refresh its local view state."""
        screen = self.screens[name]
        screen.tkraise()
        screen.refresh()

    def show_diagram(self, topic: str | None) -> None:
        """Open a small instructional diagram only when a topic has one."""
        if topic is None:
            messagebox.showinfo("Diagram", "Ask about a supported topic first.")
            return
        visual = get_visual(topic)
        if visual is None:
            messagebox.showinfo(
                "Diagram",
                "No diagram has been added for this lesson yet. A visual should be added only when it improves understanding.",
            )
            return

        window = tk.Toplevel(self)
        window.title(visual.title)
        window.geometry("500x380")
        ttk.Label(window, text=visual.title, style="Section.TLabel").pack(pady=(16, 4))
        ttk.Label(window, text=visual.description, wraplength=430).pack(padx=20, pady=(0, 8))
        canvas = tk.Canvas(window, width=430, height=220, bg="white", highlightthickness=1)
        canvas.pack(padx=20, pady=10)
        self._draw_visual(canvas, topic)

    @staticmethod
    def _draw_visual(canvas: tk.Canvas, topic: str) -> None:
        """Draw simple concept diagrams using the built-in Canvas widget."""
        if topic == "gravity":
            canvas.create_oval(185, 25, 245, 85, fill="#F4A261", outline="#7F5539")
            canvas.create_line(215, 90, 215, 160, width=3, arrow=tk.LAST, fill="#D62828")
            canvas.create_text(260, 125, text="gravity", fill="#D62828", anchor="w")
            canvas.create_arc(60, 145, 370, 320, start=0, extent=180, fill="#4A90A4", outline="#24536A")
            canvas.create_text(215, 195, text="Earth", fill="white", font=("Segoe UI", 12, "bold"))
        elif topic == "momentum":
            canvas.create_rectangle(80, 120, 210, 185, fill="#76C893", outline="#386641")
            canvas.create_text(145, 152, text="mass", font=("Segoe UI", 11, "bold"))
            canvas.create_line(220, 152, 365, 152, width=4, arrow=tk.LAST, fill="#1D3557")
            canvas.create_text(292, 130, text="velocity", fill="#1D3557")
            canvas.create_text(215, 205, text="momentum = mass x velocity")
        elif topic == "force":
            canvas.create_rectangle(150, 100, 280, 180, fill="#F4A261", outline="#7F5539")
            canvas.create_text(215, 140, text="object")
            canvas.create_line(45, 140, 140, 140, width=4, arrow=tk.LAST, fill="#D62828")
            canvas.create_text(65, 118, text="force", fill="#D62828")
        else:  # Newton's second law
            canvas.create_rectangle(160, 105, 260, 175, fill="#A8DADC", outline="#457B9D")
            canvas.create_text(210, 140, text="mass")
            canvas.create_line(40, 140, 150, 140, width=4, arrow=tk.LAST, fill="#D62828")
            canvas.create_text(70, 116, text="force", fill="#D62828")
            canvas.create_line(270, 140, 390, 140, width=4, arrow=tk.LAST, fill="#1D3557")
            canvas.create_text(300, 116, text="acceleration", fill="#1D3557")
            canvas.create_text(215, 205, text="F = m x a")


class Screen(ttk.Frame):
    """Common base class for a page in the single-window application."""

    def __init__(self, parent: ttk.Frame, app: LearningApp) -> None:
        super().__init__(parent)
        self.app = app

    def refresh(self) -> None:
        """Update a page after navigation. Subclasses override when useful."""


class HomeScreen(Screen):
    """Starting page for language, level, subject, and culture settings."""

    def __init__(self, parent: ttk.Frame, app: LearningApp) -> None:
        super().__init__(parent, app)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        preferences = app.controller.preferences()
        self.language = tk.StringVar(value=preferences.language)
        self.level = tk.StringVar(value=preferences.level)
        subjects = app.controller.supported_subjects() or ("Physics",)
        initial_subject = preferences.subject if preferences.subject in subjects else subjects[0]
        self.subject = tk.StringVar(value=initial_subject)
        self.culture_mode = tk.BooleanVar(value=preferences.culture_mode)

        intro = ttk.Frame(self, padding=(30, 40))
        intro.grid(row=0, column=0, columnspan=2, sticky="nsew")
        ttk.Label(intro, text="MALVANI LEARNING AI", style="Title.TLabel").pack()
        ttk.Label(
            intro,
            text="Learn • Think • Solve • Explore",
            style="Subtitle.TLabel",
        ).pack(pady=(8, 24))
        ttk.Label(
            intro,
            text=(
                "Offline-first learning with local draft lessons, guided practice, "
                "and source-gated local context."
            ),
            wraplength=610,
            justify="center",
        ).pack()

        form = ttk.LabelFrame(self, text="Start learning", padding=22)
        form.grid(row=1, column=0, columnspan=2, padx=120, pady=15, sticky="ew")
        form.columnconfigure(1, weight=1)
        self.language_label = ttk.Label(form)
        self.language_label.grid(row=0, column=0, padx=(0, 16), pady=8, sticky="w")
        ttk.Combobox(form, textvariable=self.language, values=SUPPORTED_LANGUAGES, state="readonly").grid(
            row=0, column=1, pady=8, sticky="ew"
        )
        self.level_label = ttk.Label(form)
        self.level_label.grid(row=1, column=0, padx=(0, 16), pady=8, sticky="w")
        ttk.Combobox(form, textvariable=self.level, values=LEVELS, state="readonly").grid(
            row=1, column=1, pady=8, sticky="ew"
        )
        self.subject_label = ttk.Label(form)
        self.subject_label.grid(row=2, column=0, padx=(0, 16), pady=8, sticky="w")
        ttk.Combobox(form, textvariable=self.subject, values=subjects, state="readonly").grid(
            row=2, column=1, pady=8, sticky="ew"
        )
        ttk.Checkbutton(
            form,
            text="Use verified local context when available",
            variable=self.culture_mode,
        ).grid(row=3, column=0, columnspan=2, pady=(12, 8), sticky="w")
        self.start_button = ttk.Button(form, style="Accent.TButton", command=self.start_learning)
        self.start_button.grid(row=4, column=0, columnspan=2, pady=(16, 0))

        dashboard = ttk.LabelFrame(self, text="Your local learning", padding=16)
        dashboard.grid(row=2, column=0, columnspan=2, padx=120, pady=(12, 8), sticky="ew")
        dashboard.columnconfigure(0, weight=1)
        self.dashboard_text = ttk.Label(dashboard, justify="left", wraplength=620)
        self.dashboard_text.grid(row=0, column=0, sticky="w")
        ttk.Button(dashboard, text="Browse Lesson Library", command=lambda: app.show_screen("library")).grid(
            row=1, column=0, sticky="w", pady=(10, 0)
        )

        self.language.trace_add("write", lambda *_: self._update_labels())
        self._update_labels()

    def _update_labels(self) -> None:
        language = self.language.get()
        self.language_label.configure(text=interface_text("language", language))
        self.level_label.configure(text=interface_text("level", language))
        self.subject_label.configure(text=interface_text("subject", language))
        self.start_button.configure(text=interface_text("start_learning", language))

    def start_learning(self) -> None:
        """Save preferences and move to the learning interface."""
        self.app.controller.save_preferences(
            LearningPreferences(
                language=self.language.get(),
                level=self.level.get(),
                subject=self.subject.get(),
                culture_mode=self.culture_mode.get(),
            )
        )
        self.app.show_screen("learning")

    def refresh(self) -> None:
        preferences = self.app.controller.preferences()
        self.language.set(preferences.language)
        self.level.set(preferences.level)
        self.subject.set(preferences.subject)
        self.culture_mode.set(preferences.culture_mode)
        self.dashboard_text.configure(text=self.app.controller.dashboard_text())


class LearningScreen(Screen):
    """Question-answer and guided-lesson screen."""

    def __init__(self, parent: ttk.Frame, app: LearningApp) -> None:
        super().__init__(parent, app)
        self.rowconfigure(3, weight=1)
        self.columnconfigure(0, weight=1)
        self.question = tk.StringVar()
        self.reasoning = tk.StringVar()
        self.challenge_answer = tk.StringVar()
        self.status = tk.StringVar(value="Offline local mode")

        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Learning", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        for column, (label, target) in enumerate(
            (("Home", "home"), ("Quiz", "quiz"), ("Progress", "progress"), ("Library", "library"), ("Settings", "settings")), start=1
        ):
            ttk.Button(header, text=label, command=lambda page=target: self.navigate(page)).grid(
                row=0, column=column, padx=3
            )

        ttk.Label(self, textvariable=self.status, style="Subtitle.TLabel").grid(
            row=1, column=0, sticky="w", pady=(0, 8)
        )
        question_row = ttk.Frame(self)
        question_row.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        question_row.columnconfigure(0, weight=1)
        question_entry = ttk.Entry(question_row, textvariable=self.question)
        question_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        question_entry.bind("<Return>", lambda _event: self.ask_question())
        ttk.Button(question_row, text="Ask", command=self.ask_question).grid(row=0, column=1)

        self.lesson_cards = ScrollableLessonCards(self)
        self.lesson_cards.grid(row=3, column=0, sticky="nsew", pady=(0, 10))

        reasoning_frame = ttk.LabelFrame(self, text="Think through the idea", padding=8)
        reasoning_frame.grid(row=4, column=0, sticky="ew", pady=(0, 6))
        reasoning_frame.columnconfigure(0, weight=1)
        ttk.Entry(
            reasoning_frame,
            textvariable=self.reasoning,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(
            reasoning_frame,
            text="Check My Reasoning",
            command=self.check_reasoning,
        ).grid(row=0, column=1)
        self.reasoning_feedback = ttk.Label(reasoning_frame, text="", wraplength=850)
        self.reasoning_feedback.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))

        self.challenge_frame = ttk.LabelFrame(self, text="Challenge attempt", padding=8)
        self.challenge_frame.grid(row=5, column=0, sticky="ew", pady=(0, 6))
        self.challenge_frame.columnconfigure(0, weight=1)
        ttk.Entry(self.challenge_frame, textvariable=self.challenge_answer).grid(
            row=0, column=0, sticky="ew", padx=(0, 8)
        )
        ttk.Button(
            self.challenge_frame,
            text="Submit Challenge Attempt",
            command=self.submit_challenge_attempt,
        ).grid(row=0, column=1)
        self.challenge_feedback = ttk.Label(self.challenge_frame, text="", wraplength=850)
        self.challenge_feedback.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))
        self.challenge_frame.grid_remove()

        actions = ttk.Frame(self)
        actions.grid(row=6, column=0, sticky="ew")
        action_buttons = (
            ("Explain simply", "simple"),
            ("Give example", "example"),
            ("Give hint", "hint"),
            ("Give challenge", "challenge"),
            ("Show solution", "solution"),
            ("Ask me a question", "think"),
            ("Continue", "continue"),
        )
        for index, (label, action) in enumerate(action_buttons):
            ttk.Button(actions, text=label, command=lambda item=action: self.show_action(item)).grid(
                row=index // 4, column=index % 4, padx=2, pady=2, sticky="ew"
            )
        ttk.Button(actions, text="Show diagram", command=self.show_diagram).grid(
            row=1, column=3, padx=2, pady=2, sticky="ew"
        )

    def navigate(self, target: str) -> None:
        if target == "quiz":
            view = self.app.controller.start_quiz()
            if view is None:
                self.write_output("Choose a migrated lesson with a quiz first (Gravity, Force, Momentum, or Newton's laws).")
                return
            self.app.quiz_screen.begin(view)
        self.app.show_screen(target)

    def ask_question(self) -> None:
        text = self.question.get().strip()
        if not text:
            return
        response = self.app.controller.answer_question(text)
        self.render_response(response, append=False)
        if response.start_quiz:
            quiz = self.app.controller.quiz_view()
            if quiz is not None:
                self.app.quiz_screen.begin(quiz)
                self.app.show_screen("quiz")
                return
        if response.topic and self.app.controller.current_topic == response.topic:
            self.status.set(f"Offline local mode • Topic: {response.topic}")
            self._reset_lesson_interaction_widgets()
        self.question.set("")

    def show_action(self, action: str) -> None:
        response = self.app.controller.lesson_action(action)
        self.render_response(response, append=True)
        if action == "challenge" and self.app.controller.current_problem_session is not None:
            self.challenge_answer.set("")
            self.challenge_feedback.configure(text="Try in your own words before opening the solution.")
            self.challenge_frame.grid()

    def _reset_lesson_interaction_widgets(self) -> None:
        """Discard visual state that belongs to the previously selected lesson."""
        self.reasoning.set("")
        self.reasoning_feedback.configure(text="")
        self.challenge_answer.set("")
        self.challenge_feedback.configure(text="")
        self.challenge_frame.grid_remove()

    def check_reasoning(self) -> None:
        """Submit a student explanation to the transparent local feedback engine."""
        feedback = self.app.controller.check_reasoning(self.reasoning.get().strip())
        if feedback is None:
            self.reasoning_feedback.configure(
                text="Ask about a structured lesson before checking your reasoning."
            )
            return
        hint_text = f" Hint: {feedback.hint}" if feedback.hint else ""
        self.reasoning_feedback.configure(
            text=f"Feedback ({feedback.category}): {feedback.message}{hint_text}"
        )

    def submit_challenge_attempt(self) -> None:
        """Submit the current guided-problem attempt without exposing its answer first."""
        answer = self.challenge_answer.get().strip()
        if not answer:
            self.challenge_feedback.configure(text="Write an attempt before submitting it.")
            return
        feedback = self.app.controller.submit_challenge_attempt(answer)
        if feedback is None:
            self.challenge_feedback.configure(text="Start a challenge before submitting an attempt.")
            return
        category = "Correct" if feedback.correct else "Keep trying"
        if feedback.correct is None:
            category = "Reflect"
        self.challenge_feedback.configure(text=f"{category}: {feedback.message}")

    def show_diagram(self) -> None:
        self.app.show_diagram(self.app.controller.current_topic)

    def render_response(self, response: object, append: bool) -> None:
        """Keep structured sections visible while actions add focused new cards."""
        topic = getattr(response, "topic", None)
        title = topic.title() if isinstance(topic, str) else "Malvani Learning AI"
        self.lesson_cards.render(
            title=title,
            text=str(getattr(response, "text", "")),
            sections=getattr(response, "sections", ()),
            append=append,
        )

    def write_output(self, text: str) -> None:
        """Render an unstructured status note for legacy and navigation cases."""
        self.lesson_cards.render("Malvani Learning AI", text, append=False)

    def refresh(self) -> None:
        preferences = self.app.controller.preferences()
        if self.app.controller.current_topic is None:
            self._reset_lesson_interaction_widgets()
        self.status.set(
            f"Offline local mode • {preferences.subject} • {preferences.level} • Requested language: {preferences.language}"
        )
        if not self.lesson_cards.rendered_text().strip():
            self.write_output(
                "Ask about a topic in your selected subject. You can then explain your reasoning, try a challenge, and use hints before a solution."
            )


class QuizScreen(Screen):
    """Interactive local quiz screen with hints and score tracking."""

    def __init__(self, parent: ttk.Frame, app: LearningApp) -> None:
        super().__init__(parent, app)
        self.columnconfigure(0, weight=1)
        self.answer = tk.StringVar()
        self.feedback = tk.StringVar()
        self.pending_view: QuizView | None = None

        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Quiz", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Button(header, text="Back to Learning", command=lambda: app.show_screen("learning")).grid(row=0, column=1)

        self.question_label = ttk.Label(self, text="Choose a lesson and start a quiz.", wraplength=800, style="Section.TLabel")
        self.question_label.grid(row=1, column=0, sticky="w", pady=(10, 10))
        self.options_frame = ttk.Frame(self)
        self.options_frame.grid(row=2, column=0, sticky="w")
        self.answer_entry = ttk.Entry(self, textvariable=self.answer, width=45)
        self.answer_entry.grid(row=3, column=0, sticky="w", pady=10)
        self.hint_label = ttk.Label(self, text="", wraplength=800, foreground="#6C584C")
        self.hint_label.grid(row=4, column=0, sticky="w", pady=4)
        self.feedback_label = ttk.Label(self, textvariable=self.feedback, wraplength=800)
        self.feedback_label.grid(row=5, column=0, sticky="w", pady=8)
        controls = ttk.Frame(self)
        controls.grid(row=6, column=0, sticky="w", pady=10)
        self.hint_button = ttk.Button(controls, text="Hint", command=self.show_hint)
        self.hint_button.grid(row=0, column=0, padx=(0, 6))
        self.submit_button = ttk.Button(controls, text="Submit Answer", command=self.submit)
        self.submit_button.grid(row=0, column=1, padx=6)
        self.next_button = ttk.Button(controls, text="Next", command=self.next_question, state="disabled")
        self.next_button.grid(row=0, column=2, padx=6)
        self.reveal_button = ttk.Button(
            controls,
            text="Show explanation and continue",
            command=self.reveal_explanation,
            state="disabled",
        )
        self.reveal_button.grid(row=0, column=3, padx=6)

    def begin(self, view: QuizView) -> None:
        """Load a fresh quiz question into the screen."""
        self.pending_view = view
        self._show_view(view)

    def _show_view(self, view: QuizView) -> None:
        for widget in self.options_frame.winfo_children():
            widget.destroy()
        self.answer.set("")
        self.feedback.set("")
        self.hint_label.configure(text="")
        self.next_button.configure(state="disabled")
        self.reveal_button.configure(state="disabled")
        self.submit_button.configure(state="normal")
        self.hint_button.configure(state="normal")

        if view.question is None:
            self.question_label.configure(
                text=f"Quiz complete: {view.score}/{view.total} correct. Check Progress for your recommendation."
            )
            self.answer_entry.grid_remove()
            self.hint_button.configure(state="disabled")
            self.submit_button.configure(state="disabled")
            self.next_button.configure(text="View Progress", state="normal")
            return

        self.next_button.configure(text="Next question")
        self.question_label.configure(
            text=f"{view.topic.title()} quiz • Question {view.position}/{view.total}\n\n{view.question.question}"
        )
        self.answer_entry.grid()
        if view.question.options:
            self.answer_entry.grid_remove()
            for option in view.question.options:
                ttk.Radiobutton(self.options_frame, text=option, value=option, variable=self.answer).pack(
                    anchor="w", pady=2
                )

    def show_hint(self) -> None:
        hint = self.app.controller.quiz_hint()
        if hint:
            self.hint_label.configure(text=f"Hint: {hint}")
        if self.app.controller.can_reveal_quiz_explanation():
            self.reveal_button.configure(state="normal")

    def submit(self) -> None:
        if not self.answer.get().strip():
            self.feedback.set("Enter or choose an answer first.")
            return
        result = self.app.controller.submit_quiz_answer(self.answer.get())
        if result is None:
            self.feedback.set("No active quiz. Return to Learning and start one.")
            return
        if result.correct:
            self.feedback.set(f"{result.message}\nExplanation: {result.explanation}")
            self.pending_view = self.app.controller.quiz_view()
            self.submit_button.configure(state="disabled")
            self.hint_button.configure(state="disabled")
            self.next_button.configure(state="normal")
            return

        # Keep the same question active. The student may request a hint and
        # retry; the explanation is intentionally withheld until it is solved.
        self.feedback.set(f"{result.message} The explanation will appear after a correct answer.")
        self.answer.set("")
        self.next_button.configure(state="disabled")
        if self.app.controller.can_reveal_quiz_explanation():
            self.reveal_button.configure(state="normal")

    def reveal_explanation(self) -> None:
        """Use the explicit retry escape hatch after sufficient learner effort."""
        result = self.app.controller.reveal_quiz_explanation()
        if result is None:
            self.feedback.set("Try the question again or request another hint first.")
            return
        self.feedback.set(f"{result.message}\nExplanation: {result.explanation}")
        self.pending_view = self.app.controller.quiz_view()
        self.submit_button.configure(state="disabled")
        self.hint_button.configure(state="disabled")
        self.reveal_button.configure(state="disabled")
        self.next_button.configure(state="normal")

    def next_question(self) -> None:
        if self.pending_view is not None and self.pending_view.question is None:
            self.app.show_screen("progress")
            return
        if self.pending_view is not None:
            self._show_view(self.pending_view)

    def refresh(self) -> None:
        if self.app.controller.quiz_session is None:
            self.question_label.configure(text="Choose a migrated lesson and start a quiz from Learning.")


class ProgressScreen(Screen):
    """Show only local, aggregate progress and a simple recommendation."""

    def __init__(self, parent: ttk.Frame, app: LearningApp) -> None:
        super().__init__(parent, app)
        self.columnconfigure(0, weight=1)
        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Progress", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Button(header, text="Back to Learning", command=lambda: app.show_screen("learning")).grid(row=0, column=1)
        self.summary = ttk.Label(self, justify="left", wraplength=780, font=("Segoe UI", 12))
        self.summary.grid(row=1, column=0, sticky="nw", padx=20, pady=20)

    def refresh(self) -> None:
        self.summary.configure(text=self.app.controller.progress_text())


class LibraryScreen(Screen):
    """Browse only the actual structured lessons available locally."""

    def __init__(self, parent: ttk.Frame, app: LearningApp) -> None:
        super().__init__(parent, app)
        self.columnconfigure(0, weight=1)
        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Lesson Library", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Button(header, text="Home", command=lambda: app.show_screen("home")).grid(row=0, column=1)
        self.subject = tk.StringVar()
        selector = ttk.Frame(self)
        selector.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        ttk.Label(selector, text="Subject:").grid(row=0, column=0, padx=(0, 8))
        self.subject_box = ttk.Combobox(selector, textvariable=self.subject, state="readonly")
        self.subject_box.grid(row=0, column=1, sticky="w")
        self.subject_box.bind("<<ComboboxSelected>>", lambda _event: self._build_lesson_buttons())
        self.lesson_buttons = ttk.Frame(self)
        self.lesson_buttons.grid(row=2, column=0, sticky="nw")

    def _build_lesson_buttons(self) -> None:
        for widget in self.lesson_buttons.winfo_children():
            widget.destroy()
        lessons = self.app.controller.available_lessons(self.subject.get())
        if not lessons:
            ttk.Label(self.lesson_buttons, text="No structured local lessons are installed for this subject yet.").pack(
                anchor="w"
            )
            return
        ttk.Label(
            self.lesson_buttons,
            text="Choose a local draft lesson. Content review status is shown inside the lesson.",
            wraplength=700,
        ).pack(anchor="w", pady=(0, 8))
        for lesson in lessons:
            ttk.Button(
                self.lesson_buttons,
                text=lesson.title,
                command=lambda topic=lesson.topic: self.open_lesson(topic),
            ).pack(anchor="w", pady=3)

    def open_lesson(self, topic: str) -> None:
        response = self.app.controller.open_library_lesson(topic)
        self.app.learning_screen.render_response(response, append=False)
        if response.topic:
            self.app.learning_screen.status.set(f"Offline local mode • Topic: {response.topic}")
        self.app.show_screen("learning")

    def refresh(self) -> None:
        subjects = self.app.controller.supported_subjects()
        self.subject_box.configure(values=subjects)
        preference = self.app.controller.preferences().subject
        self.subject.set(preference if preference in subjects else subjects[0])
        self._build_lesson_buttons()


class SettingsScreen(Screen):
    """Show local-mode configuration and honest availability notices."""

    def __init__(self, parent: ttk.Frame, app: LearningApp) -> None:
        super().__init__(parent, app)
        self.columnconfigure(0, weight=1)
        ttk.Label(self, text="Settings", style="Title.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 16))
        self.details = ttk.Label(self, justify="left", wraplength=780)
        self.details.grid(row=1, column=0, sticky="nw", padx=20, pady=10)
        ttk.Button(self, text="Change preferences", command=lambda: app.show_screen("home")).grid(
            row=2, column=0, sticky="w", padx=20, pady=10
        )
        ttk.Button(self, text="Back to Learning", command=lambda: app.show_screen("learning")).grid(
            row=3, column=0, sticky="w", padx=20, pady=2
        )

    def refresh(self) -> None:
        preferences = self.app.controller.preferences()
        voice = DisabledVoiceProvider()
        self.details.configure(
            text=(
                f"Language requested: {preferences.language}\n"
                f"Class / level: {preferences.level}\n"
                f"Subject: {preferences.subject}\n"
                f"Verified local-context mode: {'On' if preferences.culture_mode else 'Off'}\n\n"
                "The core app runs locally without an API key. The small offline neural model only routes lesson actions; it does not generate factual content.\n\n"
                f"Voice: {voice.unavailable_reason()}"
            )
        )
