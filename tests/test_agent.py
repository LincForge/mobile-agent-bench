import json
import subprocess
import sys
from pathlib import Path

from mobile_agent_bench.agent import (
    build_command,
    ensure_confinement,
    final_answer_text,
    verify_task,
)
from mobile_agent_bench.schema import Task, Tool, Verify


def _task(verify: Verify) -> Task:
    return Task(
        id="t", tier="A", name="t", prompt="do the thing",
        app_package="dev.lincforge.benchtarget",
        app_apk="target-app/app/build/outputs/apk/stock/debug/app-stock-debug.apk",
        reset=("force-stop",), verify=verify, timeout_s=60,
    )


def _transcript(tmp_path: Path, answer: str) -> Path:
    p = tmp_path / "transcript.jsonl"
    p.write_text(json.dumps({"type": "result", "result": answer}) + "\n")
    return p


def test_build_command_pins_model_and_strict_mcp(tmp_path):
    tool = Tool(id="x", name="x", mcp_config="tools/x.mcp.json")
    cmd = build_command(_task(Verify(type="manual")), tool, "claude-sonnet-5")
    assert cmd[:3] == ["claude", "-p", "do the thing"]
    assert "--strict-mcp-config" in cmd
    assert cmd[cmd.index("--model") + 1] == "claude-sonnet-5"
    # mcp-config is now absolute (agent runs from a neutral cwd) but still points
    # at the tool's config file.
    mcp = cmd[cmd.index("--mcp-config") + 1]
    assert mcp.endswith("tools/x.mcp.json")
    assert mcp.startswith("/")


def test_build_command_confines_agent_to_tool_under_test(tmp_path):
    """Fairness invariant: no built-in shell/fs/web/subagent tools reach the
    agent — only the tool-under-test's MCP surface (+ ToolSearch to load it)."""
    tool = Tool(id="x", name="x", mcp_config="tools/x.mcp.json")
    cmd = build_command(_task(Verify(type="manual")), tool, "claude-sonnet-5")
    assert "--disallowedTools" in cmd
    denied = cmd[cmd.index("--disallowedTools") + 1].split(",")
    # Shell / file-search / write / web / subagent are denied (adb-bypass +
    # ground-truth-discovery vectors).
    for banned in ("Bash", "Write", "Edit", "Grep", "Glob", "WebFetch", "WebSearch", "Task"):
        assert banned in denied, f"{banned} must be denied"
    # Erratum #3: the harness orchestration surface must be denied too — `Monitor`
    # runs arbitrary shell (`command` field) in a background loop, which confined
    # agents used to run raw adb/jdb and bypass the tool-under-test.
    for banned in ("Monitor", "ScheduleWakeup", "TaskCreate", "TaskStop",
                   "CronCreate", "Workflow", "Skill", "SendMessage"):
        assert banned in denied, f"{banned} (orchestration/exec) must be denied"
    # Read is ALLOWED (CEO 2026-07-09): tools that hand back screenshot file paths
    # need it; without Bash/Grep/Glob the agent can't discover ground-truth paths.
    assert "Read" not in denied
    # ToolSearch must NOT be denied — MCP tools are deferred and need it to load.
    assert "ToolSearch" not in denied


def test_read_guard_blocks_source_allows_screenshots(tmp_path):
    """Erratum #2: the PreToolUse Read-guard denies reads of app source / SPEC
    (ground truth reachable via a guessed absolute path) while leaving screenshot
    paths and the tools' own logs readable."""
    ensure_confinement(tmp_path)
    guard = tmp_path / ".mab_read_guard.py"
    settings = tmp_path / ".claude" / "settings.json"
    assert guard.exists() and settings.exists()
    cfg = json.loads(settings.read_text())
    assert cfg["hooks"]["PreToolUse"][0]["matcher"] == "Read"

    def rc(path: str) -> int:
        payload = json.dumps({"tool_name": "Read", "tool_input": {"file_path": path}})
        return subprocess.run(
            [sys.executable, str(guard)], input=payload, capture_output=True, text=True
        ).returncode

    # ground truth => denied (exit 2)
    assert rc("/Users/somebody/projects/mobile-agent-bench/target-app/app/src/main/java/CheckoutViewModel.kt") == 2
    assert rc("/Users/somebody/forge/BenchTarget/app/src/main/java/Foo.kt") == 2
    assert rc("/anywhere/SPEC.md") == 2
    # screenshots + tool-own logs => allowed (exit 0)
    assert rc("/var/folders/bz/T/nerve-output/abc/serial_0003_screenshot.png") == 0
    assert rc("/tmp/benchtarget_item013_crash.png") == 0
    assert rc("/Users/somebody/.maestro/maestro.log") == 0
    # a non-Read tool is never touched by the guard
    payload = json.dumps({"tool_name": "mcp__linc-nerve__nerve_tap", "tool_input": {}})
    assert subprocess.run([sys.executable, str(guard)], input=payload, capture_output=True, text=True).returncode == 0


def test_answer_verification_pass_and_fail(tmp_path):
    task = _task(Verify(
        type="answer", pattern="BENCH-STABLE",
        match_samples=("is BENCH-STABLE",), reject_samples=("is BENCH-DEV",),
    ))
    ok = _transcript(tmp_path, "The build channel is BENCH-STABLE.")
    verdict, _ = verify_task(task, {}, ok)
    assert verdict == "PASS"
    bad = _transcript(tmp_path, "The build channel is PROD.")
    verdict, _ = verify_task(task, {}, bad)
    assert verdict == "FAIL"


def test_answer_verification_lookaheads(tmp_path):
    task = _task(Verify(
        type="answer", pattern="(?=.*Catalog)(?=.*Form)(?=.*About)(?=.*Checkout)",
        match_samples=("Catalog, Form, About, Checkout",),
        reject_samples=("Catalog, Form, About",),
    ))
    partial = _transcript(tmp_path, "I can see Catalog, Form and About buttons.")
    assert verify_task(task, {}, partial)[0] == "FAIL"
    full = _transcript(tmp_path, "Buttons: Catalog, Form, About, Checkout.")
    assert verify_task(task, {}, full)[0] == "PASS"


def test_manual_verification_is_unverified(tmp_path):
    verdict, _ = verify_task(_task(Verify(type="manual")), {}, _transcript(tmp_path, "x"))
    assert verdict == "UNVERIFIED"


def test_final_answer_takes_last_result_record(tmp_path):
    p = tmp_path / "t.jsonl"
    p.write_text(
        json.dumps({"type": "result", "result": "first"}) + "\n"
        + json.dumps({"type": "result", "result": "second"}) + "\n"
    )
    assert final_answer_text(p) == "second"
