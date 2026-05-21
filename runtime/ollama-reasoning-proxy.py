#!/usr/bin/env python3
import argparse
import copy
import http.client
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


HOP_BY_HOP_HEADERS = {
    "connection",
    "content-length",
    "host",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}

MAX_REASONING_MODELS = {
    "cogito-2.1:671b-cloud",
    "deepseek-v3.1:671b-cloud",
    "deepseek-v3.2:cloud",
    "deepseek-v4-flash:cloud",
    "deepseek-v4-pro:cloud",
    "gemini-3-flash-preview:cloud",
    "gemma4:31b-cloud",
    "glm-4.7:cloud",
    "glm-4.6:cloud",
    "glm-5.1:cloud",
    "glm-5:cloud",
    "gpt-oss:120b-cloud",
    "gpt-oss:20b-cloud",
    "kimi-k2.5:cloud",
    "kimi-k2.6:cloud",
    "minimax-m2.1:cloud",
    "minimax-m2.5:cloud",
    "minimax-m2.7:cloud",
    "minimax-m2:cloud",
    "nemotron-3-nano:30b-cloud",
    "nemotron-3-super:cloud",
    "qwen3-vl:235b-cloud",
    "qwen3.5:397b-cloud",
}

HIGH_REASONING_MODELS = {
    "qwen3-next:80b-cloud",
}

XHIGH_REASONING_TARGETS = {model: "max" for model in MAX_REASONING_MODELS}
XHIGH_REASONING_TARGETS.update({model: "high" for model in HIGH_REASONING_MODELS})


def rewrite_payload(payload):
    model = payload.get("model")
    xhigh_target = XHIGH_REASONING_TARGETS.get(model)
    if not xhigh_target:
        return False, payload

    rewritten = copy.deepcopy(payload)
    changed = False

    reasoning = rewritten.get("reasoning")
    if isinstance(reasoning, dict) and reasoning.get("effort") == "xhigh":
        reasoning["effort"] = xhigh_target
        changed = True
    elif reasoning == "xhigh":
        rewritten["reasoning"] = xhigh_target
        changed = True

    if rewritten.get("reasoning_effort") == "xhigh":
        rewritten["reasoning_effort"] = xhigh_target
        changed = True

    return changed, rewritten


class ReasoningProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    upstream = None

    def do_GET(self):
        if self.path == "/__codex_ollama_reasoning_proxy_health":
            body = b'{"ok":true}\n'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.forward_request()

    def do_POST(self):
        self.forward_request()

    def do_OPTIONS(self):
        self.forward_request()

    def do_HEAD(self):
        self.forward_request(send_body=False)

    def forward_request(self, send_body=True):
        body = self.rfile.read(int(self.headers.get("content-length", "0") or "0"))
        outbound_body = body
        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in HOP_BY_HOP_HEADERS
        }

        content_type = self.headers.get("content-type", "")
        if body and "application/json" in content_type:
            try:
                payload = json.loads(body)
                changed, rewritten = rewrite_payload(payload)
                if changed:
                    outbound_body = json.dumps(rewritten, separators=(",", ":")).encode("utf-8")
                    headers["Content-Type"] = "application/json"
            except json.JSONDecodeError:
                pass

        parsed = self.upstream
        connection_cls = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        upstream_path = self.path
        if parsed.path and parsed.path != "/":
            upstream_path = parsed.path.rstrip("/") + self.path

        connection = connection_cls(parsed.hostname, port, timeout=300)
        try:
            connection.request(self.command, upstream_path, body=outbound_body, headers=headers)
            response = connection.getresponse()
            self.send_response(response.status, response.reason)
            for key, value in response.getheaders():
                if key.lower() not in HOP_BY_HOP_HEADERS:
                    self.send_header(key, value)
            self.send_header("Connection", "close")
            self.end_headers()

            if not send_body:
                return

            while True:
                chunk = response.read(65536)
                if not chunk:
                    break
                self.wfile.write(chunk)
                self.wfile.flush()
        except BrokenPipeError:
            pass
        finally:
            connection.close()
            self.close_connection = True

    def log_message(self, fmt, *args):
        return


def main():
    parser = argparse.ArgumentParser(description="Rewrite Codex xhigh reasoning to Ollama max reasoning.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=11435)
    parser.add_argument("--upstream", default="http://127.0.0.1:11434")
    args = parser.parse_args()

    parsed = urlparse(args.upstream)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise SystemExit(f"invalid upstream URL: {args.upstream}")

    ReasoningProxyHandler.upstream = parsed
    server = ThreadingHTTPServer((args.host, args.port), ReasoningProxyHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
