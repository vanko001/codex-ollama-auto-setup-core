#!/usr/bin/env python3
import argparse
import re
from pathlib import Path


APP_ID = "codex-desktop-ollama"
PROVIDER = "ollama-launch"
WORKFLOW_PLUGINS = (
    "documents@openai-primary-runtime",
    "spreadsheets@openai-primary-runtime",
    "presentations@openai-primary-runtime",
    "github@openai-curated",
    "superpowers@openai-curated",
    "chrome@openai-bundled",
)


def set_top_level_key(text, key, value):
    rendered = f'{key} = "{value}"'
    return set_top_level_raw(text, key, rendered)


def set_top_level_raw(text, key, rendered):
    pattern = re.compile(rf"(?m)^{re.escape(key)}\s*=.*$")
    if pattern.search(text):
        return pattern.sub(rendered, text, count=1)
    prefix = rendered + "\n"
    return prefix + text.lstrip("\n")


def replace_table(text, table_name, table_body):
    header = f"[{table_name}]"
    pattern = re.compile(
        rf"(?ms)^{re.escape(header)}\n.*?(?=^\[|\Z)"
    )
    replacement = header + "\n" + table_body.rstrip() + "\n\n"
    if pattern.search(text):
        return pattern.sub(replacement, text, count=1)
    return text.rstrip() + "\n\n" + replacement


def configure(text, *, model, catalog_path, proxy_port):
    text = set_top_level_key(text, "model", model)
    text = set_top_level_key(text, "model_provider", PROVIDER)
    text = set_top_level_key(text, "model_catalog_json", str(catalog_path))
    text = set_top_level_key(text, "model_reasoning_effort", "xhigh")
    text = set_top_level_raw(text, "project_root_markers", "project_root_markers = []")

    provider_body = "\n".join(
        [
            'name = "Ollama"',
            f'base_url = "http://127.0.0.1:{proxy_port}/v1"',
        ]
    )
    text = replace_table(text, f"model_providers.{PROVIDER}", provider_body)

    profile_body = "\n".join(
        [
            f'model = "{model}"',
            f'model_provider = "{PROVIDER}"',
        ]
    )
    text = replace_table(text, "profiles.ollama-launch", profile_body)
    text = replace_table(text, "profiles.ollama-cloud", profile_body)
    text = replace_table(text, "notice", "hide_full_access_warning = true")

    for plugin in WORKFLOW_PLUGINS:
        text = replace_table(text, f'plugins."{plugin}"', "enabled = true")

    return text


def main():
    parser = argparse.ArgumentParser(description="Configure the isolated Codex Ollama profile.")
    parser.add_argument(
        "--config",
        default=str(Path.home() / ".codex-ollama" / "config.toml"),
    )
    parser.add_argument(
        "--catalog",
        default=str(Path.home() / ".local" / "share" / APP_ID / "ollama-cloud-model-catalog.json"),
    )
    parser.add_argument("--model", default="kimi-k2.6:cloud")
    parser.add_argument("--proxy-port", default="11435")
    args = parser.parse_args()

    config_path = Path(args.config).expanduser().resolve()
    catalog_path = Path(args.catalog).expanduser().resolve()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    existing = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    updated = configure(
        existing,
        model=args.model,
        catalog_path=catalog_path,
        proxy_port=args.proxy_port,
    )
    config_path.write_text(updated, encoding="utf-8")
    print(config_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
