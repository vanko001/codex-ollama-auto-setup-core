#!/usr/bin/env python3
import argparse
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / "runtime" / "ollama-cloud-model-catalog.json"
DEFAULT_PROXY = ROOT / "runtime" / "ollama-reasoning-proxy.py"


def load_proxy(path):
    spec = importlib.util.spec_from_file_location("ollama_reasoning_proxy", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit(catalog_path=DEFAULT_CATALOG, proxy_path=DEFAULT_PROXY):
    catalog = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
    proxy = load_proxy(Path(proxy_path))
    models = catalog["models"]
    reasoning = [model["slug"] for model in models if model.get("supports_reasoning_summaries")]
    mapped = proxy.XHIGH_REASONING_TARGETS
    missing = sorted(set(reasoning) - set(mapped))
    stale = sorted(set(mapped) - set(reasoning))

    return {
        "total_models": len(models),
        "reasoning_models": len(reasoning),
        "xhigh_to_max": sorted(
            model for model, target in mapped.items() if target == "max"
        ),
        "xhigh_to_high": sorted(
            model for model, target in mapped.items() if target == "high"
        ),
        "missing_proxy_mapping": missing,
        "stale_proxy_mapping": stale,
        "recommended_defaults": [
            "kimi-k2.6:cloud",
            "deepseek-v4-pro:cloud",
            "deepseek-v4-flash:cloud",
            "qwen3.5:397b-cloud",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Audit Ollama Cloud catalog optimization metadata.")
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    parser.add_argument("--proxy", default=str(DEFAULT_PROXY))
    args = parser.parse_args()
    result = audit(args.catalog, args.proxy)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result["missing_proxy_mapping"] or result["stale_proxy_mapping"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
