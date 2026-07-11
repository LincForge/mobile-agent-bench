"""Solved-but-unfinalized diagnostic outcome (v2 pre-registration decision).

v1 deep-dive: 5 of linc's 7 timeouts already contained the full ground-truth
answer in-transcript — the agent solved the task but exhausted the 900 s budget
before finalizing. The budget stays 900 s (pre-registered, competitors finish
inside it) and a timed-out run stays FAIL for every scored metric; v2
additionally reports "solved-but-unfinalized" as a distinct DIAGNOSTIC outcome,
detected mechanically (no eyeball adjudication):

- answer-type task: the frozen verify pattern matches the transcript's
  concatenated assistant text (not just the missing final answer), OR
- any task: harness verification itself passed before the timeout override.
"""

import json
from pathlib import Path

from mobile_agent_bench import agent as agent_mod
from mobile_agent_bench.schema import Task, Tool, Verify

STOCK_APK = "target-app/app/build/outputs/apk/stock/debug/app-stock-debug.apk"


def _task(verify: Verify) -> Task:
    return Task(
        id="t", tier="A", name="t", prompt="p",
        app_package="dev.lincforge.benchtarget",
        app_apk=STOCK_APK,
        reset=("force-stop",),
        verify=verify, timeout_s=60,
    )


def _answer_verify() -> Verify:
    return Verify(
        type="answer", pattern="BENCH-STABLE",
        match_samples=("is BENCH-STABLE",), reject_samples=("is BENCH-DEV",),
    )


def _write_transcript(tmp_path: Path, assistant_texts: list[str]) -> Path:
    p = tmp_path / "transcript.jsonl"
    recs = [
        {"type": "assistant", "message": {"content": [
            {"type": "text", "text": t},
            {"type": "tool_use", "name": "x", "input": {}},
        ]}}
        for t in assistant_texts
    ]
    p.write_text("\n".join(json.dumps(r) for r in recs) + "\n")
    return p


def test_transcript_assistant_text_concatenates_text_blocks(tmp_path):
    p = _write_transcript(tmp_path, ["first look", "channel reads BENCH-STABLE"])
    text = agent_mod.transcript_assistant_text(p)
    assert "first look" in text and "BENCH-STABLE" in text


def _run_one(monkeypatch, tmp_path, task, timed_out, transcript, verify_result=("FAIL", "no final answer")):
    from mobile_agent_bench import runner

    monkeypatch.setattr(runner, "device_serial", lambda: "S")
    monkeypatch.setattr(runner, "clear_uiautomation_holders", lambda serial=None: [])
    monkeypatch.setattr(
        runner, "ensure_pinned_app",
        lambda pkg, apk, serial=None: {"package": pkg, "apk_md5": "d" * 32, "action": "verified"},
    )
    monkeypatch.setattr(runner, "reset_app_state", lambda pkg, steps, serial=None: list(steps))
    monkeypatch.setattr(runner, "device_fingerprint", lambda serial=None: {"model": "x"})

    class _Tokens:
        def as_dict(self):
            return {"total_billed": 0}

    class _Result:
        wall_time_s = 1.0
        exit_code = -1 if timed_out else 0
        tokens = _Tokens()

    _Result.timed_out = timed_out
    _Result.transcript_path = transcript
    monkeypatch.setattr(agent_mod, "run_agent", lambda task, tool, model, out: _Result())
    monkeypatch.setattr(agent_mod, "verify_task", lambda task, env, tp: verify_result)
    monkeypatch.setattr(agent_mod, "write_meta", lambda out, rec: None)
    tool = Tool(id="x", name="x", mcp_config="tools/x.mcp.json")
    return runner.run_one(task, tool, "m", tmp_path)


def test_timed_out_run_with_answer_in_transcript_is_flagged_not_passed(monkeypatch, tmp_path):
    transcript = _write_transcript(tmp_path, ["the Build channel reads BENCH-STABLE, finalizing now"])
    record = _run_one(monkeypatch, tmp_path, _task(_answer_verify()), True, transcript)
    assert record["verdict"] == "FAIL", "a timed-out run can never count as complete"
    assert record["solved_unfinalized"] is True


def test_timed_out_run_without_answer_is_not_flagged(monkeypatch, tmp_path):
    transcript = _write_transcript(tmp_path, ["still scrolling the list"])
    record = _run_one(monkeypatch, tmp_path, _task(_answer_verify()), True, transcript)
    assert record["verdict"] == "FAIL"
    assert record["solved_unfinalized"] is False


def test_timed_out_shell_task_that_verifies_is_flagged(monkeypatch, tmp_path):
    """Shell verification runs against live device end-state — if it PASSes on
    a timed-out run, the task was materially done when the budget expired."""
    transcript = _write_transcript(tmp_path, ["submitting the form"])
    task = _task(Verify(type="shell", cmd="true"))
    record = _run_one(monkeypatch, tmp_path, task, True, transcript, verify_result=("PASS", "state ok"))
    assert record["verdict"] == "FAIL"
    assert record["solved_unfinalized"] is True


def test_completed_run_is_never_flagged(monkeypatch, tmp_path):
    transcript = _write_transcript(tmp_path, ["the Build channel reads BENCH-STABLE"])
    record = _run_one(
        monkeypatch, tmp_path, _task(_answer_verify()), False, transcript, verify_result=("PASS", "ok")
    )
    assert record["verdict"] == "PASS"
    assert record["solved_unfinalized"] is False


def test_report_shows_solved_unfinalized_count(tmp_path, monkeypatch, capsys):
    from mobile_agent_bench.runner import cmd_report

    monkeypatch.setenv("BENCH_RESULTS_DIR", str(tmp_path))
    for n, (verdict, sbu) in enumerate([("PASS", False), ("FAIL", True), ("FAIL", False)], start=1):
        d = tmp_path / "linc" / "a1" / f"run-{n}"
        d.mkdir(parents=True)
        (d / "meta.json").write_text(json.dumps({
            "tool": "linc", "task": "a1", "tier": "A", "verdict": verdict,
            "solved_unfinalized": sbu,
            "wall_time_s": 10.0, "capability_row": False,
            "tokens": {"total_billed": 1, "total_uncached": 1, "output_tokens": 1},
        }))
    assert cmd_report(None) == 0
    out = capsys.readouterr().out
    header = next(line for line in out.splitlines() if line.startswith("| tool"))
    assert "solved-unfin" in header
    row = next(line for line in out.splitlines() if line.startswith("| linc"))
    assert "| 1/3 " in row and "| 1 |" in row
