# UTP
Universal translation program (con-language creator) w/languages such as vulcan built from it.

The UTP builds whole constructed languages the way natural languages grow: a proto-language, sound laws for each daughter language, roots checked against the language's sound rules, later meanings built from older words, and eras. Everything else (dictionaries, guides, phrasebooks, lessons, speech) is generated from one dictionary file, so nothing drifts out of date.

Vulcan is the first language built with it: a historically layered family from Tribal Vulcan through Classical and Unified to Federation Standard, with Romulan splitting away at the Sundering. 3,645 dictionary entries so far, 0 errors. Andorian (Andorii and Aenar) is the second, being built from canon, the licensed novels, fan work and real-world parallels by the method in `utp/METHOD.md`.

It is made for science-fiction and fantasy writers, game masters and players (Star Trek Adventures tables included): a polyglot language workshop that runs on your own computer, with or without a model.

## Building a language: from nothing, or from sources

Every language follows the same steps (`utp/METHOD.md`): gather sources, find the words they already use, decide the design question by question, find sound laws that produce the attested words, then grow the vocabulary in reviewed batches. In the app, each language's **Workshop** has a page per step.

- **Sources** go into a private library for each language (SQLite with full-text search, plus meaning-based search if you set an embedding model): scripts, subtitles, saved wiki pages, novels, papers, your notes. Each source has a tier: your own decisions, canon, licensed, fan, or real-world science. Your library stays on your computer; only files in `sources/public/` are published with the language.
- **Attested words** are found by a model and kept only if they really appear in the passage they cite.
- **Design** questions (who speaks it, their bodies, world, history, sound, grammar, persons, registers...) come with options argued from canon, body, world, society, history, sound and use, with citations. Your answers go into `DESIGN.md`, which every later prompt reads.
- **Sound laws** are proposed by a model and run by the engine on every attested word; accepted laws lock those words into the dictionary, and every build checks them.

With no sources, the same steps work from scratch: Design asks you instead of citing.

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

**Double-click** `Start UTP.command` (macOS), `Start UTP.bat` (Windows) or `start-utp.sh` (Linux). Each language folder has its own `Open <Language>` file that opens the app straight on that language. Once it's running, **Settings → Startup → Make desktop and menu shortcuts** puts UTP in your Applications folder, Start menu or app launcher.

From a terminal:

```
python3 utp/utp.py app                          # the app: chat, languages, files, Labs and courses, in your browser
python3 utp/utp.py new nerani --language Nerani --order SOV   # a new language, with its Lab and course
python3 utp/utp.py expand vulcan "weather and the sky"        # a model proposes words; you approve; apply rebuilds
python3 utp/tests/test_vulcan_pack.py           # the engine reproduces the Vulcan dictionary exactly
```

The app also runs in its own window (Electron): `cd desktop && npm install && npm start`. With Node.js installed, the double-click files use the window automatically.

**Settings** (bottom left in the app, or Ctrl/Cmd+, in the window) is one page for everything:

- **Models:** as many connections as you like, local or hosted: Ollama, any OpenAI-compatible server (LM Studio, llama.cpp, vLLM, Open WebUI, OpenAI) or Anthropic's Claude. Add, edit, test, delete. One connection chats, another can build (for example, a local model to chat and Claude to grow the dictionary). The chat bar can switch connections for one conversation.
- **Appearance:** light, dark, or follow the system, for the app and every Lab and course (each page also has its own switch at the top).
- **Speech:** the Kokoro address and voice.
- **Folders:** where new languages are made, and any other folders to show in the file list.
- **Startup:** desktop window or browser, the port, which Python the window uses.

Everything is saved in `~/.utp/config.json`, readable only by you; API keys never reach the page. `python3 utp/utp.py config` does the same from a terminal. With a local model nothing leaves your machine. Setup details: `utp/OFFLINE.md`.

## Status

- Vulcan: anatomy and clinical medicine added (batch 24); eight proposed roots await approval.
- Next: the number system and logic-game vocabulary, then technical vocabulary toward 6,000 entries.
- Andorian: library seeded (canon, licensed, fan, science), 56 attested words and names, seven design questions drafted and waiting for decisions.
- UTP: new languages, the workshop (sources library, audit, design, sound laws), model-assisted growth with review, a Lab and course per language, and the chat app are done. The typology checker, script module and a second, canon-anchored pack (Klingon is the leading candidate) are planned; see `utp/docs/design.md`.

## License and credits

Code and original material: Apache License 2.0 (`LICENSE`). Star Trek names and on-screen terms belong to their owners; see `NOTICE` for what that covers and for the sources this work draws on.
