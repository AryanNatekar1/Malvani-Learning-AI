# V2.5 Problem Solver and Go Deeper decisions

## Goal

V2.5 adds one complete learning loop for Momentum:

```text
Understand -> predict -> calculate -> compare -> hint/retry -> review -> investigate -> reflect
```

It is intentionally a small vertical slice. The project now has a real place
to test the teaching flow before adding more subjects, visual effects, GPS, or
an external language model.

## First activity

The first record is `physics.momentum.cart-comparison`.

- Cart A has mass `2 kg` and velocity `3 m/s`.
- Cart B has mass `3 kg` and velocity `2 m/s`.
- The student calculates `p = m x v` for each cart, then compares them.
- Both momenta are `6 kg m/s`.

The values are explicitly labelled **illustrative computer-model values**.
They are not a collision, a road-safety prediction, field data, a local fact,
GPS data, or a measurement from a student or community.

The physics-concept source is separate from the provenance of the values. A
future author must never use a source citation to imply that invented model
numbers were measured in a real place.

## Architecture boundary

`problem_scenario_engine.py` is separate from `problem_engine.py`.

- `problem_engine.py` remains responsible for the normal challenge inside a
  structured lesson.
- `problem_scenario_engine.py` loads and validates sourced, supplied-data
  models and runs their independent guided steps.
- `AppController` keeps `current_scenario_session` separately from
  `current_problem_session` and `quiz_session`.

This prevents starting Problem Solver from silently replacing a learner's
ordinary challenge or in-progress quiz.

## Privacy boundary

The app never saves a model answer, hypothesis, analysis, proposed test, or
reflection. It saves only aggregate counters and fixed event names such as
`scenario_attempt` or `research_hypothesis_completed`, plus the lesson topic
and optional correctness for exact model steps. There are no coordinates,
manual-context identifiers, school names, GPS values, or network requests.

## Honest assessment boundary

Problem Solver checks exact, authored responses after harmless punctuation
normalisation. It does not understand a student's reasoning.

Go Deeper marks that a prompt was completed in the current session. It tells
the learner that it cannot determine whether the writing is scientifically
correct. A future semantic assessment needs teacher-reviewed rubrics and
evaluation against real student work before it can make stronger claims.

## Review before expansion

Before publishing the Momentum activity for classroom use:

1. A Physics teacher should review the explanation, model prompts, answers,
   units, scope, and source use.
2. A reviewer should change its `NEEDS_REVIEW` status only after that review.
3. Each new activity should provide a concept source, an explicit data
   provenance statement, safety limits, validation tests, and a student-facing
   non-local/non-GPS label where it uses authored values.
4. Local or cultural scenarios must still use the existing independent
   source-and-verification gates; a Problem Solver scenario must not bypass
   them.
