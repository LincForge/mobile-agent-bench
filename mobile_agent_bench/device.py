"""Scripted device/app state reset between runs (fairness: identical app state).

All adb access goes through BENCH_DEVICE_SERIAL from the environment (or
bench.local.yaml, which is gitignored) — the published repo never contains a
device serial. Reset steps are declared per-task and executed in order before
EVERY run, for every tool identically.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import yaml

LOCAL_CONFIG = Path("bench.local.yaml")


class DeviceError(RuntimeError):
    pass


def device_serial() -> str:
    serial = os.environ.get("BENCH_DEVICE_SERIAL", "")
    if not serial and LOCAL_CONFIG.exists():
        serial = (yaml.safe_load(LOCAL_CONFIG.read_text()) or {}).get("device_serial", "")
    if not serial:
        raise DeviceError(
            "no device configured: set BENCH_DEVICE_SERIAL or device_serial in bench.local.yaml"
        )
    return serial


def adb(*args: str, serial: str | None = None, timeout: int = 60) -> subprocess.CompletedProcess:
    serial = serial or device_serial()
    cmd = ["adb", "-s", serial, *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        raise DeviceError(f"adb {' '.join(args)} failed rc={proc.returncode}: {proc.stderr.strip()}")
    return proc


def reset_app_state(package: str, steps: tuple[str, ...], serial: str | None = None) -> list[str]:
    """Execute the task's declared reset steps; returns the log of what ran."""
    serial = serial or device_serial()
    log: list[str] = []
    for step in steps:
        if step == "force-stop":
            adb("shell", "am", "force-stop", package, serial=serial)
        elif step == "clear-data":
            adb("shell", "pm", "clear", package, serial=serial)
        elif step == "home":
            adb("shell", "input", "keyevent", "KEYCODE_HOME", serial=serial)
        elif step == "wake":
            adb("shell", "input", "keyevent", "KEYCODE_WAKEUP", serial=serial)
        else:  # schema validation makes this unreachable; belt-and-braces
            raise DeviceError(f"unknown reset step {step!r}")
        log.append(step)
    return log


def device_fingerprint(serial: str | None = None) -> dict:
    """Model + OS for the run record (never the serial — publishable as-is)."""
    serial = serial or device_serial()
    def prop(name: str) -> str:
        return adb("shell", "getprop", name, serial=serial).stdout.strip()
    return {
        "model": prop("ro.product.model"),
        "android_version": prop("ro.build.version.release"),
        "sdk": prop("ro.build.version.sdk"),
        "build": prop("ro.build.id"),
    }
