#!/usr/bin/env python3
import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import NamedTuple


APP_ID = "codex-desktop-ollama"
DEFAULT_MODEL = "kimi-k2.6:cloud"
DEFAULT_PROXY_PORT = "11435"
DEFAULT_UPSTREAM = "http://127.0.0.1:11434"


class Locations(NamedTuple):
    codex_home: Path
    runtime_dir: Path


def load_script(repo_root, script_name):
    path = Path(repo_root) / "scripts" / script_name
    module_name = script_name.replace("-", "_").replace(".py", "")
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def detect_platform():
    if sys.platform == "darwin":
        return "macos"
    if sys.platform.startswith("win"):
        return "windows"
    return "linux"


def default_locations(platform, home=None, appdata=None):
    home = Path(home or Path.home())
    codex_home = home / ".codex"

    if platform == "macos":
        runtime_dir = home / "Library" / "Application Support" / APP_ID
    elif platform == "windows":
        runtime_root = Path(appdata or os.environ.get("APPDATA") or (home / "AppData" / "Roaming"))
        runtime_dir = runtime_root / APP_ID
    elif platform == "linux":
        runtime_dir = home / ".local" / "share" / APP_ID
    else:
        raise ValueError(f"unsupported platform: {platform}")

    return Locations(codex_home=codex_home, runtime_dir=runtime_dir)


def default_hook_python(platform):
    if platform == "windows":
        return "py -3"
    return "python3"


def backup_file(path):
    if not path.exists():
        return None
    stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    backup = path.with_name(f"{path.name}.bak.{stamp}")
    shutil.copy2(path, backup)
    return backup


def install_runtime(repo_root, runtime_dir):
    runtime_dir.mkdir(parents=True, exist_ok=True)
    source_dir = Path(repo_root) / "runtime"
    installed = []
    for source in sorted(source_dir.iterdir()):
        if not source.is_file():
            continue
        if source.suffix != ".py" and source.name != "ollama-cloud-model-catalog.json":
            continue
        target = runtime_dir / source.name
        shutil.copy2(source, target)
        if target.suffix == ".py":
            target.chmod(0o755)
        installed.append(target)
    return installed


def write_proxy_helpers(runtime_dir, *, proxy_port, upstream, hook_python):
    shell_helper = runtime_dir / "start-reasoning-proxy.command"
    shell_helper.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                'RUNTIME_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"',
                f'PROXY_PORT="${{CODEX_OLLAMA_REASONING_PROXY_PORT:-{proxy_port}}}"',
                f'UPSTREAM="${{CODEX_OLLAMA_UPSTREAM:-{upstream}}}"',
                f'exec {hook_python} "$RUNTIME_DIR/ollama-reasoning-proxy.py" '
                '--host 127.0.0.1 --port "$PROXY_PORT" --upstream "$UPSTREAM"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    shell_helper.chmod(0o755)

    powershell_helper = runtime_dir / "Start-ReasoningProxy.ps1"
    powershell_helper.write_text(
        "\n".join(
            [
                "$ErrorActionPreference = 'Stop'",
                "$RuntimeDir = Split-Path -Parent $MyInvocation.MyCommand.Path",
                f"$Port = if ($env:CODEX_OLLAMA_REASONING_PROXY_PORT) {{ $env:CODEX_OLLAMA_REASONING_PROXY_PORT }} else {{ '{proxy_port}' }}",
                f"$Upstream = if ($env:CODEX_OLLAMA_UPSTREAM) {{ $env:CODEX_OLLAMA_UPSTREAM }} else {{ '{upstream}' }}",
                "$Proxy = Join-Path $RuntimeDir 'ollama-reasoning-proxy.py'",
                "& py -3 $Proxy --host 127.0.0.1 --port $Port --upstream $Upstream",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return shell_helper, powershell_helper


def configure_existing_app(
    *,
    repo_root,
    codex_home,
    runtime_dir,
    platform,
    model,
    proxy_port,
    upstream,
    hook_python,
    backup,
):
    repo_root = Path(repo_root).resolve()
    codex_home = Path(codex_home).expanduser()
    runtime_dir = Path(runtime_dir).expanduser()
    config_path = codex_home / "config.toml"
    hooks_path = codex_home / "hooks.json"

    configure_profile = load_script(repo_root, "configure-profile.py")
    write_hooks = load_script(repo_root, "write-hooks.py")

    codex_home.mkdir(parents=True, exist_ok=True)
    install_runtime(repo_root, runtime_dir)
    write_proxy_helpers(
        runtime_dir,
        proxy_port=proxy_port,
        upstream=upstream,
        hook_python=hook_python,
    )

    backups = []
    if backup:
        for path in (config_path, hooks_path):
            backup_path = backup_file(path)
            if backup_path:
                backups.append(str(backup_path))

    existing = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    updated_config = configure_profile.configure(
        existing,
        model=model,
        catalog_path=runtime_dir / "ollama-cloud-model-catalog.json",
        proxy_port=proxy_port,
    )
    config_path.write_text(updated_config, encoding="utf-8")

    command_platform = "windows" if platform == "windows" else "posix"
    hooks_payload = write_hooks.hooks_payload(
        runtime_dir,
        python_cmd=hook_python,
        command_platform=command_platform,
    )
    hooks_path.write_text(json.dumps(hooks_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return {
        "codex_home": str(codex_home),
        "runtime_dir": str(runtime_dir),
        "config": str(config_path),
        "hooks": str(hooks_path),
        "model": model,
        "proxy_url": f"http://127.0.0.1:{proxy_port}/v1",
        "backups": backups,
    }


def maybe_trust_hooks(repo_root, codex_home):
    codex = shutil.which("codex")
    if not codex:
        return {"trusted": False, "reason": "codex CLI not found"}
    result = subprocess.run(
        [
            sys.executable,
            str(Path(repo_root) / "scripts" / "trust-hooks.py"),
            "--codex-home",
            str(codex_home),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
    )
    return {
        "trusted": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": result.stdout[-2000:],
        "stderr": result.stderr[-2000:],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Attach the Codex Ollama runtime to an existing Codex app profile."
    )
    parser.add_argument("--platform", choices=("auto", "macos", "windows", "linux"), default="auto")
    parser.add_argument("--codex-home", help="Existing Codex config home. Defaults to ~/.codex.")
    parser.add_argument("--runtime-dir", help="Runtime install dir. Defaults to an OS-native app data path.")
    parser.add_argument("--model", default=os.environ.get("CODEX_OLLAMA_DEFAULT_MODEL", DEFAULT_MODEL))
    parser.add_argument("--proxy-port", default=os.environ.get("CODEX_OLLAMA_REASONING_PROXY_PORT", DEFAULT_PROXY_PORT))
    parser.add_argument("--upstream", default=os.environ.get("CODEX_OLLAMA_UPSTREAM", DEFAULT_UPSTREAM))
    parser.add_argument("--hook-python", help="Python command used in Codex hook commands.")
    parser.add_argument("--no-backup", action="store_true", help="Do not back up existing config.toml/hooks.json.")
    parser.add_argument("--trust-hooks", action="store_true", help="Attempt to trust generated hooks with codex app-server.")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    platform = detect_platform() if args.platform == "auto" else args.platform
    locations = default_locations(platform)
    codex_home = Path(args.codex_home).expanduser() if args.codex_home else locations.codex_home
    runtime_dir = Path(args.runtime_dir).expanduser() if args.runtime_dir else locations.runtime_dir
    hook_python = args.hook_python or default_hook_python(platform)

    result = configure_existing_app(
        repo_root=repo_root,
        codex_home=codex_home,
        runtime_dir=runtime_dir,
        platform=platform,
        model=args.model,
        proxy_port=args.proxy_port,
        upstream=args.upstream,
        hook_python=hook_python,
        backup=not args.no_backup,
    )
    result["platform"] = platform
    result["proxy_helpers"] = {
        "macos_linux": str(runtime_dir / "start-reasoning-proxy.command"),
        "windows": str(runtime_dir / "Start-ReasoningProxy.ps1"),
    }
    if args.trust_hooks:
        result["trust_hooks"] = maybe_trust_hooks(repo_root, codex_home)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
