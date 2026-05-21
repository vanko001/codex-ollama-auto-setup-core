# Build Process

Quy trình build không đưa binary Codex Desktop vào repo. Script sẽ dùng bản Codex Desktop Linux đã cài trên máy làm source, rồi tạo một bản app id riêng.

## Bước build

1. Copy `~/.local/opt/codex-desktop-linux/codex-app` sang `~/.local/opt/codex-desktop-ollama/codex-app`.
2. Patch `start.sh`:
   - `CODEX_LINUX_APP_ID=codex-desktop-ollama`
   - `CODEX_LINUX_APP_DISPLAY_NAME=Codex Desktop Ollama`
   - `CODEX_LINUX_WEBVIEW_PORT=${CODEX_WEBVIEW_PORT:-5176}`
3. Patch webview `model-queries-*.js` để tắt model availability allowlist. Nếu không patch, model custom/Ollama có thể hiện nhưng không chọn được đúng.
4. Cài launcher `~/.local/bin/codex-desktop-ollama`.
5. Cài runtime vào `~/.local/share/codex-desktop-ollama`.
6. Tạo profile riêng `~/.codex-ollama/config.toml`.
7. Tạo và trust hooks trong `~/.codex-ollama/hooks.json`.

## Lệnh auto setup

```bash
./scripts/auto-setup.sh
```

Script này luôn chạy `scripts/install.sh`, build desktop clone nếu tìm thấy source app, chạy `scripts/verify-install.sh`, rồi chạy `codex doctor` với `CODEX_HOME=~/.codex-ollama` nếu Codex CLI có sẵn.

## Lệnh từng bước

```bash
./scripts/build-codex-desktop-ollama.sh
./scripts/verify-install.sh
```

## Port

- Codex Desktop Ollama webview: `5176`
- Reasoning proxy: `11435`
- Ollama upstream: `11434`

Có thể override:

```bash
CODEX_WEBVIEW_PORT=5181 CODEX_OLLAMA_REASONING_PROXY_PORT=11436 ./scripts/install.sh
```
