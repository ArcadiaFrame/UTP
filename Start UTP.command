#!/bin/bash
# macOS: double-click to open the UTP app. (First time: right-click > Open, because it was downloaded.)
cd "$(dirname "$0")" || exit 1
PY="$(command -v python3 || command -v python)"
if [ -z "$PY" ]; then
  osascript -e 'display alert "UTP needs Python 3" message "Install it from python.org, then double-click Start UTP again."'
  exit 1
fi
exec "$PY" utp/app/launch.py "$@"
