"""Native `/v1/responses` and open-weight MCP agent loop for Meta Muse models.

Why this exists (LINC rule c887e8a3):
Meta's Anthropic-compatible `POST /v1/messages` endpoint returns HTTP 400 when a
Claude Code harness sends `container`, `inference_geo`, `stop_sequences`,
`top_k`, or `thinking.type="disabled"`. Running `muse-*` and `meta-models/*`
through a direct MCP stdio loop over `POST /v1/responses` (or OpenAI-compatible
`/v1/chat/completions` for open-weight endpoints) preserves every mobile-agent-bench
fairness invariant while replaying `reasoning.encrypted_content` and maintaining
a stable `prompt_cache_key` across turns.

Fairness & confinement invariants (identical to `agent.py`):
- Runs in `AGENT_CWD` (`/tmp/mab-agent-cwd`) outside the benchmark repo.
- Spawns ONLY the MCP servers declared in `resolve_mcp_config(tool)`.
- Exposes ONLY the MCP server tools plus a synthetic `Read(file_path)` tool
  enforcing the exact `READ_GUARD` regex (blocking benchmark source / SPEC.md
  while allowing `/tmp` screenshots and tool logs).
- Emits the same `transcript.jsonl` (`assistant` + terminal `result` records)
  and runs `sanitize_file` + `parse_transcript` so `verify_task`, `bench report`,
  and `bench regrade` behave identically across Claude and Meta runs.
"""

from __future__ import annotations

import base64
import json
import math
import mimetypes
import os
import re
import selectors
import subprocess
import threading
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

from .agent import AGENT_CWD, AgentRun, ensure_confinement, resolve_mcp_config
from .sanitize import sanitize_file
from .schema import Task, Tool
from .tokens import parse_transcript

META_MODEL_PREFIXES = ("muse-", "meta-models/")
DEFAULT_META_BASE_URL = "https://api.meta.ai/v1"
DEFAULT_OPEN_WEIGHT_BASE_URL = "https://inference.baseten.co/v1"
# Safety stop only: the task's wall-clock timeout_s is the binding budget, as for
# the Claude baseline cells (c9 used 101-165 turns). The original 40 cut the
# 2026-10-27 c9 cell off at 131 s of a 900 s budget.
DEFAULT_MAX_TURNS = 300
MAX_TURNS_ENV = "BENCH_META_MAX_TURNS"
MAX_READ_TEXT_BYTES = 65_536

# Exact regex from agent.py READ_GUARD (Erratum #2): blocks app source & SPEC.md
# while permitting screenshot PNGs and tool logs in /tmp.
READ_GUARD_PATTERN = re.compile(
    r"(mobile-agent-bench|target-app|/src/(main|test)/|\.kt$|\.java$|SPEC\.md$)",
    re.IGNORECASE,
)

# Published Meta API token rates (USD per 1M tokens) from dev.meta.ai/docs/pricing-rate-limits
# for cost reporting when available; None if unknown (e.g. self-hosted / open-weight endpoints).
_MODEL_PRICING_PER_M: dict[str, tuple[float, float, float]] = {
    # (uncached_input_per_m, cached_input_per_m, output_per_m)
    "muse-spark-1.3": (1.25, 0.15, 4.25),
    "muse-spark-1.3-contributor": (0.10, 0.002, 0.20),
    "muse-wonder-1.0": (4.00, 0.20, 20.00),
    "muse-spark-1.2": (1.25, 0.15, 4.25),
    "muse-spark-1.2-contributor": (0.10, 0.002, 0.20),
    "muse-spark-1.1": (1.25, 0.15, 4.25),
    "meta-models/Muse-Glimmer-30B": (0.35, 0.04, 1.50),
}

SYNTHETIC_READ_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "file_path": {
            "type": "string",
            "description": "Absolute path to the file (e.g. screenshot PNG or log) to read.",
        }
    },
    "required": ["file_path"],
}

SYSTEM_INSTRUCTIONS = (
    "You are an autonomous mobile-device benchmark agent. Complete the task "
    "using ONLY the provided MCP tools (and Read for viewing screenshot files "
    "returned by tools). When finished, state your final answer clearly."
)


def is_meta_model(model: str) -> bool:
    """Return True if *model* should run through the Meta / open-weight MCP loop."""
    if not isinstance(model, str):
        return False
    stripped = model.strip()
    return stripped.startswith(META_MODEL_PREFIXES)


def is_read_blocked(file_path: str) -> bool:
    """Enforce Erratum #2 Read-guard: block repo ground-truth, allow screenshots."""
    if not isinstance(file_path, str) or not file_path.strip():
        return True
    return bool(READ_GUARD_PATTERN.search(file_path))


def execute_read_tool(file_path: str) -> tuple[str, list[str]]:
    """Execute the confined `Read` tool, returning `(text_output, image_data_urls)`."""
    if is_read_blocked(file_path):
        return (
            "Read blocked: benchmark ground-truth (app source/SPEC) is off-limits. "
            "Use the device tools to obtain information, not the source.",
            [],
        )
    path = Path(file_path).expanduser()
    if not path.is_file():
        return f"Error: file not found: {file_path}", []
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return f"Error reading {file_path}: {exc}", []

    mime, _ = mimetypes.guess_type(str(path))
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        mime = "image/png"
    elif raw.startswith(b"\xff\xd8\xff"):
        mime = "image/jpeg"
    elif raw.startswith(b"RIFF") and raw[8:12] == b"WEBP":
        mime = "image/webp"

    if mime and mime.startswith("image/"):
        b64 = base64.b64encode(raw).decode("ascii")
        data_url = f"data:{mime};base64,{b64}"
        return f"Loaded image {file_path} ({len(raw)} bytes, {mime}).", [data_url]

    text = raw[:MAX_READ_TEXT_BYTES].decode("utf-8", errors="replace")
    if len(raw) > MAX_READ_TEXT_BYTES:
        text += f"\n...[truncated {len(raw) - MAX_READ_TEXT_BYTES} bytes]"
    return text, []


def _keychain_secret(account: str, service: str = "linc-env") -> str | None:
    """Read a secret from macOS Keychain without ever echoing it."""
    try:
        proc = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-a", account, "-w"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    secret = (proc.stdout or "").strip()
    return secret or None


def resolve_api_key(model: str, env: dict[str, str] | None = None) -> str:
    """Resolve the API key for *model* from environment variables or Keychain."""
    environ = env if env is not None else os.environ
    if model.startswith("meta-models/"):
        candidates = ("BASETEN_API_KEY", "TOGETHER_API_KEY", "OPENAI_API_KEY", "META_AI_API_KEY", "META_API_KEY")
    else:
        candidates = ("META_AI_API_KEY", "META_API_KEY")

    for name in candidates:
        val = (environ.get(name) or "").strip()
        if val:
            return val
    for name in candidates:
        val = _keychain_secret(name)
        if val:
            return val
    raise RuntimeError(
        f"Missing API key for model {model!r}; set {candidates[0]} in env or Keychain (service 'linc-env')."
    )


def normalize_usage(raw_usage: dict[str, Any] | None) -> dict[str, int]:
    """Convert `/v1/responses` or `/v1/chat/completions` usage to `tokens.py` schema.

    In Meta / OpenAI responses, `input_tokens` (or `prompt_tokens`) is the TOTAL
    input token count including `cached_tokens`. `mobile_agent_bench/tokens.py`
    computes:
      - `total_billed = input_tokens + output_tokens + cache_creation + cache_read`
      - `total_uncached = input_tokens + output_tokens + cache_creation`
    Therefore `input_tokens` here MUST be the uncached input portion
    (`raw_input - cached_tokens`), and `cache_read_input_tokens` is `cached_tokens`.
    """
    if not isinstance(raw_usage, dict):
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
            "reasoning_tokens": 0,
            "raw_input_tokens": 0,
        }

    def _safe_nonneg_int(val: Any) -> int:
        if isinstance(val, bool) or val is None:
            return 0
        if isinstance(val, float) and not math.isfinite(val):
            return 0
        try:
            return max(0, int(val))
        except (TypeError, ValueError):
            return 0

    raw_input = _safe_nonneg_int(
        raw_usage.get("input_tokens", raw_usage.get("prompt_tokens", 0))
    )
    raw_output = _safe_nonneg_int(
        raw_usage.get("output_tokens", raw_usage.get("completion_tokens", 0))
    )
    in_details = (
        raw_usage.get("input_tokens_details")
        or raw_usage.get("prompt_tokens_details")
        or {}
    )
    out_details = (
        raw_usage.get("output_tokens_details")
        or raw_usage.get("completion_tokens_details")
        or {}
    )
    cached = _safe_nonneg_int(in_details.get("cached_tokens", 0)) if isinstance(in_details, dict) else 0
    if cached > raw_input:
        cached = raw_input
    reasoning = (
        _safe_nonneg_int(out_details.get("reasoning_tokens", 0))
        if isinstance(out_details, dict)
        else 0
    )
    uncached_input = raw_input - cached
    return {
        "input_tokens": uncached_input,
        "output_tokens": raw_output,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": cached,
        "reasoning_tokens": reasoning,
        "raw_input_tokens": raw_input,
    }


def estimate_cost_usd(model: str, usage: dict[str, int]) -> float | None:
    """Estimate run cost in USD when model pricing is known."""
    rates = _MODEL_PRICING_PER_M.get(model)
    if rates is None:
        return None
    in_rate, cached_rate, out_rate = rates
    cost = (
        usage.get("input_tokens", 0) * in_rate
        + usage.get("cache_read_input_tokens", 0) * cached_rate
        + usage.get("output_tokens", 0) * out_rate
    ) / 1_000_000.0
    return round(cost, 6)


def clean_json_schema(schema: Any) -> dict[str, Any]:
    """Ensure a tool parameter schema is a valid JSON Schema object for `/v1/responses`."""
    if not isinstance(schema, dict):
        return {"type": "object", "properties": {}}
    cleaned = {k: v for k, v in schema.items() if k != "$schema"}
    cleaned.setdefault("type", "object")
    cleaned.setdefault("properties", {})
    return cleaned


def build_replay_items(output_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter and normalize assistant `output` items for `/v1/responses` multi-turn replay.

    Preserves item order (`reasoning` with `encrypted_content`, `message`, and
    `function_call`) as required by Meta's stateless `/v1/responses` contract.
    """
    replay: list[dict[str, Any]] = []
    for item in output_items:
        if not isinstance(item, dict):
            continue
        itype = item.get("type")
        if itype == "reasoning":
            rec: dict[str, Any] = {
                "type": "reasoning",
                "summary": item.get("summary") if isinstance(item.get("summary"), list) else [],
            }
            if item.get("id"):
                rec["id"] = item["id"]
            if "encrypted_content" in item and item["encrypted_content"] is not None:
                rec["encrypted_content"] = item["encrypted_content"]
            replay.append(rec)
        elif itype == "message":
            msg: dict[str, Any] = {
                "type": "message",
                "role": item.get("role", "assistant"),
                "content": item.get("content") if isinstance(item.get("content"), list) else [],
            }
            if item.get("id"):
                msg["id"] = item["id"]
            replay.append(msg)
        elif itype == "function_call":
            fc: dict[str, Any] = {
                "type": "function_call",
                "call_id": str(item.get("call_id") or ""),
                "name": str(item.get("name") or ""),
                "arguments": (
                    item["arguments"]
                    if isinstance(item.get("arguments"), str)
                    else json.dumps(item.get("arguments") or {})
                ),
            }
            if item.get("id"):
                fc["id"] = item["id"]
            replay.append(fc)
    return replay


def extract_assistant_blocks(output_items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    """Extract Claude-compatible `content` blocks and plain text strings from `/v1/responses` output."""
    blocks: list[dict[str, Any]] = []
    texts: list[str] = []
    for item in output_items:
        if not isinstance(item, dict):
            continue
        itype = item.get("type")
        if itype == "message":
            for part in item.get("content") or []:
                if isinstance(part, dict) and part.get("type") in ("output_text", "text"):
                    txt = str(part.get("text") or "")
                    if txt:
                        texts.append(txt)
                        blocks.append({"type": "text", "text": txt})
        elif itype == "function_call":
            raw_args = item.get("arguments")
            try:
                parsed_args = json.loads(raw_args) if isinstance(raw_args, str) else (raw_args or {})
            except json.JSONDecodeError:
                parsed_args = {"_raw": str(raw_args)}
            blocks.append({
                "type": "tool_use",
                "id": str(item.get("call_id") or ""),
                "name": str(item.get("name") or ""),
                "input": parsed_args,
            })
    return blocks, texts


class StdioMcpServer:
    """Minimal JSON-RPC 2.0 stdio client for a single MCP server subprocess."""

    def __init__(self, name: str, command: str, args: list[str], env: dict[str, str], cwd: Path) -> None:
        self.name = name
        self.command = command
        self.args = args
        self.env = env
        self.cwd = cwd
        self.proc: subprocess.Popen[bytes] | None = None
        self._next_id = 1
        self._stderr_chunks: list[str] = []
        self._stderr_thread: threading.Thread | None = None
        self._read_buf = b""

    def start(self, deadline: float) -> None:
        self.proc = subprocess.Popen(
            [self.command, *self.args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self.env,
            cwd=str(self.cwd),
        )
        self._stderr_thread = threading.Thread(target=self._drain_stderr, daemon=True)
        self._stderr_thread.start()

        self.request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "mobile-agent-bench", "version": "0.1.0"},
            },
            deadline=deadline,
        )
        self.notify("notifications/initialized", {})

    def _drain_stderr(self) -> None:
        if self.proc is None or self.proc.stderr is None:
            return
        try:
            for raw_line in iter(self.proc.stderr.readline, b""):
                self._stderr_chunks.append(raw_line.decode("utf-8", errors="replace"))
        except Exception:
            return

    def stderr_tail(self, limit: int = 2000) -> str:
        return "".join(self._stderr_chunks)[-limit:]

    def notify(self, method: str, params: dict[str, Any]) -> None:
        if self.proc is None or self.proc.stdin is None:
            raise RuntimeError(f"MCP server {self.name} is not running")
        payload = json.dumps({"jsonrpc": "2.0", "method": method, "params": params}) + "\n"
        self.proc.stdin.write(payload.encode("utf-8"))
        self.proc.stdin.flush()

    def request(self, method: str, params: dict[str, Any], deadline: float) -> dict[str, Any]:
        if self.proc is None or self.proc.stdin is None or self.proc.stdout is None:
            raise RuntimeError(f"MCP server {self.name} is not running")
        req_id = self._next_id
        self._next_id += 1
        payload = (
            json.dumps({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}) + "\n"
        )
        self.proc.stdin.write(payload.encode("utf-8"))
        self.proc.stdin.flush()

        while True:
            line = self._read_line(deadline)
            stripped = line.strip()
            if not stripped:
                continue
            try:
                msg = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if not isinstance(msg, dict):
                continue
            if msg.get("id") != req_id:
                continue
            if "error" in msg and msg["error"] is not None:
                err = msg["error"]
                raise RuntimeError(f"MCP {self.name}.{method} error: {err}")
            res = msg.get("result")
            return res if isinstance(res, dict) else {}

    def _read_line(self, deadline: float) -> str:
        assert self.proc is not None and self.proc.stdout is not None
        fd = self.proc.stdout.fileno()
        while b"\n" not in self._read_buf:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"Timed out waiting for MCP server {self.name}")
            with selectors.DefaultSelector() as sel:
                sel.register(fd, selectors.EVENT_READ)
                events = sel.select(timeout=min(remaining, 1.0))
            if not events:
                if self.proc.poll() is not None:
                    raise RuntimeError(
                        f"MCP server {self.name} exited early (code {self.proc.returncode}): "
                        f"{self.stderr_tail(500)}"
                    )
                continue
            chunk = os.read(fd, 65_536)
            if not chunk:
                raise RuntimeError(
                    f"MCP server {self.name} closed stdout unexpectedly: {self.stderr_tail(500)}"
                )
            self._read_buf += chunk

        raw_line, self._read_buf = self._read_buf.split(b"\n", 1)
        return raw_line.decode("utf-8", errors="replace")

    def list_tools(self, deadline: float) -> list[dict[str, Any]]:
        res = self.request("tools/list", {}, deadline=deadline)
        tools = res.get("tools")
        return [t for t in tools if isinstance(t, dict)] if isinstance(tools, list) else []

    def call_tool(
        self, name: str, arguments: dict[str, Any], deadline: float
    ) -> tuple[str, list[str]]:
        res = self.request(
            "tools/call",
            {"name": name, "arguments": arguments},
            deadline=deadline,
        )
        content = res.get("content") or []
        texts: list[str] = []
        images: list[str] = []
        if isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue
                btype = block.get("type")
                if btype == "text":
                    texts.append(str(block.get("text") or ""))
                elif btype == "image" and block.get("data"):
                    mime = str(block.get("mimeType") or "image/png")
                    images.append(f"data:{mime};base64,{block['data']}")
        output_text = "\n".join(texts) if texts else json.dumps(res)
        return output_text, images

    def close(self) -> None:
        if self.proc is None:
            return
        try:
            if self.proc.stdin:
                self.proc.stdin.close()
        except Exception:
            pass
        try:
            self.proc.terminate()
            self.proc.wait(timeout=2)
        except Exception:
            try:
                self.proc.kill()
            except Exception:
                pass
        self.proc = None


@dataclass
class McpToolRouter:
    """Routes tool calls across configured MCP servers plus the confined `Read` tool."""

    servers: list[StdioMcpServer] = field(default_factory=list)
    tool_map: dict[str, tuple[StdioMcpServer, str]] = field(default_factory=dict)
    tool_Specs: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_config_path(
        cls, mcp_config_path: str, env: dict[str, str], cwd: Path, deadline: float
    ) -> McpToolRouter:
        router = cls()
        cfg = json.loads(Path(mcp_config_path).read_text())
        servers_cfg = cfg.get("mcpServers") or {}
        for srv_name, spec in servers_cfg.items():
            if not isinstance(spec, dict):
                continue
            command = str(spec["command"])
            args = [str(a) for a in (spec.get("args") or [])]
            srv_env = {**env, **{str(k): str(v) for k, v in (spec.get("env") or {}).items()}}
            srv = StdioMcpServer(srv_name, command, args, srv_env, cwd)
            srv.start(deadline=deadline)
            router.servers.append(srv)
            for t in srv.list_tools(deadline=deadline):
                orig_name = str(t.get("name") or "")
                if not orig_name:
                    continue
                exposed_name = (
                    orig_name
                    if orig_name not in router.tool_map and orig_name != "Read"
                    else f"{srv_name}__{orig_name}"
                )
                router.tool_map[exposed_name] = (srv, orig_name)
                router.tool_Specs.append(
                    {
                        "type": "function",
                        "name": exposed_name,
                        "description": str(t.get("description") or ""),
                        "parameters": clean_json_schema(t.get("inputSchema")),
                    }
                )

        router.tool_Specs.append(
            {
                "type": "function",
                "name": "Read",
                "description": (
                    "Read a local screenshot image (.png/.jpg) or tool log file by absolute path."
                ),
                "parameters": SYNTHETIC_READ_SCHEMA,
            }
        )
        return router

    def invoke(self, tool_name: str, raw_arguments: Any, deadline: float) -> tuple[str, list[str]]:
        if isinstance(raw_arguments, str):
            try:
                args = json.loads(raw_arguments) if raw_arguments.strip() else {}
            except json.JSONDecodeError as exc:
                return f"Error: malformed JSON arguments for {tool_name}: {exc}", []
        elif isinstance(raw_arguments, dict):
            args = raw_arguments
        else:
            return f"Error: arguments for {tool_name} must be a JSON object", []

        if not isinstance(args, dict):
            return f"Error: arguments for {tool_name} must decode to a JSON object", []

        if tool_name == "Read":
            return execute_read_tool(str(args.get("file_path") or ""))

        target = self.tool_map.get(tool_name)
        if target is None:
            return f"Error: unknown tool {tool_name!r}", []

        srv, orig_name = target
        try:
            return srv.call_tool(orig_name, args, deadline=deadline)
        except TimeoutError:
            raise
        except Exception as exc:
            return f"Error calling {tool_name}: {exc}", []

    def stderr_summary(self) -> str:
        parts = []
        for srv in self.servers:
            tail = srv.stderr_tail()
            if tail:
                parts.append(f"[{srv.name}]\n{tail}")
        return "\n".join(parts)[-4000:]

    def close(self) -> None:
        for srv in self.servers:
            srv.close()


def post_json(
    url: str,
    api_key: str,
    payload: dict[str, Any],
    timeout_s: float,
) -> dict[str, Any]:
    """Send an authenticated JSON POST request and return the decoded JSON object."""
    if timeout_s <= 0:
        raise TimeoutError("Request deadline exceeded before HTTP call")
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "mobile-agent-bench/0.1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=max(1.0, timeout_s)) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        err_body = ""
        try:
            err_body = exc.read().decode("utf-8", errors="replace")[:1000]
        except Exception:
            pass
        raise RuntimeError(f"HTTP {exc.code} from {url}: {err_body}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        if isinstance(exc, TimeoutError) or "timed out" in str(exc).lower():
            raise TimeoutError(f"HTTP request to {url} timed out") from exc
        raise RuntimeError(f"HTTP request to {url} failed: {exc}") from exc

    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise RuntimeError(f"Expected JSON object from {url}, got {type(parsed).__name__}")
    return parsed


def _chat_completion_to_responses_shape(chat_resp: dict[str, Any]) -> dict[str, Any]:
    """Adapt an OpenAI-compatible `/v1/chat/completions` response to `/v1/responses` shape."""
    choices = chat_resp.get("choices") or []
    msg = (choices[0].get("message") if choices and isinstance(choices[0], dict) else None) or {}
    output: list[dict[str, Any]] = []
    content_text = msg.get("content")
    if isinstance(content_text, str) and content_text:
        output.append(
            {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": content_text}],
            }
        )
    for tc in msg.get("tool_calls") or []:
        if not isinstance(tc, dict):
            continue
        fn = tc.get("function") or {}
        output.append(
            {
                "type": "function_call",
                "call_id": str(tc.get("id") or f"call_{uuid.uuid4().hex[:8]}"),
                "name": str(fn.get("name") or ""),
                "arguments": str(fn.get("arguments") or "{}"),
            }
        )
    return {"output": output, "usage": chat_resp.get("usage") or {}, "_assistant_msg": msg}


def resolve_max_turns(env: Mapping[str, str]) -> int:
    """Turn cap from BENCH_META_MAX_TURNS; anything but a plain positive int falls back."""
    raw = env.get(MAX_TURNS_ENV, "")
    if re.fullmatch(r"[1-9][0-9]{0,5}", raw):
        return int(raw)
    return DEFAULT_MAX_TURNS


def run_muse_agent(
    task: Task,
    tool: Tool,
    model: str,
    out_dir: Path,
    *,
    http_post: Callable[[str, str, dict[str, Any], float], dict[str, Any]] = post_json,
    router_factory: Callable[[str, dict[str, str], Path, float], McpToolRouter] | None = None,
) -> AgentRun:
    """Run a benchmark task using Meta `/v1/responses` or open-weight `/v1/chat/completions`."""
    out_dir.mkdir(parents=True, exist_ok=True)
    transcript = out_dir.resolve() / "transcript.jsonl"
    env = {**os.environ, **tool.env}
    AGENT_CWD.mkdir(parents=True, exist_ok=True)
    ensure_confinement(AGENT_CWD)

    start = time.monotonic()
    deadline = start + float(task.timeout_s)
    timed_out = False
    exit_code = 0
    stderr_notes: list[str] = []

    cumulative_usage = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
        "reasoning_tokens": 0,
        "raw_input_tokens": 0,
    }
    num_turns = 0
    final_text = ""
    max_turns = resolve_max_turns(env)

    mcp_config_path = resolve_mcp_config(tool)
    build_router = router_factory or McpToolRouter.from_config_path
    router: McpToolRouter | None = None

    try:
        api_key = resolve_api_key(model, env)
        router = build_router(mcp_config_path, env, AGENT_CWD, deadline)
        prompt_cache_key = f"mab-{tool.id}-{task.id}-{uuid.uuid4().hex[:8]}"
        is_open_weight = model.startswith("meta-models/")

        if is_open_weight:
            base_url = (
                env.get("OPENAI_BASE_URL")
                or env.get("BASETEN_BASE_URL")
                or DEFAULT_OPEN_WEIGHT_BASE_URL
            ).rstrip("/")
            endpoint = f"{base_url}/chat/completions"
            chat_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t.get("description", ""),
                        "parameters": t["parameters"],
                    },
                }
                for t in router.tool_Specs
            ]
            chat_messages: list[dict[str, Any]] = [
                {"role": "system", "content": SYSTEM_INSTRUCTIONS},
                {"role": "user", "content": task.prompt},
            ]
        else:
            base_url = env.get("META_API_BASE_URL", DEFAULT_META_BASE_URL).rstrip("/")
            endpoint = f"{base_url}/responses"
            input_items: list[dict[str, Any]] = [
                {"role": "system", "content": SYSTEM_INSTRUCTIONS},
                {"role": "user", "content": task.prompt},
            ]

        with transcript.open("w", encoding="utf-8") as sink:
            for _turn in range(max_turns):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    timed_out = True
                    exit_code = -1
                    break

                if is_open_weight:
                    req_payload: dict[str, Any] = {
                        "model": model,
                        "messages": chat_messages,
                        "tools": chat_tools,
                        "temperature": 1.0,
                        "top_p": 0.95,
                    }
                    raw_resp = http_post(endpoint, api_key, req_payload, remaining)
                    resp = _chat_completion_to_responses_shape(raw_resp)
                else:
                    req_payload = {
                        "model": model,
                        "store": False,
                        "include": ["reasoning.encrypted_content"],
                        "reasoning": {"effort": "high"},
                        "prompt_cache_key": prompt_cache_key,
                        "tools": router.tool_Specs,
                        "input": input_items,
                    }
                    resp = http_post(endpoint, api_key, req_payload, remaining)

                output_items = resp.get("output") or []
                if not isinstance(output_items, list):
                    output_items = []

                turn_usage = normalize_usage(resp.get("usage"))
                for k in cumulative_usage:
                    cumulative_usage[k] += turn_usage.get(k, 0)
                num_turns += 1

                blocks, texts = extract_assistant_blocks(output_items)
                if texts:
                    final_text = "\n".join(texts)

                assistant_record = {
                    "type": "assistant",
                    "message": {
                        "model": model,
                        "role": "assistant",
                        "content": blocks,
                        "usage": turn_usage,
                    },
                }
                sink.write(json.dumps(assistant_record) + "\n")
                sink.flush()

                function_calls = [
                    item
                    for item in output_items
                    if isinstance(item, dict) and item.get("type") == "function_call"
                ]
                if not function_calls:
                    break

                if is_open_weight:
                    chat_messages.append(resp.get("_assistant_msg") or {"role": "assistant"})
                else:
                    input_items.extend(build_replay_items(output_items))

                pending_images: list[str] = []
                for fc in function_calls:
                    call_id = str(fc.get("call_id") or "")
                    fn_name = str(fc.get("name") or "")
                    fn_args = fc.get("arguments")
                    out_text, out_images = router.invoke(fn_name, fn_args, deadline=deadline)
                    pending_images.extend(out_images)
                    if is_open_weight:
                        chat_messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": call_id,
                                "content": out_text,
                            }
                        )
                    else:
                        input_items.append(
                            {
                                "type": "function_call_output",
                                "call_id": call_id,
                                "output": out_text,
                            }
                        )

                if pending_images:
                    if is_open_weight:
                        chat_messages.append(
                            {
                                "role": "user",
                                "content": [
                                    {"type": "image_url", "image_url": {"url": url}}
                                    for url in pending_images
                                ],
                            }
                        )
                    else:
                        input_items.append(
                            {
                                "role": "user",
                                "content": [
                                    {"type": "input_image", "image_url": url}
                                    for url in pending_images
                                ],
                            }
                        )
            else:
                # Loop ran out of turns while the model was still calling tools:
                # a cut-off run, not a finished answer.
                exit_code = 2
                stderr_notes.append(f"max turns ({max_turns}) reached before a final answer")

            if not timed_out and exit_code == 0:
                result_record = {
                    "type": "result",
                    "result": final_text,
                    "num_turns": num_turns,
                    "total_cost_usd": estimate_cost_usd(model, cumulative_usage),
                    "usage": cumulative_usage,
                }
                sink.write(json.dumps(result_record) + "\n")
                sink.flush()

    except TimeoutError as exc:
        timed_out = True
        exit_code = -1
        stderr_notes.append(f"TimeoutError: {exc}")
    except Exception as exc:
        exit_code = 1
        stderr_notes.append(f"Error: {exc}")
    finally:
        if router is not None:
            mcp_err = router.stderr_summary()
            if mcp_err:
                stderr_notes.append(mcp_err)
            router.close()

    wall = time.monotonic() - start
    if not transcript.exists():
        transcript.write_text("", encoding="utf-8")

    (out_dir / "stderr.txt").write_text("\n".join(stderr_notes)[-4000:], encoding="utf-8")
    sanitize_file(transcript)
    sanitize_file(out_dir / "stderr.txt")

    tokens = parse_transcript(transcript)
    return AgentRun(
        transcript_path=transcript,
        wall_time_s=wall,
        exit_code=exit_code,
        timed_out=timed_out,
        tokens=tokens,
    )
