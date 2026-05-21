#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    path = ROOT / "scripts" / name
    module_name = name.replace("-", "_").replace(".py", "")
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PackagingScriptsTest(unittest.TestCase):
    def test_auto_setup_entrypoint_runs_install_build_and_verify(self):
        script = ROOT / "scripts" / "auto-setup.sh"
        self.assertTrue(script.is_file())
        text = script.read_text(encoding="utf-8")

        self.assertIn("scripts/install.sh", text)
        self.assertIn("scripts/build-codex-desktop-ollama.sh", text)
        self.assertIn("scripts/verify-install.sh", text)
        self.assertIn("codex doctor", text)

    def test_hooks_payload_contains_95_percent_guard_stack(self):
        writer = load_script("write-hooks.py")
        payload = writer.hooks_payload(Path("/tmp/runtime"))

        self.assertEqual(
            set(payload["hooks"]),
            {"UserPromptSubmit", "PreToolUse", "Stop"},
        )
        rendered = json.dumps(payload)
        self.assertIn("codex-ollama-prompt-router.py", rendered)
        self.assertIn("codex-ollama-tool-guard.py", rendered)
        self.assertIn("codex-ollama-stop-guard.py", rendered)

    def test_configure_profile_points_codex_at_reasoning_proxy(self):
        config = load_script("configure-profile.py")
        updated = config.configure(
            "",
            model="kimi-k2.6:cloud",
            catalog_path=Path("/tmp/catalog.json"),
            proxy_port="11435",
        )

        self.assertIn('model = "kimi-k2.6:cloud"', updated)
        self.assertIn('model_provider = "ollama-launch"', updated)
        self.assertIn('model_reasoning_effort = "xhigh"', updated)
        self.assertIn('base_url = "http://127.0.0.1:11435/v1"', updated)
        self.assertIn("project_root_markers = []", updated)
        self.assertIn("[profiles.ollama-launch]", updated)
        self.assertIn("[profiles.ollama-cloud]", updated)
        self.assertIn("[notice]", updated)
        self.assertIn("hide_full_access_warning = true", updated)
        self.assertIn('[plugins."superpowers@openai-curated"]', updated)
        self.assertIn('[plugins."github@openai-curated"]', updated)
        self.assertIn('[plugins."chrome@openai-bundled"]', updated)

    def test_model_picker_patch_disables_allowlist(self):
        patcher = load_script("patch-model-picker.py")
        with tempfile.TemporaryDirectory() as tmp:
            asset_dir = Path(tmp) / "content" / "webview" / "assets"
            asset_dir.mkdir(parents=True)
            asset = asset_dir / "model-queries-demo.js"
            asset.write_text(
                "function C(){let u=c.useHiddenModels&&o!==`amazonBedrock`,d;return d}",
                encoding="utf-8",
            )

            changed = patcher.patch_file(asset)

            self.assertTrue(changed)
            self.assertIn("let u=!1,d;return", asset.read_text(encoding="utf-8"))

    def test_catalog_audit_has_no_mapping_drift(self):
        audit_script = load_script("audit-ollama-catalog.py")
        result = audit_script.audit()

        self.assertGreaterEqual(result["total_models"], 30)
        self.assertGreaterEqual(result["reasoning_models"], 20)
        self.assertEqual(result["missing_proxy_mapping"], [])
        self.assertEqual(result["stale_proxy_mapping"], [])
        self.assertIn("kimi-k2.6:cloud", result["recommended_defaults"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
