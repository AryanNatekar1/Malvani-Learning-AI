# V2 architecture decisions

## Why preserve the terminal chatbot?

The terminal chatbot is a small, useful offline baseline. Keeping it means the
new GUI and structured lesson system can evolve without removing a working
learning tool.

## Why JSON for structured lessons?

The existing text files are excellent early prototypes, but quizzes, sources,
language variants, and verification status need dependable fields. JSON is
read and validated by Python's standard library, avoids a new dependency, and
is easier for software to check than free-form text. The original `.txt` files
remain untouched.

## Why Tkinter?

Tkinter comes with the installed Python environment, works locally, and keeps
the prototype free of a GUI dependency. It is appropriate for a student-facing
desktop prototype; a web/mobile interface can be added later without changing
the learning engines.

## Why a small neural network instead of a large model?

The included neural network demonstrates a real, inspectable one-hidden-layer
model for classifying a few interface requests. It has intentionally narrow
responsibility. It is not a language model and must not generate facts,
cultural claims, or unreviewed translations. Structured lesson data remains
the factual foundation, with its review status shown explicitly to students.

## How is cultural safety enforced?

`culture_engine.py` displays a context entry only when it is `VERIFIED` and
has a source. `COMMUNITY_PROVIDED` and `NEEDS_REVIEW` entries can be retained
for review but are not silently shown to students.

## How is student privacy protected?

Aggregate local progress and non-text event records are written by default to
`local_data/malvani_learning.db`, which Git ignores. The earlier JSON
`ProfileStore` remains as a compatibility/testing adapter. The app requires no
name, account, internet connection, or cloud database.
