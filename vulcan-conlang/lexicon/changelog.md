# Dictionary changelog

## Batch 2 (9 Nov 2026)

Rebuilds now freeze accepted words: a word keeps its form and id unless a change is logged here.

**Replaced by canon.** Batch 1 generated words for meanings that canon dialogue already supplies. Canon wins:

| Meaning | Batch 1 form | Canon form | Evidence |
| --- | --- | --- | --- |
| person | het'es | banut | ihk-banut "that person" (Star Trek II) |
| be | klam | wim | wimish "I am" (Star Trek III) |
| what | zhel | wakli | "Wakli ak'wikman, ot-lan?" (Star Trek II) |
| come | lor | sarla | ki'sarlah "it has come" (Star Trek III) |
| trust | chaul | sarafel | "Dungi tu sahrafel?" (Star Trek III) |
| here | khik | tan | tanfi (ENT "Home") |
| plant | meislul | glomak | glomahk (DIS "Project Daedalus") |
| sand | chutuk | mazhiv | "fi'aifa mazhiv" (Star Trek: TMP) |
| want | sinei | dawru | dawru "wanted" (ENT "Home") |
| speak | tathu | stariben | kup-stariben "can you speak" (Star Trek III) |

The batch 1 form *lor* now means **bring**, which canon *lorun* "brought" supports.

**Regenerated.** *eat* (was *kam*): clashed with the canon diminutive -kam. *six* (was *eir*): law C1 was narrowed, which would have made it the English word *air*.

**Law changes.**
- C1 (*ai > ei*) no longer applies at the start of a word, so canon *aifa* "these" survives.
- New C7 (*lnt > ld*) and C8 (final *nt > d*) derive canon *avalde* "colleague" and *pod* "commander".
- R1 (Romulan *s- > r-*) now applies only before a vowel or h. This changed five Romulan forms, for example *rtar* to *star* "voice"; no Standard forms changed.

**Gloss and register refinements.** ni = "very, so (intensifier)"; dom = "thus (discourse)"; ihk = "yonder, that (out of sight)"; ish-ve is formal and bosh is the casual "he/she".

## Batch 3 (9 Nov 2026): grammar, culture, science and ship words

**New canon-read grammar:** -un (past), ki'- (completed action), -wizh (object), -bi (it, them), -ik (participle, root of seheik "declared"), plus *seha* "declare", *kolinar* "Kolinahr" and liturgical *he* "and".

**Designed grammar** (generated and checked): plural -k'oo; evidentials *ho* (seen), *aukh* (inferred), *k'en* (reported), *tekh* (melded); speech levels -mush (honorific), -fum (humble), *cheil* (address); *lith* (relative), *t'ei* (than), -pe (agent), -hol (abstract), *lir* "you all".

**Culture:** Classical society modeled on Edo Japan and Rome (lord, retainer, patron, client, council, oath, tribute, estate); Surak's teaching on Confucian and Buddhist lines (propriety, filial reverence, right-naming, mindfulness, non-attachment, compassion, suffering, cause, harmony).

**Science and ship:** 45 words, including *shelek* "ship", *tuskash* "fascinating", and science and philosophy built from one root, *mik t'wul* "inquiry of things" and *mik t'kash* "inquiry of the mind", as the novel Crisis on Vulcan describes.

**New check E7:** a generated word may never take a canon word that has no reliable meaning yet. Those words are reserved.

**Regenerated** (each clashed with canon):
| Meaning | Old form | New form | Why |
| --- | --- | --- | --- |
| yes | ik | il | ik is the canon participle -ik |
| who | ki | thuh | sounded like the canon prefix ki'- |
| probability | nen | cheemas | sat on canon Nehn (DIS) |
| how | ka | ar | ka is an unglossed canon word |
| nine | nei | ke | nei is an unglossed word in Spock's World |

## Batch 4 (9 Nov 2026): the honorific system and everyday words

Derived from a cultural analysis of Vulcan and Romulan society (see the Culture and speech tab in the design bible).

**Honorific machinery:** formal particle *suh*; designed etymons *mushak* "exalt" (source of -mush) and *fumel* "bow low" (source of -fum); honored "you" *ihk-ve* "that one yonder"; 14 honorific and humble verbs and nouns (eat *spek*, drink *sesar*, come or be present *krom*, say *ulat* and *momi*, see *kuk'*, offer *orer*, receive *kilash*, pass on *kleen*, rest *wel*, residence *sato*, name *t'akak*, touch with leave *usul*, presume to know *kesne*).

**Seniority and titles:** *alen* elder sibling, *tasas* younger sibling, *bal* great-grandparent, *mok* lineage, *khit* ambassador, *sivki* healer, *laluhk* master of a discipline, *raun* adept, *chotsher* priestess.

**Everyday vocabulary:** 72 words for the body, food, home, nature, colors, feelings and daily actions.

**New status:** "designed etymon", for reconstructed source words that explain a grammatical ending.

No earlier word changed. 512 entries, 0 errors.

## Batch 5: touch, the orders, and feeling (619 entries)

Source analysis: the "Batch 5" section of the Culture and speech tab (touch as weapon, intimacy and crime; the pre-Surak orders; emotion in speech by era; Romulan rank-and-touch divergence). Farscape's Delvians (Unity, the Pa'u levels, Zhaan and Bitaal) were used as calibration.

- 107 new entries, 0 errors, no earlier word changed.
- Canon anchors added: pa'nar (ENT "Stigma"), rumarie (VOY "Meld"), nirak (ENT "Kir'Shara"), v'tosh ka'tur (ENT "Fusion"); novel anchor val'reth (Vanguard).
- Dropped before acceptance: "rite", which the E5 check flagged as a duplicate of canon ut (koon-ut). Use ut.
- New era value `Romulan`: coined after the Sundering, so it has no Vulcan or Ceremonial form (lexicon.py fill()).
- New check E8: a Romulan form may not have a letter three times in a row. It caught candor *falhlhek > fallllik; regenerated as *qook > qhook.
- The Romulan hand words were changed from generated roots to compounds of inherited poth "hand": pothhrur take in hand (downward), pothvrik give the hand (upward), pothhol "the hand" (authority), poththuhk release from the hand.
- Ids V0520-V0626 were renumbered once before publication so they stay contiguous.
- Glosser: 7 new examples (Classical exclamative, Standard distancing with kon, evidential on another's feeling, causative reproach, lapse formula, granting leave, forced meld).

## Batch 6: conversation (802 entries)

- 183 new entries, 0 errors. Function and grammar words for dialogue, courtesy and discourse words, everyday verbs, adjectives, adverbs and nouns.
- ozh'esta adopted from fandom as the old Classical word, now intimate colloquial (register `colloquial`). finger-touch (sileil) re-dated Unified, register formal: the Surakian euphemism.
- Canon greeting aligned with low confidence: t'nar greetings, pak regard (canon pahk), sarat extend, y'rani to your house, jaral likewise. kal-toh added.
- Dropped before acceptance, as canon already has them: logic (kthia), do (tor), remember (vokau), time (pon). logical = kthia + -uk; illogical = suhk-kthiauk.
- New check E9: a compound whose parts name a key with no root form.
- Spelling: every derived Vulcan form now passes through phon.standardize. One published word changed spelling only: build toya > toia. sehlat and kal-toh carry logged exceptions to keep their canon spellings.
- New corpus/phrasebook.csv (56 lines). The Lab glosses every line on load and flags missing words. It caught pahk, kal-toh and t'Vulkan; the Glosser now matches exact canon spellings first and reads t' + a capitalized name.

## Batch 7: daily life (1,111 entries)

- 309 new entries, 0 errors, no earlier word changed. Home, food, body and health, clothing, people and trades, learning, city and directions, nature and materials, time, ship and technology, everyday verbs and qualities.
- Dropped before acceptance, as canon already has them: fire (far), blood (plak), fever (tow), heal (vo), marriage (V0204). Reworded to clear E5 clashes: ship-bridge, receive-guest.
- Nine trade nouns built as compounds with -pe (teacher sharsheipe, builder toiape, hunter, cook, writer, singer, traveler, observer, learner).
- lexicon.py: each piece of a compound is now spelled to the standard (so builder is toiape after toia). No existing compound changed.
- Phrasebook: three glossed scenes (a meal, a briefing, a family lesson), 85 lines in all, all understood by the Glosser.

## Batch 8: the canon backlog and abstract words (1,308 entries)

- 197 new entries, 0 errors, no earlier word changed: 55 canon and novel anchors (every remaining glossed single term), 81 abstract nouns, 60 verbs of thought and discussion, and IDIC as a compound (karneesh sheruk mur sheruk).
- Logged exceptions (relative chronology): kaiidth and l'tak terai postdate the ai > ei shift (C1); faitukh and qualsetu are Old Vulcan spellings from before C1 and S1.
- lexicon.py: std_keep() applies standard spelling while keeping a word's own hyphens and spaces.
- Dropped: thought (canon nap). kleeet respelled klee-et (source spelling) to clear E8.

## Batch 9: society, science, arts and the land (1,595 entries)

- 287 new entries, 0 errors, no earlier word changed: government, law and war; science and measures; arts; Vulcan terrain, weather, fauna and flora; everyday nouns and qualities.
- Dropped: sandstorm (canon storm takak covers it).
- New check E10: a Vulcan form with a doubled apostrophe or a letter three times in a row. It caught kat''ash (canyon), regenerated as loka.

## Batch 10: Romulan (1,669 entries)

- 74 new Romulan-only entries (84 with batch 5's): canon (jolan tru, Tal Shiar, Qowat Milat, Zhat Vash), 34 Duane anchors, and designed grammar and vocabulary.
- Grammar: modes -'nra (upward), -ha (downward), -hwe (level), -'nrae (upward question), -d'ifv (downward question); -hna'h activation imperative; -ha singular, -nsu plural; aihr- copula; t', tr', i- and ch' name prefixes; -'ssei abstract address; hwil (discretion) and khnai (rumor) particles; hwaen, "you" to a Reman (downward only); qhaev candor speech (no mode endings).
- lexicon.py: an era-Romulan row with attested_romulan is spelled as attested, with no sound laws and no Vulcan form; the E5 duplicate-meaning check now keys on branch too.
- Lab: the Glosser has a Vulcan/Romulan switch, the phrasebook has a lang column, and 17 Romulan lines were added (102 lines, all understood).
- Open: Duane's ssuaj-ha (glossed as upward) conflicts with mnekha (downward).
- Fixed: the standalone `lexicon.py check` command never loaded the key-to-root table, so it could not resolve compounds. The new E9 check exposed it. Both build and check now report 0 errors on identical data.

## Batch 11: the rebuild by root and derivation (1,672 entries)

The first ten batches gave nearly every English meaning its own random root (82% of entries), which made the vocabulary English-shaped. Batch 11 rebuilt it.

- Basis, in order: canon Vulcan patterns (-tor, ve, kau, -ik, -kam, noun compounds, mik t'X); anthropology (Swadesh and Leipzig-Jakarta meanings stay roots; Berlin-Kay colour order; social, institutional, abstract and technical meanings are built later); English, Latin and Japanese as cross-checks (if two of the three build a meaning, Vulcan does). Vulcan culture overrides: green from blood (plakuk), blue from the void (zhokouk), mirage "false water", Federation "worlds joined" (spak-kau).
- tools/derivation.py: 316 built meanings, each with its basis and Latin and Japanese parallels. New endings (generated): -uth action noun, -puhl place, -ot collective, -kith some-, -pes every-. The instrument element is the noun sowash. Prepositions also serve as prefixes (uhf- without, kir- again, pu- before, tok- in, tol- out, er- with).
- 321 forms changed (the full old-to-new list is the diff against the batch 10 lexicon). Canon, sound laws, grammar and Romulan unchanged.
- Retired: the generated agent suffix -pe (canon ve does the job) and learner (same as student).
- abstract -hol and adverbial -fu re-dated Classical. New check E11: a built word may not be dated earlier than its parts.
- Fix: a logged exception now shows the attested form (kaiidth, l'tak terai, qualsetu, faitukh), with the sound-law output kept in notes.
- New: tools/templates.py. The phrasebook (102 lines) and Glosser examples (19) are {key} templates rendered at build, so they can never go stale.
- New: tools/export.py writes docs/ (dictionaries Vulcan–English, English–Vulcan, Romulan; phrasebook; word-building; timeline) from the dictionary and docs_src/ templates. New README.md (start here).
- Bible: new Word-building and Timeline tabs. Grammar and Culture tabs updated to the current forms. Batch logs keep their historical forms, with a note.

## Batch 12: filling the semantic fields (1,936 entries)

- 264 new entries, 0 errors: 36 new roots (basic vocabulary only) and 228 built words. Batches now follow the Intercontinental Dictionary Series semantic fields.
- New file lexicon/derivations.csv (key, gloss, pos, field, era, register, parts, basis). derivation.py reads it and adds any new meaning it names.
- Kin built descriptively (aunt-uncle, cousin as clan-sibling, niece-nephew, twin, in-law, heir). Numbers 11-90 are regular (ten-one, two-ten), plus ordinals second through tenth.
- Changed: the fractions third-part (veet-khasni) and quarter (ir-khasni) are now "three-part" and "four-part", so they no longer share a form with the new ordinals third and fourth. No other earlier word changed.
- lexicon.py: a loanword can enter a compound as it is (humanity komihnhol, from komihn).
- Gloss reworded to clear E5: scale-w ("weighing scale, balance").
- Phrasebook: two new scenes (a family gathering, the market), 122 lines, all understood. word-building doc: new Numbers and kin section.

## Batch 13: cognition, speech, society, household, health (2,057 entries)

- 121 new entries, 0 errors, no earlier word changed: 31 roots (basic body, health, speech and cognition meanings) and 90 built words.
- Dropped: noble (canon fal "noble, high" covers it); nobility is built on fal (falot).
- Built on canon: funeral arek-ut (death + rite, as koon-ut), naming rite gor-ut, marry koon-tor, light a fire kar-far, put out a fire far-kolesh.
- Culture: contagious is "touch-sick" (nakan-kuhvholuk).
- Phrasebook: a new scene, the healer (12 lines), 134 lines in all, all understood.
- New learning docs: docs/grammar.md (full grammar reference, every example rendered from the dictionary) and docs/pronunciation.md (vowels, consonants, stress, era differences, reading practice). export.py now capitalizes example sentences.

## Batch 14: nature, motion, possession, time, space, quantity (2,201 entries)

- 144 new entries, 0 errors, no earlier word changed: 33 roots and 111 built words.
- Canon -kam made the productive diminutive: pebble sheka-kam, stream sisir-kam, flame far-kam, sehlat cub sehlat-kam.
- Desert seasons in place of four temperate ones: hot season peltakh-pon, cold, storm and bloom seasons. Flash flood is "rain-river", earthquake "ground-shake", horizon "sky-border".
- Trade: buy fezha-srur ("take for a price") and sell fezha-vrek ("give for a price", as Latin ven-dere). Built on price, not money, so they date from the Classical era.
- lexicon.py: a logged canon spelling (sehlat) keeps that spelling inside compounds.
- Fixed before acceptance: loss rebuilt as "a lacking" (it duplicated defeat); free-of-charge gloss reworded.
- Phrasebook: a new scene, the desert crossing (11 lines), 145 lines in all, all understood. New docs/lessons.md: lessons 1 to 4 with practice and answers.

## Batch 15: law, war, religion, the Federation world (2,311 entries)

- 110 new entries, 0 errors, no earlier word changed: 9 roots and 101 built words.
- Built on canon: trial vosan-kas ("law-ordeal", kas), priest ut-ve ("rite-one", ut), the Time of Awakening akiluth-pon, the Hall of Ancient Thought sof t'ok'ut-nap (nap "thought").
- Federation world (Standard era): Starfleet mune-shelekot ("star-fleet"), Earth komihn-spak ("Human-world"), alien ko-spak-ve ("other-world one"), holodeck seli-spakpuhl ("false-world place"), replicator, warp drive, first contact.
- 15 fields of study on the mik t'X pattern (linguistics mik t'sitvokhhol, psychology mik t'ponan, and others).
- Fixed before acceptance: armor (no "body" key; now chest-shield), purify (it duplicated clean-v; now "make pure"), medicine-field gloss.
- Phrasebook: a new scene, the trial (10 lines), 155 lines in all, all understood. New docs/style-guide.md.

## Batch 16: regular derivatives and the last basic roots (3,001 entries)

- 690 new entries, 0 errors, no earlier word or id changed. The average-fluency target of 3,000 is reached.
- Regular derivatives across the inventory, as a dictionary lists them:
  - action nouns (verb + -uth) for every everyday verb that lacked one
  - person nouns (verb + ve) for action verbs only (making, conflict, speech, food, rank, ritual, discipline, mind)
  - quality nouns (adjective + -hol) for root adjectives only
  - 91 participles in canon -ik with hand-written English glosses (carved, healed, born, forgiven)
  - The 23 that duplicated an existing word (explanation, prediction, lost, broken, beloved and others) were dropped automatically.
- New roots: body parts (nose, lip, cheek, jaw, thumb, wrist, spine, the meld point), nature (clay, frost, dew, current, gorge, ember), animals and plants (spider, ant, bat, moth, vine, moss, reed, fungus, resin).
- Culture: nerve pinch "neck-squeeze", telepath "mind-touch one", touch telepathy, self-control, self-mastery, school of logic, logician, plomeek soup, the Vulcan salute "hand-greeting".
- Fixed: a damaged line in lexicon.csv. The 14 batch 15 ids it shifted are restored, and lexicon.py now skips any row without a proper id.
- Phrasebook: a new scene, the school of logic (6 lines), 161 lines in all, all understood. docs/lessons.md has lessons 5 to 8 (comparing and counting, building words, speech levels, feeling and touch).

## Batch 17: gender, the body, sexuality, insults and slang (3,091 entries)

- 91 new entries, 0 errors, no earlier word changed. New registers: vulgar, euphemism, clinical, colloquial and slang. Same meanings may now exist in several registers.
- Layers by era: frank Tribal and Classical roots (now vulgar); Surakian euphemisms ("the self below", "joined skin", "carrying a katra", "the necessary place"); Standard clinical compounds ("male part", "seed-vessel", "month-blood", anatomy "inquiry of form"); 23rd-24th century slang by clipping (suhkthi, kthi), doubling (sa-sa, ni-ni), -kam (chekh-kam, wan-kam) and loans (okei); Romulan colloquial and slang words (10).
- Gender: pronouns stay neutral. New words for male, female, gender, masculine, feminine, boy, girl, androgynous, nonbinary (ko-si'anuk) and transgender person (katra-si'an-ve, "one whose form follows the katra").
- Sexuality: attraction is described rather than named as an identity (drawn to men, women or both); same-bond and other-bond; attraction kahol, from the novels' kah.
- Insults and oaths, with weight noted: houseless (gravest), half-breed (offensive), coward, show-off, sehlat dung, fire and sand.
- Fixed before acceptance: traitor duplicated betray-er (gloss now "traitor, one who betrays"); attraction rebuilt on ka (it duplicated the act of pulling).
- New docs/registers.md, plus a register note in the style guide. Phrasebook: a new scene, cadet slang (7 lines), 168 lines in all, all understood.

## Batch 18: the mind sciences (3,153 entries)

- 62 new entries, 0 errors, no earlier form or id changed.
- Touch telepathy as a system:
  - Three channels, each with a Classical folk name and a Standard clinical name: field (life-heat / bio-field, at the canon qui'lari), chemical (mind-salts / neurotransmitter, the touch-exchange), wave (mind-wave, attunement).
  - Directions (receptive, projective, mind-voice, bridging) and scopes of reflection (inner, outer, group, self-meld).
  - Seven grades of the Order of Communion, from the Open Hand to the Carrying, plus a lost eighth.
  - Acts (surface, emotion and memory reading, calm-send, pain-block, pain-take, memory share, give and wipe, mind-seed, probe, far-touch, katra-give, other-meld); bonds (form, sense, sever, meld-ash); dangers (bleed-over, untrained melder).
- Six archaic words with meanings partly lost (register archaic), recorded as reconstructions.
- Era fixes: 24 roots that an early rule had dated Standard because of their field are re-dated to fit anthropology (receive, tool, money, week, nation, colony, academy, cargo, captain, officer, ambassador, ship and its parts, and others). 22 built words that depended on them were lowered to match. Spaceport, shuttle and other spacefaring words stay Standard. No forms changed.
- New docs/telepathy.md. Phrasebook: a new scene, a teaching meld (10 lines), 178 lines in all, all understood.

## Batch 19: the emotive layer, romance and argument (3,221 entries)

- 68 new entries, 0 errors, no earlier form or id changed.
- Eight Classical emotive inflections, each with its fate by era in the notes: -pi endearment, -tith pejorative, -shith emphatic, -kuhl longing, the tag sheil ("is it not so?"), the challenge vash, the coaxing yo, and the exclamation le. Under Surak, what performs a feeling went down to intimate, coarse or archaic; what names a feeling (kon) stayed.
- Romance and flirting (Classical): court, tease, charm, tempt, suitor, sweetheart, love song, love letter, blush ("blood rising", a green flush), jealous, devotion ("giving the heart"), heartbreak, elope ("bond-flee"), seduce, admire ("see the beauty").
- Argument (Classical): bicker (doubled quarrel), contradict ("say otherwise"), rebuke, defy, resent, sulk, sneer, gloat ("victory-joy"), sarcasm ("false praise"), temper, furious, stubborn, arrogant, comfort, relief, despair ("without hope").
- Standard reserved forms: hold in regard (the Vulcan "I love you"), find acceptable, the value of one's company, ask for a bond, disagree, register an objection.
- Romulan kept the layer in everyday speech: aehn'ru darling, mnaelh court openly, khrrhae quarrel loudly, fve'hna! I dare you, llhoi a fond insult.
- Fixed before acceptance: devotion and company-value were rebuilt (they duplicated "the act of adoring" and "society"); longing was dropped, since yearn-act already means it.
- Tools: phrasebook notes may now use {key} templates, and export stops on any unknown key in the phrasebook.
- New docs/emotive.md. Phrasebook: two new scenes, courtship and a quarrel, each "then and now" (13 lines), plus 3 Romulan lines; 194 lines in all, all understood.

## Batch 20: after Surak, the contemplative culture and the surveillance years (3,277 entries)

- 56 new entries, 0 errors, no earlier form or id changed.
- The disciplines of the mind, built from older roots, with their Earth analogues noted: impermanence, no-mind (mushin), new mind (shoshin), remaining mind (zanshin), sudden insight (satori), logic-riddle (koan), the middle path, non-attachment, stillness, life-purpose (ikigai), crack-beauty (wabi-sabi, kintsugi), moment-grief (mono no aware), the silence between (ma), daily refinement (kaizen). Practices: breath, flame and walking meditation, the mind-chant, the stone garden; the Teachings.
- The code of conduct: humaneness (ren), righteousness (yi), the exemplary person (junzi), ancestor reverence, rectify names (zhengming). Propriety (li), filial reverence and equanimity already existed and are reused.
- The surveillance years under the High Command (Standard, to 2161): surveillance, informer, denounce ("give a name"), dossier, watch list, suspicion ("the doubting eye"), interrogation, classified, censorship and self-censorship, propaganda ("government-word"), orthodoxy, dissent, re-education, checkpoint, identity papers, listening device, paranoia, and openness, the Federation-era answer.
- A new generated particle, lul, "sanctioned: this may be said", the mark of approved speech. It fell out of use after 2161 and is now archaic or ironic. It mirrors the Romulan discretion particle hwil.
- Fixed before acceptance: a new "command" root duplicated command-v (High Command now uses command-v); loyalty oath duplicated "swearing fealty" and was dropped.
- Seven Sayings of the Teachings and "the walls have ears", templated in corpus/idioms.csv (now with a template column, rendered in the Lab) and in the Phrasebook.
- New docs/after-surak.md. Phrasebook: two new scenes (the meditation hall; a checkpoint, 2150s) and the sayings, 216 lines in all, all understood.

## Batch 21: social life, survival, bonds and rank, plus a calque audit (3,397 entries)

- 120 new entries, 0 errors: 1 root (trap, *kashak*) and 119 built words.
- **Calque audit.** Every built word was checked for parts that follow an English pun or idiom instead of Vulcan logic. Three failed and were rebuilt:

| Meaning | Old form | New form | Why |
| --- | --- | --- | --- |
| courtship | tet'ispuhluth | koon-stiluth | was "court of law" + act; now "bond-pursuit" |
| suitor | tet'ispuhl-ve | koon-stil-ve | was "court of law" + one; now "bond-pursuer" |
| sweetheart | sizha-kekru | kekru-pi | was the English idiom "sweet heart"; now heart + the endearment ending |

- Kept after review, because the metaphor is not English-only: head for chief (LA caput, JA kashira), seed for semen, wave for frequency and brainwave (JA nami), tongue for language. Six glosses with spelling slips were corrected (forgetting, transmitting, admitting, splitting, forbidding, and busyness, which read "business"). docs/emotive.md had used the law-court word for the verb "court"; it now uses the new *koon-stil*.
- **Bonds:** the heart-whisper, *kekru-vrakh* (confide a heart-matter about one who is absent, among bond-kin only), with its noun, the confidant ("heart-keeper"), keeping a confidence, and the declaration made to the person (*kekru-kauk*). Also woo, crush ("hidden attraction"), unrequited, refusing a suitor, matchmaker, bond-gift, reunion, estranged, devoted, jealousy, oath-sibling, companion-in-arms, foster sibling.
- **Social life:** acquaintance, introduce ("share names"), favor ("help-debt", the JA on), reciprocity, reputation ("name-voice"), the honor of a House, loss of standing, the water-first (water before any word), guest-gift, etiquette, compliment, the Standard congratulation, condolence, idle talk, interrupt, eavesdrop, distrust, rivalry, and expose (*k'onar-tor*).
- **Survival:** water-skin, cache and water-finding, ration, forage, edible, famine, storm shelter, camp, night-fire, the night-cold, signal fire, cairn, star-reading, trap, snare, trail, tracking, heat-sickness, dehydration, frostbite ("cold-wound"), antidote, splint, tourniquet, survive ("life-keep"), the desert way, nomad clan ("path-clan"), caravan.
- **Rank:** the war-Houses (warlord, liege "oath-lord", sworn, superior and subordinate, chain of command, war-band, squad, vanguard, rearguard, flank, battle order, banner, war council, war cry, recruit, veteran, lookout, night watch, duel, champion, second, concede, spare, ransom, promotion, demotion) and the training hall (grandmaster, disciple "master's child", senior and junior student "before-" and "after-companion", bow in greeting, practice, fighting form, spar "hands joined", bout, stance, block, counter-strike, feint, grapple, rank-belt, rank test).
- Fixed before acceptance: two glosses reworded to clear E5 (duelist's second; fighting form). disciple-m and grand-master were raised to Unified because master-n is Unified.
- New concept card: *kekru-vrakh* (corpus/concepts.csv).
- New docs/social-life.md. Phrasebook: four new scenes (a heart-whisper, lost in the deep desert, the training hall, a guest arrives) and seven Sayings of the desert and the House; 260 lines in all.

## Batch 22: life in the bond, and the course's Conversation level (3,433 entries)

- 36 new built words, 0 errors, all intimate and interpersonal: what the bond reports (bond-warmth *koon-eekhikh*, bond-ache *koon-kisuhk*, bond-silence *koon-kut*, reach through the bond *koon-atik*), presence ("mind-nearness"), miss and missing ("feel the distance"), homesickness, the private name (*gor-pi*, the given name with -pi), hold hands, the comforting touch, share silence, feel safe ("the Standard understatement for intimacy"), rely on ("trust-rest"), entrust one's katra, lower one's shields, unshielded and vulnerability, guard one's heart, cherish ("treasure-hold"), reassure ("tell safe"), worry about ("carry worry"), heart-wound and hurt feelings, nightmare ("fear-dream"), lullaby ("sleep-song"), watch over a sleeper, hearth, keepsake ("memory-thing"), tender-hearted, softly, bonding anniversary, fidelity, a shared life.
- Dropped before acceptance because the dictionary already had them: first meeting (*vauksakh-nizhikhuth* already means first contact and covers it), reconcile and reconciliation (*kir-kau*, *kir-kauuth*). The katra-trust gloss was reworded to clear E5.
- New concept card k20: the three bond states, which let a Standard speaker report a feeling as evidence with tekh.
- Phrasebook: five new scenes (a homecoming, in the night, mending a quarrel, the private name, before a parting) and four Sayings of the bond; 301 lines in all, all understood by the Lab glosser.
- docs/social-life.md gains "Life in the bond"; docs/emotive.md gains miss and cherish.
- Course: the Conversation level opens with nine units built from the Batch 21 and 22 scenes, with spot-the-mistake drills and four stories (the water-first, the heart-keeper, the storm, come back). Every course sentence passes the Lab glosser.

## Batch 23: tales and how Vulcans tell them (3,440 entries)

- 7 new built words, 0 errors: catch ("chase-hold"), goal ("path-end"), long ago (*ok'ut-pon*, "ancient time"), storyteller, teaching tale (*airek-took'wul*), enlightenment (*kash-fakha*, "mind-dawn"), refrain.
- New docs/tales.md: the Vulcan tale form, drawn from canon (VOY "Innocence", SNW "The Sehlat Who Ate Its Tail", TAS "Yesteryear", ENT "Carbon Creek"), and three tales with English: *The sehlat who ate its tail*, the opening verses and last verse of *Falor's Journey*, and *The kahs-wan*.
- Idiom i01 now has its Vulcan form: *Sehlat lith tewku sok-wizh sokzha-un*.
- Phrasebook: a "Telling a tale" set (opening, closing, the closing question, the sehlat saying, the Falor refrain); 306 lines.
- Course: the Literary and Ceremonial level opens with two units (Telling a tale; Journeys and trials) and the three tales as stories. The Conversation story *Come back* now uses the name T'Rena, because T'Mir is a canon name (ENT "Carbon Creek").

## Audit 1: canon, novels, the VLD and fandom (3,457 entries, 18 Nov 2026)

Full findings: `analysis/audit-canon-fandom.md`. The complete before-and-after list of every changed form is `analysis/respelled.csv`. No id changed, no meaning was removed, and no Romulan or Ceremonial form changed.

**Decisions:**
- Words heard on screen keep their screen spelling.
- The person word is spelled *-veh*.
- VLD and fandom words enter as dated or register variants, as *ozh'esta* did.

**Screen spellings restored.** 26 on-screen words are now logged exceptions, and every compound built on them follows:

| Screen spelling | Was | Source |
| --- | --- | --- |
| kroykah, ahn-woon, koon-ut-kal-if-fee, pon farr | kroika, anwoon, koon-ut-kalifee, pon far | TOS "Amok Time" |
| kahs-wan | kaswan | TAS "Yesteryear" |
| Kolinahr, nahp, eh, heh (in *dif-tor heh smusma*) | kolinar, nap, e, he | Star Trek: TMP |
| ish-veh (and veh "one": 328 words, e.g. nash-veh, vo-veh, koon-veh), ot-lan | ish-ve, ve, otlan | Star Trek II |
| sarlah, sahrafel | sarla, sarafel | Star Trek III |
| ghishun, pahk, pash tah, mol-kom, tarul-etek, suus mahna, surah'tahn | gishun, pak, pash ta, molkom, taruletek, suus mana, sura'tan | ENT |
| k'oh-nar, soo-lak, shon-ha'lock, fal-tor-voh | k'onar, soolak, shon-ha'lok, fal-tor-vo | VOY |
| qui'lari | kui'lari (the note said it kept q; now the form does) | DS9 "The Muse" |
| glomahk | glomak | DIS "Project Daedalus" |

- New spelling rule: a screen spelling's final length-*h* drops before a fused vowel ending, so *sarlah* + *-uth* gives *sarlauth*, and *veh* + *-hol* gives *vehol*. The vowel *uh* is not affected.
- Novel and RPG words keep the house spelling (kthia, not cthia).

**Fandom variants added (17).** None replaces an existing word.

| Word | Meaning | Era, register | Source |
| --- | --- | --- | --- |
| ashaya, ashau | tender love; love tenderly | Classical, intimate | VLD |
| ashayam | beloved, said to a bondmate | Classical, intimate | VLD |
| ashal-veh, ashalik | darling; dearly loved | Classical, intimate | VLD |
| taluhk | precious, dear | Classical, everyday | VLD |
| tal-kam | dear little one | Classical, intimate | VLD |
| k'diwa | bond-beloved | Unified, intimate | Jean Lorrah |
| adun, adun'a | husband, wife | Classical, everyday | Jean Lorrah |
| nartau | embrace, hold close | Classical, intimate | VLD |
| el'ru'esta | hand-embrace (the partner of ozh'esta) | Classical, colloquial | VLD |
| sa-mekh | father, as a child says it | Classical, intimate | VLD |
| shok-tor | kiss | Standard, colloquial | VLD |
| teraya-martaya | hug (children's word) | Standard, colloquial | VLD |
| tonk'peh | hello (casual) | Standard, colloquial | VLI lessons |
| lok | penis | Standard, slang | VLD |

**Tools.**
- lexicon.py: E4 no longer treats two empty readings (names) as sound-alikes.
- lexicon.py: the length-*h* rule for compounds.

**Pending.**
- **The full VLD pass.** It waits on the attached VLD lists. VLD function words (nam-tor, du, ra, uf, rom, aru, lesek, osu, k', and the ko-mekh family) wait for that pass.
- **Re-rendering.** The lessons, grammar, phrasebook, other guides, the Lab and the course re-render at that build. They are templates, so the new spellings flow in. The Lab glosser's tidy step and the hard-coded "-ve" in lesson 6 and the course tip need updating then.

## Spec 1: orthography and morphology (3,457 entries, 18 Nov 2026)

New reference docs:
- `docs/orthography.md`: the native script (central staff, after ENT "The Seventh") and its writing direction by era (a proposal, still to be confirmed); the letters; spelling rules; hyphen, fusion and space; capitals; punctuation in romanization and in the script; numbers in writing.
- `docs/morphology.md`: the shape of a word (compounds are modifier-first, phrases head-first); every word-building ending, bound word, prefix, grammatical ending and particle, with what each attaches to; joining sound changes; how to make a new word.

Checker:
- **E12**: word-building endings fuse and bound words take a hyphen. Four words broke the rule and were fixed: *frighten* fes-t'au → fest'au, *enrage* skukh-t'au → skukht'au, and their -act forms.
- **W3**: an ending on an unusual base is flagged for review (9 words, listed in check_report.md).

Joining rule added: **a diphthong absorbs a like vowel** at a fused join (sekau + uth → sekauth, sharshei + ik → sharsheik). 20 forms changed: *-auuth* → *-auth* (16) and *-eiik* → *-eik* (4).

Rebuilt: *stillness* kevhol → shekahol, "stone-ness". It had been built on kev "still, yet", an English pun.

Fixed: *kolinahr* now has a pronunciation. It had been on the English-name list, which left its reading empty.

All 23 changed forms are appended to `analysis/respelled.csv`.

## Batch 24: the body, physiology and clinical medicine (3,645 entries, 18 Nov 2026)

Built from the setting's species design notes (18 Nov). The guide is the new `docs/anatomy.md`.

- 188 new entries, 0 errors, no earlier form or id changed.
- **8 proposed roots, awaiting approval:** *hesi* body, *wawar* fat, *pakit* guts, *sosha* kidney, *beik* milk, *keikh'esh* navel, *pik* sinew, *fulo* gland. *Hesi* and *fulo* were picked from the generator's short candidates, because words this common should be short; the generator's first form for "body" (*feimk'ef*) was replaced. Each entry's notes say "Awaiting approval".
- **180 built words**, transparent compounds in the manner of German and Japanese medicine:
  - **Body and tissue:** tissue "body-cloth", organ "body-part", joint "bones joined", marrow "bone-fat", pelvis "hip-bowl", gland, secretion, mucosa.
  - **Blood:** artery "heart-river", capillary "little vessel", heart chamber and valve, plasma, clot "blood-stone", the copper carrier *plak-khrein* "blood-copper" (not Earth hemocyanin), blood type, transfusion, anemia, copper deficiency and poisoning, the immune system "body-guard", pathogen "illness-seed", inflammation "fire-swelling".
  - **Breath, heat and water:** oxygen "breath-element", airway, diaphragm "breath-wall", core temperature (cooler than Human; no figure), thermoregulation, cold stress, the kidney and urinary words, electrolyte "body-salt", water balance.
  - **Digestion and medicine:** digest, absorb "drink in", metabolism "body-burning", "fast in, slow out", dose, sedative, stimulant, analgesic, anesthetic.
  - **Nerves:** spinal cord, brainstem "brain-root", cerebellum "little brain", synapse, reflex, proprioception, concussion, *neural burn* (a setting term), the psi cortex.
  - **Reproduction**, following REP-01 to REP-05 and AND-01:
    - the male protective base *haushmik-virvu* (fandom's "sheath": responsive, non-locking) and the distal region *nal-kiruk*; retract and extend;
    - ovary "egg-vessel", follicle "egg-nest", cervix "womb-neck", ovulation and induced ovulation;
    - conception *suni-karuth* "the kindling of a life", placenta "child-root", embryo, fetus, lactation;
    - *vauksakh-pon* "the first time" (a Vulcan's first pon farr; euphemism).
  - **The cycle and plak tow, every concept in the species notes with its own word:**
    - the long cycle, the cycle gland, the prodrome, the fever threshold (on *lee'il-shuk'* "threshold", door-edge);
    - the fever spiral, decompensation, stabilize, resolve, the after-rest, the fever-scar (sensitization);
    - bond co-regulation *koon-shimyak*, the clinical *er-shimyak-toruth*, and medical stabilization;
    - **the healer's link *vo-koon*** and its disparaging name ***stik-koon* "the borrowed bond"** (HEAL-01, HEAL-02);
    - informed and surrogate consent.
  - **Water economy:** aquifer, well-right, irrigation "water-leading", water-steward, water-share.
- *Hafei-plak* "menstruation": the entry now notes that scant, reabsorbed shedding is a working hypothesis.
- The Classical sweet-rite forms in the species notes are still not imported, as the notes require.
- **Tools:** `lexicon/derivations.csv` was reconciled with the working copy. The batch 21–23 rows and the courtship, suitor and sweetheart audit fixes were kept, and *stillness* now reads "stone-ness" there too, so `derivation.py` can no longer undo it.

## Batch 25: numbers, counting and the seven-count (3,688 entries, 18 Nov 2026)

Arcadia approved batch 24's eight roots (*hesi* body, *wawar* fat, *pakit* guts, *sosha* kidney, *beik* milk,
*keikh'esh* navel, *pik* sinew, *fulo* gland) and decided the counting question: **base ten for daily life and
science, with a ritual count by sevens beside it.**

- 43 new entries, 0 errors, no earlier form or id changed. All built from older words; no new roots.
- **Arithmetic:** subtract *srur-wa* "take away", multiply *ok'-tor* "make many", remainder, digit "finger-number"
  (Latin *digitus*), numeral, integer "whole number", even "pair-number" and odd "unpaired number" (as Japanese
  *guusuu*, *kisuu*), prime "undivided number", square and cube "second and third power", square root "two-root",
  fraction "part-number" (Japanese *bunsuu*), a fifth, a tenth, decimal, decimal point, negative number, infinite,
  estimate, approximately, exactly.
- **Order and frequency:** hundredth, thousandth; once, twice, three times (*vauk-pon* "one time");
  distributives by repeating the number (*vauk-vauk* one by one, *yik-yik* two by two).
- **Sets and spans:** trio *veetot*, foursome *irot*, decade, millennium, abacus *shil-sheka* "count-stones"
  (Latin *calculus* "pebble"), none *suhk-vauk* "not one".
- **The two counts:** the ten-count *vak-shil* and the ceremonial seven-count *huk-shil*: its unit *hukot* "a seven",
  the great seven *huk-hukot* (forty-nine), the seven-year *huk-ka'ke*, and *hukuk* "sevenfold", in rites "complete".
- Docs: `docs/word-building.md` (numbers) and `docs/orthography.md` §7.

## Batch 26: mind and method (3,800 entries, 18 Nov 2026)

Logic, games, science, technology, the starship and medicine. 112 new entries, all built from older words; 0 errors;
no earlier form or id changed. Twenty planned words already existed (conclusion *liyanuth*, analysis *sotauth*,
navigation *vikezhuth*, warp drive *gar-toos* and others) and were reused rather than added twice.

- **Logic and reasoning (Unified, the era of Surak's logic):** premise *khriv-seenoom* "the ground of reasoning",
  infer, deduce *vosan-liyan* "conclude from the law", induction *ok'-liyanuth* "concluding from many", theorem
  *sekil-vosan* "proven law", axiom *ishuk-patuhol* "root-truth", disprove, refute *fivunuth-yath* "break the
  argument", valid *sekiluk*, fallacy *seli-seenoom*, paradox *yik-patuhol* "two truths", contradiction, consistent
  *vauk-motoluk* "of one way", tautology "same-saying", imply *khat-pokok* "say within", probable *li-kupuk*,
  uncertain, model *nahp-si'an* "thought-form", synthesis, irrational, bias *vauk-peisat* "one-side", subjective
  *lu-naluk* "self-feeling" and objective, binary, category *nuk-gor* "group-name", classify, analogy, ambiguous
  *yik-motoluk* "two-wayed", accurate, reasoning, hypothesize.
- **Games:** move (a piece), game board, opponent, draw *yakuh-nawak* "equal end", gambit *krokh-motol*
  "sacrifice-way", score, match, tournament *sikilot*, novice, dice *vukol-sheka* "chance-stones", luck, wager,
  three-dimensional chess *veet-sikil-sasheish* "the three-board game", and kal-toh's rod *koru-vakik* and lattice.
- **Science:** acceleration, chemical compound and reaction, electric charge, wavelength, warp factor, impulse drive
  *weellir-toos* "near-engine", dimension, evolution *suni-falavuth* "life-change", climate, microbe, virus.
- **Technology and the ship:** code, algorithm, password *skas-pifo* "key-word", input and output, software
  *cheilfer-kash* "machine-mind" and hardware *cheilfer-hesi* "machine-body", malfunction "machine-sickness",
  override, backup, reactor *tekak-kekru* "energy-heart", generator, battery, wire, cable, alloy, laser *fise-troos*
  "focused light", interface *khi-itat* "between-face", device, alert, evacuate, orbit, ensign, mission, ship's
  log, stardate *mune-tanakh* "star-day", quarters, airlock *funa-sral* "breath-lock", curriculum, data file.
- **Medicine:** vaccine *pu-nazhe* "fore-cure", surgery, physician, sickbay.
