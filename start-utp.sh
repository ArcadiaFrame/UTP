#!/bin/sh
# Linux: run this once, or double-click it if your file manager runs scripts.
# For a menu and desktop icon: python3 utp/utp.py shortcut  (or Settings > Startup > Make shortcuts)
cd "$(dirname "$0")" || exit 1
PY="$(command -v python3 || command -v python)"
[ -z "$PY" ] && { echo "UTP needs Python 3."; exit 1; }
exec "$PY" utp/app/launch.py "$@"
