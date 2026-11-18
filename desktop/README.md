# UTP desktop (Electron)

The UTP app in its own window. It starts the same local server the browser version uses
(`utp/app/server.py`, Python standard library only) and shows it; closing the window stops it.
Nothing leaves your machine unless you choose a hosted model (Anthropic or OpenAI) in **Settings**.

## Run from the repository

Needs Node.js 18+ and Python 3.8+.

```
cd desktop
npm install
npm start                                  # the whole app
npm start -- --language vulcan             # opened on one language
npm start -- --language vulcan --page lab  # straight to its Lab
npm start -- --settings                    # straight to Settings
```

Or double-click `Start UTP` in the repository (or a language's `Open <Language>` file): with Node.js installed
they open this window, running `npm install` the first time. **Settings → Startup** chooses the window or the
browser, and makes desktop and menu shortcuts.

No Electron? The same app runs in any browser: `python3 utp/utp.py app`, or `python3 languages/<name>/open.py`.

## Build an installer

```
npm run dist        # AppImage (Linux), .dmg (macOS) or installer (Windows) in desktop/dist/
```

The installer bundles the repository (engine, languages, Labs and courses); it still uses the
Python already on the computer. If Python is not on the PATH, give its path in **Settings → Startup**
(or set `UTP_PYTHON`).

## Settings

**File → Settings…** (Ctrl+,) or **UTP → Settings…** (Cmd+, on macOS) opens the same Settings page as the
browser: model connections (add, edit, test, delete; one to chat, one to build), speech, folders, startup.
They are saved in `~/.utp/config.json` (or `$UTP_HOME/config.json`). From a terminal:

```
python3 utp/utp.py config                                          # show the connections
python3 utp/utp.py config --name "Ollama on my desktop" --provider ollama --url http://desktop.local:11434/v1 --model qwen3.5:9b
python3 utp/utp.py config --name Claude --provider anthropic --model claude-sonnet-5-5 --key sk-ant-... --role build
```
