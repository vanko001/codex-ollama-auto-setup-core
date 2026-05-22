#!/usr/bin/env python3
import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "runtime" / "ollama-cloud-model-catalog.json"


class OllamaCatalogTest(unittest.TestCase):
    def test_all_models_have_skill_workflow_router(self):
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        required_fragments = [
            "Skill Workflow Router v5",
            "superpowers:using-superpowers",
            "superpowers:systematic-debugging",
            "superpowers:test-driven-development",
            "superpowers:verification-before-completion",
            "read the applicable SKILL.md with a shell command before touching code",
            "Never use cat >, tee, printf >, or heredoc redirection",
            "Do not run kill, pkill, killall",
            "final answer exactly",
        ]

        self.assertGreaterEqual(len(catalog["models"]), 30)
        for model in catalog["models"]:
            instructions = model["base_instructions"]
            for fragment in required_fragments:
                with self.subTest(model=model["slug"], fragment=fragment):
                    self.assertIn(fragment, instructions)


if __name__ == "__main__":
    unittest.main(verbosity=2)
