from mobile_agent_bench import sanitize
from mobile_agent_bench.sanitize import sanitize_text


def test_home_dirs_always_redacted():
    out = sanitize_text("wrote /Users/somebody/projects/x.log and /home/dev/y")
    assert "/Users/<REDACTED>" in out
    assert "/home/<REDACTED>" in out
    assert "somebody" not in out


def test_extra_literals_redacted():
    out = sanitize_text("host is bench-host.internal.example ok", ["bench-host.internal.example"])
    assert "bench-host" not in out
    assert "<REDACTED-X0>" in out


# Enumerated-serial coverage (improvement ca4499a4): tool output inside a
# transcript can list EVERY attached device (nerve_discover, adb devices via
# any MCP tool) — not just the one configured bench serial. Sanitization must
# redact every serial adb can currently see, or the published transcript leaks
# the rest of the bench fleet.


def test_runtime_enumerated_serials_redacted(monkeypatch):
    monkeypatch.setattr(sanitize, "connected_serials", lambda: ["4A091FDAQ000XY", "5B182GEBR111ZW"])
    out = sanitize_text("discover -> phone 4A091FDAQ000XY (online), watch 5B182GEBR111ZW (online)")
    assert "4A091FDAQ000XY" not in out
    assert "5B182GEBR111ZW" not in out
    assert "<DEVICE_SERIAL-0>" in out and "<DEVICE_SERIAL-1>" in out


def test_runtime_serial_redaction_is_stable_across_adb_ordering(monkeypatch):
    """The placeholder index must come from the sorted serial, not adb's
    enumeration order, so re-sanitizing the same transcript is idempotent."""
    monkeypatch.setattr(sanitize, "connected_serials", lambda: ["BBB222", "AAA111"])
    first = sanitize_text("AAA111 and BBB222")
    monkeypatch.setattr(sanitize, "connected_serials", lambda: ["AAA111", "BBB222"])
    second = sanitize_text("AAA111 and BBB222")
    assert first == second == "<DEVICE_SERIAL-0> and <DEVICE_SERIAL-1>"


def test_sanitize_survives_adb_absence(monkeypatch):
    """A third-party clone with no adb on PATH must sanitize identically."""
    def boom():
        raise FileNotFoundError("adb not found")

    monkeypatch.setattr(sanitize, "connected_serials", boom)
    out = sanitize_text("wrote /Users/somebody/x.log")
    assert "/Users/<REDACTED>" in out


def test_connected_serials_parses_adb_devices(monkeypatch):
    import subprocess

    from mobile_agent_bench import device

    def fake_run(cmd, **kw):
        assert cmd[:2] == ["adb", "devices"]
        return subprocess.CompletedProcess(
            args=cmd, returncode=0,
            stdout=(
                "List of devices attached\n"
                "4A091FDAQ000XY\tdevice\n"
                "5B182GEBR111ZW\tunauthorized\n"
                "emulator-5554\toffline\n"
                "\n"
            ),
            stderr="",
        )

    monkeypatch.setattr(device.subprocess, "run", fake_run)
    assert device.connected_serials() == ["4A091FDAQ000XY", "5B182GEBR111ZW", "emulator-5554"]
