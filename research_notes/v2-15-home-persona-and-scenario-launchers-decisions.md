# V2.15 GUI persona and one-click scenario launcher decisions

## Why this change

The GUI worked but read as a settings form first and a tutor second, and the
three real Problem Solver scenarios (Momentum, Force, Motion) were buried
behind several clicks (Home → set preferences → Learn → ask a question →
Problem Solver). V2.15 makes two purely additive, low-risk changes: a small
tutor identity on Home and the Learning screen header, and a "Solve a real
problem" section on Home that opens any of the three scenarios and starts
its Problem Solver in one click.

## Why additive, not a rewrite

`gui.py` is ~2000 lines with dozens of tests that reach into it by exact
widget attribute name (`problem_solver_frame`, `research_entries`,
`start_button`, `manual_context_box`, and more — see
`tests/test_gui_smoke.py`). A broad visual rewrite risks silently breaking
that contract. Every change here either:

- adds a new widget/row that did not previously exist (Home's persona block,
  the "Solve a real problem" `LabelFrame` at `row=4`), or
- restructures strictly *inside* an existing single grid cell (wrapping the
  Learning screen's title in a small `title_row` frame at `row=0, column=0`,
  which does not change any other widget's row number).

No existing widget was renamed, removed, or reparented outside its original
cell. The one flaky test failure seen during verification
(`test_problem_solver_cart_visual_stays_gated_and_local_when_display_is_available`,
an `app.focus_get()` assertion in the unrelated Momentum visual dialog) also
failed to reproduce in isolation and touches code this change never edited,
confirming it as pre-existing OS focus contention, not a regression.

## What was added

- `src/ui_theme.py`: `PersonaMark`/`PersonaName`/`PersonaTagline` label
  styles, a `Badge` label style, a `Highlight.TLabelframe` (accent-bordered
  card) style, and a `Scenario.TButton` style — all new style names, nothing
  existing was redefined.
- `HomeScreen`: a small persona line ("🎓 Hi, I'm your learning companion...")
  above the existing title, and a new `REAL_LIFE_SCENARIO_LAUNCHERS`-driven
  "Solve a real problem" card row with a "Try it" button per scenario. Each
  button calls `start_real_life_scenario(topic)`, which reuses
  `LibraryScreen.open_lesson` (already-tested navigation) and then
  `LearningScreen.start_problem_solver()` — no new controller behavior, only
  a two-call composition of existing screen methods.
- `LearningScreen`: the header title now sits next to the same persona mark,
  purely inside its existing grid cell.

## Verification

`python -m unittest discover -s tests -v` passes at 126/126. Because pixel
screenshots proved unreliable on this shared/active desktop (another
application's window was intermittently captured instead of the app's own),
verification instead drove the real `LearningApp` widget tree the same way
`tests/test_gui_smoke.py` does: constructed a real window, clicked each of
the three "Try it" launchers, and asserted `problem_solver_frame.grid_info()`
is truthy, the active screen is `"learning"`, and the correct first guided
step prompt is shown for each of the three topics (`motion`, `momentum`,
`force`). One clean screenshot was also captured confirming the persona
header and page layout render as designed.
