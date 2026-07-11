"""Verify-regex sample tests (improvements 8881e5a3 / ffb4ada1).

v1 shipped three flawed answer-graders (AMENDMENTS.md): b7 false-FAILED every
correct table-form answer, c9's bare `block` false-PASSED a SHIP verdict, and
c10's bare `0[.,]755` false-PASSED a hedged range. None of these needed a
device to catch — a single sample answer run through the pattern would have.

Every answer-type task must now carry frozen ``match_samples`` and
``reject_samples`` in its YAML, and the schema validates the pattern against
its own samples at load time through the SAME matcher the harness grades with
(``Verify.matches``) — a task file whose grader fails its own evidence refuses
to load, so CI catches a flawed grader before any cell runs.
"""

from pathlib import Path

import pytest

from mobile_agent_bench.schema import ConfigError, Verify, load_all_tasks

ROOT = Path(__file__).resolve().parent.parent


def _answer_verify(**kw) -> Verify:
    kw.setdefault("type", "answer")
    kw.setdefault("pattern", "BENCH-STABLE")
    kw.setdefault("match_samples", ("value is BENCH-STABLE",))
    kw.setdefault("reject_samples", ("value is BENCH-DEV",))
    return Verify(**kw)


def test_answer_verify_requires_samples():
    with pytest.raises(ConfigError, match="match_samples"):
        _answer_verify(match_samples=())
    with pytest.raises(ConfigError, match="reject_samples"):
        _answer_verify(reject_samples=())


def test_match_sample_the_pattern_rejects_refuses_to_load():
    with pytest.raises(ConfigError, match="not matched"):
        _answer_verify(match_samples=("the build channel is BENCH-DEV",))


def test_reject_sample_the_pattern_matches_refuses_to_load():
    with pytest.raises(ConfigError, match="matched"):
        _answer_verify(reject_samples=("value is BENCH-STABLE, done",))


def test_matches_is_case_insensitive_and_dotall():
    v = _answer_verify(
        pattern="(?=.*alpha)(?=.*beta)",
        match_samples=("ALPHA\nthen much later\nBeta",),
        reject_samples=("alpha only",),
    )
    assert v.matches("Alpha ...\n... BETA")
    assert not v.matches("beta only")


def test_all_committed_answer_tasks_carry_validated_samples():
    """Loading already self-validates each pattern against its samples; this
    pins that every answer grader HAS frozen evidence in the repo."""
    tasks = load_all_tasks(ROOT / "tasks")
    answer_tasks = [t for t in tasks if t.verify.type == "answer"]
    assert sorted(t.id for t in answer_tasks) == [
        "a1", "a4", "b5", "b6", "b7", "b8", "c10", "c9",
    ]
    for t in answer_tasks:
        assert len(t.verify.match_samples) >= 1, t.id
        assert len(t.verify.reject_samples) >= 1, t.id


def test_historical_grader_failures_are_encoded_as_samples():
    """The three v1 grader flaws (AMENDMENTS.md) must be frozen as samples so
    a future pattern edit that reintroduces one fails CI."""
    tasks = {t.id: t for t in load_all_tasks(ROOT / "tasks")}

    # c9: bare `block` once false-PASSED a SHIP verdict ("no blocking issues").
    assert any(
        "blocking" in s.lower() and "ship" in s.lower() for s in tasks["c9"].verify.reject_samples
    ), "c9 must keep the 'no blocking issues, SHIP' false-PASS shape as a reject sample"

    # c10: bare 0.755 once false-PASSED a hedged back-division range.
    assert any(
        "0.755" in s and ("to 0.7" in s or "- 0.7" in s) for s in tasks["c10"].verify.reject_samples
    ), "c10 must keep the range-hedge false-PASS shape as a reject sample"

    # b7: the original inline-only pattern false-FAILED table-form answers.
    assert any(
        "\n" in s for s in tasks["b7"].verify.match_samples
    ), "b7 must keep a multi-line (table-form) correct answer as a match sample"
