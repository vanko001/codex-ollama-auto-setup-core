# Codex Ollama Auto Setup Core

Repo này đóng gói core auto-setup cho **Codex Desktop Ollama**: profile riêng `~/.codex-ollama`, runtime riêng `~/.local/share/codex-desktop-ollama`, launcher riêng `codex-desktop-ollama`, Ollama/OpenAI-compatible endpoint qua `http://127.0.0.1:11435/v1`, model catalog Ollama Cloud, và hook stack để hành vi gần Codex thường hơn.

Mục tiêu thực tế là khoảng **95% workflow parity**, không phải 100% model parity. Phần còn lại phụ thuộc vào khả năng tool planning, instruction following và plugin/tool semantics native của từng model Ollama Cloud.

## Có gì bên trong

- `scripts/auto-setup.sh`: entrypoint core chạy install, build desktop clone nếu source app có sẵn, verify và `codex doctor`.
- `scripts/install.sh`: cài runtime, hooks, profile config, plugin toggles và trust hook tự động.
- `scripts/configure-existing-codex-app.py`: gắn runtime Ollama vào Codex app có sẵn trên macOS/Windows bằng cách cấu hình profile `~/.codex` hiện tại, có backup.
- `scripts/build-codex-desktop-ollama.sh`: clone bản Codex Desktop Linux đang có trong máy sang app id riêng.
- `runtime/ollama-reasoning-proxy.py`: proxy rewrite `xhigh` của Codex sang reasoning native của Ollama Cloud, ví dụ `max` hoặc `high`.
- `runtime/ollama-cloud-model-catalog.json`: catalog model Ollama Cloud có base instructions ép skill routing, TDD, verification và `apply_patch`.
- `runtime/codex-ollama-prompt-router.py`: `UserPromptSubmit` hook inject context ngắn để model tự chọn skill phù hợp.
- `runtime/codex-ollama-tool-guard.py`: `PreToolUse` hook chặn shell write kiểu `cat >`, `tee`, `printf >`, `fs.writeFileSync`, `Path(...).write_text`, ép dùng `apply_patch`.
- `runtime/codex-ollama-stop-guard.py`: `Stop` hook chặn câu trả lời “done/fixed/pass” nếu transcript chưa có verification command thành công.
- `scripts/configure-profile.py`: cấu hình model/provider, reasoning `xhigh`, profile alias `ollama-launch`/`ollama-cloud`, plugin toggles hiện dùng (`superpowers`, `github`, `chrome`, docs/sheets/presentations).

## Quick Start

Yêu cầu:

- Codex CLI hoạt động: `codex --version`
- Codex Desktop Linux đã cài ở `~/.local/opt/codex-desktop-linux/codex-app` nếu muốn clone app desktop riêng
- Ollama đang chạy ở `http://127.0.0.1:11434`

Auto setup:

```bash
git clone https://github.com/vanko001/codex-ollama-auto-setup-core.git
cd codex-ollama-auto-setup-core
./scripts/auto-setup.sh
~/.local/bin/codex-desktop-ollama
```

Nếu Codex Desktop source nằm chỗ khác:

```bash
CODEX_DESKTOP_SOURCE_APP=/path/to/codex-app ./scripts/auto-setup.sh
```

CLI check:

```bash
CODEX_HOME=~/.codex-ollama codex -m kimi-k2.6:cloud doctor
```

## Dùng với Codex app có sẵn trên macOS/Windows

Nếu đã có Codex app thường và chỉ muốn thêm cấu hình Ollama Cloud vào profile hiện tại, dùng:

macOS:

```bash
python3 scripts/configure-existing-codex-app.py \
  --platform macos \
  --model kimi-k2.6:cloud \
  --trust-hooks
~/Library/Application\ Support/codex-desktop-ollama/start-reasoning-proxy.command
```

Windows PowerShell:

```powershell
py -3 scripts\configure-existing-codex-app.py `
  --platform windows `
  --model kimi-k2.6:cloud `
  --hook-python "py -3" `
  --trust-hooks
powershell -ExecutionPolicy Bypass -File "$env:APPDATA\codex-desktop-ollama\Start-ReasoningProxy.ps1"
```

Sau đó mở Codex app có sẵn như bình thường. Script mặc định ghi vào `~/.codex` hoặc `%USERPROFILE%\.codex`, copy runtime vào app data OS-native, và backup `config.toml`/`hooks.json` trước khi sửa. Chi tiết: [`docs/configure-existing-codex-app.md`](docs/configure-existing-codex-app.md).

## Test

```bash
python3 -m unittest discover -s tests
./scripts/audit-ollama-catalog.py
```

## Tối ưu model Ollama Cloud

Khuyến nghị hiện tại:

- `kimi-k2.6:cloud`: tốt nhất cho coding dài, nhưng cần prompt router + stop guard để ổn định skill/TDD.
- `glm-5.1:cloud`: gọi tool ổn và nhanh hơn trong web benchmark vừa chạy, nhưng workflow discipline kém Kimi hơn.
- `deepseek-v4-pro:cloud`: hợp task khó, context lớn; `xhigh` được proxy map sang `max`.
- `deepseek-v4-flash:cloud`: đang không phù hợp với Codex tool-call protocol trong setup hiện tại.
- `qwen3-coder-next:cloud`: gọi tool được nhưng bị stall trên web benchmark vừa-vừa.
- Model không có reasoning summaries vẫn chạy được, nhưng không nên kỳ vọng workflow bằng Kimi/DeepSeek.

## Giới hạn

Các hook và catalog giúp model đi đúng quy trình hơn, nhưng không thể thay thế hoàn toàn Codex native model. Muốn tiến tới 100% cần model có tool-use alignment ngang Codex, plugin/skill semantics native, và khả năng tự kiểm chứng ổn định mà không cần guard cưỡng chế.
