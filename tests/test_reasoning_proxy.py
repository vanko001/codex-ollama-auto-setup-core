#!/usr/bin/env python3
import importlib.util
import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
PROXY_PATH = ROOT / "runtime" / "ollama-reasoning-proxy.py"
CATALOG_PATH = ROOT / "runtime" / "ollama-cloud-model-catalog.json"


def load_proxy_module():
    spec = importlib.util.spec_from_file_location("ollama_reasoning_proxy", PROXY_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReasoningProxyTest(unittest.TestCase):
    def test_maps_xhigh_to_model_native_max_or_high(self):
        proxy = load_proxy_module()

        changed, rewritten = proxy.rewrite_payload(
            {"model": "kimi-k2.6:cloud", "reasoning": {"effort": "xhigh"}}
        )
        self.assertTrue(changed)
        self.assertEqual(rewritten["reasoning"]["effort"], "max")

        changed, rewritten = proxy.rewrite_payload(
            {"model": "qwen3-next:80b-cloud", "reasoning": {"effort": "xhigh"}}
        )
        self.assertTrue(changed)
        self.assertEqual(rewritten["reasoning"]["effort"], "high")

    def test_leaves_non_reasoning_models_unchanged(self):
        proxy = load_proxy_module()
        payload = {"model": "qwen3-coder-next:cloud", "reasoning": {"effort": "xhigh"}}
        changed, rewritten = proxy.rewrite_payload(payload)
        self.assertFalse(changed)
        self.assertEqual(rewritten, payload)

    def test_proxy_reasoning_models_match_catalog(self):
        proxy = load_proxy_module()
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        catalog_models = {
            model["slug"]
            for model in catalog["models"]
            if model.get("supports_reasoning_summaries") is True
        }

        self.assertEqual(set(proxy.XHIGH_REASONING_TARGETS), catalog_models)


if __name__ == "__main__":
    unittest.main(verbosity=2)
