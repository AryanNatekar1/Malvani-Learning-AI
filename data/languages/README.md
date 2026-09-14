# Contributed language files

This folder is how a speaker of a language adds it to the app **without
writing any code**.

It exists because of a rule the project does not bend: the app never invents a
word, a translation, or a dialect form. English and Marathi labels are built
in, and Hindi was added from its standard written form. Konkani and Malvani
are not, and will not be, guessed at — Malvani in particular is mostly a spoken
variety of Konkani with no settled spelling, so there is no honest way to write
it without a speaker.

So the app shows English for those languages, and says so plainly, until
someone who actually speaks the language fills in a file here.

## Add a language

1. Copy `Konkani.example.json` to `Konkani.json` (or `Malvani.json`).
2. Fill in the words under `interface_text`.
3. Leave `verification_status` as `NEEDS_REVIEW` while you work.

The app ignores the file entirely until **both** of these are true:

- `verification_status` is `VERIFIED`
- `reviewed_by` names a real person

That is deliberate. A half-finished draft cannot reach a student by accident.

## Why a reviewer is named

A translation is a claim about someone's language. If it is wrong, a student
learns it wrong, and the mistake carries the app's authority. Naming the
reviewer means the claim has a person behind it, the same way lesson content
carries a source.

One speaker may write and review their own file — the point is that the name
is recorded, not that two people are involved.

## Fields

| Field | Meaning |
|---|---|
| `language` | Must match a name in `SUPPORTED_LANGUAGES` exactly |
| `verification_status` | `NEEDS_REVIEW` or `VERIFIED` |
| `reviewed_by` | Name of the speaker who checked the words |
| `source` | Dictionary, school book, or "native speaker, <place>" |
| `notes` | Anything a later reader should know — village, spelling choice, doubts |
| `interface_text` | The labels themselves |

Partial files are fine. Any label you leave out falls back to English, so you
can contribute five words today and the rest later.

## A note on Malvani spelling

Malvani is written rarely and inconsistently. If you are unsure between two
spellings, put your choice in `interface_text` and record the alternative in
`notes`. Recording the uncertainty is more useful than hiding it — and for
this project, a documented disagreement between two speakers is data worth
keeping, not a problem to resolve by guessing.
