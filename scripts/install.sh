#!/usr/bin/env bash
set -euo pipefail

APP_ID="codex-desktop-ollama"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_HOME="${CODEX_HOME:-${HOME}/.codex-ollama}"
RUNTIME_DIR="${CODEX_OLLAMA_RUNTIME_DIR:-${HOME}/.local/share/${APP_ID}}"
BIN_DIR="${HOME}/.local/bin"
DEFAULT_MODEL="${CODEX_OLLAMA_DEFAULT_MODEL:-kimi-k2.6:cloud}"
PROXY_PORT="${CODEX_OLLAMA_REASONING_PROXY_PORT:-11435}"

mkdir -p "$CODEX_HOME" "$RUNTIME_DIR" "$BIN_DIR"
install -m 755 "${REPO_ROOT}/runtime/"*.py "$RUNTIME_DIR/"
install -m 644 "${REPO_ROOT}/runtime/ollama-cloud-model-catalog.json" "$RUNTIME_DIR/"
install -m 755 "${REPO_ROOT}/scripts/codex-desktop-ollama" "${BIN_DIR}/codex-desktop-ollama"

python3 "${REPO_ROOT}/scripts/configure-profile.py" \
    --config "${CODEX_HOME}/config.toml" \
    --catalog "${RUNTIME_DIR}/ollama-cloud-model-catalog.json" \
    --model "$DEFAULT_MODEL" \
    --proxy-port "$PROXY_PORT" >/dev/null

python3 "${REPO_ROOT}/scripts/write-hooks.py" \
    --runtime-dir "$RUNTIME_DIR" \
    --output "${CODEX_HOME}/hooks.json" >/dev/null

if command -v codex >/dev/null 2>&1; then
    python3 "${REPO_ROOT}/scripts/trust-hooks.py" --codex-home "$CODEX_HOME" >/dev/null
else
    echo "codex CLI not found; hooks were written but not trusted automatically." >&2
fi

echo "Installed ${APP_ID} runtime into ${RUNTIME_DIR}"
