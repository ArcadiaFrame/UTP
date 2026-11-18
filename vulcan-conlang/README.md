# Vulcan language family: start here

A complete, historically layered Vulcan language built from canon: Proto-Vulcan → Classical and Ceremonial → Unified → Federation Standard Vulcan, with Romulan splitting away at the Sundering. Sound laws derive every form, a checker prevents duplicates, and every sentence in these files renders from the dictionary.

**Status:** 3,645 dictionary entries, 0 errors. Batch 24 added the body, physiology and clinical medicine; its eight proposed roots await approval.
- A 306-line phrasebook in 29 scenes, plus three sets of sayings and the tale formulas.
- Three tales and lessons 1 to 8.
- An interactive course: Foundations, Conversation and the first Literary units.
- Guides to grammar, pronunciation, registers, the emotive layer, telepathy, post-Surak culture, social life and rank, and style.

**Spelling update (audit, 18 Nov 2026).** Words heard on screen now use their screen spelling:
- *kroykah*, *Kolinahr*, *kahs-wan*, *k'oh-nar*, *sahrafel*, *sarlah*, *nahp*, *eh*
- the person word *-veh* (*nash-veh*, *ish-veh*, *vo-veh*)

Seventeen VLD and fandom words were added as variants, among them *ashayam*, *k'diwa*, *taluhk*, *adun* and *adun'a*, and *sa-mekh*. All guides, the phrasebook and the course plan were re-rendered on 18 Nov with the new spellings; the published Lab and course pages pick them up at their next republish. When anything disagrees, **the dictionary wins**. See `analysis/audit-canon-fandom.md` and the changelog.

**Spelling spec (18 Nov 2026).** `docs/orthography.md` and `docs/morphology.md` now define how Vulcan is spelled and how words are built; the checker enforces the hyphen-versus-fusion rule. 23 more forms changed, among them *-auuth* → *-auth* (*sekauth*), *fest'au* and *shekahol* "stillness".

## Which file to open

| You want to… | Open |
|---|---|
| Spell, punctuate or write Vulcan (letters, hyphens, capitals, the native script and its direction) | `docs/orthography.md` |
| Build or split a word (every ending, prefix and particle, what it attaches to, joining rules) | `docs/morphology.md` |
| Look up a word (Vulcan → English) | `docs/dictionary-vulcan-english.md` |
| Find the Vulcan for an English word | `docs/dictionary-english-vulcan.md` |
| Look up a Romulan word | `docs/dictionary-romulan.md` (Romulan-only words); every Vulcan entry also lists its inherited Romulan form |
| Use ready-made lines and scenes | `docs/phrasebook.md` |
| Write about melds and touch telepathy | `docs/telepathy.md` (channels, grades, acts, lost words) |
| Find body, sex, insult and slang words by register and era | `docs/registers.md` |
| Write romance, flirting or a quarrel, in any era | `docs/emotive.md` (emotive endings and their fates; frank vs reserved words). The fandom endearments (*ashayam*, *k'diwa*, *taluhk*, *tal-kam*) are in the dictionary as intimate variants |
| Write hospitality, confiding and courting, life between bondmates, desert survival, the war-Houses or a martial school | `docs/social-life.md` (the heart-whisper, life in the bond, the water-first, survival craft, rank in the Houses and the training hall, sayings) |
| Tell a Vulcan story, or have a character tell one | `docs/tales.md` (the tale form from canon, and three tales with English: the sehlat who ate its tail, Falor's Journey, the kahs-wan) |
| Write the body, medicine, pon farr and plak tow clinically (anatomy, blood, breath, reproduction, the fever threshold, the healer's link) | `docs/anatomy.md` |
| Write meditation, Surakian sayings, or the 22nd-century High Command | `docs/after-surak.md` (contemplative terms, the code of conduct, sayings, surveillance words, the sanctioned-speech particle) |
| Write or translate Vulcan in fiction | `docs/style-guide.md` (voice by character, glossing, untranslatables, workflow) |
| Learn the language step by step | `docs/lessons.md` (lessons with practice and answers), or the Vuhlkansu Course (link below): units, review, progress saved; see `course/README.md` |
| Learn the grammar | `docs/grammar.md` (full reference, every example checked) |
| Pronounce it | `docs/pronunciation.md` |
| Understand how words are built | `docs/word-building.md` |
| Know which words fit which period | `docs/timeline.md` |
| Check what is canon, novel, VLD or fandom, and how each was handled | `analysis/audit-canon-fandom.md`; `analysis/respelled.csv` lists every form the audit changed |
| Read the full grammar, culture analysis and Romulan grammar | the Design Bible (link below): Grammar, Culture and speech, Romulan tabs |
| Gloss or check a sentence interactively | the Vuhlkansu Lab (link below): Glosser with a Vulcan/Romulan switch |
| See what changed and why | `lexicon/changelog.md` |

The three pages below are published as private claude.ai artifacts; the Lab and the course can be rebuilt from this folder (`tools/build_lab.py`, `tools/build_course.py`).

- Design Bible: https://claude.ai/artifact/Woh7FBsenuP2bJgt7Y2uEz
- Vuhlkansu Lab: https://claude.ai/artifact/2Wd6qXGw3CkTiqGonA3y2Z
- Vuhlkansu Course: https://claude.ai/artifact/S7cevZEhPpjeXKhvGaAsZh

## Grammar on one card

- **Word order:** subject, object, verb, with the evidential last. *Shelek tanfi sarlah-un ho.* "The ship came here (I saw it)."
- **Question words come first.** For a yes-or-no question, move the auxiliary to the front or open with *kuth*.
- **No verb "to be"** in descriptions; *wim* is used for identity.
- **Endings:**
  - nouns: *-k'oo* plural, *-wizh* object (on the last word of the object phrase), *-fi* toward
  - verbs: *-pil* ongoing, *-un* past, *ki'-* completed, *dungi* future
- **Evidentials:** *ho* seen, *aukh* inferred, *k'en* reported, *tekh* known by touch. In Standard Vulcan, stating someone else's feeling needs one.
- **Speech levels:** *-mush* honorific, *-fum* humble, *ihk-veh* "you (honored)", *suh* formal. Between t'hy'la there are no honorifics at all.
- **Feeling, by era:** Classical says *Nash-veh skukh!* "I rage!" Standard says *Sik tok nash-veh kon.* "There is anger in me. Noted."
- **Romulan:** mode endings *-'nra* (to a superior) and *-ha* (to an inferior), the copula *aihr-*, and no evidentials; *hwil* marks "not to be repeated."

## Using the language in fiction

- **Italicize Vulcan** in prose. Gloss a word the first time it appears, through the narration or context rather than brackets, and leave it bare after that.
- **Use the dictionary form exactly.**
  - On-screen words keep their screen spelling (*kroykah*, *sahrafel*, *nash-veh*).
  - Novel and RPG words use the house spelling, and each entry's notes give the published spelling (*kthia* for Duane's *cthia*).
  - A word's screen *h* drops before a vowel ending: *sarlah*, but *sarlauth* "coming".
- **Fandom words** (VLD, Jean Lorrah) are variants with an era and register. *Ashayam* is intimate Classical, so a Standard Vulcan says it only to a bondmate, and *lok* is slang. Canon-built words stay the default.
- **Match the era and register.** The timeline says which words a character would know. Ceremonial forms belong in rites, archaic forms in quotation, and Standard in daily speech.
- **Untranslatables** (t'hy'la, katra, k'oh-nar, mnhei'sahe and others) are explained in the bible's concepts and should not be forced into a single English word.
- **Canon terms belong to Paramount.** This is fine for fan fiction; for publication outside fan works, use the original coinages, which are yours.

## For AI assistants (Claude, local models)

When asked to translate, write Vulcan or Romulan, or teach the language:

1. Look up every word in the dictionary files before using it. Never invent a Vulcan word silently.
2. If a word is missing, say so. Offer a form built from existing pieces by the rules in `docs/word-building.md`, label it "proposed," and suggest adding it to the dictionary.
3. Follow the grammar card above and the bible's Grammar tab, keeping the character's era and register.
4. For fiction, give the Vulcan line, a literal gloss, and a natural English rendering.
5. Do not edit the files in `docs/`: they are generated. Changes go through `lexicon/meanings.csv` or `tools/derivation.py` and a rebuild.

Paste this into a chat project's custom instructions so every chat follows it (for local models, see `utp/LLM-INSTRUCTIONS.md`):

> For anything in Vulcan or Romulan, use the vulcan-conlang files in https://github.com/ArcadiaFrame/utp. Start with vulcan-conlang/README.md, look up every word in the dictionary files, never invent a word silently (propose it, labeled), follow the grammar card and the character's era and register, and give Vulcan, a literal gloss and natural English.

## How the files are built

| File | Role |
|---|---|
| `corpus/` | Sources: canon, novels, Romulan, concepts, idioms, interlinear, phrasebook and examples (as templates) |
| `tools/rules.json`, `tools/sca.py` | Sound laws for each branch, with test cases |
| `lexicon/meanings.csv` | Build input: the list of meanings, with English labels as IDs only. The Vulcan forms are not made from the English. Screen and fandom spellings are logged in its `exception` column |
| `tools/derivation.py`, `lexicon/derivations.csv` | Which meanings are built from older words, and why (canon pattern, anthropology, Latin and Japanese cross-checks); later batches add rows to the CSV |
| `tools/lexicon.py` | Generator and checker: `build` makes `lexicon/lexicon.csv`; checks E1–E12 refuse duplicates, sound-alikes, bad shapes and era errors |
| `tools/export.py` | Writes everything in `docs/` from the dictionary |
| `tools/build_lab.py` | Builds the Lab page |

Rebuild order: `python3 tools/derivation.py`, then `python3 tools/lexicon.py build`, `python3 tools/export.py`, `python3 tools/build_lab.py` and `python3 tools/build_course.py`.
