"""Task and tool config loading + validation.

Tasks live in tasks/*.yaml, tool adapters in tools/*.yaml. Both are frozen at
the pre-registration tag; the harness refuses to run a task file that is
missing any locked field so a half-written task can't silently produce rows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

VALID_TIERS = {"A", "B", "C"}
VALID_RESET_STEPS = {"force-stop", "clear-data", "home", "wake"}
VALID_VERIFY_TYPES = {"shell", "answer", "manual"}

REQUIRED_TASK_FIELDS = {"id", "tier", "name", "prompt", "app", "reset", "verify", "timeout_s"}
REQUIRED_TOOL_FIELDS = {"id", "name", "mcp_config"}


class ConfigError(ValueError):
    """A task/tool file violates the frozen schema."""


@dataclass(frozen=True)
class Verify:
    type: str  # "shell": cmd exits 0 on pass; "answer": regex over the agent's
    #            final answer text (frozen ground truth); "manual": UNVERIFIED
    cmd: str | None = None
    pattern: str | None = None

    def __post_init__(self) -> None:
        if self.type not in VALID_VERIFY_TYPES:
            raise ConfigError(f"verify.type must be one of {sorted(VALID_VERIFY_TYPES)}, got {self.type!r}")
        if self.type == "shell" and not self.cmd:
            raise ConfigError("verify.type=shell requires verify.cmd")
        if self.type == "answer" and not self.pattern:
            raise ConfigError("verify.type=answer requires verify.pattern")


@dataclass(frozen=True)
class Task:
    id: str
    tier: str
    name: str
    prompt: str
    app_package: str
    reset: tuple[str, ...]
    verify: Verify
    timeout_s: int
    notes: str = ""
    capability_row: bool = False  # tier-B watch task: reported separately, never averaged

    def __post_init__(self) -> None:
        if self.tier not in VALID_TIERS:
            raise ConfigError(f"task {self.id}: tier must be one of {sorted(VALID_TIERS)}")
        bad = set(self.reset) - VALID_RESET_STEPS
        if bad:
            raise ConfigError(f"task {self.id}: unknown reset steps {sorted(bad)}")
        if self.timeout_s <= 0:
            raise ConfigError(f"task {self.id}: timeout_s must be positive")


@dataclass(frozen=True)
class Tool:
    id: str
    name: str
    mcp_config: str  # path (repo-relative) to the claude --mcp-config JSON
    notes: str = ""
    env: dict[str, str] = field(default_factory=dict)  # extra env for the agent process


def load_task(path: Path) -> Task:
    raw = yaml.safe_load(path.read_text())
    if not isinstance(raw, dict):
        raise ConfigError(f"{path}: not a mapping")
    missing = REQUIRED_TASK_FIELDS - raw.keys()
    if missing:
        raise ConfigError(f"{path}: missing required fields {sorted(missing)}")
    return Task(
        id=raw["id"],
        tier=raw["tier"],
        name=raw["name"],
        prompt=raw["prompt"].strip(),
        app_package=raw["app"]["package"],
        reset=tuple(raw["reset"]),
        verify=Verify(
            type=raw["verify"]["type"],
            cmd=raw["verify"].get("cmd"),
            pattern=raw["verify"].get("pattern"),
        ),
        timeout_s=int(raw["timeout_s"]),
        notes=raw.get("notes", ""),
        capability_row=bool(raw.get("capability_row", False)),
    )


def load_tool(path: Path) -> Tool:
    raw = yaml.safe_load(path.read_text())
    if not isinstance(raw, dict):
        raise ConfigError(f"{path}: not a mapping")
    missing = REQUIRED_TOOL_FIELDS - raw.keys()
    if missing:
        raise ConfigError(f"{path}: missing required fields {sorted(missing)}")
    return Tool(
        id=raw["id"],
        name=raw["name"],
        mcp_config=raw["mcp_config"],
        notes=raw.get("notes", ""),
        env=dict(raw.get("env", {})),
    )


def load_all_tasks(tasks_dir: Path) -> list[Task]:
    tasks = [load_task(p) for p in sorted(tasks_dir.glob("*.yaml"))]
    ids = [t.id for t in tasks]
    if len(ids) != len(set(ids)):
        raise ConfigError(f"duplicate task ids in {tasks_dir}")
    return tasks


def load_all_tools(tools_dir: Path) -> list[Tool]:
    tools = [load_tool(p) for p in sorted(tools_dir.glob("*.yaml"))]
    ids = [t.id for t in tools]
    if len(ids) != len(set(ids)):
        raise ConfigError(f"duplicate tool ids in {tools_dir}")
    return tools
