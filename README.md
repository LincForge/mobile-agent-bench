# mobile-agent-bench

A reproducible benchmark of **agent-operated mobile-device tooling**: four MCP
tool stacks driven by the same confined AI agent, same pinned model, same
physical devices, on ten pre-registered tasks — plus raw transcripts for every
run.

Three complete grids have been run and published: **v1**, **v2**, and **v3**,
200 cells each (10 tasks × 5 runs × 4 tools = **600 cells total**).

**→ Read the [combined v1+v2+v3 report](REPORT.md).**

| Stack | Vendor |
|---|---|
| [nerve](https://github.com/LincForge/nerve) + [crucible](https://github.com/LincForge/crucible) + [spectra](https://github.com/LincForge/spectra) | LincForge (that's us — see the disclosure below) |
| Maestro MCP | mobile.dev |
| mobile-mcp | mobile-next (community) |
| agent-device | Callstack |

## Results at a glance

Completion over the 45 scored phone cells per tool (the Wear OS row is a
capability row, reported separately and never averaged), plus the **7-task UI +
Logcat** phone subset (excluding the two JDWP debugger tasks `c10` and `c11`)
and the **3-task UI-Only** subset (`a5, a6, c9`):

| | v1 (45 cells) | v2 (45 cells) | v3 7-task UI+Logcat (`n=35`) | v3 3-task UI-Only (`n=15`) | v3 9-task Phone (`n=45`) |
|---|---|---|---|---|---|
| linc | 33/45 (73%) | **44/45 (98%)** | **34/35 (97%)** | **15/15 (100%)** | **44/45 (98%)** |
| agent-device | 32/45 (71%) | 32/45 (71%) | **34/35 (97%)** | **15/15 (100%)** | 34/45 (76%) |
| mobile-mcp | 25/45 (56%) | 28/45 (62%) | 18/35 (51%) | **15/15 (100%)** | 20/45 (44%) |
| Maestro | 26/45 (58%) | 20/45 (44%) | 14/35 (40%) | 13/15 (87%) *(14/15 adj.)* | 14/45 (31%) |

The three-grid arc, and the reason all three grids are published together:

1. **v1 was a loss.** Our stack came first by two points, was the *slowest*
   column on the grid (7 timeouts, against 1–3 for everyone else), and scored
   **0/5 on c10** — runtime state inspection, the one task our debugger uniquely
   exists for. So did every other tool: c10 was 0/0/0/0.
2. **v2 fixed what v1 exposed — with an overfitting caveat.** Both root causes
   were filed as P0s against our own stack, fixed, pinned, and the
   byte-identical grid was re-run under `v2-prereg`. `c10` went to 5/0/0/0 and
   median wall time dropped to 138s (0 timeouts). Because we fixed defects on
   tasks we had already watched fail, we named the objection ourselves: read v2
   as *"the vendor can fix what this benchmark measures,"* and Remedy 2 was a
   **v3 with unseen tasks** and updated competitor releases.
3. **v3 tested unseen tasks against upgraded competitors and the frozen
   `linc-nerve==0.1.0` PyPI release — scored once with zero post-hoc re-runs.**
   On the **7-task UI + Logcat phone subset (`n=35`)**, Callstack's upgraded
   **`agent-device 0.21.27` and `linc` match at 34/35 (97.1%)** (`agent-device`
   is faster at the per-task median on 5 of 7 tasks, `64.1s` vs `80.6s` pooled
   median; `linc` uses fewer uncached tokens on 6 of 7 tasks, `$1.01/pass` vs
   `$1.41/pass`). The 10-cell difference on the 9-task phone grid (`44/45` vs
   `34/45`) comes entirely from `c10` and `c11`, which require a JVM debugger
   (`linc-spectra` goes `10/10`, while tools without JDWP support go `0/10` or
   `2/10` via UI curve-fitting). All three packages in the `linc` column are now
   open-source (`Apache-2.0`) on GitHub and PyPI (`linc-nerve`, `linc-crucible`,
   `linc-spectra`); note that the published `v3` grid was scored once against the
   frozen pre-release commits `crucible@cf04279` and `spectra@c471dad` paired
   with `linc-nerve==0.1.0`.

## Disclosure

We are the vendor of one of the stacks under test. That is exactly why this
repo exists in this shape: pre-registered criteria, vendor-recommended
configuration for every competitor, harness + target app published as source,
and a raw sanitized transcript behind every number. If you think a row is
unfair, clone it and re-run it.

Every deviation from pre-registration is recorded with receipts in
[`AMENDMENTS.md`](AMENDMENTS.md), including the interference we caught that
*helped* us and the contaminated cells we voided that had already passed.
Voided cells are kept in `results_invalid/` rather than deleted. In **v3**,
in-harness lock detection (`is_device_locked` pre/post cell) ran across all 200
cells with **0 locked cells and 0 amendments**.

## Reading order

1. [`REPORT.md`](REPORT.md) — the combined v1+v2+v3 report (start here)
2. [`PREREGISTRATION.md`](PREREGISTRATION.md) — the v1 frozen contract (`v1-prereg` tag)
3. [`PREREGISTRATION-v2.md`](PREREGISTRATION-v2.md) — the v2 frozen contract (`v2-prereg` tag)
4. [`PREREGISTRATION-v3.md`](PREREGISTRATION-v3.md) — the v3 frozen contract (`v3-prereg` tag), incl. unseen task hashes & PyPI wheel SHA-256
5. [`AMENDMENTS.md`](AMENDMENTS.md) — every deviation, with receipts
6. [`docs/v1-deep-dive.md`](docs/v1-deep-dive.md) · [`docs/v2-deep-dive.md`](docs/v2-deep-dive.md) · [`docs/v3-deep-dive.md`](docs/v3-deep-dive.md) — per-task analysis

The `v1-prereg`, `v2-prereg`, and `v3-prereg` git tags are the integrity
anchors: each was pushed *before* the first comparative cell of its grid ran.
Git history is deliberately never rewritten in this repo.

## Layout

```
REPORT.md              # combined v1+v2+v3 report
PREREGISTRATION.md     # the frozen v1 contract (v1-prereg tag)
PREREGISTRATION-v2.md  # the frozen v2 contract (v2-prereg tag)
PREREGISTRATION-v3.md  # the frozen v3 contract (v3-prereg tag)
AMENDMENTS.md          # every post-freeze deviation, with rationale + receipts
tasks/                 # 10 frozen v1/v2 task definitions (prompt + reset + verification + APK pin)
tasks_v3/              # 10 frozen v3 task definitions (4 v1/v2 anchors + 6 unseen tasks)
tools/                 # 4 tool adapters (MCP config, vendor-recommended)
target-app/            # BenchTarget: purpose-built open-source target app (SPEC.md + v3 additions)
mobile_agent_bench/    # harness: runner, agent invocation, token accounting, lock guard, reset, sanitize
results/               # v1 raw run logs: <tool>/<task>/run-<n>/{transcript.jsonl,meta.json}
results_v2/            # v2 raw run logs, same shape
results_v3/            # v3 raw run logs, same shape
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

# reproduce the v2 or v3 grid's scoreboard from the published rows
BENCH_RESULTS_DIR=results_v2 uv run bench report
BENCH_RESULTS_DIR=results_v3 BENCH_TASKS_DIR=tasks_v3 uv run bench report
```

- Machine-local MCP command paths go in `tools/<id>.local.mcp.json`
  (gitignored); the committed configs assume vendor binaries on PATH.
- `bench.local.yaml` (gitignored) also carries redaction literals — every
  transcript is scrubbed of serials/hostnames/user paths at capture time.
- The target app is built from `target-app/` (Gradle; `stock` flavor for all
  tasks except c9, which uses `seeded`). Each task pins the exact APK by digest.

## Status

- [x] Harness, token accounting, scripted reset, confinement, in-harness lock guard
- [x] Task suite + target-app spec frozen (`v1-prereg`)
- [x] BenchTarget implementation matching the frozen spec
- [x] **v1 grid complete** (200/200 cells) + report + deep-dive
- [x] **v2 grid complete** (200/200 cells) under `v2-prereg` + combined report
- [x] **v3 grid complete** (200/200 cells) under `v3-prereg` (6 unseen tasks, PyPI `linc-nerve==0.1.0` freeze, updated competitor versions, 0 locked cells)

## If you build one of these tools

Run it yourself and tell us where we're wrong. Open an issue with the cell and
the transcript. A row we cannot defend is a row we retract.

## License

MIT — see [LICENSE](LICENSE).
