# The rules this project runs on

Malvani Learning AI helps students in Sindhudurg understand school science by
connecting it to the place they live and the language they speak.

That aim makes a particular kind of mistake very easy to make, and the whole
design exists to prevent it. An app that invents a plausible local detail, a
Malvani word, or a confident fact is more harmful than an app that says
nothing, because a student has no way to tell the invented part from the rest,
and the mistake carries the app's authority into their exam.

So the rules below are not aspirations. Each one is enforced somewhere in the
code, and the place it is enforced is named. If you change the code, these are
what you must not break. If you are reviewing content, these are what you are
checking against.

---

## 1. The app may say "I don't know". It may never make something up.

This is the rule the others serve.

Refusing to answer costs a student one lookup. Answering wrongly costs them
the thing they came for, and they will not find out until it matters.

**Where this lives:** `src/grounded_answer.py` drops any claim a source does
not support. `src/culture_engine.py` hides unverified local context. An empty
answer renders as *"I could not find this in a source I can show you, so I am
not going to guess."*

---

## 2. A model is never the source. It may only rearrange what a source said.

A language model may rewrite retrieved passages for a younger reader. It may
not add a fact, an example, a number, a date, or a place name that was not in
those passages.

Every sentence it returns names the passage it came from, and anything that
passage does not support is dropped before a learner sees it.

**Where this lives:** `src/external_model.py` constrains the model to a schema
of claim-plus-passage. `src/grounded_answer.py` then checks every one. The
check is lexical, so it catches wholesale invention and not subtle distortion;
the code says so rather than implying it is proof.

---

## 3. Nothing is called reviewed until a person has reviewed it.

`verification_status` is `NEEDS_REVIEW` until a human has read the content and
put their name to it. It is not a formality. The app reads that field when
deciding what a student may be shown as settled fact.

A machine may never set it to `VERIFIED`. Nothing in this repository does.

**Where this lives:** every file under `data/`. Drafts live in
`data/lesson_drafts/`, which the lesson loader does not read, so nothing
machine-assembled can reach a student by accident.

---

## 4. The app cannot see where a learner is, and must never pretend to.

"There is a pond near your school" is an invention. The app does not know.

A lesson may say *"if you can find still water — a pond, a bucket, a puddle"*
and let the learner supply the place. That is true everywhere, and it hands
the learner the more interesting job: being the one who looks.

Naming a real, documented place is different and is allowed — Sindhudurg Fort
stands off Malvan whether or not the reader has been there. The line is
between public geography anyone can check and a claim about one person that
nobody can.

**Where this lives:** `observe_around_you` in every lesson, tested by
`tests/test_observation_activities.py`. Documented places live in
`data/places/`, and each one must cite its sources and list what a local
teacher still has to confirm.

---

## 5. Malvani is not guessed at.

The app is named after a language it contains none of. That is the honest
state, and it is better than the alternative.

Malvani is mostly spoken and has no settled spelling. A machine asked for
Malvani will produce Marathi with a few words changed and present it as
Malvani, which is exactly the invention this project refuses — and it cannot
be caught by any check, because there is no source to check against.

Marathi and Hindi are different: they have standard written forms, and
Wikipedia editions written by speakers, which the app reads directly so a
learner gets real content in the language with no translation step at all.

**Where this lives:** `src/language_engine.py` ships no Konkani or Malvani
labels. `data/languages/` accepts contributed words from a speaker and ignores
the file until a named reviewer signs it off.

---

## 6. What a learner does stays on their machine.

No account, no server, no analytics. Progress is stored locally. Research
writing and typed answers are never saved at all — only aggregate counts.

Searching the web is the single action that leaves the device, so it is opt-in,
it never happens on its own, and the app says what is being sent before the
learner presses it.

**Where this lives:** `src/student_engine.py` stores counts and never answer
text. `AppController.look_up_topic` is the only networked path, and a test
asserts that asking a question never reaches the network by itself.

---

## 7. It has to work with no internet.

Students on weak or metered rural connections are the point. Every lesson,
quiz, diagram and activity works offline after one visit. The model and the
web search are additions on top of that, never requirements.

**Where this lives:** `sw.js` precaches the app and every lesson file.
`tests/test_offline_and_promises.py` disables the socket layer entirely and
runs the lessons, quizzes and teaching actions through it.

---

## 8. Both apps teach the same thing.

The desktop app and the website read the same JSON, but that is only half of
it. For a while the desktop app parsed observations and places and never
showed them, so a student there silently saw less.

Sharing a data directory is not parity. What reaches a learner is.

**Where this lives:** `tests/test_desktop_content_parity.py`, and
`tests/test_answer_checking_parity.py`, which runs the website's real
JavaScript in a browser against the same answers as the Python, because a
divergence there tells a student their correct answer is wrong.

---

## 9. Ask before correcting.

A list headed "these are not true" tells every learner the same thing and
finds out nothing about any of them.

Asked as a question first, the same sentence does two jobs: a learner meets
their own belief a moment before the correction, which is when a correction
has a chance of sticking — and the answer says which misconception *this*
learner holds. Two students wrong about photosynthesis may be wrong in
entirely different ways.

**Where this lives:** the misconception check at the top of every lesson in
`index.html`, with what a learner marked true kept on their own device and
shown back to them as something to revisit, never as a score.

---

## 10. Say what the thing actually is.

The app is a well-built offline tutor with cited search. It is not a
conversational AI, and the small intent classifier in `src/neural_intent.py`
is not a language model.

Describing it accurately costs nothing and is the same discipline as the rest
of this file. A reviewer who finds one overstatement will doubt everything
else.

**Where this lives:** `STATUS.md`, which separates what works from what is
drafted from what is planned.

---

## If you are adding something

Ask the three questions this project keeps coming back to:

1. **Where did this come from, and can a reader check it?**
2. **Would this still be true for a student in a different village?**
3. **If this is wrong, how would anyone find out?**

A feature that cannot answer the third one needs a test before it needs
polish.
