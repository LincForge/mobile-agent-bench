"""Token accounting from a claude-CLI stream-json transcript.

Fairness note (pre-registered): the per-task token number is EVERYTHING the
agent consumed for the run — input, output, and cache creation/read tokens —
taken from the CLI's own cumulative `result` record, not from our arithmetic.
Cache reads are reported both included and excluded so a tool that leans on
prompt caching is visible rather than penalized or hidden. This is the
measurement agent-device's >50%-cut claim is about, so it is reported at full
granularity for every tool identically.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class TokenReport:
    input_tokens: int
    output_tokens: int
    cache_creation_tokens: int
    cache_read_tokens: int
    num_turns: int
    total_cost_usd: float | None
    source: str  # "result-record" (authoritative) or "summed-messages" (fallback)

    @property
    def total_billed(self) -> int:
        """All tokens the run consumed, cache traffic included."""
        return (
            self.input_tokens
            + self.output_tokens
            + self.cache_creation_tokens
            + self.cache_read_tokens
        )

    @property
    def total_uncached(self) -> int:
        return self.input_tokens + self.output_tokens + self.cache_creation_tokens

    def as_dict(self) -> dict:
        d = asdict(self)
        d["total_billed"] = self.total_billed
        d["total_uncached"] = self.total_uncached
        return d


def _usage_fields(usage: dict) -> tuple[int, int, int, int]:
    return (
        int(usage.get("input_tokens", 0)),
        int(usage.get("output_tokens", 0)),
        int(usage.get("cache_creation_input_tokens", 0)),
        int(usage.get("cache_read_input_tokens", 0)),
    )


def parse_transcript(path: Path) -> TokenReport:
    """Parse a stream-json transcript (one JSON object per line).

    Prefers the terminal `result` record's cumulative usage (the CLI's own
    accounting). Falls back to summing per-assistant-message usage if the run
    died before emitting a result record — flagged via `source` so partial
    rows are never silently mixed with complete ones.
    """
    result_usage: dict | None = None
    total_cost: float | None = None
    result_turns = 0
    assistant_turns = 0
    summed = [0, 0, 0, 0]

    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue  # truncated tail line from a killed run
            rtype = rec.get("type")
            if rtype == "result":
                result_usage = rec.get("usage")
                total_cost = rec.get("total_cost_usd")
                result_turns = int(rec.get("num_turns", 0))
            elif rtype == "assistant":
                usage = (rec.get("message") or {}).get("usage")
                if usage:
                    for i, v in enumerate(_usage_fields(usage)):
                        summed[i] += v
                    assistant_turns += 1

    if result_usage is not None:
        inp, out, cc, cr = _usage_fields(result_usage)
        return TokenReport(inp, out, cc, cr, result_turns, total_cost, "result-record")
    return TokenReport(*summed, assistant_turns, None, "summed-messages")
