"""Local-only student preferences and progress tracking."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Protocol


PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_PROFILE_PATH = PROJECT_DIR / "local_data" / "student_profile.json"
DEFAULT_DATABASE_PATH = PROJECT_DIR / "local_data" / "malvani_learning.db"


@dataclass
class StudentProfile:
    """Minimal, optional profile data stored only on the student's computer."""

    name: str = ""
    class_level: str = "Class 8"
    preferred_language: str = "English"
    preferred_subject: str = "Physics"
    culture_mode: bool = True
    topics_studied: list[str] = field(default_factory=list)
    questions_attempted: int = 0
    questions_correct: int = 0
    topic_attempts: dict[str, int] = field(default_factory=dict)
    topic_correct: dict[str, int] = field(default_factory=dict)
    hints_used: int = 0
    reasoning_attempts: int = 0
    challenge_attempts: int = 0
    challenge_correct: int = 0
    topic_hints: dict[str, int] = field(default_factory=dict)
    topic_reasoning_attempts: dict[str, int] = field(default_factory=dict)

    def record_lesson(self, topic: str) -> None:
        """Record a lesson once, avoiding duplicate topic entries."""
        if topic not in self.topics_studied:
            self.topics_studied.append(topic)

    def record_question(self, topic: str, correct: bool) -> None:
        """Store aggregate performance without collecting answer text."""
        self.questions_attempted += 1
        self.topic_attempts[topic] = self.topic_attempts.get(topic, 0) + 1
        if correct:
            self.questions_correct += 1
            self.topic_correct[topic] = self.topic_correct.get(topic, 0) + 1

    def record_hint(self, topic: str) -> None:
        """Record an actual hint request for later learner reflection."""
        self.hints_used += 1
        self.topic_hints[topic] = self.topic_hints.get(topic, 0) + 1

    def record_reasoning_attempt(self, topic: str) -> None:
        """Record that a learner submitted reasoning, without storing its text."""
        self.reasoning_attempts += 1
        self.topic_reasoning_attempts[topic] = (
            self.topic_reasoning_attempts.get(topic, 0) + 1
        )

    def record_challenge_attempt(self, correct: bool | None) -> None:
        """Record a challenge attempt only when the learner actually submits one."""
        self.challenge_attempts += 1
        if correct:
            self.challenge_correct += 1

    @property
    def accuracy(self) -> float:
        """Return overall quiz accuracy as a percentage."""
        if not self.questions_attempted:
            return 0.0
        return (self.questions_correct / self.questions_attempted) * 100

    def weak_topics(self) -> list[str]:
        """Return topics with at least one answer and below 60% accuracy."""
        weak: list[str] = []
        for topic, attempts in self.topic_attempts.items():
            correct = self.topic_correct.get(topic, 0)
            if attempts and correct / attempts < 0.6:
                weak.append(topic)
        return sorted(weak)


class ProfileStore:
    """Read and write one local JSON profile. No network or database is used."""

    def __init__(self, profile_path: Path = DEFAULT_PROFILE_PATH) -> None:
        self.profile_path = profile_path

    def load(self) -> StudentProfile:
        """Return saved settings, or a safe default when no profile exists."""
        if not self.profile_path.exists():
            return StudentProfile()
        try:
            data = json.loads(self.profile_path.read_text(encoding="utf-8"))
        except (OSError, TypeError, json.JSONDecodeError):
            return StudentProfile()
        return StudentProfile(**data)

    def save(self, profile: StudentProfile) -> None:
        """Save profile data locally, creating the ignored data folder as needed."""
        self.profile_path.parent.mkdir(parents=True, exist_ok=True)
        self.profile_path.write_text(
            json.dumps(asdict(profile), ensure_ascii=False, indent=2), encoding="utf-8"
        )


class StudentRepository(Protocol):
    """Local persistence boundary that a future server-backed repository can match."""

    def load(self) -> StudentProfile:
        """Load the current student's local profile."""

    def save(self, profile: StudentProfile) -> None:
        """Persist aggregate student data."""

    def record_event(
        self, event_type: str, topic: str | None = None, correct: bool | None = None
    ) -> None:
        """Persist a real learning event without saving free-text student answers."""


class SQLiteProfileStore:
    """SQLite-backed local profile store for desktop use and future API migration.

    The database contains one optional local profile and aggregate event rows.
    It intentionally never stores a learner's raw reasoning or quiz answer text.
    """

    def __init__(self, database_path: Path = DEFAULT_DATABASE_PATH) -> None:
        self.database_path = database_path
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self.database_path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA user_version = 1")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS student_profile (
                    profile_id INTEGER PRIMARY KEY CHECK (profile_id = 1),
                    profile_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS learning_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    topic TEXT,
                    correct INTEGER,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def load(self) -> StudentProfile:
        """Load saved profile data, or return a privacy-preserving default."""
        try:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT profile_json FROM student_profile WHERE profile_id = 1"
                ).fetchone()
        except sqlite3.DatabaseError:
            return StudentProfile()
        if row is None:
            return StudentProfile()
        try:
            return StudentProfile(**json.loads(row[0]))
        except (TypeError, json.JSONDecodeError):
            return StudentProfile()

    def save(self, profile: StudentProfile) -> None:
        """Store the current aggregate profile in a single SQLite row."""
        profile_json = json.dumps(asdict(profile), ensure_ascii=False, sort_keys=True)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO student_profile (profile_id, profile_json, updated_at)
                VALUES (1, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(profile_id) DO UPDATE SET
                    profile_json = excluded.profile_json,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (profile_json,),
            )

    def record_event(
        self, event_type: str, topic: str | None = None, correct: bool | None = None
    ) -> None:
        """Store a real aggregate event, never the learner's free-text response."""
        stored_correct = None if correct is None else int(correct)
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO learning_events (event_type, topic, correct) VALUES (?, ?, ?)",
                (event_type, topic, stored_correct),
            )

    def event_count(self, event_type: str | None = None) -> int:
        """Return persisted event count; used for local diagnostics and tests."""
        with self._connect() as connection:
            if event_type is None:
                row = connection.execute("SELECT COUNT(*) FROM learning_events").fetchone()
            else:
                row = connection.execute(
                    "SELECT COUNT(*) FROM learning_events WHERE event_type = ?",
                    (event_type,),
                ).fetchone()
        return int(row[0])
