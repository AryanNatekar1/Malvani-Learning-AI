# V2.8 research writing decisions

## Goal

Go Deeper asks a student to form a hypothesis, analyse supplied data, propose
a fair next test, and reflect. These are scientific writing tasks, so a
single-line input made the interface work against the learning goal.

V2.8 replaces those one-line inputs with compact multi-line writing areas.
They are intentionally plain local text fields: a student can write a few
connected sentences without the app pretending to evaluate them.

## Privacy and assessment boundary

The writing exists only inside the visible Tkinter field for the current app
session. When the learner records a writing check-in, `AppController` receives
the text only long enough to reject an empty submission. It records an
aggregate completion counter and a fixed event name. The completed text stays
visible only in its disabled on-screen field until the learner changes or
clears the lesson. No hypothesis, analysis, proposed test, or reflection is
written to the JSON or SQLite progress stores.

The app does not use the text to score scientific quality. A completed prompt
means only that the learner chose to mark it complete. Stronger feedback would
need teacher-reviewed rubrics and evaluation with real student work.

## Interaction decision

After a prompt's writing check-in is recorded its field is disabled for the rest
of that session. This prevents accidental duplicate completion events and
shows the learner which step they have finished. The next unfinished field is
scrolled into view and receives keyboard focus, including on the supported
800x600 compact window.

## What this does not add

This change does not add an LLM, a semantic grader, cloud storage, GPS,
location collection, cultural claims, or new scenario data. It improves the
existing authored Momentum computer-model activity while preserving its
`NEEDS_REVIEW` content status and local-only data boundary.
