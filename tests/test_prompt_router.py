#!/usr/bin/env python3
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "runtime" / "codex-ollama-prompt-router.py"


def run_router(prompt):
    event = {"hook_event_name": "UserPromptSubmit", "prompt": prompt}
    return subprocess.run(
        [sys.executable, str(ROUTER)],
        input=json.dumps(event),
        text=True,
        capture_output=True,
        check=False,
    )


class PromptRouterTest(unittest.TestCase):
    def test_injects_skill_and_editing_context(self):
        result = run_router("Fix this failing test and implement the change.")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        output = payload["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "UserPromptSubmit")
        context = output["additionalContext"]
        self.assertIn("superpowers:using-superpowers", context)
        self.assertIn("superpowers:test-driven-development", context)
        self.assertIn("superpowers:systematic-debugging", context)
        self.assertIn("superpowers:verification-before-completion", context)
        self.assertIn("apply_patch", context)
        self.assertIn("rg", context)

    def test_context_is_brief_enough_for_every_prompt(self):
        result = run_router("hello")

        self.assertEqual(result.returncode, 0, result.stderr)
        context = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertLess(len(context.split()), 260)


if __name__ == "__main__":
    unittest.main(verbosity=2)
