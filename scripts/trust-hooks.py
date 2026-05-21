#!/usr/bin/env python3
import argparse
import json
import os
import selectors
import subprocess
import sys
from pathlib import Path


class AppServerClient:
    def __init__(self, codex_home):
        env = os.environ.copy()
        env["CODEX_HOME"] = str(codex_home)
        self.process = subprocess.Popen(
            ["codex", "app-server", "--listen", "stdio://"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)

    def close(self):
        if self.process.stdin:
            self.process.stdin.close()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            self.process.wait(timeout=5)
        if self.process.stdout:
            self.selector.unregister(self.process.stdout)
            self.process.stdout.close()
        if self.process.stderr:
            self.process.stderr.close()
        self.selector.close()

    def send(self, message):
        self.process.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
        self.process.stdin.flush()

    def response_for(self, request_id, timeout=15):
        deadline = timeout
        while deadline > 0:
            events = self.selector.select(timeout=1)
            deadline -= 1
            for key, _ in events:
                line = key.fileobj.readline()
                if not line:
                    continue
                payload = json.loads(line)
                if payload.get("id") == request_id:
                    return payload
        stderr = self.process.stderr.read() if self.process.stderr else ""
        raise RuntimeError(f"timed out waiting for app-server response {request_id}: {stderr}")


def initialize(client):
    client.send(
        {
            "method": "initialize",
            "id": 1,
            "params": {
                "clientInfo": {"name": "codex-ollama-trust-hooks", "version": "0"},
                "capabilities": None,
            },
        }
    )
    response = client.response_for(1)
    if "result" not in response:
        raise RuntimeError(response)
    client.send({"method": "initialized", "params": None})


def list_hooks(client, cwd):
    client.send({"method": "hooks/list", "id": 2, "params": {"cwds": [str(cwd)]}})
    response = client.response_for(2)
    return response["result"]["data"][0]["hooks"]


def trust_hooks(client, hooks):
    state = {
        hook["key"]: {"enabled": True, "trusted_hash": hook["currentHash"]}
        for hook in hooks
        if "codex-ollama-" in hook.get("command", "")
    }
    if not state:
        raise RuntimeError("no Codex Ollama hooks found in hooks/list response")

    client.send(
        {
            "method": "config/batchWrite",
            "id": 3,
            "params": {
                "edits": [
                    {
                        "keyPath": "hooks.state",
                        "value": state,
                        "mergeStrategy": "upsert",
                    }
                ],
                "filePath": None,
                "expectedVersion": None,
                "reloadUserConfig": True,
            },
        }
    )
    response = client.response_for(3)
    if "result" not in response:
        raise RuntimeError(response)
    return state


def main():
    parser = argparse.ArgumentParser(description="Trust Codex Ollama hooks in Codex config.")
    parser.add_argument("--codex-home", default=str(Path.home() / ".codex-ollama"))
    parser.add_argument("--cwd", default=str(Path.home()))
    args = parser.parse_args()

    client = AppServerClient(Path(args.codex_home).expanduser().resolve())
    try:
        initialize(client)
        hooks = list_hooks(client, Path(args.cwd).expanduser().resolve())
        state = trust_hooks(client, hooks)
    finally:
        client.close()

    print(json.dumps({"trusted": sorted(state)}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FileNotFoundError as exc:
        print(f"codex executable not found: {exc}", file=sys.stderr)
        raise SystemExit(127)
