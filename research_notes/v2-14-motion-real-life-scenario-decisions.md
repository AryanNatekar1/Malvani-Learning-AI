# V2.14 Motion lesson and real-life scenario decisions

## Why this change

Every prior Problem Solver scenario used an abstract textbook object (two
carts, two blocks). The project's stated goal is real-life, not-bookish
learning, so V2.14 migrates Motion from its legacy `.txt` file into a
structured lesson and pairs it with a scenario framed around an everyday
situation: walking to collect water.

```text
Motion lesson (structured) -> "A Real Journey: Carrying Water" scenario
one-way time -> round-trip time -> does load change return speed?
-> Go Deeper: vary return speed, hold distance constant
```

## Staying inside the existing safety boundary

`data/scenarios/README.md` already forbids putting a real pond, village,
household, or family into a scenario. A "relatable" real-life frame is not an
exemption from that rule, so the introduction explicitly disclaims it:

> "This is not a measurement of any real household, family, village, or
> specific place — it is a supplied illustrative model."

This mirrors the project's own earlier internal discussion about avoiding
unverified claims about specific groups (for example, not asserting who
walks to collect water in a given place as fact). The scenario instead uses
"in many places, a person may need to..." framing and keeps every numeric
value labelled `ILLUSTRATIVE_COMPUTER_MODEL`, exactly like Momentum and
Force. `test_introduction_never_claims_a_real_household_or_place` in
`tests/test_problem_scenario_engine.py` checks this directly, including that
neither "Sindhudurg" nor "Konkan" appears anywhere in the rendered text.

## Content

The Motion lesson content, quiz question, and reasoning guide follow the
exact shape already used by `force.json` and `momentum.json` (see
`src/lesson_models.py`), including a `NEEDS_REVIEW` `local_example` with
`source: null`, so it carries the same review obligation as every other
starter lesson rather than a special exception.

The scenario's concept source, OpenStax *Physics* 2.2 "Speed and Velocity",
was fetched and confirmed live (not guessed) before being written into
`content_source`, the same verification step used for the Force scenario's
citation in V2.13.

## Why no scenario visual

`MomentumCartComparisonVisual.from_mapping` still restricts
`MOMENTUM_CART_COMPARISON` to a Momentum `COMPUTER_MODEL` scenario, and no
second visual kind exists. Adding a distance/time visual for Motion was out
of scope here and needs its own reviewed design.

## Verification

`python -m unittest discover -s tests -v` passes at 126 tests (5 new tests in
`MotionRealLifeScenarioTests`, following the same shape as V2.13's
`ForceScenarioTests`). A manual `AppController` smoke run confirmed
`Explain motion` now opens the structured lesson (not the legacy `.txt`),
`problem_scenario_available()` is `True`, all three guided steps accept their
declared answers, and Go Deeper renders with the slower-return-speed data
table.
