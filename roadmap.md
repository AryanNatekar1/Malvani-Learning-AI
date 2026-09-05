# Roadmap

## Completed V2 foundation

- Preserve and test the terminal knowledge-file prototype.
- Add structured local lessons without deleting V1 data.
- Build a teaching, quiz, guided-problem, progress, language, culture-safety,
  media, voice-boundary, and AI-provider architecture.
- Build a working Tkinter desktop interface.
- Add a small local neural intent classifier for UI routing only.
- Add a local SQLite persistence boundary, aggregate learning events, a lesson
  library, and a source-gated legacy-content renderer.
- Add a learn → think → try → hint → retry → solution flow with transparent,
  deterministic feedback and retry/reveal quiz rules.
- Add a polished shared desktop shell, responsive navigation, question-and-
  answer trail, study-oriented cards, and honest local progress metrics.
- Add deterministic lesson-bound follow-up questions for stored explanations,
  formulas, examples, uses, misconceptions, careers, and next steps.
- Add one interactive Momentum visual lab with learner-controlled mass and
  velocity, a prediction-before-reveal comparison, an accessible text
  alternative, and no decorative animation loop or stored learner choice.
- Add explainable recommendations from real quiz-attempt evidence and installed
  author-linked next lessons; do not imply mastery or predict ability.
- Harden local profile loading/saving so malformed or unavailable local storage
  preserves the live session and produces a student-friendly notice.
- Add a topic-scoped, manual Contextual Learning Engine boundary. It accepts
  only source-backed `VERIFIED` records, keeps the selection session-only, and
  never accesses or stores device location.
- Add the first separate **Problem Solver → Go Deeper** vertical slice for
  Momentum. It uses source-attributed concept content and explicitly labelled
  illustrative computer-model values, preserving the normal challenge and quiz
  sessions. It has guided model steps, progressive hints, a solution gate, and
  non-semantic research prompts while storing aggregate progress only.
- Make guided desktop actions usable on compact screens: opening Problem Solver
  or Go Deeper scrolls the next input into view and gives it keyboard focus.
- Give Go Deeper's hypothesis, analysis, proposed-test, and reflection prompts
  multi-line local writing areas, while retaining the no-free-text-storage and
  no-semantic-grading boundaries.
- Guide the first Go Deeper activity through a transparent beginner sequence
  (hypothesis, analysis, fair next test, reflection), with later stages locked
  until the preceding local check-in is recorded. Add an explicitly
  schema-scoped numeric/unit matcher for the two authored momentum calculation
  steps; do not broaden it into a free-text grader.
- Make normal keyboard focus reveal an off-screen page control in the existing
  viewport, while allowing multi-line writing fields to keep native scrolling.
- Place research check-in feedback beside the relevant writing field and keep
  it visible on compact screens, rather than putting a validation message at
  the bottom of the whole research form.
- Add a scenario-bound, prediction-first Momentum cart visual. It consumes a
  typed `visual_model` from reviewed scenario JSON, unlocks only after its
  authored calculation placement, provides a text alternative, and keeps its
  local prediction outside progress storage.
- Add a second Problem Solver → Go Deeper scenario, Force (Newton's second
  law), reusing the existing `COMPUTER_MODEL` schema unchanged with its own
  verified OpenStax citation and illustrative values. This exercised the
  schema and controller wiring beyond a single installed scenario without
  broadening the engine itself.

## Next: content quality and community review

1. Review each starter lesson with a subject teacher and mark published content
   only after review.
2. Add source-backed cultural-context entries with community/subject input.
3. Add reviewed Marathi interface and lesson content.
4. Add reviewed Malvani vocabulary and lesson content only with appropriate
   linguistic/community verification.
5. Migrate and enrich the remaining original Physics files.
6. Add more actual lessons before creating additional subject folders.
7. Create the first teacher-reviewed contextual learning record and a matching
   Waves lesson; begin with a manual generic setting before considering device
   location, maps, or sensors.
8. Review the Momentum and Force Problem Solver scenarios with a subject
   teacher, then continue adding one source-backed scenario at a time with
   separate concept sources and data provenance. Do not turn authored model
   values into local claims.

## Later product work

- Improve adaptive recommendations using meaningful learner feedback.
- Add teacher-reviewed short-answer rubrics before claiming that research or
  reasoning writing can be assessed semantically.
- Add more question types and teacher-reviewed rubrics for short answers.
- Add optional local or hosted LLM adapters behind `AIProvider`.
- Add more diagrams and accessible visual descriptions where they improve a
  concept, using the Momentum lab as the small local implementation pattern.
- Build one reusable, reduced-motion-aware Canvas animation at a time, starting
  with Gravity only after defining its learning objective and text alternative.
- Add optional, reviewed speech-recognition and text-to-speech adapters.
- Build a lightweight web/mobile-friendly interface.
- Conduct opt-in student testing with minimal, anonymized data collection.

## Research questions

- Do culturally relevant, verified examples improve conceptual understanding?
- Do Marathi/Malvani explanations improve accessibility when linguistically
  reviewed?
- Does guided problem solving improve independent reasoning?
- Which lesson formats and visual aids help most on low-bandwidth devices?
