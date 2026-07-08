from pathlib import Path

from mobile_agent_bench.runner import results_root


def test_results_root_defaults_to_results(monkeypatch):
    monkeypatch.delenv("BENCH_RESULTS_DIR", raising=False)
    assert results_root() == Path("results")


def test_results_root_honors_env_override(monkeypatch):
    monkeypatch.setenv("BENCH_RESULTS_DIR", "results_s10")
    assert results_root() == Path("results_s10")
