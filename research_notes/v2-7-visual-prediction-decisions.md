# V2.7 Momentum visual prediction decisions

## Learning goal

The Momentum explorer now follows a small prediction loop:

```text
Change mass or velocity -> predict greater / smaller / same -> test -> inspect the result
```

This asks the learner to compare momentum *size* before seeing the calculated
answer. It supports the project goal of developing independent reasoning rather
than presenting a calculator result immediately.

## What the visual does

- Uses the already-authored relationship `p = m x v`.
- Keeps a visible reference cart: `2 kg` at `5 m/s`, with momentum size
  `10 kg m/s`.
- Shows the candidate cart's mass, velocity, direction, and a velocity arrow
  while the result is hidden.
- Reveals the candidate momentum result only after the learner selects
  greater, smaller, or same and presses **Test prediction**.
- Explains that momentum size and direction are separate: equal magnitudes can
  still point in different directions.

## Honest boundaries

The prediction check compares one of three explicit choices using the formula.
It does not understand or grade a written explanation, infer ability, or claim
mastery. The selected choice is not stored in the local profile or SQLite
database.

The visual has no automatic or looping animation. The arrow is a static model
cue, with a live text alternative so no essential information is available only
through colour, shape, or Canvas drawing.

## Scope decision

This feature stays inside the generic `MomentumLab`. It does not reuse the
Problem Solver's two-cart scenario values, because those values are not yet a
typed visual-data field. A future scenario-bound visual must be driven by a
validated JSON `visual_model` field; it must not extract numbers from prose.
