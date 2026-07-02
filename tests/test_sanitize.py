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
