# Malvani Learning AI — Status

Current Version: **V2.12 local learning application prototype**

## Working now

- Tkinter GUI: Home, Learning, Quiz, Progress, Library, and Settings.
- Polished desktop shell with consistent navigation, responsive compact mode,
  study-oriented cards, quiz progress, local progress metrics, and scrollable
  page views that keep controls reachable at 800×600.
- Preserved terminal chatbot and original file-based Physics knowledge.
- Structured **draft** lessons across Physics, Mathematics, Chemistry, Biology,
  and Computer Science.
- Guided teaching actions: simple explanation, example, hint, challenge,
  solution, thinking question, and next-step exploration.
- Offline quizzes with retry/reveal rules, progressive hints, and local SQLite
  progress/event tracking.
- Safe local persistence fallback: malformed/unavailable profile storage does
  not stop learning; the app shows an honest storage notice instead.
- English lesson content with honest Marathi/Malvani fallback behavior.
- Safety gate for cultural content: only source-backed `VERIFIED` entries may
  appear in student output.
- Privacy-safe Contextual Learning Engine foundation: a student can select a
  reviewed manual context when one is installed; it is topic-scoped,
  session-only, and never GPS/location data. No reviewed context records are
  installed yet, so the normal lesson path remains the default.
- Small offline neural intent classifier and provider-neutral AI interface.
- Built-in concept diagrams for selected Physics lessons and an interactive,
  local Momentum explorer with mass/velocity controls, a prediction-before-
  reveal comparison, a directional diagram, and a text alternative. It has no
  looping animation and does not store or claim to assess a learner's choice.
- Data-bound related-question tutor flow for why/how, formula, example, uses,
  misconceptions, careers, and next steps; missing stored data is named
  instead of invented.
- Explainable next-step recommendations based on local quiz attempts and
  author-linked installed lessons. The displayed reason states the evidence.
- Explicit “teach/explain topic” questions open the complete guided teaching
  flow; focused follow-ups remain focused on the active lesson.
- In-progress quizzes resume when a learner navigates away and returns.
- Momentum now has a separate, sourced **Problem Solver → Go Deeper** flow:
  three transparent computer-model steps, progressive hints, a gated worked
  solution, and labelled research-question, hypothesis, data, analysis,
  proposed-next-test, and reflection prompts. It uses illustrative supplied
  values only—never GPS, local measurements, or student data—and never stores
  a learner's typed model answer or research writing.
- Problem Solver sessions do not replace the existing lesson challenge or quiz
  session. Reopening or changing a lesson clears stale activity controls.
- Opening Problem Solver or Go Deeper on a compact screen scrolls its next
  answer field into view and gives it keyboard focus, so the learner can act
  immediately instead of searching below the fold.
- Go Deeper now gives each hypothesis, analysis, proposed-test, and reflection
  prompt a multi-line writing area. The text is available only while that
  screen is open; recording a writing check-in saves only an aggregate count.
- The Momentum investigation now guides beginner writing in order—hypothesis,
  analysis, fair next test, then reflection—without claiming that writing is
  correct or that all real investigations must be linear. Later stages remain
  visibly locked until the preceding check-in is recorded.
- Its two calculation steps use an author-declared numeric/unit rule, so safe
  forms such as `6.0`, `p = 6 kg m/s`, and `6 kg*m/s` work while wrong values,
  wrong units, and arbitrary prose stay unsupported.
- Keyboard users are now brought to the focused page control on compact
  screens, including Home's Start Learning action. Multiline research fields
  retain their own mouse-wheel scrolling for longer on-screen writing.
- Research check-in feedback now appears beneath the exact writing field that
  produced it. A compact-screen validation reminder remains visible while its
  editable field stays focused for a retry.
- Momentum's Problem Solver now has a separate, scenario-bound visual model.
  It uses typed, validated JSON cart inputs (never values extracted from
  prose), appears only after the linked calculation step or a deliberate
  worked-solution review, and asks for a local prediction before revealing its
  model comparison. It is non-modal, has a text alternative, keeps the
  supplied-value/draft notices visible, and never stores a visual choice or
  changes progress. Its compact popup body scrolls, including for keyboard
  focus, so the full text alternative and controls remain reachable.
- Student-facing local-context notices use clear availability language without
  exposing draft or verification implementation details.
- 116 automated tests, including GUI flow, compact-layout reachability,
  question-trail, state-reset, privacy-boundary, and resize smoke tests.

## Not yet claimed as complete

- Reviewed Marathi or Malvani educational lesson content.
- Verified Sindhudurg/Konkan cultural data records.
- Reviewed manual learning-context records, device location, map data, or
  sensor data.
- Reviewed Problem Solver scenario content beyond the first `NEEDS_REVIEW`
  Momentum computer model, real-world observation workflows, or semantic
  free-text scientific assessment.
- A configured external LLM or local language model.
- Voice input/output.
- Web/mobile interface, cloud sync, or real-student evaluation.

Status: **Working locally; ready for content review and iterative testing.**
