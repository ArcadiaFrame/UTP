# Running the UTP offline

Everything runs on your own machines. The engine needs Python 3.8 or newer and nothing else. A local model server and a local Kokoro server are optional.

## 1. The engine

Clone the repository and run from its top folder (the one holding `utp/` and `vulcan-conlang/`):

```
python3 utp/tests/test_vulcan_pack.py      # should end ALL PASS
python3 utp/utp.py build sample            # 9,584 entries in about a second
```

The repository carries the Vulcan files the UTP reads: rules, sound-change and spelling tools, the dictionary, and the dictionary and grammar docs. The full Vulcan toolkit (export, Lab, course) is in `vulcan-conlang/tools/`.

## 2. A local model (optional)

Any OpenAI-compatible server works. Ollama is the default:

```
export UTP_LLM_URL=http://<server address>:11434/v1    # or http://localhost:11434/v1 on the same machine
export UTP_LLM_MODEL=qwen3.5:9b
```

LM Studio (`http://localhost:1234/v1`), a llama.cpp server or Open WebUI's API also work. Set `UTP_LLM_KEY` if the server wants a key.

**Open WebUI:** follow "Setting up a chat app" in `LLM-INSTRUCTIONS.md`. Load the dictionary files as a knowledge collection and use the "Translator and writer" section as the system prompt.

## 3. Kokoro speech (optional)

Run Kokoro-FastAPI in Docker on any machine with a GPU to spare, or on CPU:

```
docker run -p 8880:8880 ghcr.io/remsky/kokoro-fastapi-cpu:latest      # or kokoro-fastapi-gpu:latest
export UTP_KOKORO_URL=http://<that machine>:8880
python3 utp/utp.py say vulcan "Dif-tor heh smusma" --out greeting.wav
```

The UTP sends Vulcan to Kokoro's phoneme endpoint (`/dev/generate_from_phonemes`), not as text, so Kokoro speaks the IPA rather than guessing from English spelling. Human languages go through `/v1/audio/speech` with a voice for the language: English, British English, Spanish, French, Hindi, Italian, Japanese, Portuguese and Mandarin.

What to expect:
- Kokoro has no ɬ and no ejective stops. The Vulcan pack says ɬ as ʃl and an ejective as a stop plus a glottal stop; change `speech` → `map` in `packs/vulcan/pack.json` to taste.
- Stress is still an open design question. First-syllable stress is a placeholder.
- The voice is `bm_george` by default. Try `am_onyx`, `bm_lewis` or a voice blend.

## 4. Lessons

```
python3 utp/tutor.py drill vulcan --speak --n 20     # spaced repetition, oldest words first
python3 utp/tutor.py drill vulcan --reverse          # see the word, recall the meaning
python3 utp/tutor.py talk vulcan --speak             # conversation; every turn checked against the dictionary
python3 utp/tutor.py talk --language Japanese --speak
```

Progress is saved in `~/.utp/progress/`. Audio plays through `afplay` (macOS) or `aplay`/`paplay`/`ffplay` (Linux), and the last clip is always kept at `~/.utp/audio/last.wav`.
