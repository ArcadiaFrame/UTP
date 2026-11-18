# Vuhlkansu Course

A Duolingo-style course in Federation Standard Vulcan, published as an artifact:
https://claude.ai/artifact/S7cevZEhPpjeXKhvGaAsZh

## How it is built

- `corpus/course.json` is the course plan: levels, units (3 to 9 items each, words before phrases before sentences), spot-the-mistake drills, and stories. A unit names its source with `lesson` (Foundations, from `docs/lessons.md`) or `from` (Conversation, from a Phrasebook scene). Every Vulcan form is a `{key}` template.
- `tools/build_course.py` renders the templates from `lexicon/lexicon.csv`, works out syllables, stress, IPA, sound features, word tiles and fill-the-gap variants, and writes `course/vuhlkansu-course.html` from `tools/course.template.html`. It stops on any unknown key.
- Rebuild after any lexicon or course change, then republish the page to the same URL. Item ids are a hash of each template, so progress survives reordering units; only rewriting an item's template starts that item fresh.

## Exercises

Learn card, read-aloud check (self-graded against syllables and IPA), meaning and reverse multiple choice, typed recall, word-tile sentence building, fill the gap (endings and evidentials), spot the mistake, and stories with comprehension questions.

## Progress

Each learner's progress is one document in the artifact's database: collection `learners`, document id = the learner's user id. It is mirrored in the browser. Fields:

- `items`: per item id, `b` (review box 1-5), `due` (date), `r`/`w` (right and missed counts), `first`, `last`
- `sounds`: per item id, read-aloud self-grades (`ok`, `miss`)
- `units`: completed units with date and best score; `stories`: stories read
- `days`: days practised (for the streak); `sessions`: the last 60 sessions with scores

Review boxes wait 1, 3, 7, 16 and 35 days. A miss drops an item to box 1.

To run a lesson or progress check in chat, read `learners` with ArtifactData and match item ids to `course.json` by rebuilding the data, or by the rendered forms in the page.

## Growing it

Levels: Foundations (18 units, lessons 1 to 8), Conversation (9 units from the Batch 21 and 22 scenes) and the first two Literary and Ceremonial units (tales, from `docs/tales.md`) are open. Academy is planned. Add units to `course.json` with `"level"` set, rebuild, republish. Before republishing, run every course sentence through the Lab glosser (`phraseKnown`); all should be understood.
