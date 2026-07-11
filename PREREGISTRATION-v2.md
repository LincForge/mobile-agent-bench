# Pre-registration — mobile-agent-bench v2

**Frozen at tag `v2-prereg` — before any v2 comparative run.**

v2 is a full re-run of the v1 grid after the v1 findings were remediated: the
two LINC-stack P0s (nerve UI-element blindness, spectra runtime inspection)
and every harness-integrity gap the v1 deep-dive surfaced. The v1 rules carry
forward unchanged except where stated below. This document, the task files
under `tasks/`, the tool adapters under `tools/`, the target-app spec
(`target-app/SPEC.md`), the pinned stack SHAs, and the pinned model are frozen
as of the `v2-prereg` git tag. Any later change is an **amendment** in
`AMENDMENTS.md` and invalidates every row it touches. Nothing is quietly
edited. v1 results remain published as v1; v2 does not replace them.

## Pinned LINC stack (new in v2)

The `linc` column runs from dedicated pin worktrees, frozen at:

| component | SHA | what changed since the v1 runs |
|---|---|---|
| linc-nerve | `783fc88` | #105 typed UI-dump failures + self-heal of leaked UiAutomation holders (v1 ran most cells at the pre-fix SHA); #107 ensure_ready leaked-UiAutomation gate |
| linc-spectra | `badcee7` | #35 runtime inspection end-to-end (PID discovery, adapter discovery, attach handshake, zero-config method breakpoints); #37 jdb exception catchpoints + honest breakpoint warnings |
| linc-crucible | `a717296` | tool-description improvements only; no grid-surfaced defect was found in crucible |

Competitors run in their vendor-recommended configuration, exactly as in v1;
adapter files record the exact installed version per run. Model:
**`claude-sonnet-5`**, pinned, identical for all four stacks (v1 rationale
stands). Same agent binary version for all runs in a wave, recorded per run.

## Harness-integrity changes since v1 (all landed before this freeze)

1. **Per-cell UiAutomation hygiene** (#3): known UiAutomation-holder drivers
   are force-stopped before EVERY cell, identically for every tool; the run
   meta records what was cleared. (v1 contamination vector — see AMENDMENTS.)
2. **Per-task APK digest pinning** (#4): every task YAML pins the exact APK
   (`app.apk`); before every cell the harness verifies the installed
   `base.apk` md5 against the repo-built artifact and reinstalls on mismatch
   (`app_pin` in meta). c9 can only run against the `seeded` flavor; every
   other task against `stock` (b8: the Wear APK).
3. **Grader sample validation** (#5): every answer pattern carries frozen
   `match_samples`/`reject_samples` in the task file, validated at load time
   through the same predicate that grades runs. The three v1 grader flaws are
   frozen as regression samples. **No verify pattern changed for v2.**
4. **Sanitizer covers enumerated serials** (#6): every serial adb can see is
   redacted from transcripts, not just the configured bench serial.
5. **Token medians at full granularity** (#7): the report breaks out median
   billed / uncached / output per cell.

## Outcome reporting decision (pre-registered)

The per-run budget stays **900 s** (600 s for a1–a4), unchanged from v1 for
comparability — competitors finish inside it. A timed-out run remains **FAIL**
for every scored metric. New in v2: the harness mechanically flags
**solved-but-unfinalized** (#8) — a timed-out run whose harness verification
passed, or (answer tasks) whose frozen pattern matches the assistant text
produced before the kill. It is reported as a separate diagnostic column and
is **never** counted toward completion. Rationale: 5 of linc's 7 v1 timeouts
contained the full ground-truth answer in-transcript; v2 keeps the scoring
honest while making that failure mode visible for every tool identically.

## What is being measured (unchanged from v1)

Same four stacks (`linc`, `maestro`, `mobile-mcp`, `agent-device`), same five
locked metrics (time-to-task, token cost at full granularity, harness-verified
completion rate, catch-rate on the defect subset, determinism/flake), same ten
tasks (a1–c10) with **prompts and verify patterns byte-identical to v1** —
task files gained only the `app.apk` pin and grader samples. N=5 per cell,
round-robin interleaved by tool. Confinement is the post-erratum-#3 hardened
set (deny-list + Read-guard + neutral cwd), identical for every tool.

## Corrected expectation: b8 (Wear OS capability row)

v1 pre-registered "only the LINC stack completes b8" — **falsified**: all four
tools completed it. v2 keeps b8 as a capability row (reported separately,
never averaged) with the corrected expectation that all tools can complete it;
the row now measures Wear reliability/efficiency rather than exclusivity.

## Devices and preconditions

- Same physical hardware as v1: Pixel 8 Pro (phone tasks), Pixel Watch 2 (b8).
  No emulators. Models/OS recorded per run; serials never published.
- Pre-run condition: both devices attached, lock-free (no secure keyguard),
  and unreserved (`nerve_pool`); nightly device jobs honor reservations
  (linc-ops #468), so an overnight grid cannot be contaminated by cron.
- `ensure_ready` (nerve #107) gates readiness: a leaked-UiAutomation device
  that cannot self-heal reports not-ready and the cell does not run.

## Run protocol (per cell)

1. Clear UiAutomation holders (hygiene, logged to meta).
2. Verify/install the task's pinned APK (digest check, logged to meta).
3. Reset app state per the task's frozen `reset:` steps.
4. Spawn the agent (pinned model, tool-under-test MCP config only, hardened
   confinement), store the sanitized raw stream-json transcript.
5. Harness runs the frozen verification; verdict + solved-unfinalized flag +
   timing + token report → `meta.json`.

v2 rows land under `results_v2/` (`BENCH_RESULTS_DIR`), keeping v1's
`results/` immutable.

## Publication commitment (unchanged)

Every pre-registered cell publishes, including losses. Every figure traces to
a stored raw run log. Harness authorship and the vendor conflict are disclosed
exactly as in v1; harness, tasks, target app, and transcripts are published so
the benchmark is re-runnable by anyone. Timebox: v2 comparative runs
2026-07-13 → 2026-07-20; at the hard stop, what exists publishes and gaps are
stated as gaps.
