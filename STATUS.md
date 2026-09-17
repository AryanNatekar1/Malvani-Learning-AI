# Malvani Learning AI — Status

Current Version: **V3.0 local desktop app + deployable web app**

## Working now

- Tkinter GUI: Home, Learning, Quiz, Progress, Library, and Settings.
- Polished desktop shell with consistent navigation, responsive compact mode,
  study-oriented cards, quiz progress, local progress metrics, and scrollable
  page views that keep controls reachable at 800×600.
- Preserved terminal chatbot and original file-based Physics knowledge.
- A browser web app (`index.html`) deployed to GitHub Pages, carrying every
  lesson, quiz, challenge and Problem Solver activity. It reads the same
  `data/` JSON the desktop app reads, so content has one source of truth, and
  it keeps the same safety rules about unverified context and draft status.
- The web app is installable and fully offline: a service worker precaches the
  page and every lesson file, so it opens with no connection after one visit.
- A concept diagram for all fifteen lessons, several of them interactive
  (work as an area, momentum as a bar, friction as opposing arrows, gravity as
  two balls falling level). Each has a written text alternative.
- Search across every lesson and problem with `Ctrl`+`K`, a phone bottom-nav,
  and a "continue where you left off" card.
- Structured **draft** lessons across Physics, Mathematics, Chemistry, Biology,
  and Computer Science — 15 in total. All ten original Physics topics are now
  structured lessons; their `.txt` originals are preserved, and Waves has been
  added as the first topic written directly for the structured schema.
- A "Look around you" observation on every lesson: something to go and watch
  happen, using only what a student already has. It never asserts what is near
  the learner, because the app cannot know that — it invites, and the learner
  supplies the place.
- Documented **places** in Sindhudurg and the Konkan, each explaining how it
  came to be that way and what it can teach: laterite and why the soil is red,
  the sea fort, Amboli and the rain shadow, why Konkan rivers run fast, Devgad,
  and the coast. Naming a real place is allowed here because it is public
  geography rather than a claim about an individual. Every record names its
  sources and lists what a local teacher still has to confirm.
- Guided teaching actions: simple explanation, example, hint, challenge,
  solution, thinking question, and next-step exploration.
- Offline quizzes with retry/reveal rules, progressive hints, and local SQLite
  progress/event tracking.
- Safe local persistence fallback: malformed/unavailable profile storage does
  not stop learning; the app shows an honest storage notice instead.
- Five declared languages: English, Marathi, Hindi, Konkani, Malvani, with a
  picker in the web app. Interface labels exist for the first three. Konkani
  and Malvani are deliberately blank rather than guessed at — Malvani is
  largely spoken and has no settled spelling — and fall back to English with an
  honest notice. `data/languages/` lets a speaker contribute reviewed labels as
  data, ignored until a named reviewer signs the file off.
- The same language gate now runs in both apps: a non-English lesson variant
  must be `VERIFIED` **and** name a source before a student sees it. A test
  compares the JavaScript gate against the Python one so the two cannot drift.
- Waves carries the first Marathi lesson draft. It is machine-assisted and
  unreviewed, so it stays hidden; it is in the repository for a Marathi speaker
  to correct, and becomes visible only when they set it `VERIFIED` and sign it.
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
- A second Problem Solver → Go Deeper scenario now covers Force (Newton's
  second law), reusing the same `COMPUTER_MODEL` schema as Momentum with its
  own OpenStax-sourced concept reference and illustrative block/force values.
  It has no scenario visual yet — the current visual kind is Momentum-only —
  and confirms the schema and controller wiring work for more than one
  authored scenario.
- A new structured **Motion** lesson (migrated from the original `motion.txt`)
  pairs with a third Problem Solver scenario, "A Real Journey: Carrying
  Water" — a relatable, real-life-framed distance/speed/time activity about
  walking to collect water, instead of an abstract textbook cart or block. It
  is explicit that its 300 m/1.2 m/s values are an illustrative computer
  model, not a measurement of any real household, family, or place, and its
  Go Deeper stage lets a learner investigate how a slower, load-carrying
  return speed would change the total round-trip time.
- 156 automated tests, including GUI flow, compact-layout reachability,
  question-trail, state-reset, privacy-boundary, and resize smoke tests, plus
  checks that observations name no place and that every place cites a source.

## Not yet claimed as complete

- Reviewed Marathi or Malvani educational lesson content.
- Verified Sindhudurg/Konkan cultural data records.
- Reviewed manual learning-context records, device location, map data, or
  sensor data.
- Reviewed Problem Solver scenario content: the Momentum, Force, and Motion
  computer models are all still `NEEDS_REVIEW`, and there are no real-world
  observation workflows or semantic free-text scientific assessment yet.
- A configured external LLM or local language model.
- Voice input/output.
- Cloud sync, or real-student evaluation. The browser app is live and works
  on phones, but no student has used it in a classroom yet.

Status: **Desktop app working locally, web app live at
[aryannatekar1.github.io/Malvani-Learning-AI](https://aryannatekar1.github.io/Malvani-Learning-AI/);
ready for content review and iterative testing.**
