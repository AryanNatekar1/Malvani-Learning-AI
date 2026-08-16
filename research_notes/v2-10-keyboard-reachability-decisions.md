# V2.10 keyboard reachability decisions

## Problem observed

At the supported compact `800x600` window size, Home's **Start Learning**
button could receive keyboard focus while still sitting below the visible page
area. A keyboard learner could tab to a control without seeing where they had
landed.

The project already had `ScrollableScreen.scroll_widget_into_view()` for a
learner who explicitly opened Problem Solver or Go Deeper. V2.10 reuses that
same geometry helper when an ordinary page descendant receives focus.

## Interaction boundary

The behavior scrolls the current page only after the operating system/Tk has
already assigned focus. It does not force focus, alter tab order, animate, or
move a learner between controls. Nested lesson-card scroll areas remain
excluded so the outer viewport cannot compete with their independent scroll
area.

## Multiline writing boundary

Go Deeper's `tk.Text` fields are genuine editing controls. Binding the outer
page mouse wheel directly to them prevented native scrolling when a student
wrote more than three lines. V2.10 leaves their wheel handling alone while
still applying the focus-to-view behavior. This keeps longer private writing
reviewable on screen and does not change the no-persistence rule.

## Verification

The GUI smoke test creates the real desktop interface at `800x600`, verifies
that Home's primary action begins off-screen, focuses it, and verifies that it
becomes visible. It also asserts that a research `Text` field receives the
focus behavior but not the outer page wheel binding.
