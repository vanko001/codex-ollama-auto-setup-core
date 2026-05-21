#!/usr/bin/env python3
import json
import sys


ADDITIONAL_CONTEXT = """Codex Ollama workflow router:
- Before project inspection, read superpowers:using-superpowers/SKILL.md with a shell command, then read every applicable SKILL.md inferred from the user prompt.
- For bugs, errors, failed tests, reconnects, crashes, diagnosis, or fixes: use superpowers:systematic-debugging.
- For implementation, behavior changes, refactors, or bug fixes: use superpowers:test-driven-development before writing implementation code when feasible.
- Before claiming fixed, passing, verified, complete, or done: use superpowers:verification-before-completion and run fresh verification.
- Use rg for search/read orientation. For source, test, docs, and config edits, use apply_patch; do not write files with cat >, tee, printf >, or shell heredoc redirects.
- If multiple reads are independent, batch them with the available parallel tool. Keep the final answer evidence-based and concise.
"""


def load_event():
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def output_payload():
    return {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": ADDITIONAL_CONTEXT.strip(),
        }
    }


def main():
    load_event()
    print(json.dumps(output_payload(), ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
