#!/usr/bin/env python3
import argparse
import re
from pathlib import Path


ALLOWLIST_RE = re.compile(r"let\s+u\s*=\s*c\.useHiddenModels&&o!==`amazonBedrock`,d;return")
PATCHED = "let u=!1,d;return"


def patch_file(path):
    text = path.read_text(encoding="utf-8")
    if PATCHED in text:
        return False
    updated, count = ALLOWLIST_RE.subn(PATCHED, text, count=1)
    if count != 1:
        raise RuntimeError(f"did not find model allowlist expression in {path}")
    path.write_text(updated, encoding="utf-8")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Disable the desktop model availability allowlist so custom Ollama models can be selected."
    )
    parser.add_argument("app_dir", help="Codex desktop app directory.")
    args = parser.parse_args()
    app_dir = Path(args.app_dir).expanduser().resolve()
    assets = sorted((app_dir / "content" / "webview" / "assets").glob("model-queries-*.js"))
    if not assets:
        raise SystemExit(f"no model-queries asset found under {app_dir}")
    changed = [str(path) for path in assets if patch_file(path)]
    print("\n".join(changed) if changed else "already patched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
