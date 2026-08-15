# Contextual Learning Engine: first safe increment

## Purpose

The long-term goal is to help a student connect an academic concept with a
real, relevant setting and then reason through a problem. The engine must not
turn a location guess into a fact. Its role is to provide only reviewed,
topic-matched context to the existing teaching flow.

```text
Manual learner choice
    -> reviewed context repository
    -> topic match
    -> teaching response
    -> think / try / hint / retry
```

## What V2.4 implements

- Local JSON context records in `data/contexts/`.
- Manual selection only; no GPS, maps, network requests, device sensors, or
  reverse geocoding.
- A selection exists only in the running application. It is not placed in the
  student profile or learning-event database.
- A record must be `VERIFIED` and have a source before it can be shown.
- A record must explicitly list the lesson topics for which it is useful.
- The controller adds a `MANUAL LEARNING CONTEXT` section only to the complete
  response for a matching structured lesson.

No reviewed records ship with the project yet. Therefore the normal lesson
experience is unchanged for students until a suitable reviewer approves data.

## Why this is separate from culture data

`ContextEntry` in a lesson describes a regional or cultural claim. The new
`ContextRecord` describes an optional, independently reviewed learning setting
and its allowed lesson topics. Keeping them separate prevents a broad region
or a selected setting from being silently treated as a cultural fact.

## Reviewer checklist before adding a record

1. Identify the exact factual claim, if any.
2. Record a traceable source and an appropriate reviewer.
3. Confirm the setting genuinely helps the named lesson topic.
4. Write an educational prompt that does not imply a student's exact location.
5. Consider safety: an activity must have an observation, image, or imagined
   alternative; it must not instruct a student to approach water, traffic, or
   another hazard.
6. Mark the record `VERIFIED` only after review. Otherwise leave it out of the
   student-facing context directory.

## Planned first contextual lesson

The proposed first full demonstration is a reviewed Waves lesson with an
optional manually chosen water-surface setting. It should use wording such as
“Imagine ripples on a water surface” unless a specific local observation is
verified. The lesson can then follow:

```text
Context -> concept -> prediction -> calculation -> hint/retry
        -> application -> research question -> reflection
```

This requires a reviewed Waves lesson and a reviewed context record; neither
should be fabricated merely to make the feature appear populated.

## Future boundaries

Device location, live maps, environmental sensors, external AI, and a
Researcher-mode workflow are later increments. Each must preserve the same
source gate, explicit consent, data minimisation, offline fallback, and
student-safe error behavior.
