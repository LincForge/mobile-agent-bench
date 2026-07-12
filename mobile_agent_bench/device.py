"""Scripted device/app state reset between runs (fairness: identical app state).

All adb access goes through BENCH_DEVICE_SERIAL from the environment (or
bench.local.yaml, which is gitignored) — the published repo never contains a
device serial. Reset steps are declared per-task and executed in order before
EVERY run, for every tool identically.
"""

from __future__ import annotations

import hashlib
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
    # agent-device (Callstack) helper APKs — joined the bench after the v1
    # allowlist; the snapshot helper registers a UiAutomation connection.
    "com.callstack.agentdevice.snapshothelper",
    "com.callstack.agentdevice.multitouchhelper",
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
    # An automation server orphaned by a killed agent session survives as an
    # anonymous `app_process` under the shell uid — no package to force-stop.
    # It holds a UiAutomation *registration*, so passive dumps still work but
    # every later registration dies ("already registered!"), silently blinding
    # driver-based tools (maestro). Kill such orphans by pid. Nothing else on a
    # bench device legitimately runs as a persistent shell-uid app_process.
    detail = adb("shell", "ps", "-A", "-o", "USER,PID,NAME", serial=serial).stdout
    for line in detail.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0] == "shell" and parts[2] == "app_process":
            adb("shell", "kill", parts[1], serial=serial)
            stopped.append(f"app_process:{parts[1]}")
    return stopped


def connected_serials() -> list[str]:
    """Every serial adb can currently see, whatever its state — a transcript
    can leak any of them (nerve_discover output lists the whole fleet), so the
    sanitizer redacts them all. No serial/-s arg: this is a host-level query.
    """
    proc = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=10)
    serials: list[str] = []
    for line in proc.stdout.splitlines()[1:]:  # first line is the banner
        parts = line.split()
        if len(parts) >= 2:
            serials.append(parts[0])
    return serials


def local_apk_md5(apk_path: Path) -> str:
    """md5 of the repo-built pinned APK; refuses to run without the artifact."""
    if not apk_path.exists():
        raise DeviceError(
            f"pinned APK missing: {apk_path} — build it first "
            "(cd target-app && ./gradlew assembleStockDebug assembleSeededDebug :wear:assembleDebug)"
        )
    return hashlib.md5(apk_path.read_bytes()).hexdigest()


def installed_apk_md5(package: str, serial: str | None = None) -> str | None:
    """Digest of the installed base.apk, or None if the package is absent."""
    serial = serial or device_serial()
    try:
        out = adb("shell", "pm", "path", package, serial=serial).stdout
    except DeviceError:
        return None  # pm path exits nonzero for an absent package
    paths = [line.removeprefix("package:").strip() for line in out.splitlines() if line.strip()]
    if not paths:
        return None
    if len(paths) > 1:
        raise DeviceError(f"{package}: split APKs are not supported by the digest pin ({paths})")
    md5_out = adb("shell", "md5sum", paths[0], serial=serial).stdout
    return md5_out.split()[0]


def ensure_pinned_app(package: str, apk_path: Path, serial: str | None = None) -> dict:
    """Verify the installed app IS the pinned APK (byte digest); heal on mismatch.

    Runs before EVERY cell, for every tool identically. Byte-level pinning
    subsumes flavor and debuggable checks (c9's seeded flavor, c10's debuggable
    build are properties of the pinned bytes) and catches the v1 failure mode
    where a stale probe APK sat on the device unnoticed. Returns the pin record
    for the run meta; raises if the device cannot be brought to the pinned state.
    """
    serial = serial or device_serial()
    want = local_apk_md5(apk_path)
    have = installed_apk_md5(package, serial=serial)
    if have == want:
        return {"package": package, "apk_md5": want, "action": "verified"}
    adb("install", "-r", "-t", str(apk_path), serial=serial, timeout=300)
    now = installed_apk_md5(package, serial=serial)
    if now != want:
        raise DeviceError(
            f"{package}: installed digest {now} still differs from pinned {want} "
            f"after install of {apk_path} — uninstall the stale build and retry"
        )
    return {"package": package, "apk_md5": want, "action": "installed", "previous_md5": have}


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
