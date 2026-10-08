"""Turn a structured lesson into a paced, student-facing teaching response."""

from __future__ import annotations

from dataclasses import dataclass

from culture_engine import context_availability_notice, student_context_text
from language_engine import LanguageResolution, resolve_lesson_language
from lesson_models import Lesson, ObservationActivity
from place_engine import Place, places_for_topic


BEGINNER_LEVELS = {"Beginner", "Class 8"}


@dataclass(frozen=True)
class LessonSection:
    """One labelled section that the terminal or GUI can render."""

    title: str
    body: str


@dataclass(frozen=True)
class TeachingResponse:
    """A response with language metadata and purposeful lesson sections."""

    title: str
    topic: str
    language: LanguageResolution
    sections: tuple[LessonSection, ...]

    def as_text(self) -> str:
        """Render the response in plain text for the GUI and terminal adapters."""
        rendered_sections = [self.title]
        if self.language.notice:
            rendered_sections.append(f"LANGUAGE NOTE\n{self.language.notice}")
        rendered_sections.extend(
            f"{section.title}\n{section.body}" for section in self.sections
        )
        return "\n\n".join(rendered_sections)


class TeachingEngine:
    """Choose useful lesson sections without automatically revealing answers."""

    def build_response(
        self,
        lesson: Lesson,
        level: str,
        language: str,
        action: str = "full",
        culture_mode: bool = True,
    ) -> TeachingResponse:
        """Build a focused teaching response for one requested learning action."""
        language_resolution = resolve_lesson_language(lesson, language)
        content, _ = lesson.content_for(language_resolution.resolved)
        sections = self._sections_for_action(
            lesson, content, level, action, culture_mode
        )
        return TeachingResponse(
            title=lesson.title,
            topic=lesson.topic,
            language=language_resolution,
            sections=tuple(sections),
        )

    def _sections_for_action(
        self,
        lesson: Lesson,
        content: dict[str, object],
        level: str,
        action: str,
        culture_mode: bool,
    ) -> list[LessonSection]:
        simple_explanation = str(content.get("simple_explanation", ""))
        detailed_explanation = str(content.get("detailed_explanation", simple_explanation))
        everyday_example = str(content.get("everyday_example", ""))

        if action == "simple":
            return [LessonSection("SIMPLE EXPLANATION", simple_explanation)]
        if action == "example":
            return self._example_sections(lesson, everyday_example, culture_mode)
        if action == "hint":
            return self._challenge_section(lesson, "HINT", "hint")
        if action == "challenge":
            return self._challenge_section(lesson, "TRY IT", "question")
        if action == "solution":
            return self._challenge_section(lesson, "SOLUTION", "solution")
        if action == "think":
            return self._single_if_present("THINK", lesson.think_question)
        if action == "observe":
            return self._observation_sections(lesson.observe_around_you)
        if action == "places":
            return self._place_sections(lesson.topic)
        if action == "continue":
            return self._list_section("EXPLORE NEXT", lesson.further_exploration)

        explanation = simple_explanation if level in BEGINNER_LEVELS else detailed_explanation
        sections = [LessonSection("CONCEPT", explanation)]
        sections.extend(self._example_sections(lesson, everyday_example, culture_mode))
        sections.extend(self._list_section("REAL-WORLD USE", lesson.real_world_use))
        sections.extend(self._observation_sections(lesson.observe_around_you))
        sections.extend(self._single_if_present("THINK", lesson.think_question))
        sections.extend(self._challenge_section(lesson, "TRY IT", "question"))
        sections.extend(self._list_section("CAREER CONNECTIONS", lesson.career_connections))
        return sections

    @staticmethod
    def _observation_sections(
        activity: ObservationActivity | None,
    ) -> list[LessonSection]:
        """Render the go-and-watch activity the browser app also shows.

        The explanation is deliberately last. On screen the browser hides it
        behind a button; in plain text the best equivalent is to put it after
        the instructions and label it, so a learner who wants to look first
        can stop reading at the right point.
        """
        if activity is None:
            return []
        lines = [
            f"Find this: {activity.invitation}",
            f"Do this: {activity.what_to_do}",
            f"Watch for this: {activity.what_to_notice}",
        ]
        if activity.needs:
            lines.insert(0, "You need: " + ", ".join(activity.needs))
        if activity.safety_note:
            lines.append(f"Stay safe: {activity.safety_note}")
        lines.append(f"Why it happens (read after watching): {activity.concept_link}")
        return [LessonSection("LOOK AROUND YOU", "\n".join(lines))]

    @staticmethod
    def _place_sections(topic: str) -> list[LessonSection]:
        """Name documented places whose science connects to this lesson.

        A place record states public geography rather than a claim about the
        learner, so unlike local context it needs no verification gate to be
        shown. It still carries its draft status, which the body states.
        """
        places: tuple[Place, ...] = places_for_topic(topic)
        if not places:
            return [
                LessonSection(
                    "PLACES",
                    "No place record connects to this lesson yet.",
                )
            ]
        blocks = []
        for place in places:
            questions = [
                f"  - {question.ask}\n    {question.answer}"
                for question in place.questions
                if question.links_to == topic
            ]
            blocks.append(
                f"{place.name} ({place.where})\n"
                f"{place.known_for}\n"
                + "\n".join(questions)
            )
        blocks.append(
            "These are draft records. Each one lists what a local teacher "
            "still needs to confirm; see data/places/."
        )
        return [LessonSection("PLACES NEAR YOU", "\n\n".join(blocks))]

    @staticmethod
    def _single_if_present(title: str, text: str) -> list[LessonSection]:
        return [LessonSection(title, text)] if text else []

    @staticmethod
    def _list_section(title: str, values: tuple[str, ...]) -> list[LessonSection]:
        if not values:
            return []
        return [LessonSection(title, "\n".join(f"- {value}" for value in values))]

    @staticmethod
    def _challenge_section(lesson: Lesson, title: str, field_name: str) -> list[LessonSection]:
        if lesson.challenge is None:
            return []
        return [LessonSection(title, getattr(lesson.challenge, field_name))]

    @staticmethod
    def _example_sections(
        lesson: Lesson, everyday_example: str, culture_mode: bool
    ) -> list[LessonSection]:
        sections: list[LessonSection] = []
        if everyday_example:
            sections.append(LessonSection("EVERYDAY EXAMPLE", everyday_example))

        if culture_mode:
            for context in (lesson.local_example, lesson.culture_connection):
                displayed_context = student_context_text(context)
                if displayed_context:
                    sections.append(LessonSection("VERIFIED LOCAL CONTEXT", displayed_context))
                else:
                    notice = context_availability_notice(context)
                    if notice and not any(section.body == notice for section in sections):
                        sections.append(LessonSection("SINDHUDURG CONNECTION", notice))
        return sections
