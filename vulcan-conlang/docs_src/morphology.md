# How Vulcan words are built: the morphology spec

This is the reference for every piece that builds or bends a Vulcan word: what it does, what it attaches to, how it joins and when it entered the language. `docs/word-building.md` explains *why* a meaning is a root or a built word; this file is the rulebook for *how*. The checker enforces the joining rule (E12) and flags unusual attachments for review (W3).

Status: @STATS@

## 1. The shape of a Vulcan word

A word is a **root**, optionally with **prefixes** before it and **endings** after it, in this order:

> prefix – ROOT – word-building ending(s) – grammatical ending(s)

*{without}-{teach}{participle-ik}-{meld}-{ve}* "untrained melder" = without – teach – *-ik* (participle) – meld – one.

**Compounds** join two or more roots. Each member stands after a hyphen. In a compound **the modifier comes first and the head last**: *{starfleet}* is a "star-fleet", a kind of fleet; *{school}* is a learning-place. This is the reverse of the **noun phrase**, where the head comes first and its describers follow: *{house} {old} {my}* "my old house". Persian and Japanese show similar splits between word-building and phrase order. The rule of thumb: inside a word, the last part names what it is; inside a phrase, the first word does.

## 2. Word-building endings (fused, no hyphen)

| Ending | Makes | Attaches to | Example | Era |
|---|---|---|---|---|
| -{action} | the act or its outcome | verbs (and verb compounds) | *{learn}* → *{learning}* | Classical |
| -{abstract} | the quality or state | adjectives, nouns, stative verbs (can, must, master) | *{strong}* → *{strength}* | Classical |
| -{adjectival} | having, characterized by | nouns, verbs, other words | *{danger}* → *{dangerous}* | Classical |
| -{participle-ik} | participle: done, having undergone | verbs; on a noun, "marked by" (as English *talented*) | *{carve}* → *{carved}*; *{koon}* → *{bonded}* | Tribal |
| -{adverbial} | manner adverb | adjectives | *{clear}* → *{clearly}* | Classical |
| -{place-suf} | place where it is done or kept | verbs, nouns | *{learn}* → *{school}* | Classical |
| -{instrument} | instrument, device | verbs, nouns | *{scan}* → *{scanner}* | Classical |
| -{collective} | a body or group of | nouns | *{word}* → *{sentence-g}* | Classical |
| -{ordinal} | ordinal number | numbers | *{three}* → *{third-o}* | Classical |
| -{causative} | make someone do or feel | verbs, emotion nouns | *{joy}* → *{gladden}*; *{dread}* → *{frighten}* | Tribal |
| -{indef} | some- | question words | *{who}* → *{someone}* | Classical |
| -{univ} | every- | question words | *{who}* → *{everyone}* | Classical |
| -{toward} | toward | nouns, places, names | *{home}* → *{homeward}* | Classical |

Endings stack in this order: participle or causative first, then quality or act: *{without}-{teach}{participle-ik}*, *{frighten-act}*.

## 3. Bound words (always after a hyphen)

| Piece | Meaning | Example |
|---|---|---|
| {ve} | one, person (canon *ish-veh*) | *{vo}* → *{healer}*; *{learn}* → *{student}* |
| {kam} | little, dear (canon *Saavik-kam*) | *{stone}* → *{pebble}* |
| {tor} | make, do (canon *dif-tor*, *fal-tor-pan*) | *{name}* → *{name-v}* |
| {kau} | joined, together (canon *kashkau*) | *{hand}* → *{spar}* |
| -{endear} | endearment, dear (Classical, now intimate) | *{heart}* → *{sweetheart}* |
| -{pejorative} | wretched, contemptible (Classical, now coarse) | *{nirak}-{pejorative}* |

## 4. Prefixes (hyphen) and *ki'* (joined)

| Prefix | Meaning | Example |
|---|---|---|
| {without}- | without, un-, -less | *{without}-{pain}* "painless" |
| {again}- | again, re- | *{return}* "again-come" |
| {before}- | before, fore- | *{predict}* "fore-say" |
| {in}- | in, inner | *{inner-wall}* |
| {outside}- | out, outer | *{escape-route}* |
| {with}- | with, co- | *{compassion}* |
| {perfect-ki} (joined) | completed action: has done | *{perfect-ki}{come}* "it has come" (canon *ki'sarlah*) |

## 5. Grammatical endings in a sentence (hyphen)

| Ending | On | Meaning |
|---|---|---|
| -{plural} | nouns | plural |
| -{object-wizh} | the last word of the object phrase | definite object |
| -{them-bi} | verbs | it, them (object attached to the verb) |
| -{past-un} | verbs | past |
| -{ongoing} | verbs | ongoing: is doing, was doing (before -{past-un}) |
| -{honorific} / -{humble} | verbs | raises the other / lowers oneself |
| -{emphatic}, -{desiderative} | verbs | utterly; would that I could (Classical; now strained or poetic) |

Order on a verb: root – -{ongoing} – -{past-un} – -{honorific} or -{humble}.

## 6. Particles (separate words)

| Position | Particles |
|---|---|
| **Before a noun** (prepositions) | *{in}* in, *{from}* from, *{with}* with, *{without}* without, *{before}* before, *{after}* after, *{through}* through, *{between}* between, *{under}* under, *{above}* above, *{inside}* inside, *{outside}* outside, *{up}* up, *{down}* down, *{around}* around, *{across}* across, *{away}* away, *{front}* in front of, *{behind}* behind, *{than}* than (after the thing compared against) |
| **Before the verb** | *{dungi}* will, *{not}* not, *{must}* must, *{may}* may, *{should}* should, *{would}* would, *{hortative}* let us |
| **Opening the sentence** | *{question}* yes-or-no question, *{request}* please, *{vocative}* respected (before a title), *{exclamative}* how…! |
| **Closing the sentence** | evidentials *{ev-seen}* seen, *{ev-inferred}* concluded, *{ev-reported}* told, *{ev-melded}* known by touch; *{noting}* noted; *{formal}* formal; *{sanctioned}* sanctioned (22nd century); Classical *{tag-agree}*, *{dare}*, *{coax}* |
| **Joining clauses** | *{e}* and (*{and-cer}* liturgical), *{or}* or, *{but}* but, *{therefore}* therefore, *{because}* because, *{so-that}* so that, *{if}* if, *{while}* while, *{until}* until, *{although}* although, *{comp}* that (reported), *{relative}* who, which |
| **Linking nouns** | *{t'}* of (old possessive; the female name prefix), *{i}* of the (in compounds) |

## 7. Sound changes when pieces join

1. **Length-*h* drop:** a screen spelling's final vowel-*h* drops before a fused ending that begins with a vowel or *h*: *{come}* → *{come-act}*.
2. **A diphthong absorbs a like vowel:** after *au*, *ei*, *ai* or *oi*, an ending that begins with the same vowel loses it: *{dress}* + *-{action}* is *{dress-act}*; *{teach}* + *-{participle-ik}* is *{trained}*. After a plain vowel, a doubled vowel stays and is read long: *{work-n}*.
3. **No other joining changes yet.** A new one is added here, with a test, before any word uses it.

The checker currently flags 9 words for W3 review: endings on unusual bases, such as *-{action}* on an adjective or noun. Each will be confirmed as a recorded extension here or rebuilt.

## 8. Rules the checker enforces

| Check | Rule |
|---|---|
| E12 | word-building endings fuse; bound words take a hyphen |
| W3 | an ending on a word class not listed in §2 is flagged for review: legitimate extensions are recorded here, mistakes are rebuilt |
| E3, E4 | one spelling and one sound per meaning |
| E11 | a built word is never older than its parts |
| calque audit | every built word's parts must make sense in Vulcan, not only as an English pun (batch 21) |

## 9. Making a new word

1. Is it a basic meaning, one every culture names? Then it is a **root**, generated by the sound laws.
2. If not, **build it**:
   - pick the head (what it *is*), put the modifier before it, and add endings from §2;
   - check that the parts make sense to a Vulcan;
   - check the era: a word can be no older than its newest part.
3. Add it to `lexicon/derivations.csv` with its basis, and rebuild. The checker does the rest.
