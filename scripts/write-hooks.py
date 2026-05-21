#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path


APP_ID = "codex-desktop-ollama"


def hook_command(runtime_dir, script_name):
    python_bin = os.environ.get("CODEX_OLLAMA_HOOK_PYTHON", "/usr/bin/python3")
    return f"{python_bin} {runtime_dir / script_name}"


def hooks_payload(runtime_dir):
    return {
        "hooks": {
            "UserPromptSubmit": [
                {
                    "matcher": "",
                    "hooks": [
                        {
                            "type": "command",
                            "command": hook_command(runtime_dir, "codex-ollama-prompt-router.py"),
                            "timeout": 10,
                            "statusMessage": "Routing Codex Ollama workflow",
                        }
                    ],
                }
            ],
            "PreToolUse": [
                {
                    "matcher": "^Bash$",
                    "hooks": [
                        {
                            "type": "command",
                            "command": hook_command(runtime_dir, "codex-ollama-tool-guard.py"),
                            "timeout": 10,
                            "statusMessage": "Applying Codex Ollama tool guard",
                        }
                    ],
                }
            ],
            "Stop": [
                {
                    "matcher": "",
                    "hooks": [
                        {
                            "type": "command",
                            "command": hook_command(runtime_dir, "codex-ollama-stop-guard.py"),
                            "timeout": 10,
                            "statusMessage": "Checking Codex Ollama verification evidence",
                        }
                    ],
                }
            ],
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Write Codex Ollama hooks.json.")
    parser.add_argument(
        "--runtime-dir",
        default=str(Path.home() / ".local" / "share" / APP_ID),
        help="Installed runtime directory that contains the hook scripts.",
    )
    parser.add_argument(
        "--output",
        default=str(Path(os.environ.get("CODEX_HOME", Path.home() / ".codex-ollama")) / "hooks.json"),
        help="hooks.json output path.",
    )
    args = parser.parse_args()

    runtime_dir = Path(args.runtime_dir).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(hooks_payload(runtime_dir), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
