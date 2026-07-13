# mobile-agent-bench

A reproducible benchmark of **agent-operated mobile-device tooling**: four MCP
tool stacks driven by the same confined AI agent, same pinned model, same
physical devices, on ten pre-registered tasks — plus raw transcripts for every
run.

Two complete grids have been run and published: **v1** and **v2**, 200 cells
each (10 tasks × 5 runs × 4 tools).

**→ Read the [combined v1+v2 report](REPORT.md).**

| Stack | Vendor |
|---|---|
| nerve + crucible + spectra | LincForge (that's us — see the disclosure below) |
| Maestro MCP | mobile.dev |
| mobile-mcp | mobile-next (community) |
| agent-device | Callstack |

## Results at a glance

Completion over the 45 scored cells per tool (the Wear OS row is a capability
row, reported separately and never averaged):

| | v1 | v2 |
|---|---|---|
| linc | 73% | **44/45 (98%)** |
| agent-device | 71% | 32/45 (71%) |
| mobile-mcp | 56% | 28/45 (62%) |
| Maestro | 58% | 20/45 (44%) |

The arc, and the reason both grids are published together: **v1 was a loss.**
Our stack came first by two points, was the *slowest* column on the grid (7
timeouts, against 1–3 for everyone else), and scored **0/5 on c10** — runtime
state inspection, the one task our debugger uniquely exists for. So did every
other tool: c10 was 0/0/0/0.

Both root causes were filed as P0s against our own stack, fixed, pinned, and
the byte-identical grid was re-run under a fresh pre-registration. c10 is now
5/0/0/0 and the efficiency caveat is gone (138s median, 0 timeouts).

**The strongest objection to that result is ours, and it's in the report:** we
fixed defects on tasks we had already watched fail, and the competing tools
were run as-shipped both times. Read the v2 delta as "the vendor can fix what
this benchmark measures," not "the vendor generalizes." The two remedies —
an independent re-run, or a v3 with unseen tasks — are named in
[Limitations](REPORT.md#limitations--threats-to-validity).

## Disclosure

We are the vendor of one of the stacks under test. That is exactly why this
repo exists in this shape: pre-registered criteria, vendor-recommended
configuration for every competitor, harness + target app published as source,
and a raw sanitized transcript behind every number. If you think a row is
unfair, clone it and re-run it.

Every deviation from either pre-registration is recorded with receipts in
[`AMENDMENTS.md`](AMENDMENTS.md), including the interference we caught that
*helped* us and the contaminated cells we voided that had already passed.
Voided cells are kept in `results_invalid/` rather than deleted.

## Reading order

1. [`REPORT.md`](REPORT.md) — the combined v1+v2 report (start here)
2. [`PREREGISTRATION.md`](PREREGISTRATION.md) — the v1 frozen contract (`v1-prereg` tag)
3. [`PREREGISTRATION-v2.md`](PREREGISTRATION-v2.md) — the v2 frozen contract (`v2-prereg` tag), incl. pinned stack SHAs
4. [`AMENDMENTS.md`](AMENDMENTS.md) — every deviation, with receipts
5. [`docs/v1-deep-dive.md`](docs/v1-deep-dive.md) · [`docs/v2-deep-dive.md`](docs/v2-deep-dive.md) — per-task analysis

The `v1-prereg` and `v2-prereg` git tags are the integrity anchor: each was
pushed *before* the first comparative cell of its grid ran. Git history is
deliberately never rewritten in this repo.

## Layout

```
REPORT.md              # combined v1+v2 report
PREREGISTRATION.md     # the frozen v1 contract (v1-prereg tag)
PREREGISTRATION-v2.md  # the frozen v2 contract (v2-prereg tag)
AMENDMENTS.md          # every post-freeze deviation, with rationale + receipts
tasks/                 # 10 frozen task definitions (prompt + reset + verification + APK pin)
tools/                 # 4 tool adapters (MCP config, vendor-recommended)
target-app/            # BenchTarget: purpose-built open-source target app (SPEC.md frozen)
mobile_agent_bench/    # harness: runner, agent invocation, token accounting, reset, sanitize
results/               # v1 raw run logs: <tool>/<task>/run-<n>/{transcript.jsonl,meta.json}
results_v2/            # v2 raw run logs, same shape
results_invalid/       # voided cells, kept as receipts (never deleted)
```

## Confinement

The agent gets the tool under test and **nothing else** — no shell, no
filesystem search, no web, no subagents, `--strict-mcp-config`, a neutral cwd,
and a path-guarded `Read`. If a tool cannot see the UI tree, its agent is
blind. That is the point: the benchmark measures the *tool surface*, not the
model.

Closing that confinement took three errata in v1 (all in `AMENDMENTS.md`) —
most notably a built-in tool that could run arbitrary shell, which some agents
used to reach raw `adb` and `jdb`. The blast radius was measured per
transcript, the 8 affected cells were voided and re-run, and the remaining 112
were positively certified shell-free. That correction moved a *competitor's*
numbers, not ours.

## Running it

Prereqs: Python 3.12+ with [uv](https://docs.astral.sh/uv/), the Claude Code
CLI (`claude`), adb + a connected Android device, and the tool stacks you want
to test installed per their vendor docs (see `tools/*.yaml` notes).

```bash
uv sync
export BENCH_DEVICE_SERIAL=<your device serial>   # or bench.local.yaml (gitignored)
uv run bench run --tool mobile-mcp --task a1 --runs 5
uv run bench report

# reproduce the v2 grid's scoreboard from the published rows
BENCH_RESULTS_DIR=results_v2 uv run bench report
```

- Machine-local MCP command paths go in `tools/<id>.local.mcp.json`
  (gitignored); the committed configs assume vendor binaries on PATH.
- `bench.local.yaml` (gitignored) also carries redaction literals — every
  transcript is scrubbed of serials/hostnames/user paths at capture time.
- The target app is built from `target-app/` (Gradle; `stock` flavor for all
  tasks except c9, which uses `seeded`). Each task pins the exact APK by digest.

## Status

- [x] Harness, token accounting, scripted reset, confinement
- [x] Task suite + target-app spec frozen (`v1-prereg`)
- [x] BenchTarget implementation matching the frozen spec
- [x] **v1 grid complete** (200/200 cells) + report + deep-dive
- [x] **v2 grid complete** (200/200 cells) under `v2-prereg` + combined report
- [ ] v3 — unseen tasks, multi-device tier, in-harness lock detection

## If you build one of these tools

Run it yourself and tell us where we're wrong. Open an issue with the cell and
the transcript. A row we cannot defend is a row we retract.

## License

MIT — see [LICENSE](LICENSE).
