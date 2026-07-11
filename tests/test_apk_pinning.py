"""Per-task APK install/verify + variant pinning (improvements 9b6a0ba5 + 2d884371).

v1 precedent: a stale ``com.lincforge.bench`` probe APK sat on the bench phone
while cells assumed the BenchTarget app was current — the harness never checked
WHAT was installed before driving it. Every task now pins the exact APK it must
run against (byte-level md5 of the repo-built artifact); ``run_one`` verifies
the installed base.apk digest before every cell and installs the pinned APK on
mismatch. Digest pinning subsumes flavor and debuggable checks: c9 can only
PASS against the seeded flavor, c10's spectra path can only work against a
debuggable build — both are properties of the pinned bytes.
"""

import hashlib
import subprocess
from pathlib import Path

import pytest

from mobile_agent_bench import device
from mobile_agent_bench.device import DeviceError
from mobile_agent_bench.schema import ConfigError, load_all_tasks, load_task

ROOT = Path(__file__).resolve().parent.parent

STOCK_APK = "target-app/app/build/outputs/apk/stock/debug/app-stock-debug.apk"
SEEDED_APK = "target-app/app/build/outputs/apk/seeded/debug/app-seeded-debug.apk"
WEAR_APK = "target-app/wear/build/outputs/apk/debug/wear-debug.apk"


def _completed(stdout: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=[], returncode=0, stdout=stdout, stderr="")


# ---------------------------------------------------------------- schema ----


def _write_task(tmp_path: Path, app_block: str) -> Path:
    p = tmp_path / "t1.yaml"
    p.write_text(
        "id: t1\n"
        "tier: A\n"
        "name: t\n"
        "prompt: p\n"
        f"app:\n{app_block}"
        "reset: [home]\n"
        "verify:\n  type: manual\n"
        "timeout_s: 60\n"
    )
    return p


def test_task_without_pinned_apk_is_rejected(tmp_path):
    path = _write_task(tmp_path, "  package: dev.lincforge.benchtarget\n")
    with pytest.raises(ConfigError):
        load_task(path)


def test_task_loads_pinned_apk_path(tmp_path):
    path = _write_task(
        tmp_path,
        f"  package: dev.lincforge.benchtarget\n  apk: {STOCK_APK}\n",
    )
    task = load_task(path)
    assert task.app_apk == STOCK_APK


def test_all_committed_tasks_pin_the_right_variant():
    """c9 is the ONLY task allowed the seeded flavor; b8 pins the wear APK;
    every other task pins stock-debug (SPEC.md build-flavor contract)."""
    tasks = {t.id: t for t in load_all_tasks(ROOT / "tasks")}
    assert tasks["c9"].app_apk == SEEDED_APK
    assert tasks["b8"].app_apk == WEAR_APK
    for tid in ["a1", "a2", "a3", "a4", "b5", "b6", "b7", "c10"]:
        assert tasks[tid].app_apk == STOCK_APK, tid


# ------------------------------------------------------- ensure_pinned_app ----


def _make_apk(tmp_path: Path, content: bytes = b"apk-bytes") -> tuple[Path, str]:
    apk = tmp_path / "app-stock-debug.apk"
    apk.write_bytes(content)
    return apk, hashlib.md5(content).hexdigest()


def _patch_adb(monkeypatch, responses: dict, calls: list):
    """responses maps the first two command words to stdout or an Exception."""

    def fake_adb(*args, serial=None, timeout=60):
        calls.append(args)
        key = args[:2] if args[0] == "shell" else args[:1]
        resp = responses.get(key, "")
        if isinstance(resp, Exception):
            raise resp
        if callable(resp):
            resp = resp()
        return _completed(resp)

    monkeypatch.setattr(device, "adb", fake_adb)


def test_matching_digest_verifies_without_install(monkeypatch, tmp_path):
    apk, md5 = _make_apk(tmp_path)
    calls: list = []
    _patch_adb(
        monkeypatch,
        {
            ("shell", "pm"): "package:/data/app/xx/base.apk\n",
            ("shell", "md5sum"): f"{md5}  /data/app/xx/base.apk\n",
        },
        calls,
    )
    pin = device.ensure_pinned_app("dev.lincforge.benchtarget", apk, serial="S")
    assert pin["action"] == "verified"
    assert pin["apk_md5"] == md5
    assert all(a[0] != "install" for a in calls), "must not reinstall a verified app"


def test_missing_package_installs_pinned_apk(monkeypatch, tmp_path):
    apk, md5 = _make_apk(tmp_path)
    calls: list = []
    state = {"installed": False}

    def fake_adb(*args, serial=None, timeout=60):
        calls.append(args)
        if args[:2] == ("shell", "pm"):
            if not state["installed"]:
                raise DeviceError("pm path failed rc=1")
            return _completed("package:/data/app/xx/base.apk\n")
        if args[:2] == ("shell", "md5sum"):
            return _completed(f"{md5}  /data/app/xx/base.apk\n")
        if args[0] == "install":
            state["installed"] = True
        return _completed()

    monkeypatch.setattr(device, "adb", fake_adb)
    pin = device.ensure_pinned_app("dev.lincforge.benchtarget", apk, serial="S")
    assert pin["action"] == "installed"
    assert pin["previous_md5"] is None
    assert any(a[0] == "install" and str(apk) in a for a in calls)


def test_digest_mismatch_reinstalls_and_records_previous(monkeypatch, tmp_path):
    apk, md5 = _make_apk(tmp_path)
    stale = "0" * 32
    calls: list = []
    seen = {"md5_reads": 0}

    def fake_adb(*args, serial=None, timeout=60):
        calls.append(args)
        if args[:2] == ("shell", "pm"):
            return _completed("package:/data/app/xx/base.apk\n")
        if args[:2] == ("shell", "md5sum"):
            seen["md5_reads"] += 1
            current = stale if seen["md5_reads"] == 1 else md5
            return _completed(f"{current}  /data/app/xx/base.apk\n")
        return _completed()

    monkeypatch.setattr(device, "adb", fake_adb)
    pin = device.ensure_pinned_app("dev.lincforge.benchtarget", apk, serial="S")
    assert pin["action"] == "installed"
    assert pin["previous_md5"] == stale
    assert pin["apk_md5"] == md5
    assert any(a[0] == "install" for a in calls)


def test_install_that_fails_to_converge_raises(monkeypatch, tmp_path):
    apk, _md5 = _make_apk(tmp_path)
    calls: list = []
    _patch_adb(
        monkeypatch,
        {
            ("shell", "pm"): "package:/data/app/xx/base.apk\n",
            ("shell", "md5sum"): f"{'f' * 32}  /data/app/xx/base.apk\n",
        },
        calls,
    )
    with pytest.raises(DeviceError, match="still"):
        device.ensure_pinned_app("dev.lincforge.benchtarget", apk, serial="S")


def test_missing_local_apk_names_the_gradle_target(tmp_path):
    ghost = tmp_path / "app-stock-debug.apk"
    with pytest.raises(DeviceError, match="assembleStockDebug"):
        device.ensure_pinned_app("dev.lincforge.benchtarget", ghost, serial="S")


# ------------------------------------------------------------ run_one wiring ----


def test_run_one_pins_app_after_hygiene_before_reset(monkeypatch, tmp_path):
    """The pin check runs on every cell, after UiAutomation hygiene and before
    the task reset (reset must act on the RIGHT app), and lands in the meta."""
    from mobile_agent_bench import agent as agent_mod
    from mobile_agent_bench import runner
    from mobile_agent_bench.schema import Task, Tool, Verify

    order: list = []
    monkeypatch.setattr(runner, "device_serial", lambda: "S")
    monkeypatch.setattr(
        runner,
        "clear_uiautomation_holders",
        lambda serial=None: order.append("hygiene") or [],
    )
    monkeypatch.setattr(
        runner,
        "ensure_pinned_app",
        lambda pkg, apk, serial=None: order.append("pin")
        or {"package": pkg, "apk_md5": "d" * 32, "action": "verified"},
    )
    monkeypatch.setattr(
        runner,
        "reset_app_state",
        lambda pkg, steps, serial=None: order.append("reset") or list(steps),
    )
    monkeypatch.setattr(runner, "device_fingerprint", lambda serial=None: {"model": "x"})

    class _Tokens:
        def as_dict(self):
            return {"total_billed": 0}

    class _Result:
        wall_time_s = 1.0
        timed_out = False
        exit_code = 0
        transcript_path = tmp_path / "transcript.jsonl"
        tokens = _Tokens()

    monkeypatch.setattr(agent_mod, "run_agent", lambda task, tool, model, out: _Result())
    monkeypatch.setattr(agent_mod, "verify_task", lambda task, env, tp: ("PASS", "ok"))
    monkeypatch.setattr(agent_mod, "write_meta", lambda out, rec: None)

    task = Task(
        id="t", tier="A", name="t", prompt="p",
        app_package="dev.lincforge.benchtarget",
        app_apk=STOCK_APK,
        reset=("force-stop",),
        verify=Verify(type="manual"), timeout_s=60,
    )
    tool = Tool(id="x", name="x", mcp_config="tools/x.mcp.json")
    record = runner.run_one(task, tool, "m", tmp_path)

    assert order == ["hygiene", "pin", "reset"]
    assert record["app_pin"]["action"] == "verified"
    assert record["app_pin"]["apk_md5"] == "d" * 32
