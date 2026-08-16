# V2.12 scenario-bound Momentum visual decisions

## Learning goal

The generic Momentum explorer lets a learner change values. The first Problem
Solver scenario instead has two fixed authored carts. V2.12 adds a separate
visual that supports the final comparison without turning the activity into a
calculator or a decorative animation:

```text
Calculate Cart A -> calculate Cart B -> inspect supplied visual cues
-> predict the comparison -> test prediction -> discuss the model result
```

## Data boundary

The new optional `visual_model` is part of a `ProblemScenario`. It contains
typed JSON mass and velocity inputs, not values parsed from the introduction,
problem, or worked solution. The only initial kind is
`MOMENTUM_CART_COMPARISON`, restricted to the illustrative `COMPUTER_MODEL`
Momentum activity.

Validation requires two uniquely named carts, strict string labels, finite
numeric values, positive mass, finite calculated momentum, and a shared,
non-zero direction. This narrow rule lets the student-facing copy say
“momentum size” before reveal and accurately show the common direction after
reveal. A future opposite-direction comparison needs a separate reviewed
schema and wording; equal sizes are not automatically equal vectors.

## Learning placement and privacy

`available_after_step_id` is an explicit link to a guided calculation step.
The controller returns a visual snapshot only after Problem Solver starts, and
keeps it locked until the linked step has been completed or the learner has
deliberately reviewed the already gated worked solution. The GUI cannot invent
that decision from its own widget state.

The popup is non-modal so it can be consulted while working. It displays the
scenario's content status and illustrative-data notice. Its prediction lives
only in a Tkinter variable. Opening, closing, choosing, resetting, or testing
that prediction does not advance a scenario step, create an event, affect a
quiz/challenge, or write to JSON or SQLite.

The popup body is independently scrollable at compact window sizes. A child
that receives keyboard focus is brought into the dialog viewport, so the text
alternative and Close control remain reachable without forcing a tall window.

## Visual/accessibility choices

- Cart width and arrow length are labelled schematic cues for mass and
  velocity; they are not a scale, force arrow, collision result, or trajectory.
- Labels and a text alternative repeat all essential input values so colour or
  Canvas drawing is never the only source of information.
- Derived values and the final comparison are hidden until a learner chooses an
  option and presses **Test prediction**. A radio selection alone does not
  reveal them.
- There is no automatic animation loop. The visual is deliberately static so
  attention stays on the relationship being learned.

## Verification

Focused tests cover schema type/scope/overflow validation, no-prose data use,
session placement, the hidden/revealed text boundary, prediction handling, and
a real-Tk smoke flow. The smoke flow confirms a locked visual cannot open,
the popup is non-modal, a local prediction does not add a Problem Solver
attempt, changing lesson closes the stale popup, and the 560×400 dialog can
scroll and reveal an off-screen focused close button.
