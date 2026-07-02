# Pre-registration — mobile-agent-bench v1

**Frozen at tag `v1-prereg` — before any comparative run.**

This document, the task files under `tasks/`, the tool adapters under
`tools/`, the target-app specification (`target-app/SPEC.md`), and the pinned
model below are frozen as of the `v1-prereg` git tag. Results will be
published for every pre-registered cell, including losses and partial rows.
Any change after the tag is an **amendment**: it must be documented in
`AMENDMENTS.md` with a rationale, and it invalidates (forces re-run of) every
row it touches. Nothing is quietly edited.

## What is being measured

Four agent-operated mobile-device tool stacks, driven by the same agent on the
same model against the same physical devices, on ten pre-registered tasks:

| id | Stack | Configuration authority |
|---|---|---|
| `linc` | LINC nerve + crucible + spectra (MCP) | our stack — MJPEG streaming enabled |
| `maestro` | Maestro MCP (mobile.dev) | vendor docs (`maestro mcp`) |
| `mobile-mcp` | mobile-mcp (mobile-next) | vendor README (`npx @mobilenext/mobile-mcp@latest`) |
| `agent-device` | agent-device (Callstack) | vendor docs (global install, `agent-device mcp`) |

Every competitor runs in its **vendor-recommended configuration** — their MCP
server, their locator strategy, their documented agent-usage pattern. No
strawmen. Adapter files record the exact installed version per run.

## Metrics (locked)

1. **Time-to-task** — wall-clock seconds from agent spawn to session end, with
   completion verified by the harness afterward. Reported per run; medians per cell.
2. **Token cost per task** — every token the agent session consumed, from the
   agent CLI's own cumulative accounting: input, output, cache-creation and
   cache-read reported separately AND as a total. This is agent-device's
   headline-claim currency, so it is measured at full granularity, identically
   for every tool, with raw transcripts as receipts.
3. **Task completion rate** — N=5 runs per task per tool; a run counts **only**
   if the harness-side end-state assertion passes (`verify:` block in the task
   file — device-state check or frozen answer pattern). The agent's own claim
   of success is never trusted; a timed-out run is a FAIL.
4. **Catch-rate** — on the defect subset (b5, b6, c9, c10): did the agent+tool
   correctly detect AND localize the seeded defect/ground truth? Pass criteria
   frozen per task file.
5. **Determinism/flake** — variance across the 5 runs of each cell (wall-time
   and token dispersion + completion consistency), same prompt, same device,
   scripted state reset between runs.

## Task suite (locked — full definitions in `tasks/*.yaml`)

| id | Tier | Task | Verification |
|---|---|---|---|
| a1 | A | Launch → navigate 3 deep → report element text | answer: `BENCH-STABLE` |
| a2 | A | Form fill (text+toggle+dropdown) → submit | device state contract |
| a3 | A | Scroll long list to Item 073 → tap → detail | device state contract |
| a4 | A | Perceive + describe current screen | answer: all 4 nav targets |
| b5 | B | Repro crash from vague bug report + evidence | answer: exception class + message + item |
| b6 | B | Flaky-behavior investigation (passes 3/5) | answer: launch-counter root cause |
| b7 | B | Cold-start timing, 5 iterations + variance | answer: 5 timings + median + variance |
| b8 | B | **Wear OS** launch + interaction (capability row) | answer: `Pings: 3` |
| c9 | C | Seeded-defect build: "should this ship?" | answer: DO-NOT-SHIP + localizes tier bug |
| c10 | C | Runtime value of an internal variable | answer: `0.755` (unrecoverable from UI) |

- Tier A = table stakes (cost/speed comparison). Tier B = hard mobile reality.
  Tier C = judgment layer (ship gate, runtime debugging).
- **b8 is a capability row**: pre-registered expectation is that only the LINC
  stack completes it; it is reported separately and never averaged into
  cross-tool means.
- All tasks run against **BenchTarget** (`target-app/SPEC.md`, frozen), built
  from source in this repo. Task c9 uses the `seeded` flavor; all others `stock`.
- Task prompts are passed to the agent verbatim from the task files. Prompts
  never mention the state-file verification hook; transcripts are published,
  so hook-gaming is auditable.

## Agent + model (locked)

- **Agent:** Claude Code CLI, headless (`claude -p`), `--strict-mcp-config` so
  each run sees ONLY the tool-under-test's MCP server. Same binary version for
  all runs in a wave (recorded in run metadata).
- **Model: `claude-sonnet-5`** — pinned for all runs, all four stacks.
  *Rationale:* the benchmark should reflect what a customer would actually run
  an agent on — a mainstream, generally-available tier — not an in-house
  frontier configuration; it also keeps a 200-run grid affordable. The exact
  model ID is recorded in every run's `meta.json`. (Decided 2026-07-01 at
  harness time, per doc-044 open item.)
- One agent session per run; no retries; no human intervention mid-run.
  `--dangerously-skip-permissions` (headless) — the MCP surface is the only
  capability the agent has beyond text.

## Devices (locked)

- Phone tasks (a1–a4, b5–b7, c9, c10): **Google Pixel 8 Pro** (Android 16).
- Watch task (b8): **Google Pixel Watch 2** (Wear OS), paired to the Pixel.
- Physical hardware only; no emulators in any published row. Device model,
  OS, and build (never serials) are recorded in run metadata.
- Identical app state via scripted reset before every run (declared per task:
  wake / home / force-stop / clear-data).

## Run protocol

1. Reset device state per the task's frozen `reset:` steps.
2. Spawn the agent with the task prompt, pinned model, tool-under-test MCP config.
3. Store the full raw stream-json transcript (sanitized of device serials,
   hostnames, and user paths at capture time — transformations are mechanical
   redaction only, never content edits).
4. Harness runs the frozen verification; verdict + timing + token report →
   `meta.json`.
5. N=5 per cell; run order interleaved by tool (round-robin per task) so
   time-of-day effects don't accrue to one stack.

## Publication commitment

- Every pre-registered cell's result publishes, **including losses** — an
  honest loss on a row buys credibility for the wins.
- Every published figure traces to a stored raw run log in `results/`.
  Generated evaluation code is fine; generated *results* are not.
- Harness authorship disclosed: we (LincForge) wrote the harness, AI-assisted,
  and we are the vendor of the `linc` stack under test. The harness, tasks,
  target app, and raw transcripts are published precisely so this conflict is
  auditable and the benchmark re-runnable by anyone.
- Timebox: comparative runs 2026-07-08 → 2026-07-15. If rows are missing at
  the hard stop, what exists publishes and the gaps are stated as gaps.
