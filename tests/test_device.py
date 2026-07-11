"""Per-cell UiAutomation-holder hygiene (improvement 9c816108).

v1's own grid cells left the ``dev.mobile.maestro`` instrumentation driver
alive on the phone; a leaked driver holds the device's single UiAutomation
connection, so every later ``uiautomator dump`` is SIGKILLed — blinding
whichever tool ran next (cross-tool contamination; bench P0-A). The harness
must clear known holders before EVERY run, for every tool identically, and
record what it cleared in the run meta.
"""

import subprocess

from mobile_agent_bench import device


def _completed(stdout: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=[], returncode=0, stdout=stdout, stderr="")


def _patch_adb(monkeypatch, ps_output: str, calls: list):
    def fake_adb(*args, serial=None, timeout=60):
        calls.append(args)
        if args[:2] == ("shell", "ps"):
            return _completed(ps_output)
        return _completed()

    monkeypatch.setattr(device, "adb", fake_adb)


def test_clear_stops_leaked_holder(monkeypatch):
    calls: list = []
    _patch_adb(monkeypatch, "NAME\ncom.android.systemui\ndev.mobile.maestro\n", calls)
    cleared = device.clear_uiautomation_holders(serial="S")
    assert cleared == ["dev.mobile.maestro"]
    assert ("shell", "am", "force-stop", "dev.mobile.maestro") in calls


def test_clear_noop_on_clean_device(monkeypatch):
    calls: list = []
    _patch_adb(monkeypatch, "NAME\ncom.android.systemui\n", calls)
    assert device.clear_uiautomation_holders(serial="S") == []
    assert all(a[:2] == ("shell", "ps") for a in calls), "must not force-stop anything"


def test_clear_matches_exact_names_only(monkeypatch):
    # The Pixel Watch companion contains "maestro" as a substring but is an
    # unrelated Google app — it must never be force-stopped.
    calls: list = []
    _patch_adb(
        monkeypatch,
        "NAME\ncom.google.android.apps.wearables.maestro.companion\n",
        calls,
    )
    assert device.clear_uiautomation_holders(serial="S") == []
    assert all(a[:2] == ("shell", "ps") for a in calls)


def test_clear_stops_every_listed_holder(monkeypatch):
    calls: list = []
    _patch_adb(
        monkeypatch,
        "NAME\ndev.mobile.maestro\nio.appium.uiautomator2.server\n",
        calls,
    )
    cleared = device.clear_uiautomation_holders(serial="S")
    assert cleared == ["dev.mobile.maestro", "io.appium.uiautomator2.server"]


def test_run_one_clears_holders_before_reset_and_records(monkeypatch, tmp_path):
    """Fairness wiring: hygiene runs before the task reset, identically for
    every tool, and the run meta records what was cleared."""
    from mobile_agent_bench import agent as agent_mod
    from mobile_agent_bench import runner
    from mobile_agent_bench.schema import Task, Tool, Verify

    order: list = []
    monkeypatch.setattr(runner, "device_serial", lambda: "S")
    monkeypatch.setattr(
        runner,
        "clear_uiautomation_holders",
        lambda serial=None: order.append("hygiene") or ["dev.mobile.maestro"],
    )
    monkeypatch.setattr(
        runner,
        "ensure_pinned_app",
        lambda pkg, apk, serial=None: {"package": pkg, "apk_md5": "d" * 32, "action": "verified"},
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
        app_apk="target-app/app/build/outputs/apk/stock/debug/app-stock-debug.apk",
        reset=("force-stop",),
        verify=Verify(type="manual"), timeout_s=60,
    )
    tool = Tool(id="x", name="x", mcp_config="tools/x.mcp.json")
    record = runner.run_one(task, tool, "m", tmp_path)

    assert order == ["hygiene", "reset"], "holders must be cleared before the task reset"
    assert record["uiautomation_holders_cleared"] == ["dev.mobile.maestro"]
