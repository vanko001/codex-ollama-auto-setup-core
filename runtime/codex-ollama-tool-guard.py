#!/usr/bin/env python3
import json
import re
import sys


BLOCK_REASON = (
    "Codex Ollama Tool Guard: direct shell file writes are blocked for "
    "source/test/docs edits. Retry the edit with apply_patch."
)


PRODUCER_REDIRECT_RE = re.compile(
    r"(?ims)(?:^|[;&|]{1,2}\s*)"
    r"(cat|printf|echo)\b[^\n;&|]*"
    r"(?:^|[^<])(?:>{1,2}|[0-9]>{1,2}|&>)\s*"
    r"(?P<target>(?:'[^']+'|\"[^\"]+\"|[^\s;&|<>]+))"
)

TEE_RE = re.compile(
    r"(?ims)(?:^|[;&|]{1,2}\s*)"
    r"tee\b(?P<args>[^\n;&|]*)"
)

JS_WRITE_RE = re.compile(
    r"(?is)\b(?:writeFileSync|appendFileSync)\s*\(\s*"
    r"(?P<target>'[^']+'|\"[^\"]+\")"
)

PATHLIB_WRITE_RE = re.compile(
    r"(?is)\b(?:Path|pathlib\.Path)\s*\(\s*"
    r"(?P<target>'[^']+'|\"[^\"]+\")\s*\)\s*"
    r"\.\s*(?:write_text|write_bytes)\s*\("
)

PY_OPEN_WRITE_RE = re.compile(
    r"(?is)\bopen\s*\(\s*"
    r"(?P<target>'[^']+'|\"[^\"]+\")\s*,\s*"
    r"(?P<mode>'[wa][^']*'|\"[wa][^\"]*\")"
)

SOURCE_PATH_PREFIXES = (
    "api/",
    "config/",
    "docs/",
    "public/",
    "runtime/",
    "scripts/",
    "src/",
    "test/",
    "tests/",
)

SOURCE_FILENAMES = {
    "AGENTS.md",
    "README.md",
    "package.json",
    "pyproject.toml",
    "server.js",
    "vercel.json",
}

SOURCE_SUFFIXES = (
    ".css",
    ".html",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mjs",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".yaml",
    ".yml",
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


def event_tool_name(event):
    value = event.get("tool_name") or event.get("toolName")
    return value if isinstance(value, str) else ""


def event_command(event):
    tool_input = event.get("tool_input")
    if isinstance(tool_input, dict) and isinstance(tool_input.get("command"), str):
        return tool_input["command"]
    tool_input = event.get("toolInput")
    if isinstance(tool_input, dict) and isinstance(tool_input.get("command"), str):
        return tool_input["command"]
    value = event.get("command")
    return value if isinstance(value, str) else ""


def strip_shell_quotes(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def is_ignored_target(target):
    target = strip_shell_quotes(target)
    if target in {"/dev/null", "&1", "&2"}:
        return True
    if target.startswith("/tmp/") and target.endswith((".log", ".out")):
        return True
    return False


def starts_with_apply_patch(command):
    return re.match(r"(?is)^\s*(?:command\s+)?apply_patch\b", command) is not None


def has_producer_redirect(command):
    for match in PRODUCER_REDIRECT_RE.finditer(command):
        if not is_ignored_target(match.group("target")):
            return True
    return False


def tee_targets(args):
    for token in re.findall(r"(?:'[^']+'|\"[^\"]+\"|[^\s<>]+)", args):
        token = strip_shell_quotes(token)
        if not token or token.startswith("-"):
            continue
        if token in {">", ">>"} or token.startswith(">"):
            continue
        yield token


def has_tee_write(command):
    for match in TEE_RE.finditer(command):
        for target in tee_targets(match.group("args")):
            if not is_ignored_target(target):
                return True
    return False


def is_source_edit_target(target):
    target = strip_shell_quotes(target).replace("\\/", "/")
    if is_ignored_target(target):
        return False
    if target.startswith("/tmp/"):
        return False

    normalized = target.lstrip("./")
    if normalized in SOURCE_FILENAMES:
        return True
    if normalized.startswith(SOURCE_PATH_PREFIXES):
        return True
    return normalized.endswith(SOURCE_SUFFIXES)


def has_script_file_write(command):
    for pattern in (JS_WRITE_RE, PATHLIB_WRITE_RE, PY_OPEN_WRITE_RE):
        for match in pattern.finditer(command):
            if is_source_edit_target(match.group("target")):
                return True
    return False


def should_block(event):
    tool_name = event_tool_name(event).lower()
    if tool_name in {"apply_patch", "edit", "write"}:
        return False

    command = event_command(event)
    if not command.strip():
        return False
    if starts_with_apply_patch(command):
        return False

    return has_producer_redirect(command) or has_tee_write(command) or has_script_file_write(command)


def deny_payload():
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": BLOCK_REASON,
        }
    }


def main():
    event = load_event()
    if should_block(event):
        print(json.dumps(deny_payload(), separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
