import json
from pathlib import Path

from mobile_agent_bench.runner import cmd_report, results_root


def test_results_root_defaults_to_results(monkeypatch):
    monkeypatch.delenv("BENCH_RESULTS_DIR", raising=False)
    assert results_root() == Path("results")


def test_results_root_honors_env_override(monkeypatch):
    monkeypatch.setenv("BENCH_RESULTS_DIR", "results_s10")
    assert results_root() == Path("results_s10")


def _write_meta(root: Path, tool: str, task: str, n: int, billed: int, uncached: int, output: int):
    d = root / tool / task / f"run-{n}"
    d.mkdir(parents=True)
    (d / "meta.json").write_text(json.dumps({
        "tool": tool, "task": task, "tier": "A", "verdict": "PASS",
        "wall_time_s": 10.0, "capability_row": False,
        "tokens": {"total_billed": billed, "total_uncached": uncached, "output_tokens": output},
    }))


def test_report_breaks_out_uncached_and_output_tokens(tmp_path, monkeypatch, capsys):
    """The v1 headline (LINC token efficiency) was invisible in the report:
    total_billed folds cache reads in, so a cache-heavy tool and a lean tool
    can show the same 'median tokens'. The report must break out the uncached
    and output medians per cell (improvement 5e37e19d) — the granularity is
    already in every meta.json, only the table dropped it."""
    monkeypatch.setenv("BENCH_RESULTS_DIR", str(tmp_path))
    _write_meta(tmp_path, "linc", "a1", 1, 1000, 300, 100)
    _write_meta(tmp_path, "linc", "a1", 2, 2000, 400, 150)
    _write_meta(tmp_path, "linc", "a1", 3, 3000, 500, 200)

    assert cmd_report(None) == 0
    out = capsys.readouterr().out
    header = next(line for line in out.splitlines() if line.startswith("| tool"))
    assert "median billed" in header
    assert "median uncached" in header
    assert "median output" in header
    row = next(line for line in out.splitlines() if line.startswith("| linc"))
    assert "2,000" in row
    assert "400" in row
    assert "150" in row
