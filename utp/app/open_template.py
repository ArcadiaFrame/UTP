#!/usr/bin/env python3
"""Open the UTP app on this language (double-click "Open … .command" on macOS or "Open … .bat" on Windows,
or run this file).

  python3 open.py            the app (desktop window if installed, else your browser), on this language
  python3 open.py --lab      straight to this language's Lab
  python3 open.py --course   straight to this language's course
"""
import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).resolve().parent
repo = next((p for p in [here, *here.parents] if (p / "utp" / "app" / "launch.py").exists()), pathlib.Path("__REPO__"))
args = [sys.executable, str(repo / "utp" / "app" / "launch.py"), "--language", "__LANG__"]
for flag, page in (("--lab", "lab"), ("--course", "course")):
    if flag in sys.argv:
        args += ["--page", page]
args += [a for a in sys.argv[1:] if a in ("--browser", "--desktop")]
sys.exit(subprocess.call(args, cwd=repo))
