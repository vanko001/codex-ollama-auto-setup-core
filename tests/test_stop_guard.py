#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "runtime" / "codex-ollama-stop-guard.py"


def run_guard(event):
    return subprocess.run(
        [sys.executable, str(GUARD)],
        input=json.dumps(event),
        text=True,
        capture_output=True,
        check=False,
    )


def block_reason(result):
    if not result.stdout.strip():
        return None
    payload = json.loads(result.stdout)
    if payload.get("decision") != "block":
        return None
    return payload.get("reason")


class StopGuardTest(unittest.TestCase):
    def test_blocks_completion_claim_without_fresh_verification(self):
        result = run_guard(
            {
                "hook_event_name": "Stop",
                "last_assistant_message": "Đã fix xong, all tests pass.",
                "stop_hook_active": False,
            }
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        reason = block_reason(result)
        self.assertIsNotNone(reason, result.stdout)
        self.assertIn("verification", reason.lower())

    def test_allows_completion_claim_with_successful_test_evidence(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8") as transcript:
            transcript.write(
                json.dumps(
                    {
                        "type": "response_item",
                        "item": {
                            "type": "function_call",
                            "name": "exec_command",
                            "arguments": json.dumps(
                                {"cmd": "python3 -m unittest discover -s tests"}
                            ),
                        },
                    }
                )
                + "\n"
            )
            transcript.write(
                json.dumps(
                    {
                        "type": "function_call_output",
                        "output": "Ran 12 tests in 0.20s\n\nOK\nProcess exited with code 0",
                    }
                )
                + "\n"
            )
            transcript.flush()

            result = run_guard(
                {
                    "hook_event_name": "Stop",
                    "last_assistant_message": "Fixed. Tests pass.",
                    "transcript_path": transcript.name,
                    "stop_hook_active": False,
                }
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")

    def test_allows_non_completion_status_without_verification(self):
        result = run_guard(
            {
                "hook_event_name": "Stop",
                "last_assistant_message": "Tôi đang kiểm tra thêm log và chưa kết luận.",
                "stop_hook_active": False,
            }
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")

    def test_does_not_loop_after_stop_continuation(self):
        result = run_guard(
            {
                "hook_event_name": "Stop",
                "last_assistant_message": "Done.",
                "stop_hook_active": True,
            }
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
