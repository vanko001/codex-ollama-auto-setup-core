#!/usr/bin/env bash
set -euo pipefail

APP_ID="codex-desktop-ollama"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_APP="${CODEX_DESKTOP_SOURCE_APP:-${HOME}/.local/opt/codex-desktop-linux/codex-app}"
TARGET_APP="${CODEX_DESKTOP_OLLAMA_APP:-${HOME}/.local/opt/${APP_ID}/codex-app}"

if [ ! -f "${SOURCE_APP}/start.sh" ]; then
    echo "Source Codex Desktop app not found: ${SOURCE_APP}" >&2
    echo "Set CODEX_DESKTOP_SOURCE_APP=/path/to/codex-app and rerun." >&2
    exit 1
fi

mkdir -p "$(dirname "$TARGET_APP")"
if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete "${SOURCE_APP}/" "${TARGET_APP}/"
else
    rm -rf "$TARGET_APP"
    cp -a "$SOURCE_APP" "$TARGET_APP"
fi

python3 - "$TARGET_APP/start.sh" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
text = re.sub(r"^CODEX_LINUX_APP_ID=.*$", "CODEX_LINUX_APP_ID=codex-desktop-ollama", text, count=1, flags=re.M)
text = re.sub(r"^CODEX_LINUX_APP_DISPLAY_NAME=.*$", r"CODEX_LINUX_APP_DISPLAY_NAME=Codex\\ Desktop\\ Ollama", text, count=1, flags=re.M)
text = re.sub(r"^CODEX_LINUX_WEBVIEW_PORT=.*$", r"CODEX_LINUX_WEBVIEW_PORT=${CODEX_WEBVIEW_PORT:-5176}", text, count=1, flags=re.M)
path.write_text(text, encoding="utf-8")
PY

python3 "${REPO_ROOT}/scripts/patch-model-picker.py" "$TARGET_APP"
"${REPO_ROOT}/scripts/install.sh"

echo "Built ${APP_ID} at ${TARGET_APP}"
