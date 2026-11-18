# UTP
Universal translation program (con-language creator) w/languages such as vulcan built from it.

The UTP builds whole constructed languages the way natural languages grow: a proto-language, sound laws for each daughter language, roots checked against the language's sound rules, later meanings built from older words, and eras. Everything else (dictionaries, guides, phrasebooks, lessons, speech) is generated from one dictionary file, so nothing drifts out of date.

Vulcan is the first language built with it: a historically layered family from Tribal Vulcan through Classical and Unified to Federation Standard, with Romulan splitting away at the Sundering. 3,645 dictionary entries so far, 0 errors.

## What's here

| Folder | What it is | Start with |
|---|---|---|
| `vulcan-conlang/` | The Vulcan and Romulan language: dictionary, grammar, pronunciation, phrasebook, lessons, tales, the course and the tools that build them | `vulcan-conlang/README.md` |
| `utp/` | The language-independent engine: packs, the builder, the interlingua (meaning frames rendered in any pack's grammar), model-assisted growth, Labs and courses, the app server, Kokoro speech and a tutor | `utp/README.md` |
| `languages/` | Languages made with `utp.py new`, each with its own dictionary, Lab, course and launcher | `languages/README.md` |
| `desktop/` | The app in its own window (Electron) | `desktop/README.md` |

## Read it in a chat

Any assistant that can read a GitHub link can use the language. Point it at `vulcan-conlang/README.md`, then the dictionary files in `vulcan-conlang/docs/`. The rule for every assistant: look up every word; never invent a word silently. `utp/LLM-INSTRUCTIONS.md` has ready prompts for translating, tutoring and proposing new words.

## Run it

Python 3.8 or newer, nothing else to install.

```
python3 utp/utp.py app                          # the app: chat, languages, files, Labs and courses, in your browser
python3 utp/utp.py new nerani --language Nerani --order SOV   # a new language, with its Lab and course
python3 utp/utp.py expand vulcan "weather and the sky"        # a model proposes words; you approve; apply rebuilds
python3 utp/tests/test_vulcan_pack.py           # the engine reproduces the Vulcan dictionary exactly
```

The app also runs in its own window: `cd desktop && npm install && npm start`.

**Models:** one setting for everything, local or hosted: Ollama, any OpenAI-compatible server (LM Studio, llama.cpp, vLLM, OpenAI) or Anthropic's Claude. Choose under **Model** in the app, or `python3 utp/utp.py config --provider ...`. With a local model nothing leaves your machine. Setup details: `utp/OFFLINE.md`.

## Status

- Vulcan: anatomy and clinical medicine added (batch 24); eight proposed roots await approval.
- Next: the number system and logic-game vocabulary, then technical vocabulary toward 6,000 entries.
- UTP: new languages, model-assisted growth with review, a Lab and course per language, and the chat app are done. The typology checker, script module and a second, canon-anchored pack (Klingon is the leading candidate) are planned; see `utp/docs/design.md`.

## License and credits

Code and original material: Apache License 2.0 (`LICENSE`). Star Trek names and on-screen terms belong to their owners; see `NOTICE` for what that covers and for the sources this work draws on.
