# mobile-agent-bench

A reproducible benchmark of **agent-operated mobile-device tooling**: four MCP
tool stacks driven by the same AI agent, same pinned model, same physical
devices, on ten pre-registered tasks — plus raw transcripts for every run.

| Stack | Vendor |
|---|---|
| nerve + crucible + spectra | LincForge (that's us — see the disclosure below) |
| Maestro MCP | mobile.dev |
| mobile-mcp | mobile-next (community) |
| agent-device | Callstack |

**Read [`PREREGISTRATION.md`](PREREGISTRATION.md) first** — metrics, task
suite, pass criteria, model pin, and fairness rules were frozen at the
`v1-prereg` tag *before* the first comparative run. Results publish for every
cell, including our losses.

## Disclosure

We are the vendor of one of the stacks under test. That is exactly why this
repo exists in this shape: pre-registered criteria, vendor-recommended
configuration for every competitor, harness + target app published as source,
and a raw sanitized transcript behind every number. If you think a row is
unfair, clone it and re-run it.

## Layout

```
PREREGISTRATION.md   # the frozen contract (v1-prereg tag)
tasks/               # 10 frozen task definitions (prompt + reset + verification)
tools/               # 4 tool adapters (MCP config, vendor-recommended)
target-app/          # BenchTarget: purpose-built open-source target app (SPEC.md frozen)
mobile_agent_bench/  # harness: runner, agent invocation, token accounting, reset, sanitize
results/             # raw run logs: results/<tool>/<task>/run-<n>/{transcript.jsonl,meta.json}
```

## Running it

Prereqs: Python 3.12+ with [uv](https://docs.astral.sh/uv/), the Claude Code
CLI (`claude`), adb + a connected Android device, and the tool stacks you want
to test installed per their vendor docs (see `tools/*.yaml` notes).

```bash
uv sync
export BENCH_DEVICE_SERIAL=<your device serial>   # or bench.local.yaml (gitignored)
uv run bench run --tool mobile-mcp --task a1 --runs 5
uv run bench report
```

- Machine-local MCP command paths go in `tools/<id>.local.mcp.json`
  (gitignored); the committed configs assume vendor binaries on PATH.
- `bench.local.yaml` (gitignored) also carries redaction literals — every
  transcript is scrubbed of serials/hostnames/user paths at capture time.
- The target app is built from `target-app/` (Gradle; `stock` flavor for all
  tasks except c9, which uses `seeded`).

## Status

- [x] Harness skeleton + token accounting + scripted reset
- [x] Task suite + target-app spec frozen (`v1-prereg`)
- [ ] BenchTarget implementation matching the frozen spec
- [ ] Comparative runs (2026-07-08 → 2026-07-15)
- [ ] Results + operational-proof writeup

## License

MIT — see [LICENSE](LICENSE).
