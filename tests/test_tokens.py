import json
from pathlib import Path

from mobile_agent_bench.tokens import parse_transcript


def _write(tmp_path: Path, records: list[dict]) -> Path:
    p = tmp_path / "transcript.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    return p


def test_prefers_result_record(tmp_path):
    p = _write(tmp_path, [
        {"type": "assistant", "message": {"usage": {"input_tokens": 10, "output_tokens": 5}}},
        {"type": "result", "num_turns": 3, "total_cost_usd": 0.42, "usage": {
            "input_tokens": 100, "output_tokens": 50,
            "cache_creation_input_tokens": 200, "cache_read_input_tokens": 1000,
        }},
    ])
    report = parse_transcript(p)
    assert report.source == "result-record"
    assert report.input_tokens == 100
    assert report.total_billed == 1350
    assert report.total_uncached == 350
    assert report.total_cost_usd == 0.42
    assert report.num_turns == 3


def test_falls_back_to_summing_and_flags_it(tmp_path):
    p = _write(tmp_path, [
        {"type": "assistant", "message": {"usage": {
            "input_tokens": 10, "output_tokens": 5,
            "cache_creation_input_tokens": 1, "cache_read_input_tokens": 2}}},
        {"type": "assistant", "message": {"usage": {"input_tokens": 20, "output_tokens": 15}}},
    ])
    report = parse_transcript(p)
    assert report.source == "summed-messages"
    assert report.input_tokens == 30
    assert report.output_tokens == 20
    assert report.total_billed == 53
    assert report.num_turns == 2
    assert report.total_cost_usd is None


def test_survives_truncated_tail_line(tmp_path):
    p = tmp_path / "transcript.jsonl"
    p.write_text(
        json.dumps({"type": "assistant", "message": {"usage": {"input_tokens": 7, "output_tokens": 3}}})
        + '\n{"type": "result", "usage": {"input_to'  # killed mid-write
    )
    report = parse_transcript(p)
    assert report.source == "summed-messages"
    assert report.total_billed == 10
