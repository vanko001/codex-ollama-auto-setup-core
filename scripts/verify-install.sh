#!/usr/bin/env bash
set -euo pipefail

APP_ID="codex-desktop-ollama"
CODEX_HOME="${CODEX_HOME:-${HOME}/.codex-ollama}"
RUNTIME_DIR="${CODEX_OLLAMA_RUNTIME_DIR:-${HOME}/.local/share/${APP_ID}}"

test -x "${RUNTIME_DIR}/codex-ollama-tool-guard.py"
test -x "${RUNTIME_DIR}/codex-ollama-prompt-router.py"
test -x "${RUNTIME_DIR}/codex-ollama-stop-guard.py"
test -x "${RUNTIME_DIR}/ollama-reasoning-proxy.py"
test -f "${RUNTIME_DIR}/ollama-cloud-model-catalog.json"
test -f "${CODEX_HOME}/hooks.json"

python3 -m json.tool "${CODEX_HOME}/hooks.json" >/dev/null
python3 "${RUNTIME_DIR}/codex-ollama-prompt-router.py" <<<'{"hook_event_name":"UserPromptSubmit","prompt":"fix"}' | rg 'verification-before-completion' >/dev/null
python3 "${RUNTIME_DIR}/codex-ollama-stop-guard.py" <<<'{"hook_event_name":"Stop","last_assistant_message":"Done.","stop_hook_active":false}' | rg '"decision":"block"' >/dev/null

if command -v codex >/dev/null 2>&1; then
    CODEX_HOME="$CODEX_HOME" codex doctor >/dev/null
fi

echo "Codex Desktop Ollama install verified"
