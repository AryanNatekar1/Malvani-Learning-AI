# V2.9 guided investigation decisions

## Why order the first research activity?

The Momentum Go Deeper activity is a beginner scaffold, not a general model of
every scientific investigation. Its prompts now move in a visible order:

```text
Hypothesis -> Analysis -> Fair next test -> Reflection
```

This gives a new learner a clear next action after finishing the supplied
computer model. A later field stays locked until the preceding local writing
check-in is recorded. The controller, not just the GUI, enforces that order so
the same rule applies to future interfaces.

Recording a check-in does **not** mean the app judged the writing correct,
scientific, complete, or mastered. It still records only an aggregate counter
and fixed event name; the typed text remains in the local visible field for
the current lesson session and is never written to JSON or SQLite.

## Why add a narrow numeric rule?

Exact string matching made a correct calculation unnecessarily brittle:
`6.0` and `p = 6 kg m/s` were rejected even though they express the first
Momentum model result. V2.9 adds an optional `numeric_answer` object to a
scenario step. It declares a finite value, canonical unit, whether a unit may
be omitted, and any accepted formula symbols.

The parser accepts a whole compact response only. It permits harmless decimal,
spacing, and multiplication-symbol variations for the declared rule, but it
rejects an incorrect unit, a close-but-wrong number, and sentences that merely
contain a number. It applies only to authored Problem Solver calculation
steps—not to quizzes, lesson challenges, related questions, or free-text
reasoning.

## Boundaries retained

This change adds no LLM, semantic grader, external data source, GPS/location
access, cloud storage, or cultural/language claim. The Momentum scenario stays
an illustrative `NEEDS_REVIEW` computer model. Its source and data provenance
remain separate, and student text remains outside persistence.
