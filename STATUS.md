# Malvani Learning AI — Status

Current Version: **V2.3 local learning application prototype**

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
- Small offline neural intent classifier and provider-neutral AI interface.
- Built-in concept diagrams for selected Physics lessons and an interactive,
  local Momentum explorer with mass/velocity controls, a directional diagram,
  and a text alternative.
- Data-bound related-question tutor flow for why/how, formula, example, uses,
  misconceptions, careers, and next steps; missing stored data is named
  instead of invented.
- Explainable next-step recommendations based on local quiz attempts and
  author-linked installed lessons. The displayed reason states the evidence.
- Explicit “teach/explain topic” questions open the complete guided teaching
  flow; focused follow-ups remain focused on the active lesson.
- In-progress quizzes resume when a learner navigates away and returns.
- Student-facing local-context notices use clear availability language without
  exposing draft or verification implementation details.
- 73 automated tests, including GUI flow, compact-layout reachability,
  question-trail, state-reset, and resize smoke tests.

## Not yet claimed as complete

- Reviewed Marathi or Malvani educational lesson content.
- Verified Sindhudurg/Konkan cultural data records.
- A configured external LLM or local language model.
- Voice input/output.
- Web/mobile interface, cloud sync, or real-student evaluation.

Status: **Working locally; ready for content review and iterative testing.**
