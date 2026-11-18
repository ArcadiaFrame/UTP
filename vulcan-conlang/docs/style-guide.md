# Translator's and writer's style guide

How to use Vulcan and Romulan on the page, in fiction, games and other media, so that it reads well, stays consistent, and carries the culture.

## 1. On the page

- **Italicize** Vulcan and Romulan words and lines in prose: *t'hy'la*, *katra*. Names stay roman: Sorel, T'Pau.
- **Spell exactly as the dictionary does.** The apostrophe is a glottal stop and always written (*pa'nar*). Hyphens join compound members (*vo-veh*) and are kept.
- **Capitalize only names** and the first word of a full sentence.
- **Names:**
  - Vulcan names often begin with *T'* for women and *S* for men (*T'Pol*, *Sarek*, *Sorel*), a canon tendency rather than a law.
  - Romulan names take the house prefixes *t'* (daughter) and *tr'* (son), with *i-* for lineage, as in Duane: Ael i-Mhiessan t'Rllaillieu.

## 2. How much Vulcan to use

- **Use Vulcan where English cannot do the job:** rites, oaths, untranslatable concepts, and moments of high feeling, where a character reaches for the old tongue. A single word or a short line lands harder than a paragraph.
- **Gloss once, by meaning rather than with brackets.** Use the narration, another character's reaction, or an immediate English echo:
  - *"Kaiidth," she said. What is, is.*
  - *"Dif-tor heh smusma." Live long and prosper.*
- **After the first gloss, leave it bare.** Readers keep what they have been given.
- **For a long exchange,** write it in English and mark that the speakers are using Vulcan ("he answered in Vulcan, formally"). Then let one line surface in Vulcan.

## 3. Untranslatables

Keep the Vulcan word and let the story show its range; never fix it to one English word.

| Word | What it holds |
|---|---|
| *t'hy'la* | friend, brother or sister, and lover, alone or all at once; pre-Surak and sacred |
| *katra* | the living self that a meld can carry |
| *k'oh-nar* | total exposure: the self laid bare, with its shame |
| *kaiidth* | what is, is: acceptance without consolation |
| *shon-ha'lock* | the engulfment; love at first sight |
| *bilak par* | self-pity, named so it can be set aside |
| *mnhei'sahe* (Romulan) | the ruling passion: honor and courtesy as one law |

The full list, with each word's history, is in `corpus/concepts.csv`.

## 4. Voice: choosing speech by character

| Speaker | Speech |
|---|---|
| Vulcan elder or dignitary | Formal: *cheil* before titles, honorific *-mush*, humble *-fum*, the formal particle *suh*, and *ihk-veh* "you (honored)" |
| Vulcan in Starfleet, with Humans | Standard, plain, precise; evidentials on everything that is not seen; emotions stated as "anger is in me," closed with *kon* |
| Bondmates and t'hy'la | No honorifics at all; plain speech is the bond. *ozh'esta* only here |
| A Vulcan child, or a Vulcan losing control | Slips into the older pattern: "I rage" (*Av nash-veh skukh!*), oaths, exclamations |
| Ritual (pon farr, Gol, katra rites) | Ceremonial forms and the canon liturgy (*plak tow*, *kal-if-fee*) |
| Romulan | A mode ending on every predicate: *-'nra* upward, *-ha* downward. No evidentials; *hwil* "not to be repeated." Remans are addressed only downward. The Qowat Milat drop all modes |

**Register.** For the body, sex, insults and slang, choose by speaker and moment from `registers.md`. Polite Standard speech uses the clinical or euphemistic word. The old coarse word means lost control, an ancient speaker, or an intended insult. Slang belongs to young Vulcans and to Starfleet.

## 5. Rendering Vulcan grammar in English dialogue

When a Vulcan speaks English in your story, the grammar of their own language can show through. Used lightly, this is the most effective device of all.

| Vulcan | Render as |
|---|---|
| *ho* (seen) | "I observed…", "I have seen…" |
| *aukh* (inferred) | "I conclude…", "It follows that…", "Evidently…" |
| *k'en* (reported) | "I am told…", "It is reported…" |
| *tekh* (by touch) | "I know it. I have touched it." |
| *kon* after an emotion | "…Noted." / "I acknowledge it." |
| *nash-veh* "this one" (humble) | "this one," or simply a refusal to say "I want" |
| *ihk-veh* "that one yonder" | "you, honored," or a title in place of "you" |
| Asking leave to touch | "Permit me." / "May I?" before any contact |

A Standard Vulcan will not state another person's feelings bare: "You are angry, I conclude," never "You're angry."

## 6. A translation workflow

1. **Find every word** in `dictionary-english-vulcan.md`. If a word is missing, build it by `word-building.md` and mark it *proposed*.
2. **Order it:** subject, object, verb, then the evidential. Question words go first. Noun before adjective before possessor.
3. **Choose register and era** for the speaker (section 4) and the period (`timeline.md`).
4. **Check it** in the Lab's Glosser. Every word should come back understood.
5. **Present it in three lines:** the Vulcan, a literal gloss, and a natural English rendering.

| | |
|---|---|
| Vulcan | *Vosan uhf-fokthuhr-wizh tosh.* |
| Literal | law the-innocent-(object) protects |
| English | The law protects the innocent. |

## 7. Common mistakes

- **English word order.** The verb goes last.
- **Adding "to be"** to a description. *fukhin mooli*, not *fukhin wim mooli*.
- **Stacking honorifics,** or using any at all between t'hy'la.
- **Using *tekh*** for anything not actually known by touch.
- **A Standard Vulcan stating an emotion as "I rage."** That is the pre-Surak pattern, and a sign of lost control.
- **Giving Romulans evidentials,** or letting Romulans speak upward to Remans.
- **Inventing a word without checking.** Every invented word must be checked against the dictionary first, or it will clash with an existing one.

## 8. Rights

Canon Star Trek terms belong to Paramount, and are used here for fan works. The original coinages in this project (its roots, built words, grammar and Romulan design) are yours. For publication outside fan fiction, use only those.
