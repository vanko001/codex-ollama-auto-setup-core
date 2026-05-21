# GitHub Publish

Repo này có thể push bằng GitHub CLI sau khi login:

```bash
cd /home/vule/codex-desktop-ollama-builder
gh auth login
gh repo create codex-desktop-ollama-builder --private --source=. --remote=origin --push
```

Nếu đã tạo remote trước:

```bash
git remote add origin git@github.com:<owner>/codex-desktop-ollama-builder.git
git push -u origin main
```

Không commit các thư mục binary lớn như `codex-app/`, `app.asar`, `node_modules/`.
