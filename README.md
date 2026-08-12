# Malvani Learning AI

Malvani Learning AI is an offline-first educational application for students
in Sindhudurg, Maharashtra, and other regional communities. It is designed to
help students **learn, think, solve, and explore** instead of merely receiving
answers.

The current version is a working local desktop prototype. It combines clearly
labelled local draft lesson data, guided questions, quizzes, progress tracking,
and a small optional AI-routing component. It is not a generic
ChatGPT clone and it does not require an API key.

## What works now

- A Tkinter desktop GUI with Home, Learning, Quiz, Progress, Library, and
  Settings screens, organised in a responsive app shell with a consistent
  local-first visual theme. Page content remains reachable by scrolling at the
  supported 800×600 laptop size.
- The original terminal chatbot remains available as a fallback.
- Structured, guided starter lessons in:
  - Physics: Gravity, Force, Momentum, Newton's Laws
  - Mathematics: Fractions
  - Chemistry: Atoms
  - Biology: Photosynthesis
  - Computer Science: Algorithms
- The original ten flat Physics files remain untouched and still work through
  the terminal chatbot; the student renderer hides their unverified
  local/cultural draft sections until they are reviewed.
- Simple/detailed teaching, everyday examples, think questions, challenges,
  hints, solutions, career connections, and next-topic suggestions where a
  structured lesson provides them.
- Lesson-bound follow-up questions: after opening a structured lesson, the
  tutor can answer stored why/how, formula, example, real-world-use,
  misconception, career, and next-step questions. It names missing local data
  instead of guessing.
- Local quizzes with multiple choice and numerical/exact-answer scoring.
- Local-only progress stored by default in `local_data/malvani_learning.db`
  (ignored by Git). No account, server, or personal information is required.
- English draft lesson content, plus language selection with an honest fallback
  when reviewed Marathi or Malvani lesson text is unavailable.
- Safe cultural-context handling: entries without a source and `VERIFIED`
  status are hidden from student output.
- Built-in Canvas diagrams for Gravity, Force, Momentum, and Newton's laws,
  plus a real offline Momentum explorer: mass and velocity sliders update the
  cart, direction, and `p = m × v` result with a text alternative.
- A continuing question-and-answer trail, data-backed follow-up chips, clearer
  quiz progress, progress metrics, and lesson-library cards for a more usable
  desktop study workflow.
- Explicit requests such as “Explain momentum” start the full teaching flow;
  a focused active-lesson follow-up such as “Why?” remains a focused response.
- In-progress quizzes resume when the student returns to Quiz rather than
  silently resetting their score or attempt state.
- A small deterministic local neural network routes simple UI intents such as
  “give me a hint.” It is **not an LLM** and is never used as a source of
  educational, cultural, Marathi, or Malvani facts.
- A solution gate, progressive hints, retryable quizzes, and a transparent
  key-idea reasoning check support productive struggle rather than immediate
  answer delivery.

## Run the application

Requirements: Python 3.10+ with Tkinter (included with standard Windows Python
installations). This version has no third-party Python dependencies.

```powershell
python src\app.py
```

The original terminal prototype is still available:

```powershell
python src\chatbot.py
```

Try questions such as:

```text
What is momentum?
Explain Newton's laws of motion
What is photosynthesis?
Teach me an algorithm
```

## Test the project

```powershell
python -m unittest discover -s tests -v
```

The GUI smoke tests create and close a real window when a display is available.
Other application behavior is tested without needing the GUI.

## Architecture

```text
src/
├── app.py                 # Starts the desktop app
├── gui.py                 # Tkinter screens and simple diagrams
├── app_controller.py      # Connects UI to learning features
├── chatbot.py             # Preserved terminal fallback
├── knowledge_engine.py    # Topic matching and lesson loading
├── lesson_models.py       # Structured lesson data types/validation
├── teaching_engine.py     # Builds paced learning responses
├── related_question_engine.py # Lesson-bound follow-up answers
├── reasoning_engine.py    # Transparent local key-idea feedback
├── quiz_engine.py         # Offline quiz scoring
├── problem_engine.py      # Hint-before-solution problem flow
├── student_engine.py      # Local profile and aggregate progress
├── language_engine.py     # Language selection and honest fallback
├── culture_engine.py      # Verification-safe cultural context display
├── neural_intent.py       # Small local neural intent classifier
├── ai_provider.py         # Provider-neutral AI boundary and offline fallback
├── media_engine.py        # Useful visual specifications
├── visual_learning.py     # Small, interactive, offline teaching visuals
├── ui_theme.py            # Shared dependency-free Tkinter visual theme
└── voice_engine.py        # Optional voice-provider boundary

data/
├── *.txt                  # Original V1 Physics knowledge files (preserved)
├── lessons/               # Editable structured JSON lessons
└── culture/               # Future source-backed cultural-context entries
```

## Lesson data and safety

Structured lessons are JSON because the standard library can validate their
fields without adding a YAML or Markdown parser dependency. JSON is also a
clear fit for strict quiz answers, sources, and verification status. See
[data/lessons/README.md](data/lessons/README.md) before adding a lesson.

The current starter lessons are marked `NEEDS_REVIEW`; they are functional
project content, but should be reviewed against the intended school curriculum
before being presented as published material. Local/cultural context needs both
a source and `VERIFIED` status before the student UI will display it. Do not
invent Malvani words, local slang, traditions, or historical claims.

When a verified local connection is not available, the student interface says
so in plain language. It does not expose internal terms such as draft state or
verification metadata as part of a lesson.

## Language support

| Requested language | Current behavior |
| --- | --- |
| English | Supported lesson content |
| Marathi | Basic interface labels; lessons fall back to English until reviewed Marathi content is added |
| Malvani | Selection is supported, but lesson/interface text falls back visibly rather than inventing Malvani |

## AI and neural-network boundary

`neural_intent.py` contains a real, small one-hidden-layer feed-forward neural
network trained deterministically on local UI phrases. It can identify a few
actions (`lesson`, `hint`, `challenge`, `solution`, and `quiz`) and safely
returns `unknown` for uncertain input.

The factual source remains local lesson data. `AIProvider` is an abstraction
for a future deliberately configured OpenAI, local-model, or other adapter.
No provider, secret, or API key is included in this repository.

The reasoning check is deterministic and looks for lesson-authored key ideas;
it does **not** semantically grade a student's explanation. The UI says this
explicitly and encourages the student to revise their own reasoning.

## Related questions and data boundaries

The desktop tutor handles a bounded set of follow-up questions only when an
active structured lesson contains the needed field. For example, it can show
the Momentum formula because that equation already appears in the stored
lesson explanation. It cannot supply a Gravity formula from the current
starter data, so it names that data gap instead of deriving or inventing one.

This keeps the app useful while preserving the project rule that educational,
cultural, Marathi, and Malvani content must be reviewable local data rather
than untraceable generated text.

## Current limitations

- The project is a desktop prototype, not yet a web or mobile deployment.
- Only starter lesson content exists for four non-Physics subjects.
- Marathi and Malvani educational lessons still require linguistic and subject
  review.
- No cultural entries are yet verified and therefore none are injected into
  student lessons.
- The small neural model is a routing demonstration, not conversational AI or
  a personalized language model.
- Voice architecture exists, but no speech provider is installed.
- Progress is local to one computer; it is not synchronized or shared.

## Project direction

The next high-value work is to review lesson content with teachers, create
source-backed Sindhudurg/Konkan context records with community input, and add
reviewed Marathi and Malvani content. See [roadmap.md](roadmap.md) and
[research_notes/v2-architecture-decisions.md](research_notes/v2-architecture-decisions.md),
plus the [desktop readiness assessment](research_notes/v2-desktop-readiness-assessment.md).
