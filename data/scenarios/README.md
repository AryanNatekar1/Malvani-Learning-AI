# Problem Solver scenarios

Scenario JSON files provide small, authored journeys for the future **Problem
Solver** and **Go Deeper** screens. They are local files read with Python's
standard library; they do not access GPS, maps, sensors, the network, or a
student's location.

## Safety boundary

The first supported scenario type is `COMPUTER_MODEL`. Its
`data_provenance.kind` must be `ILLUSTRATIVE_COMPUTER_MODEL` and
`is_local_measurement` must be `false`. The engine always renders an explicit
notice that the values are illustrative and are **not** local measurements,
GPS data, or student data.

Do not put a real pond, school, village, route, household, student, or
unverified cultural fact in a scenario. A reviewed contextual-learning record
belongs in `data/contexts/` and must pass its separate verification policy.

## Source vs. data provenance

These fields deliberately answer different questions:

- `content_source` says where the underlying school concept came from. It must
  contain a `citation`, may contain an `https` URL, and may explain how it was
  used.
- `data_provenance` says where the scenario's numbers came from. For a computer
  model, state that they are illustrative inputs and set
  `is_local_measurement` to `false`.

Do not use a textbook citation as though it were the source of a local
measurement. Do not describe invented numbers as observed data.

## Required shape

```json
{
  "id": "physics.topic.scenario-name",
  "title": "Student-facing title",
  "subject": "Physics",
  "topic": "topic",
  "scenario_type": "COMPUTER_MODEL",
  "verification_status": "NEEDS_REVIEW",
  "content_source": {
    "citation": "Publisher or curriculum source",
    "url": "https://optional-source.example",
    "usage_note": "How the source was used"
  },
  "data_provenance": {
    "kind": "ILLUSTRATIVE_COMPUTER_MODEL",
    "statement": "How these illustrative values were chosen",
    "is_local_measurement": false
  },
  "introduction": "What the computer model represents",
  "problem": "The problem to solve",
  "guided_steps": [
    {
      "id": "unique-step-id",
      "prompt": "One calculation or comparison",
      "accepted_answers": ["one accepted answer"],
      "numeric_answer": {
        "value": 6,
        "unit": "kg m/s",
        "allow_unit_omission": true,
        "accepted_symbols": ["p"]
      },
      "success_feedback": "Feedback after an exact accepted answer"
    }
  ],
  "progressive_hints": ["hint one", "hint two"],
  "worked_solution": "An authored solution",
  "go_deeper": {
    "research_question": "A researchable question",
    "hypothesis_prompt": "Ask for a prediction and reason",
    "data_label": "Label supplied model data honestly",
    "data_columns": ["Column A", "Column B"],
    "data_rows": [["value", "value"]],
    "analysis_prompt": "Ask about variables and evidence",
    "proposed_solution_prompt": "Ask for a fair next test or proposal",
    "reflection_prompt": "Ask what the model can and cannot show"
  }
}
```

`numeric_answer` is optional and belongs only on a calculation step with an
explicitly authored number and unit. It accepts a complete compact response
such as `6`, `6.0 kg m/s`, or `p = 6 kg*m/s` when those forms match the
declared rule. It does not pull a number from arbitrary prose, infer a unit,
or evaluate reasoning. Keep a qualitative comparison on `accepted_answers`
unless a separate reviewable rule is genuinely needed.

## Optional scenario visual model

Use `visual_model` only when a fixed visual materially supports an authored
step. It is optional so a scenario is never forced to include a decorative
graphic. The first supported kind is a two-cart Momentum comparison:

```json
"visual_model": {
  "kind": "MOMENTUM_CART_COMPARISON",
  "prediction_prompt": "Which cart has greater momentum size?",
  "available_after_step_id": "cart-b-momentum",
  "carts": [
    {"id": "cart-a", "label": "Cart A", "mass_kg": 2, "velocity_m_per_s": 3},
    {"id": "cart-b", "label": "Cart B", "mass_kg": 3, "velocity_m_per_s": 2}
  ]
}
```

This model is accepted only for a `COMPUTER_MODEL` Momentum scenario. It
requires exactly two named carts, finite positive numeric masses, finite
numeric velocities, and the same non-zero direction. It also needs an
`available_after_step_id` that exactly names an installed guided step; this
keeps the visual's reveal placement reviewable instead of guessing from prose.
The engine rejects strings, booleans, non-finite values, duplicate cart names,
and values whose calculated momentum would overflow.

The visual may show authored inputs before a prediction, but it must not expose
derived momentum values or the comparison until its local prediction gate is
used. Do not use it for collision claims, road-safety advice, local
measurements, GPS data, or student data. A prediction stays in the open desktop
window only; it is not a Problem Solver attempt, event, or profile field.

## Review status

Use `NEEDS_REVIEW` for drafts. The renderer displays that status rather than
pretending the activity has been approved for classroom use. Use `VERIFIED`
only after appropriate subject and curriculum review; keep the source and
provenance fields accurate in either case.

Only `NEEDS_REVIEW` and `VERIFIED` computer-model records are available to
students. Records marked `UNAVAILABLE` or `COMMUNITY_PROVIDED` are retained
only as authoring states and stay hidden until their separate review policy is
complete. Scenario lookup is scoped to both its `subject` and `topic`.

## Testing an authored file

Run the focused checks after editing a scenario:

```powershell
python -m unittest discover -s tests -p "test_problem_scenario_engine.py" -v
```

The loader rejects missing fields, duplicate ids, malformed URLs, empty
answers, data tables with unequal row lengths, and any attempt to mark a
computer-model record as a local measurement.
