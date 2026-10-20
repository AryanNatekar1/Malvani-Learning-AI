# Lesson drafts

Machine-assembled drafts land here. **Nothing in this folder reaches a
student.** The app's lesson loader only reads `data/lessons/`, so a file here
is invisible to both the desktop app and the website no matter what it says.

That separation is the point. A draft is assembled by searching and copying
sentences from sources — it is not a lesson, and the only thing standing
between the two is a person.

## Making one

```powershell
py scripts/draft_lesson.py "dispersion of light" --subject Physics
```

Add `--dry-run` to see it without writing, or `--language Marathi` to read
Marathi Wikipedia instead.

## Turning a draft into a lesson

A draft is deliberately incomplete. It carries an explanation and its sources,
and nothing else, because the missing parts are the ones that need a teacher's
judgement rather than a search result.

1. **Read every sentence.** They were copied from articles written for adults,
   possibly about a different sense of the word. The pipeline cannot tell that
   an article about optical fibre is the wrong kind of dispersion for a Class 9
   student; you can.
2. **Check `claims_dropped_as_unsupported`.** These are the sentences a source
   did not back. They are worth reading: they show what the generator was
   willing to assert without evidence.
3. **Check the suggested places.** They were matched by overlapping words, not
   chosen by anyone. Delete the ones that are not a real connection.
4. **Write the parts no machine wrote**: a think question, a challenge with
   progressive hints, quiz questions, misconceptions students actually hold,
   and a *Look around you* activity that needs nothing anyone has to buy.
5. **Add a diagram** in `CONCEPT_VISUALS` in `index.html`, with a text
   alternative. A test fails if a lesson has no diagram.
6. **Register the file** in `LESSON_FILES` in `index.html` and in the
   `PRECACHE` list in `sw.js`. A test fails if you forget either.
7. **Move it** to `data/lessons/<subject>/` and run the tests.

`verification_status` stays `NEEDS_REVIEW` until a teacher has genuinely
checked the content. The field is not a formality — it is what the app reads
when deciding what a student may be shown as fact.

## Why drafts are kept rather than deleted

Reviewing one in a pull request leaves a record of what was changed and by
whom, which is worth more than a tidy folder. A draft nobody has got to yet is
not clutter; it is a queue.
