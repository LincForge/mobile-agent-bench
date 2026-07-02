"""Transcript sanitization — runs at capture time, before anything is written
to results/.

The published repo must contain zero internal topology: device serials,
hostnames, filesystem paths, usernames. Redaction patterns come from
bench.local.yaml (gitignored) plus the active device serial, so the harness a
third party clones has nothing to redact and behaves identically.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from .device import LOCAL_CONFIG

# Always-on patterns: home directories and macOS/Linux usernames leak via tool
# results (file paths in MCP tool output), regardless of local config.
_DEFAULT_PATTERNS = [
    (re.compile(r"/Users/[A-Za-z0-9_.-]+"), "/Users/<REDACTED>"),
    (re.compile(r"/home/[A-Za-z0-9_.-]+"), "/home/<REDACTED>"),
]


def _local_redactions() -> list[tuple[re.Pattern, str]]:
    pats: list[tuple[re.Pattern, str]] = []
    if LOCAL_CONFIG.exists():
        cfg = yaml.safe_load(LOCAL_CONFIG.read_text()) or {}
        for i, literal in enumerate(cfg.get("redact", []) or []):
            if literal:
                pats.append((re.compile(re.escape(str(literal))), f"<REDACTED-{i}>"))
        serial = cfg.get("device_serial")
        if serial:
            pats.append((re.compile(re.escape(str(serial))), "<DEVICE_SERIAL>"))
    return pats


def sanitize_text(text: str, extra_literals: list[str] | None = None) -> str:
    patterns = list(_DEFAULT_PATTERNS) + _local_redactions()
    for j, literal in enumerate(extra_literals or []):
        if literal:
            patterns.append((re.compile(re.escape(literal)), f"<REDACTED-X{j}>"))
    for pat, repl in patterns:
        text = pat.sub(repl, text)
    return text


def sanitize_file(path: Path, extra_literals: list[str] | None = None) -> None:
    path.write_text(sanitize_text(path.read_text(errors="replace"), extra_literals))
