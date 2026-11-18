#!/usr/bin/env python3
"""Start the UTP app: what every double-click launcher runs.

  python3 utp/app/launch.py [--language vulcan] [--page lab|course] [--browser | --desktop]

- If the app is already running, it just opens another view of it (no second copy).
- Otherwise it opens the desktop window if that is installed (desktop/node_modules) and Settings
  say "auto" or "desktop", and the browser version if not. Settings > Startup chooses.
- `utp.py shortcut` (or the button on the Settings page) puts a UTP icon on your desktop and in
  your applications menu: a .desktop file on Linux, UTP.app on macOS, a shortcut on Windows.
"""
import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import urllib.request
import webbrowser

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO))
from utp.core import config as C  # noqa: E402

DESKTOP = REPO / "desktop"
ICON = HERE / "ui" / "icon.png"


def running(port):
    """True if this repository's app already answers on the port."""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=1.5) as r:
            return pathlib.Path(json.loads(r.read()).get("repo", "")).resolve() == REPO
    except Exception:
        return False


def electron():
    exe = DESKTOP / "node_modules" / ".bin" / ("electron.cmd" if os.name == "nt" else "electron")
    dist = DESKTOP / "node_modules" / "electron" / "dist"
    return exe if exe.exists() and dist.exists() else None


def page_url(port, language=None, page=None):
    url = f"http://127.0.0.1:{port}/"
    if language:
        url += f"#lang={language}" + (f"&page={page}" if page else "")
    return url


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--language")
    ap.add_argument("--page", choices=["lab", "course"])
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--browser", action="store_true")
    g.add_argument("--desktop", action="store_true")
    a = ap.parse_args(argv)
    cfg = C.load()
    port = int(cfg["app"].get("port") or 8765)
    mode = "browser" if a.browser else "desktop" if a.desktop else cfg["app"].get("open", "auto")

    if mode != "browser":
        exe = electron()
        if not exe and mode == "desktop" and shutil.which("npm"):
            print("Installing the desktop window (first time only, about a minute)…", flush=True)
            subprocess.run(["npm", "install", "--no-audit", "--no-fund"], cwd=DESKTOP, shell=os.name == "nt")
            exe = electron()
        if exe:
            args = [str(exe), str(DESKTOP)] + (["--language", a.language] if a.language else []) + (["--page", a.page] if a.page else [])
            flags = {"start_new_session": True} if os.name != "nt" else {"creationflags": 0x00000008}   # detached
            subprocess.Popen(args, cwd=DESKTOP, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **flags)
            print("UTP desktop window starting.")
            return 0
        if mode == "desktop":
            print("The desktop window is not installed (needs Node.js: cd desktop && npm install). Opening the browser version.")

    if running(port):
        webbrowser.open(page_url(port, a.language, a.page))
        print(f"UTP is already running: opened http://127.0.0.1:{port}/")
        return 0
    from utp.app import server
    args = ["--port", str(port), "--open"] + (["--language", a.language] if a.language else []) + (["--page", a.page] if a.page else [])
    return server.main(args)


# ---------- launchers inside a language folder ----------
def write_language_launchers(home, lang_id, label):
    """`Open <Language>.command` (macOS), `.bat` (Windows) and open.py, in the language's folder."""
    home = pathlib.Path(home).resolve()
    try:
        rel = os.path.relpath(REPO, home)
        inside = REPO in home.parents
    except ValueError:                         # another drive on Windows
        rel, inside = str(REPO), False
    repo_sh = f'"$(dirname "$0")/{rel}"' if inside else f'"{REPO}"'
    repo_bat = f"%~dp0{rel}" if inside else str(REPO)
    safe = "".join(ch for ch in label if ch.isalnum() or ch in " -_'") or lang_id
    cmd = home / f"Open {safe}.command"
    cmd.write_text(f'#!/bin/bash\n# macOS: double-click to open the UTP app on {label}.\nREPO={repo_sh}\n'
                   'PY="$(command -v python3 || command -v python)"\n'
                   f'exec "$PY" "$REPO/utp/app/launch.py" --language {lang_id} "$@"\n')
    cmd.chmod(0o755)
    (home / f"Open {safe}.bat").write_text(
        f"@echo off\r\nrem Windows: double-click to open the UTP app on {label}.\r\ntitle UTP: {label}\r\n"
        f'set "REPO={repo_bat}"\r\nwhere py >nul 2>nul\r\n'
        f'if %errorlevel%==0 ( py -3 "%REPO%\\utp\\app\\launch.py" --language {lang_id} %* & goto :eof )\r\n'
        f'python "%REPO%\\utp\\app\\launch.py" --language {lang_id} %*\r\n')
    tpl = (HERE / "open_template.py").read_text().replace("__REPO__", str(REPO)).replace("__LANG__", lang_id)
    (home / "open.py").write_text(tpl)
    (home / "open.py").chmod(0o755)
    return [cmd, home / f"Open {safe}.bat", home / "open.py"]


# ---------- shortcuts ----------
def install_shortcuts():
    """Desktop and menu shortcuts for this computer. Returns lines describing what was made."""
    py, launcher, out = sys.executable, str(HERE / "launch.py"), []
    if sys.platform.startswith("linux"):
        entry = (f"[Desktop Entry]\nType=Application\nName=UTP\nComment=Build, grow and learn languages\n"
                 f'Exec="{py}" "{launcher}"\nIcon={ICON}\nTerminal=false\nCategories=Education;Languages;\n')
        for folder in (pathlib.Path.home() / ".local" / "share" / "applications", pathlib.Path.home() / "Desktop"):
            if folder.name == "Desktop" and not folder.exists():
                continue
            folder.mkdir(parents=True, exist_ok=True)
            f = folder / "utp.desktop"
            f.write_text(entry)
            f.chmod(0o755)
            if shutil.which("gio"):
                subprocess.run(["gio", "set", str(f), "metadata::trusted", "true"], capture_output=True)
            out.append(f"made {f}")
    elif sys.platform == "darwin":
        app = pathlib.Path.home() / "Applications" / "UTP.app"
        (app / "Contents" / "MacOS").mkdir(parents=True, exist_ok=True)
        (app / "Contents" / "Resources").mkdir(parents=True, exist_ok=True)
        (app / "Contents" / "Info.plist").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
            '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n<plist version="1.0"><dict>'
            "<key>CFBundleName</key><string>UTP</string><key>CFBundleExecutable</key><string>UTP</string>"
            "<key>CFBundleIdentifier</key><string>io.github.arcadiaframe.utp.launcher</string>"
            "<key>CFBundlePackageType</key><string>APPL</string><key>CFBundleIconFile</key><string>icon.png</string>"
            "</dict></plist>\n")
        run = app / "Contents" / "MacOS" / "UTP"
        run.write_text(f'#!/bin/bash\nexec "{py}" "{launcher}" "$@"\n')
        run.chmod(0o755)
        if ICON.exists():
            shutil.copy(ICON, app / "Contents" / "Resources" / "icon.png")
        out.append(f"made {app} (drag it to the Dock to keep it there)")
    elif os.name == "nt":
        pyw = pathlib.Path(py).with_name("pythonw.exe")
        target = str(pyw if pyw.exists() else py)
        for folder in ("Desktop", "Programs"):
            ps = ("$s=New-Object -ComObject WScript.Shell;"
                  f"$d=[Environment]::GetFolderPath('{'Desktop' if folder == 'Desktop' else 'Programs'}');"
                  "$l=$s.CreateShortcut((Join-Path $d 'UTP.lnk'));"
                  f"$l.TargetPath='{target}';$l.Arguments='\"{launcher}\"';$l.WorkingDirectory='{REPO}';$l.Save()")
            r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True)
            out.append(f"made UTP shortcut ({folder})" if r.returncode == 0 else f"could not make a {folder} shortcut: {r.stderr[:200]}")
    else:
        out.append("No shortcut support for this system; double-click a Start UTP file in the repository instead.")
    return out


if __name__ == "__main__":
    sys.exit(main())
