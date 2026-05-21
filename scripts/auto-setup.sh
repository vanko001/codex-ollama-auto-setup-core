#!/usr/bin/env bash
set -euo pipefail

APP_ID="codex-desktop-ollama"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_HOME="${CODEX_HOME:-${HOME}/.codex-ollama}"
SOURCE_APP="${CODEX_DESKTOP_SOURCE_APP:-${HOME}/.local/opt/codex-desktop-linux/codex-app}"

log() {
    printf '[%s] %s\n' "$APP_ID" "$*"
}

log "Installing isolated Codex Ollama runtime, profile, hooks, and catalog"
"${REPO_ROOT}/scripts/install.sh"

if [ -f "${SOURCE_APP}/start.sh" ]; then
    log "Building isolated desktop app from ${SOURCE_APP}"
    "${REPO_ROOT}/scripts/build-codex-desktop-ollama.sh"
else
    log "Desktop source app not found at ${SOURCE_APP}; runtime/profile setup completed without desktop clone"
    log "Set CODEX_DESKTOP_SOURCE_APP=/path/to/codex-app and rerun for desktop app cloning"
fi

log "Verifying install"
"${REPO_ROOT}/scripts/verify-install.sh"

if command -v codex >/dev/null 2>&1; then
    log "Running codex doctor against ${CODEX_HOME}"
    CODEX_HOME="$CODEX_HOME" codex doctor
fi

log "Auto setup complete"
log "Launch desktop: ${HOME}/.local/bin/codex-desktop-ollama"
log "CLI check: CODEX_HOME=${CODEX_HOME} codex -m ${CODEX_OLLAMA_DEFAULT_MODEL:-kimi-k2.6:cloud} doctor"
