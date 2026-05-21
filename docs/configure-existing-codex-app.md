# Configure An Existing Codex App

This path is for macOS or Windows users who already have the normal Codex app installed and want to add the Ollama Cloud profile into that existing app configuration.

It does not build or clone a separate desktop app. It writes into the existing Codex config home, which defaults to:

- macOS: `~/.codex`
- Windows: `%USERPROFILE%\.codex`

The script creates backups of existing `config.toml` and `hooks.json` unless `--no-backup` is passed.

## Precondition: Ollama Login

This repo's default flow routes Codex through the local Ollama daemon:

- Codex -> `http://127.0.0.1:11435/v1`
- reasoning proxy -> `http://127.0.0.1:11434`
- local Ollama authenticates cloud model access

For Ollama Cloud models such as `kimi-k2.6:cloud` or `glm-5.1:cloud`, sign in before configuring Codex:

```bash
ollama signin
ollama run kimi-k2.6:cloud "hello"
```

No Codex API key is needed for this default local-daemon flow. `OLLAMA_API_KEY` is only needed for direct calls to `https://ollama.com/api`, which is a separate direct-cloud mode and not what this setup writes by default.

## macOS

From this repo:

```bash
python3 scripts/configure-existing-codex-app.py \
  --platform macos \
  --model kimi-k2.6:cloud \
  --trust-hooks
```

Start the reasoning proxy before opening Codex:

```bash
~/Library/Application\ Support/codex-desktop-ollama/start-reasoning-proxy.command
```

Then open the existing Codex app normally and choose the configured Ollama model.

## Windows

From this repo in PowerShell:

```powershell
py -3 scripts\configure-existing-codex-app.py `
  --platform windows `
  --model kimi-k2.6:cloud `
  --hook-python "py -3" `
  --trust-hooks
```

Start the reasoning proxy before opening Codex:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:APPDATA\codex-desktop-ollama\Start-ReasoningProxy.ps1"
```

Then open the existing Codex app normally and choose the configured Ollama model.

## What Gets Written

Runtime files are copied to an OS-native app data directory:

- macOS: `~/Library/Application Support/codex-desktop-ollama`
- Windows: `%APPDATA%\codex-desktop-ollama`

The script writes:

- `ollama-reasoning-proxy.py`
- `ollama-cloud-model-catalog.json`
- `codex-ollama-prompt-router.py`
- `codex-ollama-tool-guard.py`
- `codex-ollama-stop-guard.py`
- `start-reasoning-proxy.command`
- `Start-ReasoningProxy.ps1`

It updates Codex config to use:

- provider: `ollama-launch`
- base URL: `http://127.0.0.1:11435/v1`
- reasoning effort: `xhigh`
- model catalog: the copied Ollama Cloud catalog
- hooks: prompt router, tool guard, verification stop guard

## Custom Paths

Use `--codex-home` when the Codex app uses a non-default profile:

```bash
python3 scripts/configure-existing-codex-app.py \
  --platform macos \
  --codex-home "$HOME/.codex-work" \
  --model glm-5.1:cloud
```

Use `--runtime-dir` when you want runtime files somewhere else:

```bash
python3 scripts/configure-existing-codex-app.py \
  --platform macos \
  --runtime-dir "$HOME/Library/Application Support/codex-ollama-custom"
```

## Model Notes

Current practical defaults from the benchmark runs:

- `kimi-k2.6:cloud`: best Ollama Cloud default for longer coding tasks.
- `glm-5.1:cloud`: faster and usable for backend/API work, but weaker than Kimi on workflow discipline.
- `deepseek-v4-flash:cloud`: currently fails Codex tool-call protocol in this setup.
- `qwen3-coder-next:cloud`: calls tools, but stalled on the medium web benchmark.

Use `CODEX_OLLAMA_DEFAULT_MODEL` or `--model` to change the installed default.
