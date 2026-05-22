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
- `runtime/codex-ollama-tool-guard.py`: `PreToolUse` hook chặn shell write kiểu `cat >`, `tee`, `printf >`, `fs.writeFileSync`, `Path(...).write_text`, ép dùng `apply_patch`; đồng thời chặn `kill`/`pkill`/`killall` và script API như `os.kill`/`process.kill` để model không tự hủy process đang chạy.
- `runtime/codex-ollama-stop-guard.py`: `Stop` hook chặn câu trả lời “done/fixed/pass” nếu transcript chưa có verification command thành công.
- `scripts/configure-profile.py`: cấu hình model/provider, reasoning `xhigh`, profile alias `ollama-launch`/`ollama-cloud`, plugin toggles hiện dùng (`superpowers`, `github`, `chrome`, docs/sheets/presentations).

## Cài Đặt

Trước khi cài, cần có:

- Codex CLI hoạt động: `codex --version`
- Ollama local hoặc Ollama Cloud endpoint tương thích OpenAI đang chạy ở `http://127.0.0.1:11434`
- Python 3.10+ (`python3` trên Linux/macOS, `py -3` trên Windows)
- Với Ollama Cloud model như `kimi-k2.6:cloud` hoặc `glm-5.1:cloud`, phải login Ollama trước:

```bash
ollama signin
ollama run kimi-k2.6:cloud "hello"
```

Setup mặc định của repo đi qua local Ollama daemon (`127.0.0.1:11434`), nên không cần nhập API key vào Codex. API key (`OLLAMA_API_KEY`) chỉ cần khi gọi trực tiếp `https://ollama.com/api`, không phải luồng mặc định này.

Clone repo:

```bash
git clone https://github.com/vanko001/codex-ollama-auto-setup-core.git
cd codex-ollama-auto-setup-core
```

### Linux

Dùng luồng isolated profile nếu muốn chạy Codex Ollama tách khỏi Codex thường:

```bash
./scripts/auto-setup.sh
```

Lệnh trên sẽ tạo:

- profile: `~/.codex-ollama`
- runtime: `~/.local/share/codex-desktop-ollama`
- launcher: `~/.local/bin/codex-desktop-ollama`

Mở app:

```bash
~/.local/bin/codex-desktop-ollama
```

Nếu Codex Desktop source nằm chỗ khác:

```bash
CODEX_DESKTOP_SOURCE_APP=/path/to/codex-app ./scripts/auto-setup.sh
```

Verify:

```bash
CODEX_HOME=~/.codex-ollama codex -m kimi-k2.6:cloud doctor
```

### macOS

Dùng luồng này nếu đã có Codex app thường và muốn gắn Ollama vào profile hiện tại `~/.codex`:

```bash
python3 scripts/configure-existing-codex-app.py \
  --platform macos \
  --model kimi-k2.6:cloud \
  --trust-hooks
```

Lệnh trên sẽ:

- backup `~/.codex/config.toml` và `~/.codex/hooks.json` nếu đã tồn tại
- copy runtime vào `~/Library/Application Support/codex-desktop-ollama`
- cấu hình provider `ollama-launch` trỏ tới `http://127.0.0.1:11435/v1`
- ghi hook stack vào `~/.codex/hooks.json`

Khởi động reasoning proxy trước khi mở Codex app:

```bash
~/Library/Application\ Support/codex-desktop-ollama/start-reasoning-proxy.command
```

Sau đó mở Codex app có sẵn như bình thường và chọn model Ollama Cloud.

Verify:

```bash
codex -m kimi-k2.6:cloud doctor
```

### Windows

Dùng PowerShell từ thư mục repo:

```powershell
py -3 scripts\configure-existing-codex-app.py `
  --platform windows `
  --model kimi-k2.6:cloud `
  --hook-python "py -3" `
  --trust-hooks
```

Lệnh trên sẽ:

- backup `%USERPROFILE%\.codex\config.toml` và `%USERPROFILE%\.codex\hooks.json` nếu đã tồn tại
- copy runtime vào `%APPDATA%\codex-desktop-ollama`
- cấu hình provider `ollama-launch` trỏ tới `http://127.0.0.1:11435/v1`
- ghi hook stack vào `%USERPROFILE%\.codex\hooks.json`

Khởi động reasoning proxy trước khi mở Codex app:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:APPDATA\codex-desktop-ollama\Start-ReasoningProxy.ps1"
```

Sau đó mở Codex app có sẵn như bình thường và chọn model Ollama Cloud.

Verify:

```powershell
codex -m kimi-k2.6:cloud doctor
```

### Tùy Chọn Thường Dùng

Đổi model mặc định:

```bash
python3 scripts/configure-existing-codex-app.py \
  --platform macos \
  --model glm-5.1:cloud
```

Ghi vào profile Codex khác:

```bash
python3 scripts/configure-existing-codex-app.py \
  --platform macos \
  --codex-home "$HOME/.codex-work" \
  --model kimi-k2.6:cloud
```

Đổi port proxy:

```bash
CODEX_OLLAMA_REASONING_PROXY_PORT=11436 \
python3 scripts/configure-existing-codex-app.py \
  --platform macos \
  --proxy-port 11436
```

### Sau Khi Cài

Kiểm tra file đã được tạo:

Linux:

```bash
test -f ~/.codex-ollama/config.toml
test -f ~/.codex-ollama/hooks.json
```

macOS:

```bash
test -f ~/.codex/config.toml
test -f ~/.codex/hooks.json
test -f ~/Library/Application\ Support/codex-desktop-ollama/ollama-reasoning-proxy.py
```

Windows PowerShell:

```powershell
Test-Path "$env:USERPROFILE\.codex\config.toml"
Test-Path "$env:USERPROFILE\.codex\hooks.json"
Test-Path "$env:APPDATA\codex-desktop-ollama\ollama-reasoning-proxy.py"
```

Chi tiết cho Codex app có sẵn: [`docs/configure-existing-codex-app.md`](docs/configure-existing-codex-app.md).

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
