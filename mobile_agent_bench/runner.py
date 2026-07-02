"""Bench CLI — orchestrates N runs per task per tool.

    bench run --tool linc --task a1 --runs 5
    bench run --tool all --task all            # full grid (week-2 mode)
    bench report                                # aggregate results/ -> markdown

Every run: reset device state -> spawn agent -> harness-side verification ->
sanitized transcript + meta.json under results/<tool>/<task>/run-<n>/.
"""

from __future__ import annotations

import argparse
import datetime
import statistics
import sys
from pathlib import Path

import yaml

from . import agent as agent_mod
from .device import device_fingerprint, device_serial, reset_app_state
from .schema import Task, Tool, load_all_tasks, load_all_tools

ROOT = Path(".")
BENCH_CONFIG = ROOT / "bench.yaml"


def load_bench_config() -> dict:
    return yaml.safe_load(BENCH_CONFIG.read_text())


def run_one(task: Task, tool: Tool, model: str, out_dir: Path) -> dict:
    serial = device_serial()
    reset_log = reset_app_state(task.app_package, task.reset, serial=serial)
    result = agent_mod.run_agent(task, tool, model, out_dir)
    verdict, verify_detail = agent_mod.verify_task(
        task, {"BENCH_DEVICE_SERIAL": serial}, result.transcript_path
    )
    if result.timed_out:
        verdict = "FAIL"  # a timed-out run can never count as complete
    record = {
        "task": task.id,
        "tier": task.tier,
        "tool": tool.id,
        "model": model,
        "started_utc": datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds"),
        "wall_time_s": round(result.wall_time_s, 2),
        "timed_out": result.timed_out,
        "agent_exit_code": result.exit_code,
        "verdict": verdict,
        "verify_detail": verify_detail[-500:],
        "reset_steps": reset_log,
        "tokens": result.tokens.as_dict(),
        "device": device_fingerprint(serial),
        "capability_row": task.capability_row,
    }
    agent_mod.write_meta(out_dir, record)
    return record


def cmd_run(args: argparse.Namespace) -> int:
    cfg = load_bench_config()
    model = args.model or cfg["model"]
    runs = args.runs or int(cfg.get("runs_per_task", 5))
    tasks = {t.id: t for t in load_all_tasks(ROOT / "tasks")}
    tools = {t.id: t for t in load_all_tools(ROOT / "tools")}

    sel_tasks = list(tasks.values()) if args.task == "all" else [tasks[args.task]]
    sel_tools = list(tools.values()) if args.tool == "all" else [tools[args.tool]]

    failures = 0
    for tool in sel_tools:
        for task in sel_tasks:
            for n in range(1, runs + 1):
                out_dir = ROOT / "results" / tool.id / task.id / f"run-{n}"
                if (out_dir / "meta.json").exists() and not args.force:
                    print(f"skip {tool.id}/{task.id}/run-{n} (exists; --force to redo)")
                    continue
                print(f"run  {tool.id}/{task.id}/run-{n} model={model}", flush=True)
                record = run_one(task, tool, model, out_dir)
                print(
                    f"  -> {record['verdict']}  {record['wall_time_s']}s  "
                    f"{record['tokens']['total_billed']} tokens",
                    flush=True,
                )
                failures += record["verdict"] != "PASS"
    return 1 if failures and args.strict else 0


def cmd_report(_args: argparse.Namespace) -> int:
    import json

    rows = []
    for meta in sorted((ROOT / "results").glob("*/*/run-*/meta.json")):
        rows.append(json.loads(meta.read_text()))
    if not rows:
        print("no results yet")
        return 0

    by_cell: dict[tuple[str, str], list[dict]] = {}
    for r in rows:
        by_cell.setdefault((r["tool"], r["task"]), []).append(r)

    print("| tool | task | tier | runs | pass | median wall s | median tokens | wall stdev |")
    print("|---|---|---|---|---|---|---|---|")
    for (tool, task), cell in sorted(by_cell.items()):
        walls = [r["wall_time_s"] for r in cell]
        toks = [r["tokens"]["total_billed"] for r in cell]
        passes = sum(r["verdict"] == "PASS" for r in cell)
        cap = " (capability row)" if cell[0].get("capability_row") else ""
        stdev = f"{statistics.stdev(walls):.1f}" if len(walls) > 1 else "n/a"
        print(
            f"| {tool} | {task}{cap} | {cell[0]['tier']} | {len(cell)} | {passes}/{len(cell)} "
            f"| {statistics.median(walls):.1f} | {statistics.median(toks):,} | {stdev} |"
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="bench")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="execute runs")
    p_run.add_argument("--tool", required=True, help="tool id or 'all'")
    p_run.add_argument("--task", required=True, help="task id or 'all'")
    p_run.add_argument("--runs", type=int, default=None)
    p_run.add_argument("--model", default=None, help="override pinned model (dev only)")
    p_run.add_argument("--force", action="store_true", help="redo existing runs")
    p_run.add_argument("--strict", action="store_true", help="nonzero exit on any FAIL")
    p_run.set_defaults(func=cmd_run)

    p_rep = sub.add_parser("report", help="aggregate results to a markdown table")
    p_rep.set_defaults(func=cmd_report)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
