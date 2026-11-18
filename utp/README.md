# UTP: the conlang engine

The UTP (named for Hoshi Sato's universal translator program) builds and runs alien languages with the method the Vulcan project proved:

- a proto-language and sound laws per branch
- roots generated against the sound system
- later meanings built from older words
- eras, a dictionary that never lists anything twice, and sentences rendered from meaning

It runs **offline**: Python 3.8+ and nothing to install. Language models and speech are optional add-ons that use your own local servers.

**Status (2026-11-14):** phases 1 and 2 done, plus the offline toolkit. See `docs/design.md` for the plan and `OFFLINE.md` for setup on your own machines.

## What it does

| | |
|---|---|
| **Build a whole language** | `utp.py build <pack>` makes 8,000+ dictionary entries from a universal registry of 4,100 meanings (Concepticon) and nine derivation templates. Roots come from the pack's sound system and laws, and every entry passes the Vulcan checks (E1–E11, W1). Builds are deterministic, and a rebuild keeps every existing word. |
| **Say sentences in it** | `utp.py render <pack> frame.json`: one language-neutral meaning frame, rendered by each pack's grammar. `utp.py parse` reads a sentence back into a frame. |
| **Use it with a language model** | `LLM-INSTRUCTIONS.md` is the system prompt for any model (Ollama, LM Studio, Open WebUI). `utp.py context` hands the model exactly the dictionary entries a request needs. `propose` and `curate` let a model suggest derivations and prune junk meanings, and every suggestion is checked and waits for your approval. |
| **Hear it** | `utp.py say <pack> "..."` sends the pack's IPA to Kokoro-FastAPI as phonemes, so Vulcan is spoken as Vulcan, not read as English spelling. |
| **Learn it** | `tutor.py drill` (spaced repetition, oldest words first, with audio) and `tutor.py talk` (conversation with a local model, dictionary-checked every turn, spoken through Kokoro). `talk --language Spanish` works for any human language your model knows. |

## Rule one: the Vulcan build never breaks

The Vulcan pack only **reads** `vulcan-conlang/`, and the builder refuses to build it. `vulcan-conlang/tools` still makes the Vulcan dictionary, exactly as before. `tests/test_vulcan_pack.py` proves on every run that no Vulcan file changes and that the core reproduces all 3,440 entries.

## Tests

```
python3 utp/tests/test_vulcan_pack.py     no-touch + the whole Vulcan dictionary reproduced
python3 utp/tests/test_builder.py         8,000+ entries, 0 errors, deterministic, frozen rebuilds, no duplicates
python3 utp/tests/test_interlingua.py     52 phrasebook frames: template, text and parse-back; Romulan; SVO sample
python3 utp/tests/test_offline_tools.py   model, Kokoro and tutor against mock servers (localhost only)
```

Last run (2026-11-14): all four pass.

## Commands

Run `python3 utp/utp.py` with no arguments for the full list. The main ones:

```
utp.py build sample                    build a pack's dictionary into packs/sample/build/
utp.py render vulcan '{"subject":{"pron":"1sg"},"goal":{"head":"house"},"verb":"go","tense":"future"}'
                                       -> Nash-ve fukhinfi dungi lish.
utp.py parse vulcan "Fa tu lish-pil?"  -> the frame: where, you, go, ongoing
utp.py context vulcan "how do I say the teacher came"
utp.py say vulcan "Sik tok nash-ve kon" --out anger.wav
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
| `core/llm.py` | Optional model client (OpenAI-compatible), dictionary context, checked proposals |
| `core/speech.py`, `core/kokoro_vocab.json` | Kokoro-FastAPI client; pack readings mapped onto Kokoro's 114 phoneme symbols |
| `concepts/` | The universal meaning registry (`concepts.csv`, from Concepticon, CC BY 4.0), derivation and grammar templates, the English blocklist, `build_concepts.py` |
| `packs/vulcan/` | Vulcan family: points at `vulcan-conlang/`; grammar for Standard Vulcan and Romulan; speech settings |
| `packs/sample/` | A test fixture: an SVO, prepositional language built at full scale. Copy it to start a real language |
| `LLM-INSTRUCTIONS.md` | Prompts for translator, tutor and builder roles; chat-app setup |
| `tutor.py`, `utp.py` | Lessons; command line |

## Starting a new language

1. Copy `packs/sample` to `packs/<name>`.
2. Write its proto sound system and branch laws in `sound_laws.json`, and its generator weights, eras, grammar and typology in `pack.json`.
3. Put culture words and canon anchors in `meanings.csv` (`key, gloss, pos, field, era, kind, proto, parts, attested_<branch>`).
4. Run `utp.py build <name>`. Check `build/check_report.md`, then refine with `propose` and `curate`.
