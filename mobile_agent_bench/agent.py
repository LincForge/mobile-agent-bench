"""Headless agent invocation — one `claude -p` session per run.

Fairness invariants (pre-registered):
- Same agent binary, same pinned model, same system context for every tool.
- `--strict-mcp-config` so ONLY the tool-under-test's MCP server is loaded —
  no ambient servers from the host machine can leak capability into a run.
- The task prompt is passed verbatim from the frozen task file.
- The raw stream-json transcript is stored (sanitized) for every run, pass or
  fail — published numbers must trace to these files.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from .sanitize import sanitize_file
from .schema import Task, Tool
from .tokens import TokenReport, parse_transcript


@dataclass(frozen=True)
class AgentRun:
    transcript_path: Path
    wall_time_s: float
    exit_code: int
    timed_out: bool
    tokens: TokenReport


def resolve_mcp_config(tool: Tool) -> str:
    """Prefer a machine-local override (tools/<id>.local.mcp.json, gitignored)
    so committed configs stay free of local paths while runs still work."""
    committed = Path(tool.mcp_config)
    local = committed.with_name(committed.name.replace(".mcp.json", ".local.mcp.json"))
    return str(local if local.exists() else committed)


def build_command(task: Task, tool: Tool, model: str) -> list[str]:
    return [
        "claude",
        "-p", task.prompt,
        "--model", model,
        "--mcp-config", resolve_mcp_config(tool),
        "--strict-mcp-config",
        "--output-format", "stream-json",
        "--verbose",
        "--dangerously-skip-permissions",  # headless; MCP surface is the only capability
    ]


def run_agent(task: Task, tool: Tool, model: str, out_dir: Path) -> AgentRun:
    out_dir.mkdir(parents=True, exist_ok=True)
    transcript = out_dir / "transcript.jsonl"
    env = {**os.environ, **tool.env}

    start = time.monotonic()
    timed_out = False
    with transcript.open("w") as sink:
        try:
            proc = subprocess.run(
                build_command(task, tool, model),
                stdout=sink,
                stderr=subprocess.PIPE,
                text=True,
                timeout=task.timeout_s,
                env=env,
            )
            exit_code = proc.returncode
            stderr_tail = (proc.stderr or "")[-4000:]
        except subprocess.TimeoutExpired as e:
            timed_out = True
            exit_code = -1
            stderr_tail = ((e.stderr or "") if isinstance(e.stderr, str) else "")[-4000:]
    wall = time.monotonic() - start

    (out_dir / "stderr.txt").write_text(stderr_tail)
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


def final_answer_text(transcript: Path) -> str:
    """The agent's final answer — the `result` field of the terminal result record."""
    answer = ""
    with transcript.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("type") == "result":
                answer = rec.get("result") or ""
    return answer


def verify_task(task: Task, serial_env: dict[str, str], transcript: Path) -> tuple[str, str]:
    """Run the task's frozen end-state assertion.

    Returns (verdict, detail): verdict is PASS / FAIL / UNVERIFIED.
    Verification runs AFTER the agent session ends, by the harness, the same
    way for every tool — the agent's own claim of success is never trusted.
    - shell: frozen command exits 0 against live device state
    - answer: frozen regex over the agent's final answer text (ground truth
      defined at pre-registration; case-insensitive, DOTALL)
    - manual: recorded UNVERIFIED (never counts toward completion rate)
    """
    if task.verify.type == "manual":
        return "UNVERIFIED", "task declares manual verification"
    if task.verify.type == "answer":
        answer = final_answer_text(transcript)
        matched = re.search(task.verify.pattern, answer, re.IGNORECASE | re.DOTALL)
        return ("PASS" if matched else "FAIL"), f"pattern={task.verify.pattern!r} answer[-500:]={answer[-500:]!r}"
    proc = subprocess.run(
        task.verify.cmd,
        shell=True,
        capture_output=True,
        text=True,
        timeout=120,
        env={**os.environ, **serial_env},
    )
    detail = (proc.stdout + proc.stderr)[-2000:]
    return ("PASS" if proc.returncode == 0 else "FAIL"), detail


def write_meta(out_dir: Path, record: dict) -> None:
    (out_dir / "meta.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
