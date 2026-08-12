"""Testable application actions used by the Tkinter interface."""

from __future__ import annotations

from dataclasses import dataclass

from ai_provider import AIProvider, OfflineAIProvider
from knowledge_engine import (
    available_subjects,
    find_topic,
    get_structured_lesson,
    load_structured_lessons,
    load_student_lesson,
)
from lesson_models import Lesson, QuizQuestion
from problem_engine import AttemptFeedback, GuidedProblemSession
from quiz_engine import QuizEvaluation, QuizSession
from related_question_engine import (
    DEFINITION,
    RelatedQuestionResponse,
    answer_related_question,
    classify_related_question,
)
from reasoning_engine import ReasoningEngine, ReasoningFeedback
from student_engine import ProfileStore, SQLiteProfileStore, StudentRepository, StudentProfile
from teaching_engine import LessonSection, TeachingEngine


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


class AppController:
    """Coordinate local content, teaching logic, progress, and AI fallback."""

    def __init__(
        self,
        profile_store: StudentRepository | ProfileStore | None = None,
        teaching_engine: TeachingEngine | None = None,
        ai_provider: AIProvider | None = None,
        reasoning_engine: ReasoningEngine | None = None,
    ) -> None:
        self.profile_store = profile_store or SQLiteProfileStore()
        self.profile = self.profile_store.load()
        self.teaching_engine = teaching_engine or TeachingEngine()
        self.ai_provider = ai_provider or OfflineAIProvider()
        self.reasoning_engine = reasoning_engine or ReasoningEngine()
        self.current_lesson: Lesson | None = None
        self.current_topic: str | None = None
        self.quiz_session: QuizSession | None = None
        self.current_problem_session: GuidedProblemSession | None = None
        self.current_problem_hints = 0

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
        self.quiz_session = None
        self.current_problem_session = None
        self.current_problem_hints = 0

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
            # "What is gravity?" remains a complete lesson-opening request.
            # More targeted requests such as a formula, example, or why-question
            # open the lesson and then answer the requested section directly.
            if related is not None and related.question_type != DEFINITION:
                if self.current_lesson is None or self.current_lesson.topic != lesson.topic:
                    self._activate_structured_lesson(lesson)
                return self._render_related_answer(related)
            if classify_related_question(question) not in {None, DEFINITION} and lesson is not None:
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
            self.quiz_session = None
            self.current_problem_session = None
            self.current_problem_hints = 0
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
        self.quiz_session = None
        self.current_problem_session = None
        self.current_problem_hints = 0
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
        text = "\n\n".join(f"{section.title}\n{section.body}" for section in sections)
        return TutorResponse(
            self.current_lesson.topic,
            text,
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
        text = "\n\n".join(f"{section.title}\n{section.body}" for section in sections)
        return TutorResponse(self.current_lesson.topic, text, True, sections=sections)

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
            response.as_text(),
            True,
            sections=sections,
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
        weak_topics = self.profile.weak_topics()
        if weak_topics:
            recommendation = "Review: " + ", ".join(weak_topics)
        elif self.current_lesson is not None and self.current_lesson.further_exploration:
            recommendation = "Try next: " + self.current_lesson.further_exploration[0]
        else:
            recommendation = "Choose a topic and try a challenge."

        return (
            f"Topics studied: {topics}\n"
            f"Quiz answer attempts: {self.profile.questions_attempted}\n"
            f"Correct submissions: {self.profile.questions_correct}\n"
            f"Answer-attempt accuracy: {self.profile.accuracy:.0f}%\n\n"
            f"Reasoning attempts: {self.profile.reasoning_attempts}\n"
            f"Hints used: {self.profile.hints_used}\n"
            f"Challenge attempts: {self.profile.challenge_attempts}\n\n"
            f"Recommendation: {recommendation}"
        )

    def dashboard_text(self) -> str:
        """Return a dashboard summary made only from actual local profile data."""
        last_topic = self.profile.topics_studied[-1] if self.profile.topics_studied else None
        continue_text = (
            f"Continue learning: {last_topic.title()}"
            if last_topic
            else "Continue learning: choose your first local lesson."
        )
        weak_topics = self.profile.weak_topics()
        recommendation = (
            f"Recommended review: {weak_topics[0].title()}"
            if weak_topics
            else "Recommended next step: browse the local lesson library."
        )
        return (
            f"{continue_text}\n"
            f"Topics opened: {len(self.profile.topics_studied)}\n"
            f"Quiz answer attempts: {self.profile.questions_attempted}\n"
            f"{recommendation}"
        )

    def _subject_for_topic(self, topic: str) -> str:
        """Resolve the real subject for structured topics and legacy Physics files."""
        lesson = get_structured_lesson(topic)
        if lesson is not None:
            return lesson.subject
        return "Physics"

    def _save_profile(self) -> None:
        self.profile_store.save(self.profile)

    def _record_event(
        self, event_type: str, topic: str | None = None, correct: bool | None = None
    ) -> None:
        """Use event persistence when the selected local store supports it."""
        record_event = getattr(self.profile_store, "record_event", None)
        if callable(record_event):
            record_event(event_type, topic, correct)
