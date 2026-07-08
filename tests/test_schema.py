"""Frozen-schema validation: every committed task/tool file must load, and the
schema must reject the failure shapes that would silently corrupt rows."""

from pathlib import Path

import pytest

from mobile_agent_bench.schema import (
    ConfigError,
    Verify,
    load_all_tasks,
    load_all_tools,
)

ROOT = Path(__file__).resolve().parent.parent


def test_all_committed_tasks_load_and_are_the_frozen_ten():
    tasks = load_all_tasks(ROOT / "tasks")
    assert sorted(t.id for t in tasks) == [
        "a1", "a2", "a3", "a4", "b5", "b6", "b7", "b8", "c10", "c9",
    ]
    assert len(tasks) == 10
    tiers = {t.id: t.tier for t in tasks}
    assert tiers["a1"] == "A" and tiers["b8"] == "B" and tiers["c10"] == "C"


def test_only_the_watch_task_is_a_capability_row():
    tasks = load_all_tasks(ROOT / "tasks")
    assert [t.id for t in tasks if t.capability_row] == ["b8"]


def test_all_committed_tools_load_and_configs_exist():
    tools = load_all_tools(ROOT / "tools")
    assert sorted(t.id for t in tools) == ["agent-device", "linc", "maestro", "mobile-mcp"]
    for tool in tools:
        assert (ROOT / tool.mcp_config).exists(), tool.mcp_config


def test_committed_files_contain_no_internal_topology():
    """Sanitization rule: no device serials, private hostnames, or home dirs in
    the repo. Generic patterns are checked here; environment-specific literals
    come from bench.local.yaml's `redact` list (gitignored), so the check is
    strongest on a maintainer machine while the public test stays secret-free.
    """
    import re

    import yaml

    # "somebody" is the documented fixture username in tests/test_sanitize.py
    banned_res = [
        re.compile(r"\bts\.net\b"),
        re.compile(r"/Users/(?!<REDACTED>|somebody\b)[A-Za-z0-9_.-]+"),
    ]
    local = ROOT / "bench.local.yaml"
    if local.exists():
        cfg = yaml.safe_load(local.read_text()) or {}
        extras = list(cfg.get("redact", []) or [])
        if cfg.get("device_serial"):
            extras.append(cfg["device_serial"])
        banned_res += [re.compile(re.escape(str(t))) for t in extras if t]

    this_file = Path(__file__).resolve()
    for path in ROOT.rglob("*"):
        if path.is_dir() or path.resolve() == this_file:
            continue
        # build/.gradle are gitignored Gradle outputs (target-app/**/build/) —
        # they embed absolute host paths by design and are never committed.
        if {".git", ".venv", "__pycache__", ".pytest_cache", "build", ".gradle"} & set(path.parts):
            continue
        if path.name in {"bench.local.yaml"} or path.name.endswith(".local.mcp.json"):
            continue  # gitignored by design
        if path.suffix in {".pyc", ".apk"}:
            continue
        text = path.read_text(errors="ignore")
        for pat in banned_res:
            assert not pat.search(text), f"{path} leaks pattern {pat.pattern!r}"


def test_verify_shell_requires_cmd():
    with pytest.raises(ConfigError):
        Verify(type="shell", cmd=None)


def test_verify_answer_requires_pattern():
    with pytest.raises(ConfigError):
        Verify(type="answer", pattern=None)


def test_verify_rejects_unknown_type():
    with pytest.raises(ConfigError):
        Verify(type="vibes")
