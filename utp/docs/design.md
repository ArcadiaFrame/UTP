# UTP design

## Why

Building Vulcan produced a working method:
- a proto-language with sound laws per branch
- roots generated against a phonotactic check
- meanings built by derivation from older words
- eras
- a dictionary that everything else is generated from

The UTP lifts that method out of Vulcan, so the same engine can build and run any alien language offline. Each new language then tests whether the method is truly general.

## Rule one: the Vulcan build never breaks

The core is new code beside the Vulcan tools, not a rewrite of them. The Vulcan pack only reads `vulcan-conlang/`, and the builder refuses to build it. `tests/test_vulcan_pack.py` proves both points on every run: nothing changes, and the core reproduces every entry.

The Vulcan pipeline (`derivation.py > lexicon.py build > export.py > build_lab.py > build_course.py`) stays the way Vulcan is built. If the Vulcan tools ever switch to the core, that happens only after the test shows byte-identical output, and only if the language's author decides to.

## Layers

| # | Layer | What it does | Phase | Status |
|---|---|---|---|---|
| 1 | Typology profile | A pack's settings: order, noun phrase, alignment, morphology, obligatory categories, prosody, script. Later, a harmony checker | 1 (data), 3 (checker) | Profiles for Vulcan, Romulan and the sample; checker pending |
| 2 | Phonology | Inventory, syllable rules, spelling standard, reading aloud | 1 | Done |
| 3 | Family tree | Proto-language and branches; daughters made by sound laws | 1 | Done |
| 4 | Lexicon | Universal meaning registry, roots, nine derivation templates, compounds, loans, branch-only coinages, exceptions, the E1–E11 checks, frozen rebuilds | 1 + offline toolkit | Done: 8,000+ entries per language |
| 5 | Interlingua | Language-neutral meaning frames; each pack's grammar renders them; the parser reads sentences back | 2 | Done for Vulcan, Romulan and an SVO sample |
| 6 | Script | Script type, glyphs and their origins, the era spelling froze | 4 | Pending |
| 7 | Contact and accent | Loanword reshaping, accent and learner-error prediction between packs | 5 | Pending |
| 8 | Output and learning | Dictionaries, model instructions and context, Kokoro speech, spaced-repetition drills, conversation tutor; a Lab and course generated for every language | offline toolkit, app | Done (Vulcan keeps its own Lab and course too) |
| 9 | Growth and the app | `utp.py new`; model-proposed batches checked and approved before they join; course sentences as frames; one model connection (Anthropic, OpenAI-compatible, Ollama); the chat app with files, Labs and courses, in a browser or Electron | app | Done 2026-11-18 |

## Phases

1. **Core + first pack.** Done 2026-11-14.
2. **Interlingua.** Done 2026-11-14. See below.
3. **Typology checker.** Feature correlations from WALS and Dryer; a flagged choice needs a history note. Vulcan's verb-final order with prepositions is the first case.
4. **Script module.**
5. **Contact and accent module.**
6. **Second real pack, unlike Vulcan, anchored in a canon language.** Candidates below.

### The offline toolkit (between phases 1 and 2)

- **Meaning registry.** `concepts/concepts.csv` holds 4,100 meanings from Concepticon 3.4. They are tiered by the same anthropological rule as Vulcan: Swadesh and Leipzig–Jakarta meanings are the oldest roots; World Loanword Database and Intercontinental Dictionary Series meanings are basic; colour terms follow Berlin–Kay; "modern world" meanings come last. 316 meanings are recognised as built from others (teacher = teach + agent, leader = lead (guide) + agent, sweet potato = sweet + potato), checked by hand against false friends (busy is not bus + y; a sweater is not one who sweats).
- **Templates.** Agent, action, place, instrument, abstract, adjectival, causative, negative and diminutive grow the registry past 8,000. A template meaning is never made when the registry already has that meaning.
- **Builder.** Seeded roots, every Vulcan check, an English blocklist (16,133 words from Concepticon's English labels), automatic regeneration of a new root when a built word lands on its spelling, deterministic output and frozen rebuilds. The sample pack builds 9,584 entries with 0 errors in under a second.
- **Models.** An OpenAI-compatible client with Ollama as the default, plus `LLM-INSTRUCTIONS.md`. Retrieval hands the model the dictionary entries a request needs. Proposals that name unknown, newer or circular parts are rejected; the rest wait for approval in a CSV.
- **Speech.** Kokoro-FastAPI's phoneme endpoint. Every one of the 3,440 Vulcan words maps onto Kokoro's 114 symbols with nothing dropped.
- **Tutor.** Leitner spaced repetition, oldest words first, audio on every card, and conversation with the dictionary checked on every turn. It also teaches human languages.

These are tested against mock servers. They have not yet been run against a real Ollama or Kokoro server.

### Phase 2 results

A frame names meanings by dictionary key and carries type, arguments, tense and aspect, modality, negation, evidence, the noting particle, speech level, rank relation, wh-focus, content clauses, conditions and vocatives. Each pack's `grammar` section gives clause and noun-phrase order, pronouns, possessives, question words and every marker with how it attaches: hyphen, fused suffix, prefix, or a separate word before or after the phrase.

Against the Vulcan phrasebook (`tests/test_interlingua.py`):
- **52/52** frames render the phrasebook's own template, key for key.
- **38/38** realize to the phrasebook's Vulcan text letter for letter.
- **52/52** parse back to a frame that says the same sentence.
- **51/52** parse back to the identical frame.

The same 52 frames render in Romulan (rank endings, no evidentials) and parse back. The SVO sample language renders and parses its own set. One frame said three ways:

- Vulcan: *Mamweekh keru vavkon t'omyan-wizh sokzha-un.*
- Romulan, said up to a superior: *Mamweekh kiru vavkoan thomyan-wizh rokzha-un'nra.*
- SVO sample: *Wu stal tefap holuuk nezcho.*

Not yet covered: relative clauses (*lith*), comparison (*t'ei li*), the exclamative, coordination (*e*, *khe*), and sentences of more than one clause other than if-clauses and reported speech.

**Phrasebook findings, still to be ruled on.** Writing frames for the phrasebook turned up four places where the phrasebook disagrees with itself or with the dictionary:
- **p61, p121:** *-fi* is hyphenated (`{school}-{toward}`, `{scale-w}-{toward}`), but fused everywhere else (`{house}{toward}`, `{oasis}{toward}`).
- **p126:** the manner adverb is fused and follows the verb (`{breathe} {slow}{adverbial}`), but elsewhere it is hyphenated and comes before (`{slow}-{adverbial} {speak}`).
- **p147:** uses `{secret}`, an adjective in the dictionary, as a noun. The dictionary's noun is `{secret-n}`. As written, the line can also be read "steal the secret defendant".

## Phase 6: canon candidates

The condition: the second real pack must be grounded in an on-screen canon alien language with a fitting structure.

| Language | What canon establishes | Unlike Vulcan in | Canon data | Fit |
|---|---|---|---|---|
| **Klingon** (tlhIngan Hol) | Okrand's grammar: object–verb–subject; nominative–accusative; primarily suffixing and agglutinative; verb prefixes mark subject and object; five ordered noun-suffix types and ten verb-suffix types; aspect without tense; three noun classes. In canon, Hoshi Sato became the first fluent Human in 2151 | Verb before subject; the verb carries both arguments; aspect only; noun classes | Complete published grammar | Best proof of generality with the least invention |
| **Xindi-Aquatic** | High and low pitched hums like whale song; switches to sonar for the past tense | A tonal, sung language | Sound and one grammar fact | The tonal candidate; room for a Tagalog-style voice system |
| **Xindi-Insectoid** | Clicking language, 67 dialects; names lengthen with age | Dialect continuum; clicks | A few facts | Tests the family tree with many sister dialects |
| **Tamarian** | Words translate but the structure does not; speech by reference to stories | Meaning in shared narrative | Episode dialogue | Stress test for the interlingua |
| **Kreetassan** | Each word has many meanings by context | Heavy polysemy | One fact | Too thin alone |

No canon language is documented with a Philippine-type voice system or ergative alignment.

**Recommendation:** Klingon. Its structure is fully canon, and it differs from Vulcan on the axes that test the engine.

Sources: Klingon grammar (Wikipedia, after Okrand, *The Klingon Dictionary*); Memory Alpha, "Xindi-Aquatic language", "Xindi-Insectoid", "Klingonese"; Wikipedia, "Darmok", "Vox Sola".
