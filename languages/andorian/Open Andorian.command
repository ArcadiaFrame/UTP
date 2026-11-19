#!/bin/bash
# macOS: double-click to open the UTP app on Andorian.
REPO="$(dirname "$0")/../.."
PY="$(command -v python3 || command -v python)"
exec "$PY" "$REPO/utp/app/launch.py" --language andorian "$@"
