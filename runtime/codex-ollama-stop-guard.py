#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path


BLOCK_REASON = (
    "Codex Ollama Verification Guard: the last answer claims fixed, verified, "
    "passing, complete, or done, but the transcript does not show a fresh "
    "successful verification command. Continue by reading "
    "superpowers:verification-before-completion/SKILL.md if applicable, run the "
    "relevant test/build/check command, inspect the output and exit code, then "
    "answer with that evidence."
)

COMPLETION_CLAIM_RE = re.compile(
    r"(?iu)"
    r"("
    r"\b(done|fixed|complete|completed|verified|passing|passes|passed)\b|"
    r"all\s+tests?\s+pass(?:ed|es)?|"
    r"tests?\s+pass(?:ed|es)?|"
    r"đã\s+(fix|sửa|xong|hoàn\s+tất|verify|pass)|"
    r"da\s+(fix|sua|xong|hoan\s+tat|verify|pass)|"
    r"hoàn\s+tất|hoan\s+tat|"
    r"thành\s+công|thanh\s+cong|"
    r"không\s+còn\s+lỗi|khong\s+con\s+loi"
    r")"
)

VERIFY_COMMAND_RE = re.compile(
    r"(?i)"
    r"("
    r"pytest|python3?\s+-m\s+unittest|python3?\s+-m\s+pytest|"
    r"npm\s+(run\s+)?(test|build|lint)|pnpm\s+(test|build|lint)|"
    r"yarn\s+(test|build|lint)|bun\s+(test|run\s+test|run\s+build)|"
    r"cargo\s+(test|check|clippy)|go\s+test|"
    r"mvn\s+test|gradle\s+test|./gradlew\s+test|"
    r"ruff\s+check|mypy|tsc\b|"
    r"codex\s+doctor|verify-install\.sh"
    r")"
)

VERIFY_SUCCESS_RE = re.compile(
    r"(?i)"
    r"("
    r"process exited with code 0|exit code[:=]\s*0|"
    r"\bOK\b|"
    r"\bpassed\b|"
    r"\b0 failed\b|"
    r"\b0 errors?\b|"
    r"\b13 ok\b|"
    r"\bSUCCESS\b|"
    r"\bBUILD SUCCESSFUL\b|"
    r"\bAll tests passed\b"
    r")"
)


def load_event():
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def walk_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from walk_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk_strings(item)


def transcript_path(event):
    for key in ("transcript_path", "transcriptPath"):
        value = event.get(key)
        if isinstance(value, str) and value:
            return Path(value)
    return None


def read_transcript_text(path):
    if not path:
        return ""
    try:
        if not path.is_file():
            return ""
        data = path.read_bytes()
    except OSError:
        return ""
    if len(data) > 2_000_000:
        data = data[-2_000_000:]
    return data.decode("utf-8", errors="replace")


def last_assistant_message(event):
    value = event.get("last_assistant_message") or event.get("lastAssistantMessage")
    return value if isinstance(value, str) else ""


def has_completion_claim(message):
    return bool(COMPLETION_CLAIM_RE.search(message or ""))


def has_successful_verification(event, transcript_text):
    combined = "\n".join([transcript_text, *walk_strings(event)])
    return bool(VERIFY_COMMAND_RE.search(combined) and VERIFY_SUCCESS_RE.search(combined))


def block_payload():
    return {
        "decision": "block",
        "reason": BLOCK_REASON,
    }


def main():
    event = load_event()
    if event.get("stop_hook_active") or event.get("stopHookActive"):
        return 0

    message = last_assistant_message(event)
    if not has_completion_claim(message):
        return 0

    transcript_text = read_transcript_text(transcript_path(event))
    if has_successful_verification(event, transcript_text):
        return 0

    print(json.dumps(block_payload(), ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
