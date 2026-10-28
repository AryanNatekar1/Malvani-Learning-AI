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
- A concept diagram for all nineteen lessons, several of them interactive
  (work as an area, momentum as a bar, friction as opposing arrows, gravity as
  two balls falling level). Each has a written text alternative.
- Search across every lesson and problem with `Ctrl`+`K`, a phone bottom-nav,
  and a "continue where you left off" card.
- Structured **draft** lessons across Physics, Mathematics, Chemistry, Biology,
  and Computer Science — 19 in total. All ten original Physics topics are now
  structured lessons and their `.txt` originals are preserved. Waves,
  Percentages, Acids and Bases, Food Chains and Loops were written directly
  for the structured schema, which brings every non-Physics subject to two
  lessons rather than one.
- A "Look around you" observation on every lesson: something to go and watch
  happen, using only what a student already has. It never asserts what is near
  the learner, because the app cannot know that — it invites, and the learner
  supplies the place. Both apps show it, on its own tab in the browser and as
  a lesson action on the desktop, with the explanation placed after the
  instructions so a learner can stop reading and go and look.
- Documented **places** in Sindhudurg and the Konkan, each explaining how it
  came to be that way and what it can teach: laterite and why the soil is red,
  the sea fort, Amboli and the rain shadow, why Konkan rivers run fast, Devgad,
  and the coast. Naming a real place is allowed here because it is public
  geography rather than a claim about an individual. Every record names its
  sources and lists what a local teacher still has to confirm. Reachable in
  both apps: a Places section in the browser, a "Places near you" lesson
  action on the desktop.
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
- The gate for generated answers, built before any generator: a retrieved
  passage must carry its source URL, every claim must name the passage it came
  from, and anything a passage does not support is stripped and reported
  instead of shown. With no search configured the result is an honest "I could
  not find this in a source I can show you" rather than a guess. The support
  check is lexical, which catches wholesale invention and nothing subtler, and
  the student-facing text says the answer was assembled rather than taught.
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
- Lesson drafting from a searched topic, for subjects the app has no lesson
  for. It assembles a draft in the same schema a hand-written lesson uses:
  explanation from cited sources, suggested places, reviewer notes, and the
  claims the generator tried to assert without evidence. It writes to
  `data/lesson_drafts/`, never `data/lessons/`, is always `NEEDS_REVIEW`, and
  invents no quiz or challenge — a plausible machine attempt at those would
  look finished when it is not. The regional connection is matched against
  already-documented places rather than written, because a fluent invented
  link to Sindhudurg is exactly the failure this project exists to refuse.
- Wikipedia retrieval, working, with no API key and no third-party packages.
  It was chosen because nothing secret enters the repository, every passage
  has a public URL a reader can check, and Marathi and Hindi editions exist.
  Every network failure returns no passages rather than raising, so a weak
  connection degrades to "I could not find this" instead of breaking the app.
- An extractive answer mode that selects sentences verbatim from retrieved
  passages rather than writing them, so grounding holds by construction and
  the whole pipeline runs today with no model, no key and no per-question
  cost. Its limits are documented rather than discovered later: it finds the
  defining sentence for a well-named topic, and it cannot tell which sense of
  a word a learner wants, nor an educational article from a coincidence. It
  is good enough to draft for a teacher and not good enough to show a student
  unreviewed, which is what the draft's reviewer notes say.
- Selection scores by which paragraph a sentence came from, which fixed two
  failures previously recorded here as beyond word-counting. A search for
  dispersion of light returned a sentence about coaxial cable, and "monsoon"
  returned one about a television contestant of that name. Both came from
  flattening an article into one block and discarding the structure it already
  had: a lead paragraph defines its subject and later ones branch into other
  senses of the same word. The distinction was never lexical.
- Looking up a topic the app has no lesson for, in the browser. Searching for
  something unknown now offers to look it up: it queries Wikipedia directly
  from the page, copies sentences verbatim from the results, and shows each
  one with a citation link and the full source list. It states plainly that
  nobody wrote it for the reader's class, no teacher has checked it, and it
  is not part of the reviewed library. Losing the network produces a message
  pointing back at the offline lessons, never a guess. The browser copy of
  the retrieval rules is compared against the Python one by tests, since a
  static page cannot import them and a silent divergence would show uncited
  text on the version most students use.
- Lookup follows the chosen language, which is the first thing the language
  picker actually changes. Marathi reads mr.wikipedia.org and Hindi reads
  hi.wikipedia.org, so a learner gets real content in the language, written
  by speakers of it and cited to them, with no translation step and nothing
  invented. Malvani and Konkani fall back to English and say so.
- Reading Devanagari required fixing a silent failure across both apps. An
  ASCII tokenizer broke Marathi words at every vowel mark and an ASCII
  sentence splitter found no sentences at all, so Marathi searches returned
  nothing while reporting no error. The gate had the same flaw independently,
  and would have dropped every Marathi claim for having no supported words.
  Both now share one tokenizer rather than keeping separate copies.
- The desktop app can look a topic up too, so both apps handle a question the
  library does not cover. Asking about an unknown topic no longer dead-ends;
  it explains that no lesson exists, refuses to guess, and offers a search.
  That action is deliberately the only one in the app that leaves the
  learner's machine, so it is opt-in, it says up front that what they typed
  goes to Wikipedia, and a test asserts asking a question never reaches the
  network on its own.
- The offline promise is now tested rather than asserted. A guard replaces the
  socket constructor so every outbound connection fails, and the lessons,
  places, teaching actions and quizzes are exercised through it — which
  catches a future feature reaching the network from somewhere nobody thought
  to mock, not just an unmocked provider.
- Claims the README makes are checked by tests: every lesson has a diagram,
  every diagram has a text alternative and a readout, no diagram points at a
  lesson that does not exist, every lesson has a quiz, a challenge and a
  source, nothing calls itself reviewed, and every quiz question's correct
  answer actually appears among its options.
- A drafting command a teacher can actually run:
  `py scripts/draft_lesson.py "dispersion of light" --subject Physics`.
  It searches, keeps only the sentences a source supports, and writes a draft
  to `data/lesson_drafts/` with its sources, the claims it dropped, and what
  still has to be done by hand. `--dry-run` shows it without writing and
  `--language Marathi` reads Marathi Wikipedia. The drafting pipeline existed
  before this and nothing could reach it, which left the library with no way
  to grow faster than one person typing.
- Drafts are structurally unable to reach a student: they live outside
  `data/lessons/`, which is the only folder the loader reads, and tests assert
  no draft is ever loaded as a lesson, that every draft on disk is marked
  unreviewed, and that none invents a quiz or challenge.
- Answer checking is compared across both apps by running the website's real
  JavaScript in a headless browser against the same answers as the Python, for
  a Problem Solver step and a quiz question. This is the highest-stakes
  duplication in the project: a divergence logs nothing, it just tells a
  student their correct answer is wrong. The comparison skips when no browser
  is present, so it cross-checks without becoming a reason CI cannot run.
- Misconceptions are asked before they are corrected. Each is a true-or-false
  question placed at the top of the lesson, ahead of the explanation, and the
  correction appears only after the learner answers. A list headed "these are
  not true" told every learner the same thing and found out nothing about any
  of them: the one who already knew skimmed it, and the one who believed it
  was contradicted before noticing they believed anything.
- That answer is also the diagnosis. Which statement a learner marks true says
  which misconception *they* hold, where a list cannot distinguish two learners
  wrong about photosynthesis in different ways — one thinking the food comes
  from the soil, the other that it comes from the air. The answers stay on the
  learner's own device so a lesson can offer to revisit one; they are never a
  score and go nowhere.
- All 35 misconceptions now carry a correction saying what is true instead,
  and are phrased as a single claim, because a learner cannot honestly answer
  true or false to two claims at once.
- The answers come back to the learner. Progress opens with "Worth another
  look": the statements they marked true, each with the correction and a link
  to the lesson it came from. It names the belief rather than scoring the
  learner, because "you got three wrong" tells nobody what to do next while
  "you thought plants feed through their roots" is a specific thing to go back
  to. Collecting answers and doing nothing with them would spend a learner's
  time and return nothing.
- An optional language model, on a leash. It is never asked for facts: it is
  given passages already retrieved and asked only to rewrite them for a
  younger reader, with every sentence naming the passage it came from, and the
  result goes through the same gate an extractive answer does. A sentence no
  passage supports is dropped before a learner sees it.
- It stays optional in three ways. No key is in the repository — it is read
  from `ANTHROPIC_API_KEY`. The `anthropic` package is not a dependency of the
  app, so a school can clone and run with nothing installed. And every failure
  (no key, no package, no network, a refusal, a malformed reply) falls back to
  selecting sentences, so an answer never depends on any of them.
- Nothing about a learner is sent. The topic and the retrieved passages go;
  name, answers, progress and writing stay on the machine, and a test asserts
  it by inspecting what the request actually contained.
- `PRINCIPLES.md` records the rules the project runs on and names the file
  that enforces each one. A test checks every path it points at exists.
- 313 automated tests, including GUI flow, compact-layout reachability,
  question-trail, state-reset, privacy-boundary, and resize smoke tests, plus
  checks that observations name no place, that every place cites a source,
  that the desktop app teaches the same content the website does, and that
  every lesson on disk is registered in both the web manifest and the
  offline precache.

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
