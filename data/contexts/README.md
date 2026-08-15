# Reviewed learning contexts

This folder is for optional, manually selected learning contexts. It is **not**
a GPS database and it must not contain a student's location, school name,
address, route, or sensor reading.

The desktop app currently reads these files only from the local computer. It
does not use a network, device location, or sensors. A selected context lasts
only for the open application session and is not written to the student
profile or learning-event database.

## Student-display rule

Only a context with both of these values may appear in the student interface:

- `"verification_status": "VERIFIED"`
- a non-empty `"source"`

Draft, community-provided, unavailable, unknown, or unsourced records are
kept out of the student interface. Do not mark a record `VERIFIED` merely
because it sounds plausible. A teacher, community reviewer, or other
appropriate reviewer must confirm both the factual claim and its educational
use.

## JSON record shape

```json
{
  "id": "short-unique-id",
  "title": "Student-facing title",
  "category": "environment",
  "educational_prompt": "An approved prompt that explains how this setting helps with a lesson.",
  "topics": ["waves"],
  "verification_status": "VERIFIED",
  "source": "A traceable reviewable source",
  "region": "Optional broad region"
}
```

`topics` is required. A context is rendered only for a lesson whose topic is
listed there; a water-related context must never be injected into an unrelated
lesson just because it is selected.

No reviewed records are installed yet. That is intentional: the app continues
with its normal lesson examples until a source-backed record is approved.
