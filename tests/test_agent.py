import json
from pathlib import Path

from mobile_agent_bench.agent import build_command, final_answer_text, verify_task
from mobile_agent_bench.schema import Task, Tool, Verify


def _task(verify: Verify) -> Task:
    return Task(
        id="t", tier="A", name="t", prompt="do the thing",
        app_package="dev.lincforge.benchtarget", reset=("force-stop",),
        verify=verify, timeout_s=60,
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
    assert cmd[cmd.index("--mcp-config") + 1] == "tools/x.mcp.json"


def test_answer_verification_pass_and_fail(tmp_path):
    task = _task(Verify(type="answer", pattern="BENCH-STABLE"))
    ok = _transcript(tmp_path, "The build channel is BENCH-STABLE.")
    verdict, _ = verify_task(task, {}, ok)
    assert verdict == "PASS"
    bad = _transcript(tmp_path, "The build channel is PROD.")
    verdict, _ = verify_task(task, {}, bad)
    assert verdict == "FAIL"


def test_answer_verification_lookaheads(tmp_path):
    task = _task(Verify(type="answer", pattern="(?=.*Catalog)(?=.*Form)(?=.*About)(?=.*Checkout)"))
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
