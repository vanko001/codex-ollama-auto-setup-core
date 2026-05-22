# 95% Workflow Parity

Mục tiêu 95% nghĩa là Codex Ollama phải giống Codex thường ở các điểm ảnh hưởng trực tiếp đến coding workflow:

1. Tự đọc skill đúng trước khi làm việc.
2. Dùng systematic debugging cho bug/failure.
3. Dùng TDD khi implement hoặc fix.
4. Sửa file qua `apply_patch`, tránh shell write không kiểm soát.
5. Không tự hủy process/tool session đang chạy bằng `kill`/`pkill`/`killall` hoặc script API như `os.kill`/`process.kill`.
6. Không claim “xong/pass/fixed” nếu chưa có verification command mới.
7. Map reasoning effort của UI Codex sang reasoning native của Ollama Cloud.

## Ba lớp ép workflow

`UserPromptSubmit` hook thêm developer context ngắn ở đầu mỗi turn. Nó không thay model, nhưng giảm lỗi model bỏ qua skill hoặc đọc code trước khi đọc skill.

`PreToolUse` hook chặn các shell command viết file trực tiếp. Đây là lớp bảo vệ quan trọng vì model local/cloud hay viết file bằng heredoc hoặc script write API hơn Codex native. Guard hiện chặn các pattern như `cat >`, `tee`, `printf >`, `echo >>`, `fs.writeFileSync`, `Path(...).write_text`, và `open(..., "w")` khi target là source/test/docs/config.

Guard cũng chặn `kill`, `pkill`, `killall`, pipeline `xargs kill`, và script API như `os.kill`, `os.killpg`, `process.kill`. `kill -0 <pid>` vẫn được phép vì chỉ là probe kiểm tra process tồn tại. Nếu command/tool session bị treo, model phải báo session/process và hỏi người dùng trước khi dừng.

`Stop` hook đọc `last_assistant_message` và transcript. Nếu câu cuối claim hoàn tất nhưng không thấy test/build/check thành công, hook trả `decision: block` để Codex tiếp tục bằng prompt verify.

## Vì sao không phải 100%

100% cần năng lực nằm trong model: tool-call planning, khả năng giữ state workflow nhiều bước, hiểu plugin/skill như Codex native, và ít hallucinate kết quả verify. Hook chỉ sửa được hành vi ở biên, không sửa được reasoning lõi của model.
