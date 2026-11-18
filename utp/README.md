# UTP: the conlang engine

The UTP (named for Hoshi Sato's universal translator program) builds and runs alien languages with the method the Vulcan project proved:

- a proto-language and sound laws per branch
- roots generated against the sound system
- later meanings built from older words
- eras, a dictionary that never lists anything twice, and sentences rendered from meaning

It runs **offline**: Python 3.8+ and nothing to install. Language models are optional: a local model (Ollama, LM Studio, llama.cpp) or a hosted one (Anthropic Claude, OpenAI), set in one place. Speech uses your own Kokoro server.

**Status (2026-11-18):** phases 1 and 2 done, the offline toolkit, and the app: new languages from one command, model-assisted growth with review, a Lab and a course for every language, and a chat app (browser or Electron desktop). See `docs/design.md` for the plan and `OFFLINE.md` for setup on your own machines.

## What it does

| | |
|---|---|
| **Build a whole language** | `utp.py build <pack>` makes 8,000+ dictionary entries from a universal registry of 4,100 meanings (Concepticon) and nine derivation templates. Roots come from the pack's sound system and laws, and every entry passes the Vulcan checks (E1–E11, W1). Builds are deterministic, and a rebuild keeps every existing word. |
| **Say sentences in it** | `utp.py render <pack> frame.json`: one language-neutral meaning frame, rendered by each pack's grammar. `utp.py parse` reads a sentence back into a frame. |
| **Use it with a language model** | `LLM-INSTRUCTIONS.md` is the system prompt for any model (Ollama, LM Studio, Open WebUI). `utp.py context` hands the model exactly the dictionary entries a request needs. `propose` and `curate` let a model suggest derivations and prune junk meanings, and every suggestion is checked and waits for your approval. |
| **Hear it** | `utp.py say <pack> "..."` sends the pack's IPA to Kokoro-FastAPI as phonemes, so Vulcan is spoken as Vulcan, not read as English spelling. |
| **Make a new one** | `utp.py new <name>` makes `languages/<name>/`: settings, sound laws, a first dictionary of about 9,500 words, its grammar card, Lab, course, and `open.py`. |
| **Grow it with a model** | `utp.py expand <name> "<topic>"` asks a model for a batch of new words, compounds of older words first. Every row is checked (unknown or newer parts, duplicates, self-reference) and saved to `batches/` for review; `utp.py apply` adds the rows you approve and rebuilds the dictionary, Lab and course. `utp.py sentences` writes course sentences as meaning frames, and only ones that render and read back are kept. Works for Vulcan too, through Vulcan's own pipeline. |
| **The app** | `utp.py app` (or `desktop/` for Electron): chat with any model, languages and a file tree on the left, opened files rendered (Markdown, CSV, Labs, courses), batches reviewed with tick boxes, and slash commands for every tool. Labs and courses opened through it gain a tutor panel. |
| **Learn it** | `tutor.py drill` (spaced repetition, oldest words first, with audio) and `tutor.py talk` (conversation with a local model, dictionary-checked every turn, spoken through Kokoro). `talk --language Spanish` works for any human language your model knows. |

## Rule one: the Vulcan build never breaks

The Vulcan pack only **reads** `vulcan-conlang/`, and the builder refuses to build it. `vulcan-conlang/tools` still makes the Vulcan dictionary, exactly as before. `tests/test_vulcan_pack.py` proves on every run that no Vulcan file changes and that the core reproduces every entry. Growing Vulcan (`expand`, `apply`) writes only to `vulcan-conlang/lexicon/derivations.csv` and `meanings.csv`, for rows you approved, then runs Vulcan's own tools.

## Tests

```
python3 utp/tests/test_vulcan_pack.py     no-touch + the whole Vulcan dictionary reproduced
python3 utp/tests/test_builder.py         8,000+ entries, 0 errors, deterministic, frozen rebuilds, no duplicates
python3 utp/tests/test_interlingua.py     52 phrasebook frames: template, text and parse-back; Romulan; SVO sample
python3 utp/tests/test_offline_tools.py   model, Kokoro and tutor against mock servers (localhost only)
python3 utp/tests/test_app.py             Anthropic/OpenAI/Ollama, new, expand, apply, sentences, the app server, Vulcan's pipeline
```

Last run (2026-11-18): all five pass.

## Commands

Run `python3 utp/utp.py` with no arguments for the full list. The main ones:

```
utp.py build sample                    build a pack's dictionary into packs/sample/build/
utp.py render vulcan '{"subject":{"pron":"1sg"},"goal":{"head":"house"},"verb":"go","tense":"future"}'
                                       -> Nash-veh fukhinfi dungi lish.
utp.py parse vulcan "Fa tu lish-pil?"  -> the frame: where, you, go, ongoing
utp.py context vulcan "how do I say the teacher came"
utp.py say vulcan "Sik tok nash-veh kon" --out anger.wav
tutor.py drill vulcan --speak
tutor.py talk vulcan --speak
```

## Layout

| Path | Role |
|---|---|
| `core/sca.py`, `core/phonotactics.py` | Sound laws as a family tree; legal roots |
| `core/lexicon.py` | Rows to forms: roots, compounds, loans, branch-only coinages, exceptions, spelling standard |
| `core/builder.py` | The whole-language builder: meanings, seeded roots, built words, checks, frozen rebuilds, outputs |
| `core/interlingua.py` | Phase 2: meaning frames, rendering by pack grammar, parsing back |
| `core/models.py` | The one model connection: Anthropic, OpenAI-compatible, Ollama; streaming; settings in `~/.utp/config.json` |
| `core/llm.py` | Dictionary context for models, grammar card, checked proposals |
| `core/newlang.py` | `utp.py new`: a language folder from a few choices (word order, branches, eras, sounds) |
| `core/expand.py` | Model-assisted growth: batches, checks, apply and rebuild, course sentences, topic suggestions |
| `core/learn.py` | Each language's Lab and course pages |
| `app/` | The app: `server.py` (standard library), `ui/` (chat, files, settings), the Lab and course templates, the tutor panel |
| `core/speech.py`, `core/kokoro_vocab.json` | Kokoro-FastAPI client; pack readings mapped onto Kokoro's 114 phoneme symbols |
| `concepts/` | The universal meaning registry (`concepts.csv`, from Concepticon, CC BY 4.0), derivation and grammar templates, the English blocklist, `build_concepts.py` |
| `packs/vulcan/` | Vulcan family: points at `vulcan-conlang/`; grammar for Standard Vulcan and Romulan; speech settings |
| `packs/sample/` | A test fixture: an SVO, prepositional language built at full scale. Copy it to start a real language |
| `LLM-INSTRUCTIONS.md` | Prompts for translator, tutor and builder roles; chat-app setup |
| `tutor.py`, `utp.py` | Lessons; command line |
| `../languages/` | Languages made with `utp.py new` |
| `../desktop/` | The Electron shell |

## Starting a new language

```
python3 utp/utp.py new nerani --language Nerani --order SOV --branches high,low \
    --eras Ancient,Old,Middle,Modern --consonants "p t k m n s l r w y h sh" --vowels "a e i o u"
```

or **+ New** in the app. Then:

1. Describe the speakers in `languages/nerani/DESIGN.md`. Every model prompt reads it.
2. Give the branches their sound changes in `sound_laws.json` (each rule: `id`, `pattern`, `replace`, `note`, `era`), and tune `pack.json` (generator weights, grammar, speech). Rebuild with `utp.py build nerani`.
3. Grow it: `utp.py expand nerani "kinship and the household"`, review the batch, `utp.py apply`. Add course sentences with `utp.py sentences`.
4. Open it: `python3 languages/nerani/open.py`, the desktop app, or `lab/index.html` straight from the folder.
