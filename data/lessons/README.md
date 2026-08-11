# Structured lessons

Each JSON file in this folder is an editable lesson record. The app uses
Python's standard-library JSON reader, so no additional package is required.

## Required fields

```json
{
  "id": "subject.topic",
  "title": "Student-facing title",
  "subject": "Physics",
  "topic": "topic",
  "levels": ["Class 8"],
  "content": {
    "English": {
      "simple_explanation": "...",
      "detailed_explanation": "..."
    }
  },
  "language_metadata": {
    "English": {
      "verification_status": "NEEDS_REVIEW",
      "source": null
    }
  }
}
```

`English` is required as an honest fallback until a reviewed translation is
available. Every language in `content` also needs matching
`language_metadata` with a verification status and source where appropriate.
Optional fields currently supported include `aliases`,
`everyday_example`, `real_world_use`, `think_question`, `challenge`,
`quiz_questions`, `career_connections`, `further_exploration`, sources, and
verification status.

## Cultural context

Use `local_example` or `culture_connection` only with:

- `text`
- `region`
- `source`
- `verification_status`
- `appropriate_usage`

Only a source-backed `VERIFIED` entry can appear in the student UI. Drafts can
be stored for review, but the app hides their claims.

## Before adding a translation

Do not label text as Marathi or Malvani until it has been reviewed by an
appropriate speaker and, ideally, a teacher. The language engine will visibly
fall back to English rather than invent content.
