# Writing Vulcan: script, direction, spelling and punctuation

This is the spec for how Vulcan is written, both in its own script and in the romanization that every project file uses. With `docs/morphology.md` (how words are built) and `docs/grammar.md` (how sentences are built), it makes the language operable: from these three, a writer can spell, divide, read aloud and punctuate any word or sentence the same way the dictionary does.

What is canon:
- the Vulcan script exists, built on a **central staff with spirals, long and short dashes, and dots** along it (ENT "The Seventh");
- the screen spellings of spoken words.

Everything else is design, marked as such.

## 1. The native script (design)

**Form.** Each word is a run of marks set along a single staff line. The staff is continuous through a word and broken between words. Marks on one side of the staff are consonants and marks on the other side are vowels, so a reader can tell syllable shape at a glance. Spirals mark the four evidentials and the sentence end, which is why the canon script looks so curled at the end of a line.

**Direction by era.** The script's direction changed with Vulcan history. This gives writers period detail, and gives a fictional archaeologist something to read.

| Era | Medium | Direction |
|---|---|---|
| Tribal | cut stone, cairns, cave walls | **from the center outward in a spiral**. The oldest ritual stones are read by turning around them |
| Classical | ink on scroll, carved lintels | **vertical columns, top to bottom; columns run right to left**. The staff is upright, the text falls like water from a spring |
| Unified (Surak) | scroll, the Kir'Shara | same vertical layout. Surak's reform standardized the mark shapes and the evidential spirals, so a Surakian text can be checked for how each claim is known |
| Standard | screens, technical records | **horizontal, left to right, lines top to bottom**, adopted for computing and Federation exchange; vertical layout remains for ceremony, literature, inscriptions and signatures |
| Romulan | separate canon script | the Romulan script diverged after the Sundering and is not a variant of this one |

*Design note:* this mirrors Japanese *tategaki* and *yokogaki* (vertical traditional and horizontal technical writing side by side), one of the project's three cross-checks. A Standard Vulcan reads both without effort; a Human used to one finds the other hard.

## 2. Romanization: the letters

Romanized Vulcan uses the Latin alphabet with a fixed value for every letter or letter pair. A pair is always one sound.

| Written | Sound | Example |
|---|---|---|
| a e i o u | a as in *father*; e as in *bet*; i as in *machine*; o as in *more*; u as in *rule* | *{sand}* |
| uh | the relaxed vowel of *sofa* | *{pain}* |
| ee, oo, aa | long *i*, *u*, *a* | *{plomeek}*, *{koon}* |
| ai, au, ei, ae, oi | diphthongs: *eye*, *ow*, *ay*, *eh-eh*, *oy* | *{kau}*, *{teach}* |
| kh | the *ch* of Scottish *loch* | *{good}* |
| sh, zh | *sh*; the *s* of *measure* | *{eat}* |
| th | *th* of *thin* | *{who}* |
| lh | a breathy *l*, Welsh *ll* | (Romulan especially) |
| ch | *ch* of *church* | *{thanks}* |
| ' (apostrophe) | the glottal catch, as in *uh-oh* | *{know}*, *{t'hy'la}* |
| y | *y* before or after a vowel; between consonants, the vowel *ɨ* (canon *t'hy'la*) | |

Full pronunciation and stress: `docs/pronunciation.md`.

## 3. Spelling rules

1. **One spelling per word.** The dictionary form is the spelling, and the checker guarantees that no two meanings share one.
2. **House spelling** for designed, generated and novel words. The sound laws write vowel length with doubled vowels and drop the vowel-lengthening *h* (*kthia*, not Duane's *cthia*). Each entry's notes give the published spelling.
3. **Screen spelling** for words heard on screen, kept as logged exceptions: *{kroika}*, *{kolinahr}*, *{kaswan}*, *{k'onar}*, *{trust}*, *{come}*, *{nap}*, *{e}*, the person word *{ve}* (*{nash-ve}*, *{ish-ve}*). Words built on them keep the screen spelling.
4. **The length-*h* drops before a fused vowel ending:** *{come}* + *-{action}* is *{come-act}*; *{ve}* + *-{abstract}* in *{loneliness}*. The vowel *uh* is not a length mark and never drops.
5. **A diphthong absorbs a like vowel** at a fused join: *{dress}* + *-{action}* is *{dress-act}*, not *-auuth*. Full joining rules: `docs/morphology.md` §7.
6. **Fandom words** (VLD, Jean Lorrah) keep the spelling fans use, logged as exceptions: *{ashayam}*, *{k'diwa}*, *{sa-mekh}*.
7. **Romulan** has its own spelling tradition (Diane Duane's): doubled consonants, *fv*, *hw*, *rrh*. Never respell Romulan into Vulcan spelling, or the reverse.

## 4. Hyphens, fusion and spaces

The hyphen is part of the spelling, not decoration. One rule decides it, and the checker enforces it (E12).

| Joined how | What | Examples |
|---|---|---|
| **Fused** (no hyphen) | word-building endings: *-{action}* act, *-{abstract}* quality, *-{adjectival}* having, *-{participle-ik}* participle, *-{adverbial}* manner, *-{place-suf}* place, *-{instrument}* instrument, *-{collective}* collective, *-{ordinal}* ordinal, *-{causative}* causative, *-{indef}* some-, *-{univ}* every-, *-{toward}* toward | *{school}*, *{learning}*, *{logical}*, *{frighten}* |
| **Hyphen** | bound words (*{ve}* one, *{kam}* little, *{tor}* make, *{kau}* joined, *-{endear}*, *-{pejorative}*); grammatical endings in a sentence (*-{past-un}*, *-{ongoing}*, *-{object-wizh}*, *-{plural}*, *-{honorific}*, *-{humble}*); prefixes (*{without}-*, *{again}-*, *{before}-*, *{in}-*); compound members | *{healer}*, *{pebble}*, *{return}*, *{come}-{past-un}* |
| **Joined, apostrophe kept** | the completed-action prefix *{perfect-ki}* | *{perfect-ki}{come}* |
| **Space** | separate words, and the *mik t'*X fields of study, where *t'* is the old "of" | *{science}*, *{philosophy}* |

A reader can therefore split any word: a hyphen marks a word boundary or a grammatical ending; a fused ending always belongs to word-building.

## 5. Capitals

- Capitalize the first word of a sentence and every name.
- **Name prefixes:** *T'* (women) and *S* (men's names commonly begin with it) are part of the name: *T'Pring*, *Sarek*. In Romulan, *t'* and *tr'* (daughter and son of a House) are written lower-case before the House name: *Ael i-Mhiessan t'Rllaillieu*.
- Titles and kin words are lower-case unless they open a sentence: *{vocative} {healer}*.

## 6. Punctuation

**In romanization:**

| Mark | Use |
|---|---|
| **.** | ends a statement. The evidential, when there is one, is the last word before it: *{ship} {here}{toward} {come}-{past-un} {ev-seen}.* |
| **?** | ends a question. Yes-or-no questions also open with *{question}* or a fronted auxiliary, so the mark confirms what the grammar already shows |
| **!** | exclamations and commands under strain; Standard speech uses it rarely, and Classical lines freely |
| **,** | after a fronted time phrase or a clause that comes first (*{if} …*), in lists, and before an address: *{vocative} {healer}, …* |
| **:** | before what is announced or said in a list: *{signal}-{object-wizh} {send}: …* |
| **" "** | quoted speech in English prose around Vulcan. Inside Vulcan, *{comp}* opens reported content and the verb of saying closes it, so quotation marks are optional |
| **…** | a trailing or deliberately withheld thought |
| **( )** | a gloss or translation in fiction, never inside Vulcan itself |

**In the native script (design):** there are no commas or full stops as separate marks. A clause ends where the staff breaks with a short stroke; a sentence ends with a spiral; the evidential spiral doubles as the sentence end, so a Surakian sentence closes on how its claim is known. A question bends the final spiral back on itself. Ceremonial texts mark each verse with a dot either side of the staff.

## 7. Numbers in writing

- In prose, write numbers as words: *{ship}-{plural} {twenty}*. The system is base ten and regular: ten-one is eleven, two-ten is twenty.
- In technical writing, use numerals.
- The number follows the noun it counts.
- The full number system is completed in the number batch (multiplicatives, distributives, collectives, decimals). That batch also decides whether a second, ritual count exists beside base ten.

## 8. A worked example

*{ish-ve} {come}-{past-un} {ev-reported}.* "He came (I was told)."
- *{ish-ve}*: screen spelling, the person word with a hyphen.
- *{come}-{past-un}*: verb, then the past ending, after a hyphen.
- *{ev-reported}*: the evidential, the last word before the full stop.
- In the native script: two words on the staff, then the "reported" spiral closing the sentence.
