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

# Known automation drivers that hold the device's single UiAutomation
# connection. A driver left alive by one cell SIGKILLs every later
# `uiautomator dump` ("Killed", rc 137), blinding whichever tool runs next —
# v1's maestro cells did exactly this to nerve (bench P0-A / improvement
# 9c816108). Exact process names only: these are test drivers, never user
# apps. com.google.android.apps.wearables.maestro.companion (Pixel Watch
# companion) contains "maestro" as a substring and must never match.
UIAUTOMATION_HOLDER_PKGS = (
    "dev.mobile.maestro",  # mobile.dev maestro driver
    "com.github.uiautomator",  # uiautomator2 server
    "com.github.uiautomator.test",
    "io.appium.uiautomator2.server",
    "io.appium.uiautomator2.server.test",
)


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


def clear_uiautomation_holders(serial: str | None = None) -> list[str]:
    """Force-stop leaked UiAutomation-holder drivers; return what was stopped.

    Runs before EVERY cell, for every tool identically (fairness), so no tool
    inherits a device blinded by the previous cell's leaked driver. Matches
    exact process names against ``UIAUTOMATION_HOLDER_PKGS`` only. adb errors
    propagate — a cell must not start on a device whose hygiene is unknown.
    """
    serial = serial or device_serial()
    ps_out = adb("shell", "ps", "-A", "-o", "NAME", serial=serial).stdout
    running = {line.strip() for line in ps_out.splitlines()}
    stopped: list[str] = []
    for pkg in UIAUTOMATION_HOLDER_PKGS:
        if pkg in running:
            adb("shell", "am", "force-stop", pkg, serial=serial)
            stopped.append(pkg)
    return stopped


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
