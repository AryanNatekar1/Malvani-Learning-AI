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
