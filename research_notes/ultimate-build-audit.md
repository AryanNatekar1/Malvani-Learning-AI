# Ultimate Build Audit — 2026-08-12

This is a factual audit of the local V2.1 baseline before the V2.2 stability
increment. It records what the project can demonstrate today and what remains
future work.

## Current architecture

```text
Tkinter desktop UI
    → AppController (local learning orchestration)
    → knowledge / teaching / related-question / reasoning / quiz / problem engines
    → structured JSON lessons + preserved V1 text files
    → local SQLite profile and aggregate events

Optional intent boundary
    → small local neural intent classifier
    → future AIProvider implementations
```

The GUI does not hold lesson logic. `AppController` coordinates teaching,
state, persistence, and the safe offline fallback. The original terminal
chatbot and flat Physics files are preserved.

## Verified working capabilities

- Eight structured starter lessons across Physics, Mathematics, Chemistry,
  Biology, and Computer Science; each has authored teaching material, a
  challenge, a reasoning guide, and one local quiz question.
- Lesson flow: concept → everyday example → think question → challenge →
  progressive hints → retry → gated solution.
- Local quiz retry/reveal policy, local progress, and SQLite event storage
  without storing free-text learner answers.
- Data-bound related questions for explanation, formula, example, use,
  misconception, career, and next step.
- English content with honest Marathi/Malvani lesson fallback. No unreviewed
  language content is represented as translated.
- Cultural-context gate: only source-backed `VERIFIED` context can be shown.
- Responsive Tkinter desktop UI with a compact navigation mode, page scrolling
  at 800×600, and tested in-progress quiz resume behavior.
- An offline interactive Momentum lab: learner-controlled mass and velocity
  update a directional cart diagram, formula result, and text alternative.

## AI and neural reality

`neural_intent.py` implements a deterministic, one-hidden-layer
bag-of-words classifier for five interface intents: lesson, hint, challenge,
solution, and quiz. It is not an LLM, does not generate factual content, and
is guarded by explicit cue phrases in the offline provider.

The factual source is local lesson data. `AIProvider` is an extension boundary
for a future deliberately configured provider; no external provider or API key
is present.

## Important limitations

- Structured content is English-only and marked `NEEDS_REVIEW`.
- No verified Sindhudurg/Konkan cultural records, reviewed Marathi lessons, or
  Malvani lesson content are installed.
- Topic recognition is English keyword/alias matching, not semantic search or
  unrestricted conversation.
- Reasoning feedback is transparent authored-cue feedback, not semantic
  grading of a student's explanation.
- Progress recommendations are currently small, local, and aggregate-based.
- There is no speech provider, external AI provider, web application, package,
  or real-student evaluation result to claim.

## Priority order after V2.2

1. Teacher-reviewable source and curriculum records; migrate the remaining
   legacy Physics lessons into structured data.
2. Add visuals only when they improve understanding; the Momentum lab is the
   first reusable local implementation pattern.
3. Expand local progress into evidence-based, explainable recommendations.
4. Build an evaluation dataset for content, pedagogy, language fallback, and
   cultural safety before adding an external language model.
5. Add packaging and CI only after the desktop learning workflow is stable.

No experiment results, cultural facts, translations, or external-AI behavior
are inferred by this audit.
