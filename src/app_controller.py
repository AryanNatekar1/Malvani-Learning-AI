"""Testable application actions used by the Tkinter interface."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from ai_provider import AIProvider, OfflineAIProvider
from context_engine import ContextFormatError, ContextRepository, ContextSelection, StudentContext
from knowledge_engine import (
    available_subjects,
    find_topic,
    get_structured_lesson,
    load_structured_lessons,
    load_student_lesson,
)
from lesson_models import Lesson, QuizQuestion
from problem_engine import AttemptFeedback, GuidedProblemSession
from problem_scenario_engine import (
    ProblemScenario,
    ProblemScenarioRepository,
    ProblemScenarioSession,
    ScenarioAttemptFeedback,
    ScenarioFormatError,
    ScenarioSection,
    render_go_deeper,
    render_problem_solver,
)
from quiz_engine import QuizEvaluation, QuizSession
from related_question_engine import (
    DEFINITION,
    EXPLANATION,
    RelatedQuestionResponse,
    answer_related_question,
    classify_related_question,
)
from reasoning_engine import ReasoningEngine, ReasoningFeedback
from recommendation_engine import LearningRecommendation, build_recommendation
from student_engine import ProfileStore, SQLiteProfileStore, StudentRepository, StudentProfile
from teaching_engine import LessonSection, TeachingEngine


# These phrases signal that a student wants the guided lesson flow, not one
# isolated fact.  Narrow requests such as a formula or an example are handled
# separately by ``related_question_engine``.
FULL_LESSON_CUES = (
    "explain",
    "teach",
    "learn about",
    "show the lesson",
    "simple explanation",
    "detailed explanation",
    "what is",
    "define",
)


RESEARCH_STAGE_LABELS = {
    "hypothesis": "Hypothesis",
    "analysis": "Analysis",
    "proposal": "Proposed next test",
    "reflection": "Reflection",
}


@dataclass(frozen=True)
class LearningPreferences:
    """The settings that influence the currently displayed learning response."""

    language: str
    level: str
    subject: str
    culture_mode: bool


@dataclass(frozen=True)
class TutorResponse:
    """A UI-ready response from structured or legacy local content."""

    topic: str | None
    text: str
    is_structured: bool
    start_quiz: bool = False
    sections: tuple[LessonSection, ...] = ()


@dataclass(frozen=True)
class QuizView:
    """The current question and progress for the GUI quiz screen."""

    topic: str
    question: QuizQuestion | None
    position: int
    total: int
    score: int


@dataclass(frozen=True)
class ProblemSolverView:
    """Small UI-facing snapshot of an active authored problem model."""

    topic: str
    title: str
    current_step_number: int
    total_steps: int
    prompt: str
    attempts: int
    hint_requests: int
    is_complete: bool
    can_reveal_solution: bool
    can_go_deeper: bool
    solution_reviewed: bool


@dataclass(frozen=True)
class ResearchView:
    """UI-facing prompts for a sourced model investigation, not an AI grader."""

    topic: str
    title: str
    hypothesis_prompt: str
    analysis_prompt: str
    proposed_solution_prompt: str
    reflection_prompt: str
    completed_stages: frozenset[str]


class AppController:
    """Coordinate local content, teaching logic, progress, and AI fallback."""

    def __init__(
        self,
        profile_store: StudentRepository | ProfileStore | None = None,
        teaching_engine: TeachingEngine | None = None,
        ai_provider: AIProvider | None = None,
        reasoning_engine: ReasoningEngine | None = None,
        context_repository: ContextRepository | None = None,
        scenario_repository: ProblemScenarioRepository | None = None,
    ) -> None:
        self._persistence_notice: str | None = None
        self._context_notice: str | None = None
        self._scenario_notice: str | None = None
        self.profile_store = profile_store or self._default_profile_store()
        self.profile = self._load_profile_safely()
        self.teaching_engine = teaching_engine or TeachingEngine()
        self.ai_provider = ai_provider or OfflineAIProvider()
        self.reasoning_engine = reasoning_engine or ReasoningEngine()
        self.context_repository = context_repository or self._default_context_repository()
        self.scenario_repository = scenario_repository or self._default_scenario_repository()
        # This is deliberately session-only. It is a learning preference for
        # the current window, not a saved location, school, or identifier.
        self.selected_manual_context_id: str | None = None
        self.current_lesson: Lesson | None = None
        self.current_topic: str | None = None
        self.quiz_session: QuizSession | None = None
        self.current_problem_session: GuidedProblemSession | None = None
        self.current_problem_hints = 0
        # This is intentionally separate from ``current_problem_session``.
        # The latter belongs to a lesson's normal Try It challenge; the former
        # owns one authored, sourced computer-model investigation.
        self.current_scenario_session: ProblemScenarioSession | None = None
        self._scenario_solution_reviewed = False
        self._research_started = False
        self._research_completed_stages: set[str] = set()
        # The GUI uses this to remove stale widgets even when a learner opens
        # the same topic again and its name therefore does not change.
        self.learning_state_version = 0

    def _default_profile_store(self) -> StudentRepository | ProfileStore:
        """Prefer SQLite, with a private in-memory-safe fallback on failure."""
        try:
            return SQLiteProfileStore()
        except (OSError, sqlite3.DatabaseError):
            self._persistence_notice = (
                "Local progress storage could not be opened. You can keep learning, "
                "but changes may not be saved after you close the app."
            )
            return ProfileStore()

    def _load_profile_safely(self) -> StudentProfile:
        """Start a usable learning session even when local storage is unavailable."""
        try:
            return self.profile_store.load()
        except (OSError, sqlite3.DatabaseError, TypeError, ValueError):
            self._persistence_notice = (
                "Local progress could not be read. You can keep learning in this session, "
                "but progress may not be available after you close the app."
            )
            return StudentProfile()

    def _default_context_repository(self) -> ContextRepository:
        """Load reviewed local context data without making it required for learning."""
        try:
            return ContextRepository.from_directory()
        except (OSError, ContextFormatError):
            self._context_notice = (
                "Reviewed learning-context data could not be loaded. Lessons will continue "
                "without a local context."
            )
            return ContextRepository()

    def _default_scenario_repository(self) -> ProblemScenarioRepository:
        """Load optional authored computer models without blocking the tutor."""
        try:
            return ProblemScenarioRepository.from_directory()
        except (OSError, ScenarioFormatError):
            self._scenario_notice = (
                "Problem Solver activities could not be loaded. Lessons will continue "
                "without those optional activities."
            )
            return ProblemScenarioRepository()

    def persistence_notice(self) -> str | None:
        """Return a learner-friendly local-storage notice, if one is needed."""
        return self._persistence_notice

    def context_notice(self) -> str | None:
        """Return a learner-safe context-data notice, if loading failed."""
        return self._context_notice

    def scenario_notice(self) -> str | None:
        """Return a learner-safe notice when optional Problem Solver data failed."""
        return self._scenario_notice

    def available_manual_contexts(self) -> tuple[StudentContext, ...]:
        """Return only source-backed context choices safe for the Home screen."""
        return self.context_repository.student_options()

    def select_manual_context(self, identifier: str | None) -> ContextSelection:
        """Remember one reviewed manual choice for this session only.

        The selection is intentionally not written to the profile or event
        store. It can become a location proxy, so closing the application or
        choosing "no context" removes it.
        """
        selection = self.context_repository.select_manual(identifier)
        self.selected_manual_context_id = (
            selection.context.identifier if selection.context is not None else None
        )
        return selection

    def clear_manual_context(self) -> None:
        """Discard the session-only manual learning context."""
        self.selected_manual_context_id = None

    def active_manual_context(self) -> StudentContext | None:
        """Return the chosen context only if it is authored for the active lesson."""
        if self.current_topic is None:
            return None
        selection = self.context_repository.select_manual(
            self.selected_manual_context_id,
            self.current_topic,
        )
        return selection.context

    def supported_subjects(self) -> tuple[str, ...]:
        """Expose only subjects with actual migrated lessons."""
        return available_subjects()

    def available_lessons(self, subject: str | None = None) -> tuple[Lesson, ...]:
        """Return real structured lessons for the Library screen."""
        lessons = load_structured_lessons()
        if subject is None:
            return lessons
        return tuple(lesson for lesson in lessons if lesson.subject == subject)

    def open_library_lesson(self, topic: str) -> TutorResponse:
        """Open a library lesson and align the selected subject with it."""
        lesson = get_structured_lesson(topic)
        if lesson is None:
            return TutorResponse(None, "That lesson is not available in the local library.", False)
        if self.profile.preferred_subject != lesson.subject:
            self.save_preferences(
                LearningPreferences(
                    language=self.profile.preferred_language,
                    level=self.profile.class_level,
                    subject=lesson.subject,
                    culture_mode=self.profile.culture_mode,
                )
            )
        return self._show_topic(topic)

    def preferences(self) -> LearningPreferences:
        """Return preferences from the local profile."""
        return LearningPreferences(
            language=self.profile.preferred_language,
            level=self.profile.class_level,
            subject=self.profile.preferred_subject,
            culture_mode=self.profile.culture_mode,
        )

    def save_preferences(self, preferences: LearningPreferences) -> None:
        """Update only local preferences; no identity information is required."""
        subject_changed = self.profile.preferred_subject != preferences.subject
        self.profile.preferred_language = preferences.language
        self.profile.class_level = preferences.level
        self.profile.preferred_subject = preferences.subject
        self.profile.culture_mode = preferences.culture_mode
        if subject_changed:
            self.clear_learning_state()
        self._save_profile()

    def clear_learning_state(self) -> None:
        """Clear lesson-specific state when a subject change makes it irrelevant."""
        self.current_lesson = None
        self.current_topic = None
        self._clear_lesson_activity_state()

    def _clear_lesson_activity_state(self) -> None:
        """Discard in-memory work that belongs to one lesson topic.

        A normal lesson challenge, quiz, Problem Solver session, and Go Deeper
        prompts all have different responsibilities.  They are cleared
        together only when the underlying lesson context changes.
        """
        self.quiz_session = None
        self.current_problem_session = None
        self.current_problem_hints = 0
        self.current_scenario_session = None
        self._scenario_solution_reviewed = False
        self._research_started = False
        self._research_completed_stages.clear()
        self.learning_state_version += 1

    def answer_question(self, question: str) -> TutorResponse:
        """Answer a topic question or a bounded follow-up from local lesson data."""
        topic = find_topic(question)
        if topic is not None:
            topic_subject = self._subject_for_topic(topic)
            if topic_subject != self.profile.preferred_subject:
                return TutorResponse(
                    topic,
                    (
                        f"{topic.title()} is available in {topic_subject}. "
                        f"You selected {self.profile.preferred_subject}; switch the subject in Home "
                        "to study this topic."
                    ),
                    False,
                )
            lesson = get_structured_lesson(topic)
            related = (
                answer_related_question(lesson, question, self.profile.preferred_language)
                if lesson is not None
                else None
            )
            related_type = classify_related_question(question)
            # A student who explicitly asks to learn or explain a new topic
            # should receive the full teaching sequence, not only a paragraph.
            # Targeted requests such as a formula or example remain focused.
            if lesson is not None and self._is_full_lesson_request(question, related_type):
                return self._show_topic(topic)
            if related is not None and related.question_type != DEFINITION:
                if self.current_lesson is None or self.current_lesson.topic != lesson.topic:
                    self._activate_structured_lesson(lesson)
                return self._render_related_answer(related)
            if related_type not in {None, DEFINITION} and lesson is not None:
                if self.current_lesson is None or self.current_lesson.topic != lesson.topic:
                    self._activate_structured_lesson(lesson)
                return self._missing_related_answer(question)
            return self._show_topic(topic)

        if self.current_lesson is not None:
            related = answer_related_question(
                self.current_lesson,
                question,
                self.profile.preferred_language,
            )
            if related is not None:
                return self._render_related_answer(related)
            if classify_related_question(question) is not None:
                return self._missing_related_answer(question)

        ai_result = self.ai_provider.generate_response(question)
        if self.current_lesson is not None and ai_result.intent in {
            "hint",
            "challenge",
            "solution",
            "lesson",
        }:
            action = "full" if ai_result.intent == "lesson" else ai_result.intent
            return self.lesson_action(action)

        if self.current_lesson is not None and ai_result.intent == "quiz":
            quiz = self.start_quiz()
            if quiz is not None:
                return TutorResponse(
                    self.current_topic,
                    "Your local quiz is ready. Opening the Quiz screen.",
                    True,
                    start_quiz=True,
                )

        return TutorResponse(
            None,
            (
                f"I am still learning this topic. Try a supported "
                f"{self.profile.preferred_subject} topic."
            ),
            False,
        )

    @staticmethod
    def _is_full_lesson_request(question: str, related_type: str | None) -> bool:
        """Return whether a topic request should start the guided lesson flow.

        ``related_type`` takes priority for targeted material such as formulas,
        examples, uses, misconceptions, careers, and next steps.  A standalone
        ``Why?`` or ``How?`` remains a follow-up question about the active
        lesson, while an explicit teach/explain request opens the full flow.
        """
        if related_type not in {None, DEFINITION, EXPLANATION}:
            return False
        normalized_question = " ".join(question.lower().split())
        return any(cue in normalized_question for cue in FULL_LESSON_CUES)

    def related_question_suggestions(self) -> tuple[str, ...]:
        """Return only follow-up prompts that the active lesson can answer.

        Suggestions are deliberately data-backed.  They do not predict a
        student's intent or manufacture links to culture, language, or topics
        that are not installed in the local lesson library.
        """
        if self.current_lesson is None:
            return ()
        candidates = (
            "Why does this happen?",
            "Give an everyday example",
            "What are its real-world uses?",
            "What is a common misconception?",
            "What careers use this?",
            "What should I learn next?",
            "What is the formula?",
        )
        return tuple(
            question
            for question in candidates
            if answer_related_question(
                self.current_lesson,
                question,
                self.profile.preferred_language,
            )
            is not None
        )

    def _show_topic(self, topic: str) -> TutorResponse:
        structured_lesson = get_structured_lesson(topic)

        if structured_lesson is not None:
            self._activate_structured_lesson(structured_lesson)
            return self.lesson_action("full")

        legacy_content = load_student_lesson(topic)
        if legacy_content is not None:
            self.current_topic = topic
            self.current_lesson = None
            self._clear_lesson_activity_state()
            self.profile.record_lesson(topic)
            self._record_event("legacy_lesson_opened", topic)
            self._save_profile()
            return TutorResponse(
                topic,
                f"{topic.title()} (local legacy lesson)\n\n{legacy_content}",
                False,
            )
        return TutorResponse(topic, f"Knowledge file missing: {topic}.txt", False)

    def _activate_structured_lesson(self, lesson: Lesson) -> None:
        """Make one structured lesson the active local learning context."""
        self.current_topic = lesson.topic
        self.current_lesson = lesson
        self._clear_lesson_activity_state()
        self.profile.record_lesson(lesson.topic)
        self._record_event("lesson_opened", lesson.topic)
        self._save_profile()

    def _render_related_answer(self, related: RelatedQuestionResponse) -> TutorResponse:
        """Present a stored follow-up answer with normal review safeguards."""
        assert self.current_lesson is not None
        sections: tuple[LessonSection, ...] = (LessonSection(related.title, related.text),)
        if related.lesson_verification_status != "VERIFIED":
            sections = (
                LessonSection(
                    "CONTENT STATUS",
                    "This local draft lesson is functional but pending academic review. "
                    "Verify important coursework with a teacher or textbook.",
                ),
                *sections,
            )
        if related.language.notice:
            sections = (LessonSection("LANGUAGE NOTE", related.language.notice), *sections)
        return TutorResponse(
            self.current_lesson.topic,
            self._rendered_text(self.current_lesson.title, sections),
            True,
            sections=sections,
        )

    def _missing_related_answer(self, question: str) -> TutorResponse:
        """Explain a local-data gap instead of filling it with a guess."""
        assert self.current_lesson is not None
        question_type = classify_related_question(question) or "answer"
        readable_type = question_type.replace("_", " ")
        body = (
            f"This local lesson does not yet contain a stored {readable_type} answer. "
            "I will not make one up. Try a simple explanation, everyday example, real-world use, "
            "or another installed lesson section instead."
        )
        sections: tuple[LessonSection, ...] = (LessonSection("LOCAL LESSON LIMIT", body),)
        if self.current_lesson.verification_status != "VERIFIED":
            sections = (
                LessonSection(
                    "CONTENT STATUS",
                    "This local draft lesson is functional but pending academic review. "
                    "Verify important coursework with a teacher or textbook.",
                ),
                *sections,
            )
        return TutorResponse(
            self.current_lesson.topic,
            self._rendered_text(self.current_lesson.title, sections),
            True,
            sections=sections,
        )

    def lesson_action(self, action: str) -> TutorResponse:
        """Show a focused structured section without revealing a solution by default."""
        if self.current_lesson is None:
            return TutorResponse(
                self.current_topic,
                "Choose a migrated lesson first. Legacy lessons are still available for reading.",
                False,
            )

        if action == "challenge":
            return self.start_challenge()
        if action == "hint":
            return self.challenge_hint()
        if action == "solution":
            return self.reveal_challenge_solution()

        return self._render_lesson_action(action)

    def _render_lesson_action(self, action: str) -> TutorResponse:
        """Render an allowed teaching action from the current structured lesson."""
        assert self.current_lesson is not None

        preferences = self.preferences()
        response = self.teaching_engine.build_response(
            self.current_lesson,
            preferences.level,
            preferences.language,
            action=action,
            culture_mode=preferences.culture_mode,
        )
        sections = response.sections
        if action == "full":
            context = self.active_manual_context()
            if context is not None:
                sections = (self._manual_context_section(context), *sections)
        if action == "full" and self.current_lesson.verification_status != "VERIFIED":
            sections = (
                LessonSection(
                    "CONTENT STATUS",
                    "This local draft lesson is functional but pending academic review. "
                    "Use it for learning practice and verify important coursework with a teacher or textbook.",
                ),
                *sections,
            )
        if response.language.notice:
            sections = (LessonSection("LANGUAGE NOTE", response.language.notice), *sections)
        return TutorResponse(
            self.current_lesson.topic,
            self._rendered_text(response.title, sections),
            True,
            sections=sections,
        )

    @staticmethod
    def _manual_context_section(context: StudentContext) -> LessonSection:
        """Render a reviewed, manual context without implying device location."""
        return LessonSection(
            "MANUAL LEARNING CONTEXT",
            (
                "You selected this learning context manually. The app did not use GPS "
                "or collect your location.\n\n"
                f"{context.educational_prompt}\n\n"
                f"Source: {context.source}"
            ),
        )

    @staticmethod
    def _rendered_text(title: str, sections: tuple[LessonSection, ...]) -> str:
        """Keep terminal, GUI, and test representations equally safety-aware."""
        rendered_sections = [title]
        rendered_sections.extend(
            f"{section.title}\n{section.body}" for section in sections
        )
        return "\n\n".join(rendered_sections)

    def _scenario_for_active_lesson(self) -> ProblemScenario | None:
        """Return the first explicitly authored model for the current lesson only."""
        if self.current_lesson is None:
            return None
        scenarios = self.scenario_repository.for_topic(
            self.current_lesson.topic,
            self.current_lesson.subject,
        )
        return scenarios[0] if scenarios else None

    def problem_scenario_available(self) -> bool:
        """Tell the GUI whether this installed lesson has a Problem Solver model."""
        return self._scenario_for_active_lesson() is not None

    @staticmethod
    def _scenario_sections(
        sections: tuple[ScenarioSection, ...],
    ) -> tuple[LessonSection, ...]:
        """Adapt framework-free scenario content to the existing lesson-card UI."""
        return tuple(LessonSection(section.title, section.body) for section in sections)

    @staticmethod
    def _scenario_source_section(scenario: ProblemScenario) -> LessonSection:
        """Keep the concept source distinct from the authored model values."""
        source = scenario.content_source.citation
        if scenario.content_source.url:
            source += f"\n{scenario.content_source.url}"
        if scenario.content_source.usage_note:
            source += f"\n\n{scenario.content_source.usage_note}"
        return LessonSection("CONCEPT SOURCE", source)

    def _scenario_response(
        self,
        title: str,
        sections: tuple[LessonSection, ...],
    ) -> TutorResponse:
        """Build one consistent terminal and GUI representation of scenario content."""
        return TutorResponse(
            self.current_topic,
            self._rendered_text(title, sections),
            True,
            sections=sections,
        )

    def start_problem_solver(self) -> TutorResponse:
        """Start or resume a separate sourced computer-model investigation.

        This deliberately does not touch the normal lesson challenge or quiz
        session.  The first implementation is one illustrative model, never
        a local observation, GPS result, or claim about a real place.
        """
        scenario = self._scenario_for_active_lesson()
        if scenario is None:
            return TutorResponse(
                self.current_topic,
                "This installed lesson does not have a Problem Solver activity yet.",
                False,
            )

        if (
            self.current_scenario_session is None
            or self.current_scenario_session.scenario.identifier != scenario.identifier
        ):
            self.current_scenario_session = ProblemScenarioSession(scenario)
            self._scenario_solution_reviewed = False
            self._research_started = False
            self._research_completed_stages.clear()
            self._record_event("scenario_started", self.current_topic)

        session = self.current_scenario_session
        overview = self._scenario_sections(render_problem_solver(scenario)[:4])
        sections = (
            overview[0],
            self._scenario_source_section(scenario),
            *overview[1:],
        )
        current_step = session.current_step_section()
        if current_step is not None:
            sections = (*sections, *self._scenario_sections((current_step,)))
        else:
            sections = (
                *sections,
                LessonSection(
                    "MODEL STEPS COMPLETE",
                    "You completed every authored model step. Choose Go Deeper to investigate "
                    "the supplied data further.",
                ),
            )
        return self._scenario_response(f"Problem Solver: {scenario.title}", sections)

    def problem_solver_view(self) -> ProblemSolverView | None:
        """Return current model-step state for the focused Problem Solver controls."""
        session = self.current_scenario_session
        if session is None or self.current_topic is None:
            return None
        step = session.current_step
        total_steps = len(session.scenario.guided_steps)
        return ProblemSolverView(
            topic=self.current_topic,
            title=session.scenario.title,
            current_step_number=(session.current_step_index + 1 if step else total_steps),
            total_steps=total_steps,
            prompt=(
                step.prompt
                if step is not None
                else "All guided model steps are complete. You can Go Deeper when ready."
            ),
            attempts=session.attempts,
            hint_requests=session.hint_requests,
            is_complete=session.is_complete,
            can_reveal_solution=session.can_reveal_solution(),
            can_go_deeper=self.can_go_deeper(),
            solution_reviewed=self._scenario_solution_reviewed,
        )

    def submit_problem_solver_attempt(self, answer: str) -> ScenarioAttemptFeedback | None:
        """Check one transparent model step and save only aggregate result data."""
        session = self.current_scenario_session
        if session is None or self.current_topic is None:
            return None
        feedback = session.submit_attempt(answer)
        if feedback.correct is not None:
            self.profile.record_problem_solver_attempt(feedback.correct)
            self._record_event("scenario_attempt", self.current_topic, feedback.correct)
            self._save_profile()
        return feedback

    def problem_solver_hint(self) -> TutorResponse:
        """Return the next authored model hint without revealing an answer."""
        session = self.current_scenario_session
        if session is None:
            return TutorResponse(
                self.current_topic,
                "Open Problem Solver first, then ask for a model hint if you need one.",
                True,
            )
        if session.is_complete:
            return self._scenario_response(
                f"Problem Solver: {session.scenario.title}",
                (
                    LessonSection(
                        "MODEL STEPS COMPLETE",
                        "The guided steps are complete. Choose Go Deeper to investigate the "
                        "supplied model data.",
                    ),
                ),
            )
        hint = session.hint()
        if self.current_topic is not None:
            self.profile.record_hint(self.current_topic)
            self._record_event("scenario_hint", self.current_topic)
            self._save_profile()
        return self._scenario_response(
            f"Problem Solver: {session.scenario.title}",
            (LessonSection(f"PROBLEM HINT {session.hint_requests}", hint),),
        )

    def reveal_problem_solver_solution(self) -> TutorResponse:
        """Reveal a worked model only after an attempt or two requested hints."""
        session = self.current_scenario_session
        if session is None:
            return TutorResponse(
                self.current_topic,
                "Open Problem Solver first. Try an answer or ask for two hints before the model solution.",
                True,
            )
        solution = session.reveal_solution()
        if not solution.available:
            return self._scenario_response(
                f"Problem Solver: {session.scenario.title}",
                (LessonSection("KEEP TRYING", solution.text),),
            )
        if not self._scenario_solution_reviewed:
            self._scenario_solution_reviewed = True
            self._record_event("scenario_solution_reviewed", self.current_topic, False)
        return self._scenario_response(
            f"Problem Solver: {session.scenario.title}",
            (
                LessonSection("MODEL SOLUTION", solution.text),
                LessonSection(
                    "LEARNING STATUS",
                    "Viewing a worked solution lets you explore further, but it does not prove "
                    "that you have mastered the model yet.",
                ),
            ),
        )

    def can_go_deeper(self) -> bool:
        """Unlock investigation after all steps or an explicit solution review."""
        session = self.current_scenario_session
        return bool(
            session is not None
            and (session.is_complete or self._scenario_solution_reviewed)
        )

    def start_go_deeper(self) -> TutorResponse:
        """Open a data-backed research-style extension without pretending to grade it."""
        session = self.current_scenario_session
        if session is None:
            return TutorResponse(
                self.current_topic,
                "Complete or review a Problem Solver activity before opening Go Deeper.",
                True,
            )
        if not self.can_go_deeper():
            return self._scenario_response(
                f"Go Deeper: {session.scenario.title}",
                (
                    LessonSection(
                        "FIRST, WORK THE MODEL",
                        "Complete the guided model steps, or deliberately review the worked "
                        "solution after making an attempt or using two hints.",
                    ),
                ),
            )
        if not self._research_started:
            self._research_started = True
            self._record_event("research_started", self.current_topic)

        scenario = session.scenario
        sections = (
            LessonSection("CONTENT STATUS", scenario.content_status_notice),
            self._scenario_source_section(scenario),
            *self._scenario_sections(render_go_deeper(scenario)),
            LessonSection(
                "RESEARCH MODE LIMIT",
                "These are supplied computer-model values, not observations from your area. "
                "This offline activity records only that you completed a prompt; it cannot "
                "semantically grade your scientific writing.",
            ),
        )
        if self._scenario_solution_reviewed and not session.is_complete:
            sections = (
                LessonSection(
                    "LEARNING STATUS",
                    "You reached Go Deeper after reviewing the model solution. Use the prompts "
                    "to practise your own investigation; this is not recorded as mastery.",
                ),
                *sections,
            )
        return self._scenario_response(f"Go Deeper: {scenario.title}", sections)

    def research_view(self) -> ResearchView | None:
        """Return research prompts once the learner has opened Go Deeper."""
        session = self.current_scenario_session
        if session is None or self.current_topic is None or not self._research_started:
            return None
        activity = session.scenario.go_deeper
        return ResearchView(
            topic=self.current_topic,
            title=session.scenario.title,
            hypothesis_prompt=activity.hypothesis_prompt,
            analysis_prompt=activity.analysis_prompt,
            proposed_solution_prompt=activity.proposed_solution_prompt,
            reflection_prompt=activity.reflection_prompt,
            completed_stages=frozenset(self._research_completed_stages),
        )

    def submit_research_response(self, stage: str, response: str) -> TutorResponse:
        """Acknowledge a research prompt without storing or falsely grading free text."""
        normalized_stage = stage.strip().lower()
        session = self.current_scenario_session
        if session is None or not self._research_started:
            return TutorResponse(
                self.current_topic,
                "Open Go Deeper before recording a research check-in.",
                True,
            )
        if normalized_stage not in RESEARCH_STAGE_LABELS:
            return self._scenario_response(
                f"Go Deeper: {session.scenario.title}",
                (LessonSection("RESEARCH CHECK-IN", "That research prompt is not available."),),
            )
        if not response.strip():
            return self._scenario_response(
                f"Go Deeper: {session.scenario.title}",
                (
                    LessonSection(
                        "RESEARCH CHECK-IN",
                        f"Write your {RESEARCH_STAGE_LABELS[normalized_stage].lower()} before "
                        "marking this prompt complete.",
                    ),
                ),
            )
        if normalized_stage in self._research_completed_stages:
            message = (
                f"Your {RESEARCH_STAGE_LABELS[normalized_stage].lower()} was already marked "
                "complete in this session. The app does not save or semantically grade the text "
                "you wrote. Compare it with the supplied model data and its limits."
            )
        else:
            self._research_completed_stages.add(normalized_stage)
            self.profile.record_research_stage()
            self._record_event(f"research_{normalized_stage}_completed", self.current_topic)
            self._save_profile()
            message = (
                f"{RESEARCH_STAGE_LABELS[normalized_stage]} marked complete for this session. "
                "The app did not save your writing and cannot determine whether it is scientifically "
                "correct. Check your ideas against the supplied model data, assumptions, and limits."
            )
        return self._scenario_response(
            f"Go Deeper: {session.scenario.title}",
            (LessonSection("RESEARCH CHECK-IN", message),),
        )

    def start_challenge(self) -> TutorResponse:
        """Start a challenge session so hints and solution gating have real state."""
        if self.current_lesson is None or self.current_lesson.challenge is None:
            return TutorResponse(
                self.current_topic,
                "This lesson does not have a structured challenge yet.",
                False,
            )
        self.current_problem_session = GuidedProblemSession(self.current_lesson.challenge)
        self.current_problem_hints = 0
        return self._render_lesson_action("challenge")

    def submit_challenge_attempt(self, answer: str) -> AttemptFeedback | None:
        """Evaluate a challenge attempt and persist only aggregate attempt data."""
        if self.current_problem_session is None or self.current_topic is None:
            return None
        feedback = self.current_problem_session.submit_attempt(answer)
        self.profile.record_challenge_attempt(feedback.correct)
        self._record_event("challenge_attempt", self.current_topic, feedback.correct)
        self._save_profile()
        return feedback

    def challenge_hint(self) -> TutorResponse:
        """Give a progressive local hint and count the actual request."""
        if self.current_problem_session is None:
            return TutorResponse(
                self.current_topic,
                "Start the challenge first, then ask for a hint if you need one.",
                True,
            )
        hint_text = self.current_problem_session.hint()
        self.current_problem_hints = self.current_problem_session.hint_requests
        if self.current_topic is not None:
            self.profile.record_hint(self.current_topic)
            self._record_event("challenge_hint", self.current_topic)
            self._save_profile()
        return TutorResponse(
            self.current_topic,
            f"HINT {self.current_problem_hints}\n{hint_text}",
            True,
        )

    def reveal_challenge_solution(self) -> TutorResponse:
        """Reveal a solution after a meaningful attempt or two hints."""
        if self.current_problem_session is None:
            return TutorResponse(
                self.current_topic,
                "Start the challenge first. Try an answer or ask for a hint before viewing the solution.",
                True,
            )
        if self.current_problem_session.attempts == 0 and self.current_problem_hints < 2:
            return TutorResponse(
                self.current_topic,
                (
                    "Try the challenge first. You can submit one attempt, or use two hints, "
                    "before opening the solution."
                ),
                True,
            )
        return TutorResponse(
            self.current_topic,
            f"SOLUTION\n{self.current_problem_session.solution()}",
            True,
        )

    def check_reasoning(self, student_reasoning: str) -> ReasoningFeedback | None:
        """Evaluate a think-question response with transparent local criteria."""
        if self.current_lesson is None or self.current_topic is None:
            return None
        if not student_reasoning.strip():
            return ReasoningFeedback(
                category="insufficient_reasoning",
                message="Write your own explanation before checking it.",
                retry_recommended=True,
                hint=(
                    self.current_lesson.challenge.hint
                    if self.current_lesson.challenge is not None
                    else None
                ),
            )
        feedback = self.reasoning_engine.evaluate(self.current_lesson, student_reasoning)
        self.profile.record_reasoning_attempt(self.current_topic)
        self._record_event("reasoning_attempt", self.current_topic)
        self._save_profile()
        return feedback

    def start_quiz(self) -> QuizView | None:
        """Start an offline quiz for the current structured lesson, if available."""
        if self.current_lesson is None or not self.current_lesson.quiz_questions:
            return None
        self.quiz_session = QuizSession(self.current_lesson.quiz_questions)
        return self.quiz_view()

    def quiz_view(self) -> QuizView | None:
        """Return current quiz state for a GUI screen."""
        if self.quiz_session is None or self.current_topic is None:
            return None
        return QuizView(
            topic=self.current_topic,
            question=self.quiz_session.current_question,
            position=self.quiz_session.current_index + 1,
            total=len(self.quiz_session.questions),
            score=self.quiz_session.correct_count,
        )

    def submit_quiz_answer(self, answer: str) -> QuizEvaluation | None:
        """Score an answer and save aggregate local progress only."""
        if self.quiz_session is None or self.current_topic is None:
            return None
        result = self.quiz_session.submit(answer)
        if result is not None:
            self.profile.record_question(self.current_topic, result.correct)
            self._record_event("quiz_attempt", self.current_topic, result.correct)
            self._save_profile()
        return result

    def quiz_hint(self) -> str | None:
        """Return the next stored quiz hint without exposing the answer."""
        if self.quiz_session is None or self.current_topic is None:
            return None
        hint = self.quiz_session.hint()
        if hint is not None:
            self.profile.record_hint(self.current_topic)
            self._record_event("quiz_hint", self.current_topic)
            self._save_profile()
        return hint

    def can_reveal_quiz_explanation(self) -> bool:
        """Whether the learner has made enough effort to reveal the explanation."""
        return self.quiz_session is not None and self.quiz_session.can_reveal_current()

    def reveal_quiz_explanation(self) -> QuizEvaluation | None:
        """Reveal and move on after the retry policy has been met."""
        if self.quiz_session is None or self.current_topic is None:
            return None
        result = self.quiz_session.reveal_and_continue()
        if result is not None:
            self._record_event("quiz_explanation_revealed", self.current_topic, False)
        return result

    def progress_text(self) -> str:
        """Build a local-only progress summary and honest recommendation."""
        topics = ", ".join(self.profile.topics_studied) or "No topics studied yet"
        recommendation = self.learning_recommendation()

        summary = (
            f"Topics studied: {topics}\n"
            f"Quiz answer attempts: {self.profile.questions_attempted}\n"
            f"Correct submissions: {self.profile.questions_correct}\n"
            f"Answer-attempt accuracy: {self.profile.accuracy:.0f}%\n\n"
            f"Reasoning attempts: {self.profile.reasoning_attempts}\n"
            f"Hints used: {self.profile.hints_used}\n"
            f"Challenge attempts: {self.profile.challenge_attempts}\n"
            f"Problem Solver model-step attempts: {self.profile.problem_solver_attempts}\n"
            f"Correct model steps: {self.profile.problem_solver_correct}\n"
            f"Research prompts completed: {self.profile.research_stages_completed}\n\n"
            f"Recommendation\n{recommendation.as_text()}"
        )
        if self._persistence_notice:
            summary += f"\n\nLocal storage note: {self._persistence_notice}"
        return summary

    def learning_recommendation(self) -> LearningRecommendation:
        """Return one next step supported by real local evidence and lesson data."""
        return build_recommendation(
            self.profile,
            load_structured_lessons(),
            self.current_lesson,
        )

    def dashboard_text(self) -> str:
        """Return a dashboard summary made only from actual local profile data."""
        last_topic = self.profile.topics_studied[-1] if self.profile.topics_studied else None
        continue_text = (
            f"Continue learning: {last_topic.title()}"
            if last_topic
            else "Continue learning: choose your first local lesson."
        )
        recommendation = self.learning_recommendation()
        summary = (
            f"{continue_text}\n"
            f"Topics opened: {len(self.profile.topics_studied)}\n"
            f"Quiz answer attempts: {self.profile.questions_attempted}\n"
            f"{recommendation.title}\n"
            f"{recommendation.message}\n"
            f"Reason: {recommendation.reason}"
        )
        if self._persistence_notice:
            summary += f"\n\nLocal storage note: {self._persistence_notice}"
        return summary

    def _subject_for_topic(self, topic: str) -> str:
        """Resolve the real subject for structured topics and legacy Physics files."""
        lesson = get_structured_lesson(topic)
        if lesson is not None:
            return lesson.subject
        return "Physics"

    def _save_profile(self) -> None:
        try:
            self.profile_store.save(self.profile)
        except (OSError, sqlite3.DatabaseError, TypeError, ValueError):
            self._persistence_notice = (
                "Local progress could not be saved. You can keep learning in this session, "
                "but changes may not be available after you close the app."
            )

    def _record_event(
        self, event_type: str, topic: str | None = None, correct: bool | None = None
    ) -> None:
        """Use event persistence when the selected local store supports it."""
        record_event = getattr(self.profile_store, "record_event", None)
        if callable(record_event):
            try:
                record_event(event_type, topic, correct)
            except (OSError, sqlite3.DatabaseError, TypeError, ValueError):
                self._persistence_notice = (
                    "Local progress could not be saved. You can keep learning in this session, "
                    "but changes may not be available after you close the app."
                )
