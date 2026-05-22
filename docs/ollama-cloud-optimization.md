# Ollama Cloud Optimization

## Reasoning mapping

Codex UI có `low`, `medium`, `high`, `xhigh`. Một số Ollama Cloud model dùng naming khác, ví dụ `max`. Vì vậy launcher chạy proxy local ở `127.0.0.1:11435` và cấu hình Codex dùng provider `ollama-launch`.

Khi payload có `reasoning.effort = xhigh` hoặc `reasoning_effort = xhigh`, proxy rewrite:

- nhóm max reasoning: `xhigh -> max`
- `qwen3-next:80b-cloud`: `xhigh -> high`
- model không có reasoning mapping: giữ nguyên payload

Test bảo đảm danh sách proxy khớp các model reasoning trong catalog.

Audit nhanh:

```bash
./scripts/audit-ollama-catalog.py
```

## Model tiers

| Tier | Model | Ghi chú |
| --- | --- | --- |
| Recommended | `kimi-k2.6:cloud` | Tool use khá, hợp task coding dài khi có hook guard |
| Strong | `deepseek-v4-pro:cloud` | Context rất lớn, hợp phân tích/refactor khó |
| Fast | `deepseek-v4-flash:cloud` | Hợp task vừa, phản hồi nhanh hơn |
| Good | `qwen3.5:397b-cloud` | Reasoning tốt, cần guard cho workflow |
| High-only | `qwen3-next:80b-cloud` | Proxy map `xhigh -> high` |

## Catalog instructions

Catalog thêm `base_instructions` cho tất cả model để ép:

- đọc `superpowers:using-superpowers` trước;
- đọc skill phù hợp trước khi inspect code;
- bug/fix dùng debugging + TDD + verification;
- edit bằng `apply_patch`;
- không tự chạy `kill`/`pkill`/`killall` để hủy process hoặc tool session;
- final phải có evidence nếu claim pass/fixed/done.

Hook vẫn quan trọng vì model ngoài Codex có thể bỏ qua instruction khi context dài hoặc khi tool-call pressure cao.
