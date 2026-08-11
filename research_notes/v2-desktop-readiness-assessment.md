# V2 desktop readiness assessment

Date: 2026-08-11

## Baseline inspected

Before the desktop-readiness improvements, the repository contained a working
Tkinter desktop app, a terminal fallback, structured JSON lesson drafts,
teaching/quiz/profile engines, an offline provider boundary, and 27 passing
tests. The original flat Physics text files were retained for compatibility.

## Current architecture

```text
Tkinter desktop UI
  -> AppController (GUI-independent application service)
    -> Knowledge / Teaching / Reasoning / Problem / Quiz engines
    -> Student repository (SQLite locally, JSON compatibility adapter)
    -> AIProvider (offline intent routing by default)
```

This keeps core learning behavior independent of Tkinter. A future FastAPI
service can call the controller/engines and use a server repository without
rewriting lesson, quiz, teaching, or safety logic.

## What is genuinely implemented

- Local lesson lookup and structured lesson validation.
- Level-aware simple/detailed explanation selection.
- Lesson cards, Library, diagrams, Home dashboard, Quiz, Progress, and
  Settings in a native desktop UI.
- Guided challenge attempts, progressive hints, solution gating, and a quiz
  retry/reveal policy.
- Deterministic key-idea feedback for reasoning attempts.
- Local SQLite aggregate progress/events; raw student answers are not stored.
- English lesson delivery with honest Marathi/Malvani fallback.
- Source-gated structured cultural context and safe rendering of legacy files.
- A real small neural network for UI-intent routing only.

## Important non-claims

- The reasoning checker is not semantic AI grading. It only checks
  lesson-authored cues and says so in the UI.
- The neural model is not an LLM, tutor, cultural source, or translation model.
- Current structured lessons are marked `NEEDS_REVIEW`; they are not published
  curriculum content.
- There is no verified Malvani lesson content, verified cultural dataset,
  external AI provider, voice provider, cloud sync, or web/mobile client.

## Desktop technology decision

The project remains on Tkinter rather than migrating immediately to PySide6.
Tkinter is already available with Python, requires no download, and supports a
working local Windows prototype. The core system does not depend on Tkinter,
so a Qt or web client can be introduced later without replacing the learning
engines. A GUI migration should be justified by a concrete accessibility,
packaging, or design requirement—not by appearance alone.

## High-value next research/product work

1. Have teachers review starter lessons and record credible curriculum sources.
2. Build source-backed Sindhudurg/Konkan context records with local community
   review.
3. Add reviewed Marathi lesson text, then verified Malvani content.
4. Evaluate the teaching flow with opt-in student feedback and pre/post tasks.
5. Add a packaging workflow once the local desktop experience is stable.
