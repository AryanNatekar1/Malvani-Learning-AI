"""Tkinter desktop interface for the offline Malvani Learning AI prototype."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from app_controller import AppController, LearningPreferences, QuizView
from language_engine import SUPPORTED_LANGUAGES, interface_text
from media_engine import get_visual
from ui_theme import PALETTE, configure_theme
from visual_learning import create_interactive_visual
from voice_engine import DisabledVoiceProvider


LEVELS = ("Beginner", "Class 8", "Class 9", "Class 10", "Class 11/12")


class ScrollableLessonCards(ttk.Frame):
    """A responsive scrollable stack of focused lesson sections."""

    def __init__(self, parent: ttk.Frame) -> None:
        super().__init__(parent, style="Soft.TFrame")
        self.canvas = tk.Canvas(
            self,
            highlightthickness=0,
            background=PALETTE["surface_soft"],
            bd=0,
        )
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.content = ttk.Frame(self, style="Soft.TFrame", padding=(8, 4))
        self._content_window = self.canvas.create_window(
            (0, 0), window=self.content, anchor="nw"
        )
        self.content.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._resize_content)
        self._bind_scroll_events(self.canvas)
        self._bind_scroll_events(self.content)
        self._rendered_text = ""
        self._body_labels: list[ttk.Label] = []

    def _update_scroll_region(self, _event: tk.Event[tk.Misc]) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_content(self, event: tk.Event[tk.Misc]) -> None:
        self.canvas.itemconfigure(self._content_window, width=event.width)
        wraplength = max(320, event.width - 68)
        for label in self._body_labels:
            if label.winfo_exists():
                label.configure(wraplength=wraplength)

    def _on_mousewheel(self, event: tk.Event[tk.Misc]) -> None:
        if event.delta:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def _scroll_up(self, _event: tk.Event[tk.Misc]) -> str:
        self.canvas.yview_scroll(-1, "units")
        return "break"

    def _scroll_down(self, _event: tk.Event[tk.Misc]) -> str:
        self.canvas.yview_scroll(1, "units")
        return "break"

    def _bind_scroll_events(self, widget: tk.Misc) -> None:
        """Let a wheel over a card scroll the lesson, not only its canvas."""
        widget.bind("<MouseWheel>", self._on_mousewheel, add="+")
        widget.bind("<Button-4>", self._scroll_up, add="+")
        widget.bind("<Button-5>", self._scroll_down, add="+")

    def render(
        self,
        title: str,
        text: str,
        sections: tuple[object, ...] = (),
        append: bool = False,
        student_question: str = "",
    ) -> None:
        """Render structured sections as cards or a single honest information card."""
        if not append:
            for widget in self.content.winfo_children():
                widget.destroy()
            self._rendered_text = ""
            self._body_labels = []

        if student_question:
            self.add_student_question(student_question)

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

    def add_student_question(self, question: str) -> None:
        """Add a small, readable prompt card to a continuing tutor trail."""
        if not question:
            return
        card = ttk.Frame(self.content, style="Soft.TFrame", padding=(14, 10))
        card.pack(fill="x", padx=6, pady=(10, 4))
        ttk.Label(card, text="YOUR QUESTION", style="CardTitle.TLabel").pack(anchor="w")
        label = ttk.Label(
            card,
            text=question,
            style="CardBody.TLabel",
            justify="left",
            wraplength=max(320, self.canvas.winfo_width() - 68),
        )
        label.pack(anchor="w", pady=(3, 0))
        self._bind_scroll_events(card)
        self._bind_scroll_events(label)
        self._body_labels.append(label)
        self._rendered_text += f"YOUR QUESTION\n{question}\n\n"

    def _add_card(self, title: str, body: str) -> None:
        card = ttk.Frame(self.content, style="LessonCard.TFrame", padding=(14, 10))
        card.pack(fill="x", padx=6, pady=5)
        ttk.Label(card, text=title, style="CardTitle.TLabel").pack(anchor="w")
        body_label = ttk.Label(
            card,
            text=body,
            justify="left",
            wraplength=max(320, self.canvas.winfo_width() - 68),
            style="CardBody.TLabel",
        )
        body_label.pack(fill="x", pady=(4, 0))
        self._bind_scroll_events(card)
        self._bind_scroll_events(body_label)
        self._body_labels.append(body_label)

    def rendered_text(self) -> str:
        """Expose displayed text for lightweight GUI tests."""
        return self._rendered_text


class ScrollableScreen(ttk.Frame):
    """A vertically scrollable page body for compact laptop windows.

    A desktop page may contain more controls than fit at 800×600.  This
    wrapper keeps every control reachable without introducing a separate
    toolkit or duplicating page layout code.  Screens that already contain a
    primary scrolling workspace (Learning) keep their focused layout.
    """

    def __init__(self, parent: ttk.Frame, app: "LearningApp") -> None:
        super().__init__(parent, style="App.TFrame")
        self.app = app
        self.canvas = tk.Canvas(
            self,
            highlightthickness=0,
            background=PALETTE["app"],
            bd=0,
        )
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.body = ttk.Frame(self.canvas, style="App.TFrame")
        self.body.columnconfigure(0, weight=1)
        self.body.rowconfigure(0, weight=1)
        self._body_window = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.content: Screen | None = None
        self.body.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._resize_body)
        self._bind_scroll_events(self.canvas)
        self._bind_scroll_events(self.body)

    def _update_scroll_region(self, _event: tk.Event[tk.Misc]) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_body(self, event: tk.Event[tk.Misc]) -> None:
        self.canvas.itemconfigure(self._body_window, width=event.width)

    def _on_mousewheel(self, event: tk.Event[tk.Misc]) -> str:
        if event.delta:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        return "break"

    def _scroll_up(self, _event: tk.Event[tk.Misc]) -> str:
        self.canvas.yview_scroll(-1, "units")
        return "break"

    def _scroll_down(self, _event: tk.Event[tk.Misc]) -> str:
        self.canvas.yview_scroll(1, "units")
        return "break"

    def _bind_scroll_events(self, widget: tk.Misc) -> None:
        if getattr(widget, "_page_scroll_bound", False):
            return
        widget.bind("<MouseWheel>", self._on_mousewheel, add="+")
        widget.bind("<Button-4>", self._scroll_up, add="+")
        widget.bind("<Button-5>", self._scroll_down, add="+")
        setattr(widget, "_page_scroll_bound", True)

    def set_content(self, content: "Screen") -> None:
        """Place one screen inside this viewport and bind its controls to scroll."""
        self.content = content
        content.grid(row=0, column=0, sticky="nsew")
        self._bind_descendants(content)

    def _bind_descendants(self, widget: tk.Misc) -> None:
        """Forward wheel events from ordinary controls to this page viewport."""
        for child in widget.winfo_children():
            # Lesson cards own their focused scroll area; forwarding their
            # wheel events to the outer page would make both canvases move.
            if isinstance(child, (ScrollableLessonCards, ScrollableScreen)):
                continue
            self._bind_scroll_events(child)
            self._bind_descendants(child)

    def refresh(self) -> None:
        """Forward navigation refreshes to the page's actual content body."""
        if self.content is not None:
            self.content.refresh()
            self._bind_descendants(self.content)
        self.after_idle(lambda: self.canvas.configure(scrollregion=self.canvas.bbox("all")))


class LearningApp(tk.Tk):
    """One window with navigable screens for local learning activities."""

    def __init__(self, controller: AppController | None = None) -> None:
        super().__init__()
        self.title("Malvani Learning AI")
        self.geometry("1180x760")
        self.minsize(800, 600)
        self.controller = controller or AppController()
        configure_theme(self)
        self._active_screen = "home"
        self._compact_navigation = False
        self._navigation_buttons: dict[str, ttk.Button] = {}

        self.shell = ttk.Frame(self, style="App.TFrame")
        self.shell.pack(fill="both", expand=True)
        self.shell.rowconfigure(0, weight=1)
        self.shell.columnconfigure(1, weight=1)

        self.sidebar = ttk.Frame(self.shell, style="Sidebar.TFrame", padding=(18, 24))
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.columnconfigure(0, weight=1)
        self._build_sidebar()

        self.main_area = ttk.Frame(self.shell, style="App.TFrame")
        self.main_area.grid(row=0, column=1, sticky="nsew")
        self.main_area.rowconfigure(2, weight=1)
        self.main_area.columnconfigure(0, weight=1)

        self.topbar = ttk.Frame(self.main_area, style="Topbar.TFrame", padding=(24, 14))
        self.topbar.grid(row=0, column=0, sticky="ew")
        self.topbar.columnconfigure(0, weight=1)
        self.page_title = tk.StringVar(value="Welcome")
        self.page_meta = tk.StringVar(value="Offline-first local learning")
        ttk.Label(self.topbar, textvariable=self.page_title, style="TopbarTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(self.topbar, textvariable=self.page_meta, style="TopbarMeta.TLabel").grid(
            row=1, column=0, sticky="w", pady=(2, 0)
        )
        ttk.Label(
            self.topbar,
            text="LOCAL MODE",
            style="Status.TLabel",
        ).grid(row=0, column=1, rowspan=2, sticky="e")

        self.compact_nav = ttk.Frame(self.main_area, style="Topbar.TFrame", padding=(16, 0, 16, 8))
        self.compact_nav.grid(row=1, column=0, sticky="ew")
        self.compact_nav.grid_remove()
        self._build_compact_navigation()

        container = ttk.Frame(self.main_area, style="App.TFrame", padding=(24, 20, 24, 24))
        container.grid(row=2, column=0, sticky="nsew")
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        # Each page sits in a lightweight scrollable viewport.  It keeps the
        # app usable on the supported 800×600 laptop size while preserving the
        # same screen objects used by the controller and tests.
        self.home_viewport = ScrollableScreen(container, self)
        self.learning_viewport = ScrollableScreen(container, self)
        self.quiz_viewport = ScrollableScreen(container, self)
        self.progress_viewport = ScrollableScreen(container, self)
        self.library_viewport = ScrollableScreen(container, self)
        self.settings_viewport = ScrollableScreen(container, self)

        self.home_screen = HomeScreen(self.home_viewport.body, self)
        self.learning_screen = LearningScreen(self.learning_viewport.body, self)
        self.quiz_screen = QuizScreen(self.quiz_viewport.body, self)
        self.progress_screen = ProgressScreen(self.progress_viewport.body, self)
        self.library_screen = LibraryScreen(self.library_viewport.body, self)
        self.settings_screen = SettingsScreen(self.settings_viewport.body, self)
        self.home_viewport.set_content(self.home_screen)
        self.learning_viewport.set_content(self.learning_screen)
        self.quiz_viewport.set_content(self.quiz_screen)
        self.progress_viewport.set_content(self.progress_screen)
        self.library_viewport.set_content(self.library_screen)
        self.settings_viewport.set_content(self.settings_screen)
        self.screens = {
            "home": self.home_viewport,
            "learning": self.learning_viewport,
            "quiz": self.quiz_viewport,
            "progress": self.progress_viewport,
            "library": self.library_viewport,
            "settings": self.settings_viewport,
        }
        for screen in self.screens.values():
            screen.grid(row=0, column=0, sticky="nsew")

        self.bind("<Configure>", self._adapt_navigation, add="+")
        self.show_screen("home")

    def _build_sidebar(self) -> None:
        """Create one consistent navigation system for every workspace."""
        mark = ttk.Label(self.sidebar, text="ML", style="SidebarBrand.TLabel")
        mark.grid(row=0, column=0, sticky="w")
        ttk.Label(self.sidebar, text="Malvani Learning AI", style="SidebarBrand.TLabel").grid(
            row=1, column=0, sticky="w", pady=(8, 0)
        )
        ttk.Label(
            self.sidebar,
            text="Ask. Think. Try. Grow.",
            style="SidebarMeta.TLabel",
        ).grid(row=2, column=0, sticky="w", pady=(2, 28))

        labels = (
            ("home", "Home"),
            ("learning", "Learn"),
            ("quiz", "Quiz"),
            ("progress", "Progress"),
            ("library", "Library"),
            ("settings", "Settings"),
        )
        for row, (screen, label) in enumerate(labels, start=3):
            button = ttk.Button(
                self.sidebar,
                text=label,
                style="Nav.TButton",
                command=lambda page=screen: self._navigate_from_shell(page),
            )
            button.grid(row=row, column=0, sticky="ew", pady=2)
            self._navigation_buttons[screen] = button

        self.sidebar.rowconfigure(10, weight=1)
        ttk.Label(
            self.sidebar,
            text="Your progress stays on this computer.",
            style="SidebarMeta.TLabel",
            wraplength=160,
            justify="left",
        ).grid(row=11, column=0, sticky="sw", pady=(24, 0))

    def _build_compact_navigation(self) -> None:
        """Provide usable navigation when the window is too narrow for a rail."""
        for column, (screen, label) in enumerate(
            (("home", "Home"), ("learning", "Learn"), ("quiz", "Quiz"), ("progress", "Progress"), ("library", "Library"), ("settings", "Settings"))
        ):
            self.compact_nav.columnconfigure(column, weight=1)
            ttk.Button(
                self.compact_nav,
                text=label,
                style="CompactNav.TButton",
                command=lambda page=screen: self._navigate_from_shell(page),
            ).grid(row=0, column=column, sticky="ew", padx=2)

    def _navigate_from_shell(self, target: str) -> None:
        """Handle navigation that may need a new quiz session first.

        Returning to Quiz must resume an in-progress local session. Starting a
        new session only when none exists protects a student's attempt, hints,
        and score from being silently reset by navigation.
        """
        if target == "quiz":
            view = self.controller.quiz_view()
            if view is None:
                view = self.controller.start_quiz()
            if view is None:
                self.show_screen("learning")
                self.learning_screen.write_output(
                    "Choose a migrated lesson, then use Start quiz after you have explored the idea."
                )
                return
            self.quiz_screen.begin(view)
        self.show_screen(target)

    def _adapt_navigation(self, event: tk.Event[tk.Misc]) -> None:
        """Switch to compact navigation before content becomes cramped."""
        if event.widget is not self:
            return
        compact = event.width < 1020
        if compact == self._compact_navigation:
            return
        self._compact_navigation = compact
        if compact:
            self.sidebar.grid_remove()
            self.shell.columnconfigure(0, weight=1)
            self.shell.columnconfigure(1, weight=0)
            self.main_area.grid_configure(column=0)
            self.compact_nav.grid()
        else:
            self.sidebar.grid()
            self.shell.columnconfigure(0, weight=0)
            self.shell.columnconfigure(1, weight=1)
            self.main_area.grid_configure(column=1)
            self.compact_nav.grid_remove()

    def show_screen(self, name: str) -> None:
        """Raise a screen and let it refresh its local view state."""
        screen = self.screens[name]
        screen.tkraise()
        self._active_screen = name
        self._update_shell_context(name)
        for target, button in self._navigation_buttons.items():
            button.configure(style="ActiveNav.TButton" if target == name else "Nav.TButton")
        screen.refresh()

    def _update_shell_context(self, name: str) -> None:
        """Keep the shell informative without repeating every page's controls."""
        titles = {
            "home": ("Welcome", "Set your learning preferences and choose a next step."),
            "learning": ("Learning space", "Understand first, then think, try, and reflect."),
            "quiz": ("Practice quiz", "Hints and retries support learning before answers are revealed."),
            "progress": ("Your progress", "Private, local activity summaries—not a measure of your potential."),
            "library": ("Lesson library", "Choose from the structured lessons installed on this computer."),
            "settings": ("Settings", "Language, privacy, and future accessibility options."),
        }
        title, meta = titles[name]
        preferences = self.controller.preferences()
        self.page_title.set(title)
        self.page_meta.set(f"{meta}  •  {preferences.subject}  •  {preferences.level}")

    def show_diagram(self, topic: str | None) -> tk.Toplevel | None:
        """Open an installed visual only when it has a learning purpose."""
        if topic is None:
            messagebox.showinfo("Diagram", "Ask about a supported topic first.")
            return None
        visual = get_visual(topic)
        if visual is None:
            messagebox.showinfo(
                "Diagram",
                "No diagram has been added for this lesson yet. A visual should be added only when it improves understanding.",
            )
            return None

        window = tk.Toplevel(self)
        window.title(visual.title)
        window.configure(background=PALETTE["app"])
        content = ttk.Frame(window, style="App.TFrame", padding=(20, 18))
        content.pack(fill="both", expand=True)
        ttk.Label(content, text=visual.title, style="Section.TLabel").pack(anchor="w")
        ttk.Label(
            content,
            text=visual.description,
            style="Subtitle.TLabel",
            wraplength=640,
            justify="left",
        ).pack(anchor="w", pady=(4, 2))
        ttk.Label(
            content,
            text=f"Learning goal: {visual.learning_goal}",
            style="Subtitle.TLabel",
            wraplength=640,
            justify="left",
        ).pack(anchor="w", pady=(0, 12))

        if visual.interaction:
            interactive_visual = create_interactive_visual(content, topic)
            if interactive_visual is not None:
                window.geometry("720x620")
                window.minsize(560, 500)
                interactive_visual.pack(fill="both", expand=True)
                # A public attribute makes the local component inspectable in
                # GUI smoke tests without relying on widget-order details.
                window.visual_lab = interactive_visual
                return window

        window.geometry("520x420")
        canvas = tk.Canvas(
            content,
            width=460,
            height=240,
            bg=PALETTE["surface"],
            highlightthickness=1,
            highlightbackground=PALETTE["border"],
        )
        canvas.pack(fill="both", expand=True, pady=(0, 4))
        self._draw_visual(canvas, topic)
        return window

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
        super().__init__(parent, style="App.TFrame")
        self.app = app

    def refresh(self) -> None:
        """Update a page after navigation. Subclasses override when useful."""


class MetricCard(ttk.Frame):
    """A compact card for one honest local-progress metric."""

    def __init__(self, parent: ttk.Frame, label: str) -> None:
        super().__init__(parent, style="Card.TFrame", padding=(16, 12))
        self.value = tk.StringVar(value="0")
        ttk.Label(self, textvariable=self.value, style="MetricValue.TLabel").pack(anchor="w")
        ttk.Label(self, text=label, style="MetricLabel.TLabel").pack(anchor="w", pady=(2, 0))


class HomeScreen(Screen):
    """Starting page for language, level, subject, and culture settings."""

    def __init__(self, parent: ttk.Frame, app: LearningApp) -> None:
        super().__init__(parent, app)
        self.columnconfigure(0, weight=1)

        preferences = app.controller.preferences()
        self.language = tk.StringVar(value=preferences.language)
        self.level = tk.StringVar(value=preferences.level)
        subjects = app.controller.supported_subjects() or ("Physics",)
        initial_subject = preferences.subject if preferences.subject in subjects else subjects[0]
        self.subject = tk.StringVar(value=initial_subject)
        self.culture_mode = tk.BooleanVar(value=preferences.culture_mode)

        intro = ttk.Frame(self, style="Surface.TFrame", padding=(28, 24))
        intro.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        ttk.Label(intro, text="MALVANI LEARNING AI", style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(
            intro,
            text="Learn • Think • Solve • Explore",
            style="SurfaceMuted.TLabel",
        ).pack(pady=(8, 24))
        ttk.Label(
            intro,
            text=(
                "Offline-first learning with local draft lessons, guided practice, "
                "and source-gated local context."
            ),
            wraplength=610,
            justify="center",
            style="Surface.TLabel",
        ).pack()

        form = ttk.LabelFrame(self, text="Learning preferences", style="Card.TLabelframe", padding=22)
        form.grid(row=1, column=0, columnspan=2, pady=(0, 14), sticky="ew")
        form.columnconfigure(1, weight=1)
        self.language_label = ttk.Label(form, style="Surface.TLabel")
        self.language_label.grid(row=0, column=0, padx=(0, 16), pady=8, sticky="w")
        ttk.Combobox(form, textvariable=self.language, values=SUPPORTED_LANGUAGES, state="readonly").grid(
            row=0, column=1, pady=8, sticky="ew"
        )
        self.level_label = ttk.Label(form, style="Surface.TLabel")
        self.level_label.grid(row=1, column=0, padx=(0, 16), pady=8, sticky="w")
        ttk.Combobox(form, textvariable=self.level, values=LEVELS, state="readonly").grid(
            row=1, column=1, pady=8, sticky="ew"
        )
        self.subject_label = ttk.Label(form, style="Surface.TLabel")
        self.subject_label.grid(row=2, column=0, padx=(0, 16), pady=8, sticky="w")
        ttk.Combobox(form, textvariable=self.subject, values=subjects, state="readonly").grid(
            row=2, column=1, pady=8, sticky="ew"
        )
        ttk.Checkbutton(
            form,
            text="Use verified local context when available",
            variable=self.culture_mode,
        ).grid(row=3, column=0, columnspan=2, pady=(12, 8), sticky="w")
        self.start_button = ttk.Button(form, style="Primary.TButton", command=self.start_learning)
        self.start_button.grid(row=4, column=0, columnspan=2, pady=(16, 0))

        dashboard = ttk.LabelFrame(self, text="Your next step", style="Card.TLabelframe", padding=18)
        dashboard.grid(row=2, column=0, columnspan=2, pady=(0, 8), sticky="ew")
        dashboard.columnconfigure(0, weight=1)
        self.dashboard_text = ttk.Label(dashboard, justify="left", wraplength=760, style="CardBody.TLabel")
        self.dashboard_text.grid(row=0, column=0, sticky="w")
        self.recommendation_button = ttk.Button(
            dashboard,
            text="Browse lesson library",
            style="Secondary.TButton",
            command=self.open_recommendation,
        )
        self.recommendation_button.grid(
            row=1, column=0, sticky="w", pady=(10, 0)
        )

        metrics = ttk.Frame(self, style="App.TFrame")
        metrics.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        for column in range(3):
            metrics.columnconfigure(column, weight=1)
        self.topics_metric = MetricCard(metrics, "Lessons opened")
        self.attempts_metric = MetricCard(metrics, "Quiz answer attempts")
        self.accuracy_metric = MetricCard(metrics, "Answer-attempt accuracy")
        self.topics_metric.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.attempts_metric.grid(row=0, column=1, sticky="ew", padx=5)
        self.accuracy_metric.grid(row=0, column=2, sticky="ew", padx=(5, 0))

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

    def open_recommendation(self) -> None:
        """Open an installed recommendation, or the real lesson library."""
        recommendation = self.app.controller.learning_recommendation()
        if recommendation.topic is not None:
            self.app.library_screen.open_lesson(recommendation.topic)
            return
        self.app.show_screen("library")

    def refresh(self) -> None:
        preferences = self.app.controller.preferences()
        self.language.set(preferences.language)
        self.level.set(preferences.level)
        self.subject.set(preferences.subject)
        self.culture_mode.set(preferences.culture_mode)
        self.dashboard_text.configure(text=self.app.controller.dashboard_text())
        recommendation = self.app.controller.learning_recommendation()
        if recommendation.topic is not None:
            self.recommendation_button.configure(text=f"Open: {recommendation.title}")
        else:
            self.recommendation_button.configure(text="Browse lesson library")
        profile = self.app.controller.profile
        self.topics_metric.value.set(str(len(profile.topics_studied)))
        self.attempts_metric.value.set(str(profile.questions_attempted))
        self.accuracy_metric.value.set(f"{profile.accuracy:.0f}%")


class LearningScreen(Screen):
    """Question-answer and guided-lesson screen."""

    def __init__(self, parent: ttk.Frame, app: LearningApp) -> None:
        super().__init__(parent, app)
        self.rowconfigure(4, weight=1)
        self.columnconfigure(0, weight=1)
        self.question = tk.StringVar()
        self.reasoning = tk.StringVar()
        self.challenge_answer = tk.StringVar()
        self.status = tk.StringVar(value="Offline local mode")
        self._trail_topic: str | None = None

        header = ttk.Frame(self, style="Surface.TFrame", padding=(18, 14))
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Ask, understand, then try", style="PageTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            header,
            text="The tutor uses installed local lesson data; it does not guess beyond it.",
            style="TopbarMeta.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(3, 0))
        ttk.Button(
            header,
            text="Clear workspace",
            style="Secondary.TButton",
            command=self.clear_workspace,
        ).grid(row=0, column=1, rowspan=2, sticky="e")

        ttk.Label(self, textvariable=self.status, style="Status.TLabel").grid(
            row=1, column=0, sticky="w", pady=(0, 8)
        )
        question_row = ttk.Frame(self, style="Surface.TFrame", padding=(12, 10))
        question_row.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        question_row.columnconfigure(0, weight=1)
        question_entry = ttk.Entry(question_row, textvariable=self.question)
        question_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        question_entry.bind("<Return>", lambda _event: self.ask_question())
        ttk.Button(question_row, text="Ask", style="Primary.TButton", command=self.ask_question).grid(
            row=0, column=1
        )

        self.related_frame = ttk.Frame(self, style="App.TFrame")
        self.related_frame.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        self.related_frame.columnconfigure(1, weight=1)
        self.related_label = ttk.Label(
            self.related_frame,
            text="Useful follow-up questions appear after you open a structured lesson.",
            style="Subtitle.TLabel",
        )
        self.related_label.grid(row=0, column=0, sticky="w")
        self.related_buttons = ttk.Frame(self.related_frame, style="App.TFrame")
        self.related_buttons.grid(row=1, column=0, sticky="ew", pady=(5, 0))

        self.lesson_cards = ScrollableLessonCards(self)
        self.lesson_cards.grid(row=4, column=0, sticky="nsew", pady=(0, 10))
        # In a page viewport, Canvas has no useful requested height by
        # default.  Reserve enough reading space for a lesson card while the
        # outer page can scroll to the Think/Try controls on small laptops.
        self.lesson_cards.canvas.configure(height=280)

        reasoning_frame = ttk.LabelFrame(
            self,
            text="Think through the idea",
            style="Card.TLabelframe",
            padding=10,
        )
        reasoning_frame.grid(row=5, column=0, sticky="ew", pady=(0, 6))
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
        self.reasoning_feedback = ttk.Label(
            reasoning_frame,
            text="",
            wraplength=850,
            style="Surface.TLabel",
        )
        self.reasoning_feedback.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))

        self.challenge_frame = ttk.LabelFrame(
            self,
            text="Try a challenge",
            style="Card.TLabelframe",
            padding=10,
        )
        self.challenge_frame.grid(row=6, column=0, sticky="ew", pady=(0, 6))
        self.challenge_frame.columnconfigure(0, weight=1)
        ttk.Entry(self.challenge_frame, textvariable=self.challenge_answer).grid(
            row=0, column=0, sticky="ew", padx=(0, 8)
        )
        ttk.Button(
            self.challenge_frame,
            text="Submit Challenge Attempt",
            command=self.submit_challenge_attempt,
        ).grid(row=0, column=1)
        self.challenge_feedback = ttk.Label(
            self.challenge_frame,
            text="",
            wraplength=850,
            style="Surface.TLabel",
        )
        self.challenge_feedback.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))
        self.challenge_frame.grid_remove()

        actions = ttk.Frame(self, style="App.TFrame")
        actions.grid(row=7, column=0, sticky="ew")
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
            style = "Primary.TButton" if action == "simple" else "Secondary.TButton"
            ttk.Button(
                actions,
                text=label,
                style=style,
                command=lambda item=action: self.show_action(item),
            ).grid(
                row=index // 4, column=index % 4, padx=2, pady=2, sticky="ew"
            )
        for column in range(4):
            actions.columnconfigure(column, weight=1)
        ttk.Button(
            actions,
            text="Explore visual",
            style="Secondary.TButton",
            command=self.show_diagram,
        ).grid(
            row=1, column=3, padx=2, pady=2, sticky="ew"
        )

    def navigate(self, target: str) -> None:
        self.app._navigate_from_shell(target)

    def ask_question(self) -> None:
        text = self.question.get().strip()
        if not text:
            return
        previous_topic = self._trail_topic
        response = self.app.controller.answer_question(text)
        active_topic = self.app.controller.current_topic
        topic_changed = (
            response.topic is not None
            and active_topic == response.topic
            and previous_topic != response.topic
        )
        append = bool(self.lesson_cards.rendered_text().strip()) and not topic_changed
        self.render_response(response, append=append, student_question=text)
        if response.start_quiz:
            quiz = self.app.controller.quiz_view()
            if quiz is not None:
                self.app.quiz_screen.begin(quiz)
                self.app.show_screen("quiz")
                return
        if response.topic and self.app.controller.current_topic == response.topic:
            self.status.set(f"Offline local mode • Topic: {response.topic}")
            if topic_changed:
                self._reset_lesson_interaction_widgets()
            self._trail_topic = response.topic
        self.refresh_related_questions()
        self.question.set("")

    def show_action(self, action: str) -> None:
        response = self.app.controller.lesson_action(action)
        self.render_response(response, append=True)
        if action == "challenge" and self.app.controller.current_problem_session is not None:
            self.challenge_answer.set("")
            self.challenge_feedback.configure(text="Try in your own words before opening the solution.")
            self.challenge_frame.grid()
        self.refresh_related_questions()

    def clear_workspace(self) -> None:
        """Clear visible conversation cards without deleting local progress."""
        self._trail_topic = self.app.controller.current_topic
        self._reset_lesson_interaction_widgets()
        self.lesson_cards.render(
            "Learning space",
            "Your visible workspace is clear. Ask a new question, or use a follow-up prompt for the active lesson.",
            append=False,
        )
        self.refresh_related_questions()

    def refresh_related_questions(self) -> None:
        """Show only questions supported by the active lesson's stored data."""
        for widget in self.related_buttons.winfo_children():
            widget.destroy()
        suggestions = self.app.controller.related_question_suggestions()
        if not suggestions:
            self.related_label.configure(
                text="Open a structured lesson to see follow-up questions based on its installed data."
            )
            return
        self.related_label.configure(text="Ask a related question")
        for index, suggestion in enumerate(suggestions[:5]):
            ttk.Button(
                self.related_buttons,
                text=suggestion,
                style="Chip.TButton",
                command=lambda item=suggestion: self.ask_related_question(item),
            ).grid(row=index // 3, column=index % 3, sticky="w", padx=(0, 5), pady=2)

    def ask_related_question(self, question: str) -> None:
        """Route a visible data-backed prompt through the normal tutor path."""
        self.question.set(question)
        self.ask_question()

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

    def render_response(
        self,
        response: object,
        append: bool,
        student_question: str = "",
    ) -> None:
        """Keep structured sections visible while actions add focused new cards."""
        topic = getattr(response, "topic", None)
        title = "Tutor response" if append else (
            topic.title() if isinstance(topic, str) else "Malvani Learning AI"
        )
        self.lesson_cards.render(
            title=title,
            text=str(getattr(response, "text", "")),
            sections=getattr(response, "sections", ()),
            append=append,
            student_question=student_question,
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
        self.refresh_related_questions()


class QuizScreen(Screen):
    """Interactive local quiz screen with hints and score tracking."""

    def __init__(self, parent: ttk.Frame, app: LearningApp) -> None:
        super().__init__(parent, app)
        self.columnconfigure(0, weight=1)
        self.answer = tk.StringVar()
        self.feedback = tk.StringVar()
        self.pending_view: QuizView | None = None

        header = ttk.Frame(self, style="Surface.TFrame", padding=(18, 14))
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Practice with feedback", style="PageTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            header,
            text="Try, use a hint, and retry. Explanations unlock after meaningful effort.",
            style="TopbarMeta.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(3, 0))
        ttk.Button(
            header,
            text="Back to learning",
            style="Secondary.TButton",
            command=lambda: app.show_screen("learning"),
        ).grid(row=0, column=1, rowspan=2, sticky="e")

        progress_row = ttk.Frame(self, style="App.TFrame")
        progress_row.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        progress_row.columnconfigure(0, weight=1)
        self.quiz_meta = tk.StringVar(value="Choose a lesson to begin")
        self.score_meta = tk.StringVar(value="Score: 0")
        ttk.Label(progress_row, textvariable=self.quiz_meta, style="Subtitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(progress_row, textvariable=self.score_meta, style="Subtitle.TLabel").grid(
            row=0, column=1, sticky="e"
        )
        self.quiz_progress = ttk.Progressbar(
            progress_row,
            style="Tutor.Horizontal.TProgressbar",
            mode="determinate",
            maximum=100,
        )
        self.quiz_progress.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5, 0))

        question_card = ttk.Frame(self, style="Card.TFrame", padding=(20, 18))
        question_card.grid(row=2, column=0, sticky="ew")
        question_card.columnconfigure(0, weight=1)
        self.question_label = ttk.Label(
            question_card,
            text="Choose a lesson and start a quiz.",
            wraplength=820,
            style="CardTitle.TLabel",
            justify="left",
        )
        self.question_label.grid(row=0, column=0, sticky="w")
        self.options_frame = ttk.Frame(question_card, style="Surface.TFrame")
        self.options_frame.grid(row=1, column=0, sticky="w", pady=(12, 0))
        self.answer_entry = ttk.Entry(question_card, textvariable=self.answer, width=45)
        self.answer_entry.grid(row=2, column=0, sticky="w", pady=(12, 0))
        self.hint_label = ttk.Label(
            question_card,
            text="",
            wraplength=820,
            style="Warning.TLabel",
        )
        self.hint_label.grid(row=3, column=0, sticky="w", pady=(10, 0))
        self.feedback_label = ttk.Label(
            question_card,
            textvariable=self.feedback,
            wraplength=820,
            justify="left",
            style="Surface.TLabel",
        )
        self.feedback_label.grid(row=4, column=0, sticky="w", pady=(10, 0))
        controls = ttk.Frame(self, style="App.TFrame")
        controls.grid(row=3, column=0, sticky="w", pady=12)
        self.hint_button = ttk.Button(controls, text="Hint", style="Secondary.TButton", command=self.show_hint)
        self.hint_button.grid(row=0, column=0, padx=(0, 6))
        self.submit_button = ttk.Button(
            controls,
            text="Submit answer",
            style="Primary.TButton",
            command=self.submit,
        )
        self.submit_button.grid(row=0, column=1, padx=6)
        self.next_button = ttk.Button(
            controls,
            text="Next",
            style="Secondary.TButton",
            command=self.next_question,
            state="disabled",
        )
        self.next_button.grid(row=0, column=2, padx=6)
        self.reveal_button = ttk.Button(
            controls,
            text="Show explanation and continue",
            style="Secondary.TButton",
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
        completed = view.total if view.question is None else max(0, view.position - 1)
        self.quiz_progress.configure(value=(completed / max(1, view.total)) * 100)
        self.score_meta.set(f"Score: {view.score}/{view.total}")

        if view.question is None:
            self.quiz_meta.set("Quiz complete")
            self.quiz_progress.configure(value=100)
            self.question_label.configure(
                text=f"Quiz complete: {view.score}/{view.total} correct. Check Progress for your recommendation."
            )
            self.answer_entry.grid_remove()
            self.hint_button.configure(state="disabled")
            self.submit_button.configure(state="disabled")
            self.next_button.configure(text="View Progress", state="normal")
            return

        self.quiz_meta.set(f"Question {view.position} of {view.total}")
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
        header = ttk.Frame(self, style="Surface.TFrame", padding=(18, 14))
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Your local progress", style="PageTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            header,
            text="These are activity signals, not a label for your ability.",
            style="TopbarMeta.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(3, 0))
        ttk.Button(
            header,
            text="Continue learning",
            style="Primary.TButton",
            command=lambda: app.show_screen("learning"),
        ).grid(row=0, column=1, rowspan=2, sticky="e")

        metrics = ttk.Frame(self, style="App.TFrame")
        metrics.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        for column in range(3):
            metrics.columnconfigure(column, weight=1)
        self.topics_metric = MetricCard(metrics, "Topics opened")
        self.attempts_metric = MetricCard(metrics, "Quiz answer attempts")
        self.accuracy_metric = MetricCard(metrics, "Answer-attempt accuracy")
        self.topics_metric.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.attempts_metric.grid(row=0, column=1, sticky="ew", padx=5)
        self.accuracy_metric.grid(row=0, column=2, sticky="ew", padx=(5, 0))

        summary_card = ttk.LabelFrame(self, text="Learning summary", style="Card.TLabelframe", padding=18)
        summary_card.grid(row=2, column=0, sticky="ew")
        summary_card.columnconfigure(0, weight=1)
        self.summary = ttk.Label(
            summary_card,
            justify="left",
            wraplength=820,
            style="CardBody.TLabel",
        )
        self.summary.grid(row=0, column=0, sticky="nw")

    def refresh(self) -> None:
        self.summary.configure(text=self.app.controller.progress_text())
        profile = self.app.controller.profile
        self.topics_metric.value.set(str(len(profile.topics_studied)))
        self.attempts_metric.value.set(str(profile.questions_attempted))
        self.accuracy_metric.value.set(f"{profile.accuracy:.0f}%")


class LibraryScreen(Screen):
    """Browse only the actual structured lessons available locally."""

    def __init__(self, parent: ttk.Frame, app: LearningApp) -> None:
        super().__init__(parent, app)
        self.columnconfigure(0, weight=1)
        header = ttk.Frame(self, style="Surface.TFrame", padding=(18, 14))
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Lesson library", style="PageTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            header,
            text="Only installed structured lessons are shown here.",
            style="TopbarMeta.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(3, 0))
        ttk.Button(
            header,
            text="Set preferences",
            style="Secondary.TButton",
            command=lambda: app.show_screen("home"),
        ).grid(row=0, column=1, rowspan=2, sticky="e")
        self.subject = tk.StringVar()
        selector = ttk.Frame(self, style="Card.TFrame", padding=(14, 12))
        selector.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        ttk.Label(selector, text="Subject:", style="Surface.TLabel").grid(
            row=0, column=0, padx=(0, 8)
        )
        self.subject_box = ttk.Combobox(selector, textvariable=self.subject, state="readonly")
        self.subject_box.grid(row=0, column=1, sticky="w")
        self.subject_box.bind("<<ComboboxSelected>>", lambda _event: self._build_lesson_buttons())
        self.lesson_buttons = ttk.Frame(self, style="App.TFrame")
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
            text="Choose a local draft lesson. Its review status is shown inside the learning space.",
            style="Subtitle.TLabel",
            wraplength=760,
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        for column in range(2):
            self.lesson_buttons.columnconfigure(column, weight=1)
        for index, lesson in enumerate(lessons):
            card = ttk.Frame(self.lesson_buttons, style="Card.TFrame", padding=(16, 14))
            card.grid(
                row=(index // 2) + 1,
                column=index % 2,
                sticky="nsew",
                padx=(0, 6) if index % 2 == 0 else (6, 0),
                pady=6,
            )
            ttk.Label(card, text=lesson.title, style="CardTitle.TLabel").pack(anchor="w")
            quiz_status = "Quiz included" if lesson.quiz_questions else "No quiz yet"
            visual_status = "Diagram available" if get_visual(lesson.topic) else "Text lesson"
            ttk.Label(
                card,
                text=f"{lesson.subject}  |  {quiz_status}  |  {visual_status}",
                style="MetricLabel.TLabel",
            ).pack(anchor="w", pady=(4, 10))
            ttk.Button(
                card,
                text="Open lesson",
                style="Primary.TButton",
                command=lambda topic=lesson.topic: self.open_lesson(topic),
            ).pack(anchor="w")

    def open_lesson(self, topic: str) -> None:
        response = self.app.controller.open_library_lesson(topic)
        self.app.learning_screen.render_response(response, append=False)
        self.app.learning_screen._trail_topic = response.topic
        self.app.learning_screen._reset_lesson_interaction_widgets()
        self.app.learning_screen.refresh_related_questions()
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
        header = ttk.Frame(self, style="Surface.TFrame", padding=(18, 14))
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        ttk.Label(header, text="Settings and privacy", style="PageTitle.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="This prototype is local-first and does not need an account or API key.",
            style="TopbarMeta.TLabel",
        ).pack(anchor="w", pady=(3, 0))

        details_card = ttk.LabelFrame(self, text="Current configuration", style="Card.TLabelframe", padding=18)
        details_card.grid(row=1, column=0, sticky="ew")
        self.details = ttk.Label(details_card, justify="left", wraplength=820, style="CardBody.TLabel")
        self.details.pack(anchor="w")
        actions = ttk.Frame(self, style="App.TFrame")
        actions.grid(row=2, column=0, sticky="w", pady=(12, 0))
        ttk.Button(
            actions,
            text="Change preferences",
            style="Primary.TButton",
            command=lambda: app.show_screen("home"),
        ).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(
            actions,
            text="Back to learning",
            style="Secondary.TButton",
            command=lambda: app.show_screen("learning"),
        ).grid(row=0, column=1, padx=6)

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
