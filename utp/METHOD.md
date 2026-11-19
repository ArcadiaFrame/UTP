# The UTP method: building a language people will believe

This is how the Vulcan family was built, written down so any language can be built the same way, by a
person, by a model, or by both. Every model prompt in the UTP includes the "For models" section below.

The method has one idea at its centre: **every decision has a reason, and every reason has a source.**
A word is believable when someone who knows the setting can ask "why is it like that?" and get an answer
that points to something: a line of dialogue, a fact about the speakers' bodies or world, a sound law, a
decision the author made on purpose. A word with no answer is a guess, and readers can hear guesses.

## The steps

| Step | What happens | Command | Kept in |
|---|---|---|---|
| 1. Make | The folder, settings, Lab and course | `utp.py new` | `pack.json`, `sound_laws.json` |
| 2. Gather | Sources go into the language's library, each with a tier | `utp.py sources add` | `sources/` (private) |
| 3. Audit | Every word the sources already use, with where it appears | `utp.py audit` | `audit/attested.csv` |
| 4. Decide | The design questions, one at a time, argued from several angles | `utp.py design` | `design/decisions.json`, `DESIGN.md` |
| 5. Sounds | A proto-language and sound laws that produce the attested words | `utp.py sounds` | `sound_laws.json`, `meanings.csv` |
| 6. Grow | Words by topic: built from older words first, new roots only when needed | `utp.py expand`, `apply` | `batches/`, `meanings.csv` |
| 7. Teach | Sentences checked by the grammar, the Lab, the course | `utp.py sentences`, `build` | `course/`, `lab/` |

Steps 2, 3 and 5 are skipped when building from nothing: the library is empty, nothing is attested, and
step 4 asks you instead of citing. With some context they run on whatever you have, and step 4 asks only
about what the sources leave open. You can return to any step later: a new source can add an attested word,
and the sound laws must then explain it too.

## Source tiers

Sources disagree. The tier says which one wins, and every citation carries its tier so a reader can judge.

| Tier | What it is | Weight |
|---|---|---|
| `author` | Your own decisions and notes. Every design decision is filed here automatically. | Overrides everything |
| `canon` | What the setting itself shows: on-screen dialogue, scripts, the official reference works | Must be explained |
| `licensed` | Official but secondary: novels, games, sourcebooks (for Star Trek, the STA books are here) | Followed unless canon contradicts |
| `fan` | Fan-made material: fan dictionaries, fan wikis, fan conlangs (the Vulcan Language Dictionary is here) | Used where it fits, never forced |
| `science` | The real world: linguistics, anthropology, biology, acoustics, ecology | Makes choices plausible |

Canon wins over licensed, licensed over fan, and your decision over all of them. Science is not in that
chain: it answers a different question (could this be so?), not which story is true.

## The angles

Every decision is argued from each angle that bears on it. A good option is one that most angles support;
when they pull apart, the decision says which one won and why.

1. **Canon.** What the sources show. Attested words are fixed points the sound system has to explain.
   A rule may never make an attested word impossible.
2. **Body.** How the speakers make and hear sound: mouth, throat, hearing range, and any channel humans
   lack (Andorian antennae, Vulcan touch telepathy). A body with an extra channel will grammaticalise it.
3. **World.** Climate, terrain, sky, food, danger. The environment decides what needs many words.
4. **Society.** Kinship, rank, sex and gender, law, religion, war, trade. These decide pronouns, honorifics,
   registers and the words that are rude.
5. **History.** Migrations, splits, empires, contact. History decides the branches, the loanwords and the
   old forms frozen in ritual (Vulcan's Ceremonial register).
6. **Sound.** What the attested words already sound like. New words must sound like the same people said them.
7. **Use.** Who will use the language: writers, game masters, players, learners. A table game needs words
   that can be said aloud on the first try; a novel can afford more.

## The design questions

`utp.py design` works through these in order. Each answer goes into `DESIGN.md` and is cited by
every later prompt. Skip any that do not matter for your language.

| Id | Question | Angles |
|---|---|---|
| speakers | Who speaks it, where, and what do they talk about most? | world, society, canon |
| body | How do their bodies make and hear language? Any extra channel? | body, science, canon |
| world | What about their world must the vocabulary be rich in? | world, science |
| history | What split the speakers into branches, and when? | history, canon |
| sound | What should it sound like, given the attested words? | sound, canon, body |
| writing | How is it written? (Romanisation first; a native script later) | history, use |
| grammar | Word order, and what the grammar must mark (evidence, rank, sex, number...) | society, body, canon |
| persons | Pronouns, sexes and genders, kinship terms | society, body, canon |
| registers | Formal, ritual, military, intimate, insulting: which exist and how they differ | society, history |
| numbers | Number base and counting | body, history |
| names | How personal, family and place names are formed | society, canon |
| metaphor | What the culture compares things to, and what it never would; taboos | world, society |

## What every decision records

A decision is never just its answer. It records the question, the options considered, the argument for
each option from each angle, the sources each argument cites, the option chosen, and why. Rejected options
are kept: they explain the language as much as the chosen ones do.

## What every proposed word records

Every word a model proposes records its meaning, part of speech, era, field and register; its parts if it
is built from older words; its basis (the reasoning: which angle, which analogy, which real-world parallel);
and the sources it rests on, by passage id. Nothing joins the dictionary until you approve it.

## What the code checks (so the model cannot drift)

- A cited passage must exist in the library, and an attested word must actually appear in the passage it cites.
- An attested word must be produced by the sound laws from its proto-form, in its branch (check E6).
- A built word must be made of words that exist and are no newer than it.
- No meaning twice, no spelling twice in a branch, no two words that sound the same.
- A course sentence must be rendered by the grammar and read back to the same meaning.

## For models

You are helping build a constructed language by the UTP method. Follow these rules in every answer.

- Ground every claim. When the library gives you passages, cite them by their ids (like `S3.2`). When
  nothing in the library supports a choice, say so plainly and mark it as invention.
- Respect the tiers: author decisions override canon; canon overrides licensed; licensed overrides fan.
  Never contradict an author decision in DESIGN.md. Science makes a choice plausible; it never overrides canon.
- Attested words are fixed. Never respell them, never give them a different meaning than their sources do,
  and never propose a rule or a word that makes one impossible.
- Argue from the angles: canon, body, world, society, history, sound, use. Name the angle in your reasoning.
- Build before you invent: a new meaning is a compound or derivation of older words when a sensible one
  exists; a new root only when the culture would name the thing on its own.
- Prefer what this culture would say over what English says. A gloss is a label, not a translation.
- Keep it sayable: words a player can read aloud at a table on the first try, unless the design says otherwise.
- Answer in the JSON shape the request asks for, and nothing else.
