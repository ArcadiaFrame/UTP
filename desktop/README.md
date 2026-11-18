# UTP desktop (Electron)

The UTP app in its own window. It starts the same local server the browser version uses
(`utp/app/server.py`, Python standard library only) and shows it; closing the window stops it.
Nothing leaves your machine unless you choose a hosted model (Anthropic or OpenAI) in **Model** settings.

## Run from the repository

Needs Node.js 18+ and Python 3.8+.

```
cd desktop
npm install
npm start                                  # the whole app
npm start -- --language vulcan             # opened on one language
npm start -- --language vulcan --page lab  # straight to its Lab
```

No Electron? The same app runs in any browser: `python3 utp/utp.py app`, or `python3 languages/<name>/open.py`.

## Build an installer

```
npm run dist        # AppImage (Linux), .dmg (macOS) or installer (Windows) in desktop/dist/
```

The installer bundles the repository (engine, languages, Labs and courses); it still uses the
Python already on the computer. Set `UTP_PYTHON` if Python is not on the PATH.

## Models

Choose in the app under **Model** (bottom left), or from the command line:

```
python3 utp/utp.py config --provider ollama --url http://localhost:11434/v1 --model qwen3.5:9b
python3 utp/utp.py config --provider openai --url http://localhost:1234/v1 --model <name>   # LM Studio
python3 utp/utp.py config --provider anthropic --model claude-sonnet-5-5 --key sk-ant-...
```
