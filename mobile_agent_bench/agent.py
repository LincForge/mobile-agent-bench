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
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from .sanitize import sanitize_file
from .schema import Task, Tool
from .tokens import TokenReport, parse_transcript

# Fairness confinement (pre-registration intent: "the MCP surface is the only
# capability"). --strict-mcp-config restricts only MCP *servers*, NOT Claude
# Code's built-in tools — so without this the agent has a full shell + repo
# access and can run adb directly (bypassing the tool-under-test) or discover &
# read SPEC.md / source for the frozen ground-truth answers.
#
# Isolation standard (CEO decision 2026-07-09): deny every built-in that runs a
# shell, searches/enumerates the filesystem, writes, or reaches the web/subagents
# — but ALLOW `Read`. Rationale: some tools (agent-device, and nerve) hand the
# agent a screenshot *file path* and expect it to open the image; blocking Read
# blinds them below their real-world capability (a strawman), whereas Bash/Grep/
# Glob are what let the agent *discover* the repo path in the first place. With
# no shell and no file search, the agent has no way to find SPEC.md/source (the
# process runs from AGENT_CWD, outside the repo), so ground-truth stays
# unreachable while file-based screenshots still work. ToolSearch is allowed
# (MCP tools are deferred; it loads their schemas, never touches the filesystem).
# ERRATUM #3 (2026-07-10): the deny list covered shell/fs/web/subagent built-ins
# but NOT the harness *orchestration* surface — and `Monitor` takes a `command`
# field and runs arbitrary shell in a background loop. Confined agents used it to
# run raw `adb logcat` / `adb shell pidof` / `adb forward`+`jdb` (a debugger),
# reading `discountFactor` straight from the running process — bypassing the
# tool-under-test entirely (and, since Monitor can `cat`, defeating the erratum-#2
# Read-guard). All three columns' agents had it. Every non-device built-in
# (orchestration, cron, worktree, resource, plan, notify) is now denied — only
# Read (path-guarded), ToolSearch (loads deferred MCP schemas), and the
# tool-under-test's MCP surface remain. See AMENDMENTS.md.
CONFINE_DISALLOWED_TOOLS = (
    "Bash,BashOutput,KillShell,KillBash,Edit,MultiEdit,Write,NotebookEdit,"
    "Glob,Grep,WebFetch,WebSearch,Task,Agent,TodoWrite,ExitPlanMode,"
    # erratum #3 — harness orchestration surface (Monitor = the shell-exec hole):
    "Monitor,ScheduleWakeup,TaskCreate,TaskUpdate,TaskList,TaskGet,TaskOutput,"
    "TaskStop,CronCreate,CronDelete,CronList,ListMcpResourcesTool,"
    "ReadMcpResourceTool,ReadMcpResourceDirTool,EnterPlanMode,EnterWorktree,"
    "ExitWorktree,PushNotification,RemoteTrigger,SendMessage,DesignSync,"
    "Artifact,AskUserQuestion,Skill,Workflow"
)

# Neutral working directory for the agent process — outside the benchmark repo,
# so even a missed tool finds no source / ground-truth / results to read.
AGENT_CWD = Path(tempfile.gettempdir()) / "mab-agent-cwd"

# ERRATUM #2 (2026-07-10): `Read` is allowed (tools hand the agent screenshot
# *paths* in /tmp), but nothing restricted WHERE it read. No-search blocks repo
# *discovery*, but a lucky absolute-path guess defeated it — one c10 run read
# `.../mobile-agent-bench/target-app/.../CheckoutViewModel.kt` and computed the
# frozen answer from source. This PreToolUse hook (a separate process the agent
# cannot disable) denies Read of the app source / SPEC while leaving screenshots
# (.png in /tmp) and the tools' own logs readable — fair to every tool.
READ_GUARD = r'''import json, re, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)  # fail-open on parse error — never wedge the agent
if d.get("tool_name") != "Read":
    sys.exit(0)
p = (d.get("tool_input") or {}).get("file_path", "") or ""
if re.search(r"(mobile-agent-bench|target-app|/src/(main|test)/|\.kt$|\.java$|SPEC\.md$)", p, re.I):
    sys.stderr.write("Read blocked: benchmark ground-truth (app source/SPEC) is "
                     "off-limits. Use the device tools to obtain information, not the source.")
    sys.exit(2)  # PreToolUse exit-2 => deny the tool call
sys.exit(0)
'''


def ensure_confinement(cwd: Path) -> None:
    """Write the Read-guard + a settings.json registering it as a PreToolUse hook.
    The agent runs with cwd=AGENT_CWD, so Claude Code auto-loads this project
    settings file. The guard lives in the /tmp cwd (no repo path is referenced),
    and it blocks reads of itself and the whole repo, so it cannot be bypassed."""
    guard = cwd / ".mab_read_guard.py"
    guard.write_text(READ_GUARD)
    claude_dir = cwd / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    (claude_dir / "settings.json").write_text(
        json.dumps(
            {"hooks": {"PreToolUse": [
                {"matcher": "Read", "hooks": [
                    {"type": "command", "command": f"python3 {guard}"}
                ]}
            ]}},
            indent=2,
        )
    )


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
    # Absolute — the agent runs from AGENT_CWD (outside the repo), so a relative
    # config path would not resolve.
    return str((local if local.exists() else committed).resolve())


def build_command(task: Task, tool: Tool, model: str) -> list[str]:
    return [
        "claude",
        "-p", task.prompt,
        "--model", model,
        "--mcp-config", resolve_mcp_config(tool),
        "--strict-mcp-config",           # only the tool-under-test's MCP servers
        "--disallowedTools", CONFINE_DISALLOWED_TOOLS,  # + no built-in shell/fs/web tools
        "--output-format", "stream-json",
        "--verbose",
        "--dangerously-skip-permissions",  # headless; confined MCP surface is the only capability
    ]


def run_agent(task: Task, tool: Tool, model: str, out_dir: Path) -> AgentRun:
    out_dir.mkdir(parents=True, exist_ok=True)
    transcript = out_dir.resolve() / "transcript.jsonl"  # absolute: subprocess cwd differs
    env = {**os.environ, **tool.env}
    AGENT_CWD.mkdir(parents=True, exist_ok=True)
    ensure_confinement(AGENT_CWD)  # PreToolUse Read-guard (erratum #2)

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
                cwd=str(AGENT_CWD),  # neutral dir outside the repo — no ground-truth reachable
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
        matched = task.verify.matches(answer)
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
