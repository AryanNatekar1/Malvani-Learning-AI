# V2.13 second Problem Solver scenario decisions

## Learning goal

The Momentum Problem Solver was the only authored `COMPUTER_MODEL` scenario,
so the schema, controller wiring, and Go Deeper flow had never been exercised
by a second, independent record. V2.13 adds one more scenario for Force,
reusing the existing schema exactly as documented in
`data/scenarios/README.md` instead of extending the engine:

```text
Block A (4 kg, 8 N) -> calculate acceleration
Block B (2 kg, 8 N) -> calculate acceleration
-> compare -> Go Deeper: vary mass, hold force constant
```

This deliberately shows a different relationship from Momentum's "equal
result from different inputs" surprise: here the same applied force produces
*different* accelerations, reinforcing the inverse relationship between mass
and acceleration in Newton's second law.

## Source and data provenance

`content_source.url` was verified live (not guessed) against
`https://openstax.org/books/physics/pages/4-3-newtons-second-law-of-motion`
before being written into the record, consistent with the project's rule
against fabricated citations. `data_provenance` again declares
`ILLUSTRATIVE_COMPUTER_MODEL` values with `is_local_measurement: false`; the
block masses and force are chosen for arithmetic clarity only.

## Scope kept narrow

No `visual_model` was added. `MomentumCartComparisonVisual.from_mapping`
explicitly restricts `MOMENTUM_CART_COMPARISON` to a Momentum
`COMPUTER_MODEL` scenario, and no second visual kind exists yet — adding one
for Force was out of scope for this change and would need its own reviewed
design.

The numeric answer unit is written as `m/s2`, not `m/s^2`. The existing
`_normalize_unit` tokenizer only accepts letters, digits, `*`, and `/`; a
caret is rejected, which would silently fail every numeric-shaped submission.
Guided-step prompts spell this out so a learner is not asked for a unit form
the schema cannot accept.

## Test and repository-ordering fallout

Adding a second scenario file exposed three tests that had implicitly
assumed there was exactly one scenario, or that `load_problem_scenarios()[0]`
was always the Momentum record (file loading is alphabetical by path, and
`force_model_comparison.json` sorts before `momentum_cart_comparison.json`):

- `tests/test_problem_scenario_engine.py` now selects the Momentum record by
  `identifier` instead of asserting `len(scenarios) == 1`, and gained a
  `ForceScenarioTests` class covering the new record's source/provenance,
  renderer output, full guided-step session flow, Go Deeper sections, and
  topic-scoped repository lookup.
- `tests/test_visual_learning.py` and
  `tests/test_student_and_controller.py::test_controller_problem_solver_matches_the_active_lesson_subject_and_topic`
  now look up the Momentum scenario by `identifier` rather than index `[0]`.
- `tests/test_student_and_controller.py::test_problem_solver_state_resets_for_same_topic_reload_and_topic_change`
  and the matching GUI smoke test switched their "topic with no scenario"
  probe from `force` to `newton`, since `force` now legitimately has one.

## Verification

`python -m unittest discover -s tests -v` passes at 121 tests. A manual
`AppController` smoke run confirmed the Force lesson reports
`problem_scenario_available() == True`, all three guided steps accept the
declared numeric/comparison answers, and Go Deeper renders after completion.
