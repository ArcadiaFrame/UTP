# How Vulcan words are built: the morphology spec

This is the reference for every piece that builds or bends a Vulcan word: what it does, what it attaches to, how it joins and when it entered the language. `docs/word-building.md` explains *why* a meaning is a root or a built word; this file is the rulebook for *how*. The checker enforces the joining rule (E12) and flags unusual attachments for review (W3).

Status: The dictionary has 3,800 entries: 211 canon words, 1,278 roots, 2237 words built from older ones, 72 designed words and 2 loan; 99 of the entries are Romulan only.

## 1. The shape of a Vulcan word

A word is a **root**, optionally with **prefixes** before it and **endings** after it, in this order:

> prefix – ROOT – word-building ending(s) – grammatical ending(s)

*uhf-sharsheiik-luhl-veh* "untrained melder" = without – teach – *-ik* (participle) – meld – one.

**Compounds** join two or more roots. Each member stands after a hyphen. In a compound **the modifier comes first and the head last**: *mune-shelekot* is a "star-fleet", a kind of fleet; *haumokpuhl* is a learning-place. This is the reverse of the **noun phrase**, where the head comes first and its describers follow: *fukhin mooli keru* "my old house". Persian and Japanese show similar splits between word-building and phrase order. The rule of thumb: inside a word, the last part names what it is; inside a phrase, the first word does.

## 2. Word-building endings (fused, no hyphen)

| Ending | Makes | Attaches to | Example | Era |
|---|---|---|---|---|
| -uth | the act or its outcome | verbs (and verb compounds) | *haumok* → *haumokuth* | Classical |
| -hol | the quality or state | adjectives, nouns, stative verbs (can, must, master) | *lun* → *lunhol* | Classical |
| -uk | having, characterized by | nouns, verbs, other words | *bor* → *boruk* | Classical |
| -ik | participle: done, having undergone | verbs; on a noun, "marked by" (as English *talented*) | *turan* → *turanik*; *koon* → *koonik* | Tribal |
| -fu | manner adverb | adjectives | *peret* → *peretfu* | Classical |
| -puhl | place where it is done or kept | verbs, nouns | *haumok* → *haumokpuhl* | Classical |
| -sowash | instrument, device | verbs, nouns | *vinik'* → *vinik'sowash* | Classical |
| -ot | a body or group of | nouns | *pifo* → *pifoot* | Classical |
| -sakh | ordinal number | numbers | *veet* → *veetsakh* | Classical |
| -t'au | make someone do or feel | verbs, emotion nouns | *mikshak* → *mikshakt'au*; *fes* → *fest'au* | Tribal |
| -kith | some- | question words | *thuh* → *thuhkith* | Classical |
| -pes | every- | question words | *thuh* → *thuhpes* | Classical |
| -fi | toward | nouns, places, names | *suk* → *sukfi* | Classical |

Endings stack in this order: participle or causative first, then quality or act: *uhf-sharsheiik*, *fest'auth*.

## 3. Bound words (always after a hyphen)

| Piece | Meaning | Example |
|---|---|---|
| veh | one, person (canon *ish-veh*) | *vo* → *vo-veh*; *haumok* → *haumok-veh* |
| kam | little, dear (canon *Saavik-kam*) | *sheka* → *sheka-kam* |
| tor | make, do (canon *dif-tor*, *fal-tor-pan*) | *gor* → *gor-tor* |
| kau | joined, together (canon *kashkau*) | *poth* → *poth-kau* |
| -pi | endearment, dear (Classical, now intimate) | *kekru* → *kekru-pi* |
| -tith | wretched, contemptible (Classical, now coarse) | *nirak-tith* |

## 4. Prefixes (hyphen) and *ki'* (joined)

| Prefix | Meaning | Example |
|---|---|---|
| uhf- | without, un-, -less | *uhf-kisuhk* "painless" |
| kir- | again, re- | *kir-sarlah* "again-come" |
| pu- | before, fore- | *pu-pokok* "fore-say" |
| tok- | in, inner | *tok-tuvri* |
| tol- | out, outer | *tol-khakik* |
| er- | with, co- | *er-vushhush* |
| ki' (joined) | completed action: has done | *ki'sarlah* "it has come" (canon *ki'sarlah*) |

## 5. Grammatical endings in a sentence (hyphen)

| Ending | On | Meaning |
|---|---|---|
| -k'oo | nouns | plural |
| -wizh | the last word of the object phrase | definite object |
| -bi | verbs | it, them (object attached to the verb) |
| -un | verbs | past |
| -pil | verbs | ongoing: is doing, was doing (before -un) |
| -mush / -fum | verbs | raises the other / lowers oneself |
| -shith, -kuhl | verbs | utterly; would that I could (Classical; now strained or poetic) |

Order on a verb: root – -pil – -un – -mush or -fum.

## 6. Particles (separate words)

| Position | Particles |
|---|---|
| **Before a noun** (prepositions) | *tok* in, *t'uhk* from, *er* with, *uhf* without, *pu* before, *nu* after, *nokh* through, *khi* between, *ur* under, *po* above, *khat* inside, *tol* outside, *kos* up, *iv* down, *ro* around, *p'i* across, *wa* away, *mo* in front of, *la* behind, *t'ei* than (after the thing compared against) |
| **Before the verb** | *dungi* will, *suhk* not, *shul* must, *wo* may, *sei* should, *ak'* would, *thu* let us |
| **Opening the sentence** | *kuth* yes-or-no question, *kor* please, *cheil* respected (before a title), *av* how…! |
| **Closing the sentence** | evidentials *ho* seen, *aukh* concluded, *k'en* told, *tekh* known by touch; *kon* noted; *suh* formal; *lul* sanctioned (22nd century); Classical *sheil*, *vash*, *yo* |
| **Joining clauses** | *eh* and (*heh* liturgical), *os* or, *khe* but, *ku* therefore, *ru* because, *hu* so that, *k'u* if, *khuk* while, *kil* until, *eet* although, *meen* that (reported), *lith* who, which |
| **Linking nouns** | *t'* of (old possessive; the female name prefix), *i* of the (in compounds) |

## 7. Sound changes when pieces join

1. **Length-*h* drop:** a screen spelling's final vowel-*h* drops before a fused ending that begins with a vowel or *h*: *sarlah* → *sarlauth*.
2. **A diphthong absorbs a like vowel:** after *au*, *ei*, *ai* or *oi*, an ending that begins with the same vowel loses it: *sekau* + *-uth* is *sekauth*; *sharshei* + *-ik* is *sharsheik*. After a plain vowel, a doubled vowel stays and is read long: *hukhnuuth*.
3. **No other joining changes yet.** A new one is added here, with a test, before any word uses it.

The checker currently flags 9 words for W3 review: endings on unusual bases, such as *-uth* on an adjective or noun. Each will be confirmed as a recorded extension here or rebuilt.

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
