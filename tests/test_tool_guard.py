#!/usr/bin/env python3
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "runtime" / "codex-ollama-tool-guard.py"


def run_guard(command, *, tool_name="Bash", event=None):
    payload = event or {
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "tool_input": {"command": command},
    }
    return subprocess.run(
        [sys.executable, str(GUARD)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )


def denial_reason(result):
    if not result.stdout.strip():
        return None
    payload = json.loads(result.stdout)
    output = payload.get("hookSpecificOutput", {})
    if output.get("permissionDecision") != "deny":
        return None
    return output.get("permissionDecisionReason")


class ToolGuardTest(unittest.TestCase):
    def assert_allowed(self, command, **kwargs):
        result = run_guard(command, **kwargs)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")
        self.assertEqual(result.stderr.strip(), "")

    def assert_blocked(self, command, **kwargs):
        result = run_guard(command, **kwargs)
        self.assertEqual(result.returncode, 0, result.stderr)
        reason = denial_reason(result)
        self.assertIsNotNone(reason, result.stdout)
        self.assertIn("apply_patch", reason)

    def assert_process_blocked(self, command, **kwargs):
        result = run_guard(command, **kwargs)
        self.assertEqual(result.returncode, 0, result.stderr)
        reason = denial_reason(result)
        self.assertIsNotNone(reason, result.stdout)
        self.assertIn("process", reason)

    def test_blocks_direct_shell_writes(self):
        self.assert_blocked("cat > test_example.py <<'EOF'\nprint('x')\nEOF")
        self.assert_blocked("tee test_example.py >/dev/null <<'EOF'\nprint('x')\nEOF")
        self.assert_blocked("printf '%s\\n' 'x' > src/example.py")
        self.assert_blocked("echo '- todo' >> notes.md")
        self.assert_blocked(
            "node -e \"require('fs').writeFileSync('src/example.js', 'module.exports = 1')\""
        )
        self.assert_blocked(
            "python3 - <<'PY'\nfrom pathlib import Path\nPath('tests/example.test.py').write_text('x')\nPY"
        )

    def test_allows_reads_and_apply_patch(self):
        self.assert_allowed("cat src/example.py")
        self.assert_allowed("python3 - <<'PY'\nprint('diagnostic')\nPY")
        self.assert_allowed("node -e \"console.log(require('fs').readFileSync('src/example.js', 'utf8'))\"")
        self.assert_allowed("pytest > /tmp/codex-test-output.log")
        self.assert_allowed("apply_patch <<'PATCH'\n*** Begin Patch\n*** End Patch\nPATCH")
        self.assert_allowed("cat > file.py <<'EOF'\nx\nEOF", tool_name="apply_patch")
        self.assert_allowed("kill -0 62992 2>/dev/null || true")

    def test_blocks_process_termination_commands(self):
        self.assert_process_blocked("kill 62992 2>/dev/null || true")
        self.assert_process_blocked("kill -9 62992")
        self.assert_process_blocked("sudo pkill -f 'gh auth login'")
        self.assert_process_blocked("killall node || true")
        self.assert_process_blocked("ps aux | rg 'vite' | awk '{print $2}' | xargs kill")


if __name__ == "__main__":
    unittest.main(verbosity=2)
