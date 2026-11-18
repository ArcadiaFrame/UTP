"""Open the UTP app on this language.

  python3 open.py            the app in your browser (works with no internet)
  python3 open.py --lab      straight to this language's Lab
  python3 open.py --course   straight to this language's course

The desktop window (Electron) does the same: see desktop/README.md.
"""
import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).resolve().parent
repo = next(p for p in [here, *here.parents] if (p / "utp" / "app" / "server.py").exists())
page = "lab" if "--lab" in sys.argv else "course" if "--course" in sys.argv else ""
args = [sys.executable, str(repo / "utp" / "app" / "server.py"), "--open", "--language", here.name]
if page:
    args += ["--page", page]
sys.exit(subprocess.call(args, cwd=repo))
