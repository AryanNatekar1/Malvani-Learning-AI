"""Offline, reviewable Problem Solver scenarios.

This module is deliberately independent from the GUI and the existing lesson
engine.  It turns small, authored JSON records into a predictable guided
problem flow that a controller can later connect to Learn, Problem Solver, or
Researcher screens.

The first record is an *illustrative computer model*.  It is not GPS data,
student data, a local observation, or a measurement from a real place.  The
schema keeps the source of the scientific concept separate from the provenance
of the scenario values so a future author cannot quietly present model values
as field data.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse


PROJECT_DIR = Path(__file__).resolve().parent.parent
SCENARIOS_DIR = PROJECT_DIR / "data" / "scenarios"

VERIFIED = "VERIFIED"
COMMUNITY_PROVIDED = "COMMUNITY_PROVIDED"
NEEDS_REVIEW = "NEEDS_REVIEW"
UNAVAILABLE = "UNAVAILABLE"
VERIFICATION_STATUSES = {
    VERIFIED,
    COMMUNITY_PROVIDED,
    NEEDS_REVIEW,
    UNAVAILABLE,
}
STUDENT_VISIBLE_STATUSES = {VERIFIED, NEEDS_REVIEW}

COMPUTER_MODEL = "COMPUTER_MODEL"
SCENARIO_TYPES = {COMPUTER_MODEL}

ILLUSTRATIVE_COMPUTER_MODEL = "ILLUSTRATIVE_COMPUTER_MODEL"
DATA_PROVENANCE_KINDS = {ILLUSTRATIVE_COMPUTER_MODEL}


class ScenarioFormatError(ValueError):
    """Raised when an editable scenario JSON record is unsafe or incomplete."""


def _required_text(value: Mapping[str, Any], field_name: str) -> str:
    """Read one required, non-empty text value with a useful author error."""
    if field_name not in value:
        raise ScenarioFormatError(f"Scenario is missing the required field: {field_name}")
    text = str(value[field_name]).strip()
    if not text:
        raise ScenarioFormatError(f"Scenario field '{field_name}' must not be empty.")
    return text


def _optional_text(value: Mapping[str, Any], field_name: str) -> str | None:
    """Read optional text, treating whitespace-only values as unavailable."""
    raw_value = value.get(field_name)
    if raw_value is None:
        return None
    text = str(raw_value).strip()
    return text or None


def _text_list(value: Mapping[str, Any], field_name: str) -> tuple[str, ...]:
    """Read a non-empty JSON string list without silently coercing bad data."""
    raw_values = value.get(field_name)
    if not isinstance(raw_values, list) or not raw_values:
        raise ScenarioFormatError(f"Scenario field '{field_name}' must be a non-empty list.")
    values = tuple(str(item).strip() for item in raw_values)
    if any(not item for item in values):
        raise ScenarioFormatError(
            f"Scenario field '{field_name}' must not contain empty values."
        )
    return values


def _normalize_identifier(identifier: str) -> str:
    """Normalize identifiers for case-insensitive repository lookup."""
    return identifier.strip().lower()


def _normalize_answer(answer: str) -> str:
    """Use transparent exact-answer matching after harmless punctuation cleanup."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", answer.lower())).strip()


@dataclass(frozen=True)
class SourceReference:
    """A source for the scientific concept, not the source of model values."""

    citation: str
    url: str | None = None
    usage_note: str | None = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "SourceReference":
        if not isinstance(value, Mapping):
            raise ScenarioFormatError("content_source must be a JSON object.")
        url = _optional_text(value, "url")
        if url is not None:
            parsed_url = urlparse(url)
            if parsed_url.scheme != "https" or not parsed_url.netloc:
                raise ScenarioFormatError("content_source.url must be an https URL when supplied.")
        return cls(
            citation=_required_text(value, "citation"),
            url=url,
            usage_note=_optional_text(value, "usage_note"),
        )


@dataclass(frozen=True)
class DataProvenance:
    """How scenario values were made, kept separate from a concept reference."""

    kind: str
    statement: str
    is_local_measurement: bool

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "DataProvenance":
        if not isinstance(value, Mapping):
            raise ScenarioFormatError("data_provenance must be a JSON object.")
        kind = _required_text(value, "kind")
        if kind not in DATA_PROVENANCE_KINDS:
            raise ScenarioFormatError(f"Unsupported data provenance kind: {kind}")
        if not isinstance(value.get("is_local_measurement"), bool):
            raise ScenarioFormatError("data_provenance.is_local_measurement must be true or false.")
        is_local_measurement = value["is_local_measurement"]
        if is_local_measurement:
            raise ScenarioFormatError(
                "This offline Problem Solver schema does not accept local measurements. "
                "Use illustrative computer-model values instead."
            )
        return cls(
            kind=kind,
            statement=_required_text(value, "statement"),
            is_local_measurement=is_local_measurement,
        )

    @property
    def student_notice(self) -> str:
        """Return an unambiguous label that is always safe to render."""
        return (
            "Illustrative computer-model values — not local measurements, GPS data, "
            "or student data. "
            f"{self.statement}"
        )


@dataclass(frozen=True)
class ScenarioStep:
    """One transparent calculation or comparison in a guided scenario."""

    identifier: str
    prompt: str
    accepted_answers: tuple[str, ...]
    success_feedback: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ScenarioStep":
        if not isinstance(value, Mapping):
            raise ScenarioFormatError("Each guided step must be a JSON object.")
        answers = _text_list(value, "accepted_answers")
        normalized_answers = tuple(_normalize_answer(answer) for answer in answers)
        if len(set(normalized_answers)) != len(normalized_answers):
            raise ScenarioFormatError("A guided step cannot repeat equivalent accepted answers.")
        return cls(
            identifier=_required_text(value, "id"),
            prompt=_required_text(value, "prompt"),
            accepted_answers=answers,
            success_feedback=_required_text(value, "success_feedback"),
        )


@dataclass(frozen=True)
class GoDeeperActivity:
    """An authored research-style extension with supplied model data."""

    research_question: str
    hypothesis_prompt: str
    data_label: str
    data_columns: tuple[str, ...]
    data_rows: tuple[tuple[str, ...], ...]
    analysis_prompt: str
    proposed_solution_prompt: str
    reflection_prompt: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "GoDeeperActivity":
        if not isinstance(value, Mapping):
            raise ScenarioFormatError("go_deeper must be a JSON object.")
        columns = _text_list(value, "data_columns")
        raw_rows = value.get("data_rows")
        if not isinstance(raw_rows, list) or not raw_rows:
            raise ScenarioFormatError("go_deeper.data_rows must be a non-empty list.")
        rows: list[tuple[str, ...]] = []
        for row_number, raw_row in enumerate(raw_rows, start=1):
            if not isinstance(raw_row, list) or len(raw_row) != len(columns):
                raise ScenarioFormatError(
                    "go_deeper.data_rows row "
                    f"{row_number} must contain exactly {len(columns)} values."
                )
            row = tuple(str(cell).strip() for cell in raw_row)
            if any(not cell for cell in row):
                raise ScenarioFormatError(
                    f"go_deeper.data_rows row {row_number} must not contain empty values."
                )
            rows.append(row)

        return cls(
            research_question=_required_text(value, "research_question"),
            hypothesis_prompt=_required_text(value, "hypothesis_prompt"),
            data_label=_required_text(value, "data_label"),
            data_columns=columns,
            data_rows=tuple(rows),
            analysis_prompt=_required_text(value, "analysis_prompt"),
            proposed_solution_prompt=_required_text(value, "proposed_solution_prompt"),
            reflection_prompt=_required_text(value, "reflection_prompt"),
        )

    def data_as_text(self) -> str:
        """Render compact plain text that works in a terminal or a GUI card."""
        header = " | ".join(self.data_columns)
        divider = " | ".join("---" for _ in self.data_columns)
        rows = (" | ".join(row) for row in self.data_rows)
        return "\n".join((self.data_label, header, divider, *rows))


@dataclass(frozen=True)
class ProblemScenario:
    """One source-attributed, reviewable, offline learning scenario."""

    identifier: str
    title: str
    subject: str
    topic: str
    scenario_type: str
    verification_status: str
    content_source: SourceReference
    data_provenance: DataProvenance
    introduction: str
    problem: str
    guided_steps: tuple[ScenarioStep, ...]
    progressive_hints: tuple[str, ...]
    worked_solution: str
    go_deeper: GoDeeperActivity

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ProblemScenario":
        if not isinstance(value, Mapping):
            raise ScenarioFormatError("Each scenario must be a JSON object.")

        scenario_type = _required_text(value, "scenario_type")
        if scenario_type not in SCENARIO_TYPES:
            raise ScenarioFormatError(f"Unsupported scenario type: {scenario_type}")
        verification_status = _required_text(value, "verification_status")
        if verification_status not in VERIFICATION_STATUSES:
            raise ScenarioFormatError(
                f"Unsupported scenario verification status: {verification_status}"
            )

        raw_steps = value.get("guided_steps")
        if not isinstance(raw_steps, list) or not raw_steps:
            raise ScenarioFormatError("guided_steps must be a non-empty list.")
        steps = tuple(ScenarioStep.from_mapping(step) for step in raw_steps)
        normalized_step_ids = tuple(_normalize_identifier(step.identifier) for step in steps)
        if any(not identifier for identifier in normalized_step_ids):
            raise ScenarioFormatError("guided step identifiers must not be empty.")
        if len(set(normalized_step_ids)) != len(normalized_step_ids):
            raise ScenarioFormatError("guided step identifiers must be unique.")

        content_source = SourceReference.from_mapping(value.get("content_source", {}))
        data_provenance = DataProvenance.from_mapping(value.get("data_provenance", {}))
        if scenario_type == COMPUTER_MODEL and data_provenance.kind != ILLUSTRATIVE_COMPUTER_MODEL:
            raise ScenarioFormatError(
                "A COMPUTER_MODEL scenario needs ILLUSTRATIVE_COMPUTER_MODEL provenance."
            )

        return cls(
            identifier=_required_text(value, "id"),
            title=_required_text(value, "title"),
            subject=_required_text(value, "subject"),
            topic=_required_text(value, "topic").lower(),
            scenario_type=scenario_type,
            verification_status=verification_status,
            content_source=content_source,
            data_provenance=data_provenance,
            introduction=_required_text(value, "introduction"),
            problem=_required_text(value, "problem"),
            guided_steps=steps,
            progressive_hints=_text_list(value, "progressive_hints"),
            worked_solution=_required_text(value, "worked_solution"),
            go_deeper=GoDeeperActivity.from_mapping(value.get("go_deeper", {})),
        )

    @property
    def content_status_notice(self) -> str:
        """Show a review state instead of pretending a draft is final content."""
        if self.verification_status == VERIFIED:
            return "Content status: verified."
        if self.verification_status == NEEDS_REVIEW:
            return (
                "Content status: needs review. This authored learning activity should be "
                "reviewed by a teacher before classroom use."
            )
        if self.verification_status == COMMUNITY_PROVIDED:
            return (
                "Content status: community-provided and unavailable to students until "
                "academic and source review is complete."
            )
        return "Content status: unavailable."

    @property
    def is_student_available(self) -> bool:
        """Allow only reviewed or clearly labelled draft computer models to render."""
        return self.verification_status in STUDENT_VISIBLE_STATUSES


@dataclass(frozen=True)
class ScenarioSection:
    """A simple labelled section that any UI can render without a framework."""

    title: str
    body: str


def render_problem_solver(scenario: ProblemScenario) -> tuple[ScenarioSection, ...]:
    """Render the solve phase with safety labels before the model values."""
    steps = tuple(
        ScenarioSection(f"STEP {index}: {step.identifier.replace('-', ' ').title()}", step.prompt)
        for index, step in enumerate(scenario.guided_steps, start=1)
    )
    return (
        ScenarioSection("CONTENT STATUS", scenario.content_status_notice),
        ScenarioSection("MODEL DATA", scenario.data_provenance.student_notice),
        ScenarioSection("SCENARIO", scenario.introduction),
        ScenarioSection("PROBLEM", scenario.problem),
        *steps,
    )


def render_go_deeper(scenario: ProblemScenario) -> tuple[ScenarioSection, ...]:
    """Render a research-style path using only authored, labelled model data."""
    activity = scenario.go_deeper
    return (
        ScenarioSection("GO DEEPER: RESEARCH QUESTION", activity.research_question),
        ScenarioSection("HYPOTHESIS", activity.hypothesis_prompt),
        ScenarioSection(
            "DATA / OBSERVATION",
            f"{scenario.data_provenance.student_notice}\n\n{activity.data_as_text()}",
        ),
        ScenarioSection("ANALYSIS", activity.analysis_prompt),
        ScenarioSection("PROPOSE A SOLUTION", activity.proposed_solution_prompt),
        ScenarioSection("REFLECT", activity.reflection_prompt),
    )


@dataclass(frozen=True)
class ScenarioAttemptFeedback:
    """Result of one exact, authored-step attempt; it does not infer reasoning."""

    correct: bool | None
    message: str
    is_complete: bool


@dataclass(frozen=True)
class ScenarioSolution:
    """A gated solution response, so a UI need not duplicate reveal rules."""

    available: bool
    text: str


class ProblemScenarioSession:
    """Keep problem attempts, hints, and solution reveal in local memory only.

    The session deliberately stores aggregate counts, not the student's typed
    answer text.  Answer checking is transparent, normalized exact matching;
    it is not an AI claim that the student's reasoning was understood.
    """

    def __init__(self, scenario: ProblemScenario) -> None:
        self.scenario = scenario
        self.current_step_index = 0
        self.attempts = 0
        self.hint_requests = 0

    @property
    def current_step(self) -> ScenarioStep | None:
        """Return the one active guided step, or None once every step is complete."""
        if self.current_step_index >= len(self.scenario.guided_steps):
            return None
        return self.scenario.guided_steps[self.current_step_index]

    @property
    def is_complete(self) -> bool:
        """Whether the learner has completed all authored guided steps."""
        return self.current_step is None

    def current_step_section(self) -> ScenarioSection | None:
        """Provide a UI-ready current-step prompt without exposing the solution."""
        step = self.current_step
        if step is None:
            return None
        return ScenarioSection(
            f"STEP {self.current_step_index + 1} OF {len(self.scenario.guided_steps)}",
            step.prompt,
        )

    def submit_attempt(self, answer: str) -> ScenarioAttemptFeedback:
        """Check one authored answer and guide retry without storing raw input."""
        step = self.current_step
        if step is None:
            return ScenarioAttemptFeedback(
                correct=None,
                message="You have completed the guided steps. Choose Go Deeper to investigate further.",
                is_complete=True,
            )

        normalized_answer = _normalize_answer(answer)
        if not normalized_answer:
            return ScenarioAttemptFeedback(
                correct=None,
                message="Write an attempt before submitting it.",
                is_complete=False,
            )

        self.attempts += 1
        accepted = {_normalize_answer(expected) for expected in step.accepted_answers}
        if normalized_answer in accepted:
            self.current_step_index += 1
            if self.is_complete:
                return ScenarioAttemptFeedback(
                    correct=True,
                    message=f"{step.success_feedback} You completed the model comparison.",
                    is_complete=True,
                )
            return ScenarioAttemptFeedback(
                correct=True,
                message=f"{step.success_feedback} Continue to the next step.",
                is_complete=False,
            )

        return ScenarioAttemptFeedback(
            correct=False,
            message="Not yet. Use a hint, check the quantities and units, then try again.",
            is_complete=False,
        )

    def hint(self) -> str:
        """Return progressively more explicit authored support, never the solution."""
        if self.is_complete:
            return "The guided steps are complete. Choose Go Deeper to investigate the model data."
        hint_index = min(self.hint_requests, len(self.scenario.progressive_hints) - 1)
        self.hint_requests += 1
        return self.scenario.progressive_hints[hint_index]

    def can_reveal_solution(self) -> bool:
        """Allow a solution after a genuine attempt or two intentionally requested hints."""
        return self.attempts > 0 or self.hint_requests >= 2

    def reveal_solution(self) -> ScenarioSolution:
        """Respect the same try/hint-before-solution learning rule as the main tutor."""
        if not self.can_reveal_solution():
            return ScenarioSolution(
                available=False,
                text=(
                    "Try one answer first, or request two hints, before opening the worked solution."
                ),
            )
        return ScenarioSolution(available=True, text=self.scenario.worked_solution)


class ProblemScenarioRepository:
    """Read-only lookup for locally authored scenarios; it makes no network calls."""

    def __init__(self, scenarios: Iterable[ProblemScenario] = ()) -> None:
        self._scenarios: dict[str, ProblemScenario] = {}
        for scenario in scenarios:
            normalized_identifier = _normalize_identifier(scenario.identifier)
            if not normalized_identifier:
                raise ScenarioFormatError("Scenario identifier must not be empty.")
            if normalized_identifier in self._scenarios:
                raise ScenarioFormatError(f"Duplicate scenario id: {scenario.identifier}")
            self._scenarios[normalized_identifier] = scenario

    @classmethod
    def from_directory(cls, scenarios_dir: Path = SCENARIOS_DIR) -> "ProblemScenarioRepository":
        """Load local JSON files only; a missing folder is a valid empty library."""
        return cls(load_problem_scenarios(scenarios_dir))

    def all(self) -> tuple[ProblemScenario, ...]:
        """Return records in their deterministic load order."""
        return tuple(self._scenarios.values())

    def get(self, identifier: str | None) -> ProblemScenario | None:
        """Find a scenario by identifier without broad keyword matching."""
        if identifier is None:
            return None
        return self._scenarios.get(_normalize_identifier(identifier))

    def for_topic(
        self,
        topic: str | None,
        subject: str | None = None,
    ) -> tuple[ProblemScenario, ...]:
        """Return student-safe records scoped to an exact topic and optional subject."""
        normalized_topic = _normalize_identifier(topic or "")
        if not normalized_topic:
            return ()
        normalized_subject = _normalize_identifier(subject or "")
        return tuple(
            scenario
            for scenario in self._scenarios.values()
            if scenario.is_student_available
            and scenario.topic == normalized_topic
            and (
                not normalized_subject
                or _normalize_identifier(scenario.subject) == normalized_subject
            )
        )


def load_problem_scenarios(
    scenarios_dir: Path = SCENARIOS_DIR,
) -> tuple[ProblemScenario, ...]:
    """Load JSON scenario records from disk without any location or network access.

    A JSON file can contain one object or a list of objects.  Parsing failures
    name the file so a student author can fix the correct record.
    """
    if not scenarios_dir.exists():
        return ()

    scenarios: list[ProblemScenario] = []
    for scenario_path in sorted(scenarios_dir.rglob("*.json")):
        try:
            raw_scenarios = json.loads(scenario_path.read_text(encoding="utf-8"))
        except OSError as error:
            raise ScenarioFormatError(f"Could not read scenario {scenario_path}: {error}") from error
        except json.JSONDecodeError as error:
            raise ScenarioFormatError(
                f"Invalid JSON in {scenario_path}: {error.msg}"
            ) from error

        records = raw_scenarios if isinstance(raw_scenarios, list) else [raw_scenarios]
        for raw_scenario in records:
            try:
                scenarios.append(ProblemScenario.from_mapping(raw_scenario))
            except ScenarioFormatError as error:
                raise ScenarioFormatError(f"Invalid scenario {scenario_path}: {error}") from error

    return tuple(scenarios)
