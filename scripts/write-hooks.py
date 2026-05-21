#!/usr/bin/env python3
import argparse
import json
import os
import shlex
from pathlib import Path


APP_ID = "codex-desktop-ollama"


def quote_arg(value, command_platform):
    rendered = str(value)
    if command_platform == "windows":
        return '"' + rendered.replace('"', r'\"') + '"'
    return shlex.quote(rendered)


def hook_command(runtime_dir, script_name, *, python_cmd=None, command_platform="posix"):
    python_cmd = python_cmd or os.environ.get("CODEX_OLLAMA_HOOK_PYTHON", "/usr/bin/python3")
    return f"{python_cmd} {quote_arg(runtime_dir / script_name, command_platform)}"


def hooks_payload(runtime_dir, *, python_cmd=None, command_platform="posix"):
    return {
        "hooks": {
            "UserPromptSubmit": [
                {
                    "matcher": "",
                    "hooks": [
                        {
                            "type": "command",
                            "command": hook_command(
                                runtime_dir,
                                "codex-ollama-prompt-router.py",
                                python_cmd=python_cmd,
                                command_platform=command_platform,
                            ),
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
                            "command": hook_command(
                                runtime_dir,
                                "codex-ollama-tool-guard.py",
                                python_cmd=python_cmd,
                                command_platform=command_platform,
                            ),
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
                            "command": hook_command(
                                runtime_dir,
                                "codex-ollama-stop-guard.py",
                                python_cmd=python_cmd,
                                command_platform=command_platform,
                            ),
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
    parser.add_argument(
        "--hook-python",
        default=os.environ.get("CODEX_OLLAMA_HOOK_PYTHON"),
        help="Python command used by hook entries. Defaults to CODEX_OLLAMA_HOOK_PYTHON or /usr/bin/python3.",
    )
    parser.add_argument(
        "--command-platform",
        choices=("posix", "windows"),
        default="windows" if os.name == "nt" else "posix",
        help="Quoting style for generated hook commands.",
    )
    args = parser.parse_args()

    runtime_dir = Path(args.runtime_dir).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            hooks_payload(
                runtime_dir,
                python_cmd=args.hook_python,
                command_platform=args.command_platform,
            ),
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
