# V2.11 research feedback placement decisions

## Problem observed

Go Deeper originally rendered every research check-in message in one label at
the bottom of the full research form. On a compact window, a learner could
submit an empty hypothesis, remain at the hypothesis field, and never see the
reason the check-in was rejected because the message was below the fold.

## Decision

Each research stage now owns a small feedback label directly below its own
multi-line editor. Only the most recent stage message is shown, which avoids
repeating the same generic wording across a long form.

For a retry, the interface keeps focus in the editable field and then scrolls
the local feedback label into view. After a successful check-in it moves to
the next unlocked field. After the final reflection it brings the final local
message into view.

## Boundaries retained

The feedback only repeats the controller's honest, deterministic status. It
does not analyse or retain student writing, change the guided-order rule, or
write raw text to local progress storage. The existing response trail remains
available as a history of app messages; the local label makes the immediate
next action clear.

## Verification

The real-Tk compact-window smoke test submits an empty hypothesis, verifies
that its feedback label is mapped and fully visible, and verifies that focus
stays in the hypothesis editor. It then continues through the normal local
writing and privacy checks.
