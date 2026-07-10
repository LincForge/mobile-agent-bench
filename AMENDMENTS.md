# Amendments to the pre-registration

Per `PREREGISTRATION.md`, any change after the `v1-prereg` tag is recorded here
with rationale. Nothing is quietly edited.

## 2026-07-10 — linc stack pinned to nerve `bb02ff1` for the whole grid

**What / why.** The pre-registration froze the task suite, model, and devices,
but did **not** pin a SHA for the linc stack (nerve/crucible/spectra) — the
harness invokes the console scripts from an *editable, shared* install
(`__editable__.linc_nerve.pth → linc-nerve/src`), which tracks whatever the
live repo HEAD is. That repo is under active development by other sessions.

The canonical Pixel 8 Pro cells **a1–a4, b5, b6** all ran between
2026-07-09 13:35Z and 21:03Z on nerve **`bb02ff1`** (verified: the tool
`nerve_device_state` appears in zero of those transcripts). Two nerve commits
landed **after** that window:

- `2acedb3` (2026-07-09 23:17Z) — adds a new `nerve_device_state` MCP tool
  (would change the agent's tool surface, and could aid the c-tier tasks).
- `40533da` (2026-07-10 04:47Z) — `nerve_key` keycode validation (behavioral
  change to a tool the agent uses).

To keep all 200 cells uniform, the remaining cells (b7, c10, c9, b8, and the
agent-device column) are run against nerve pinned to `bb02ff1` via an isolated
git worktree + venv (`~/projects/linc-nerve-pin`, sibling-located so the
`../linc-device-kit` path dep resolves to the same `22b1ea7` used in a1–b6).
The shared live nerve (daemon + other sessions) is left untouched.
`tools/linc.local.mcp.json` (gitignored) points `linc-nerve` at the pinned
binary. crucible/spectra/device-kit had **no** commits in the surrounding 24h,
so only nerve required pinning.

This is a **freeze-enforcement**, not a protocol change — no cell is
re-run and no result is altered. The improvements observed on nerve during this
run (`6a78b78b`, `46093171`, `c3409161`, `2d8b11f4`) are deferred to a future
**v2** grid (fresh pre-registration) so the delta can be published cleanly
without moving the target mid-measurement.

## 2026-07-10 — b7 verify pattern corrected (bug) + transcripts re-graded

**What / why.** The b7 (cold-start timing) verify pattern was
`(?s)(\d{2,6}\s*ms.*?){5}.*(median).*(variance|standard deviation|std|stdev)`.
It required five **inline** `NN ms` strings to appear *before* the word
"median". Every capable agent instead reported the five figures in a **table**
(bare numbers, "ms" in the column header) with median/variance below — so the
only `\d ms` matches fell in the stats lines, out of order, and the pattern
returned no match. Result: **all 15 b7 cells recorded FAIL**, including
objectively-correct answers from all three tools (e.g. linc/run-2 reported
462/449/453/455/438 ms, median 453 ms, stdev 8.85 ms, variance 78.3 ms²,
measured from the OS `Displayed`/`TotalTime` logcat metric). This was a
**grader bug, tool-agnostic** — it rejected the competitors' correct answers too.

**Fix.** The pattern now encodes the task's stated intent with order-independent
lookaheads (searched `IGNORECASE|DOTALL`): median + a variance/stdev term + `ms`
units + ≥5 numeric figures — without assuming answer layout.

**Re-grade, not re-run.** The agents' answers are frozen evidence in the
transcripts; only the grader was wrong. A new `bench regrade` subcommand
re-applies the corrected pattern to the stored transcripts and updates
`meta.json` (recording `regraded_from` + `regraded_utc`); timed-out runs are
never promoted. Re-running on-device was rejected as less defensible (it would
re-roll answers). A full-grid `regrade --dry-run` audit confirmed **only b7**
cells were affected — every other answer-task's recorded verdicts were already
correct. (Device-state tasks a2/a3 verify against the live device and cannot be
re-graded offline; both were 5/5 at run time.)

**Effect on b7:** linc 5/5, maestro 2/5, mobile-mcp 1/5 (was 0/0/0). The fix
was defined from the task's stated intent, not to make any tool pass; the human
transcript eyeball-audit for fabrication (per the task notes) still applies.

## 2026-07-10 — c10 verify tightened (too loose) + b6 false-positive adjudicated

Two reasoning-task verifies were found unreliable in the *opposite* direction
from b7 (which was too strict) — they matched a substring without checking the
answer's actual claim. Caught by a false-positive sweep (PASS answers containing
hedging/dismissal language near the matched token).

- **c10 (runtime value).** Pattern `0[.,]755` false-PASSED answers that gave
  0.755 only as the low end of a UI back-division RANGE while explicitly
  disclaiming they couldn't obtain the value (maestro: *"range from about 0.755
  to 0.770 — I can't pin it down from UI alone; I'd need a debugger"*). Tightened
  to `0[.,]755(?!\s*(?:[-–—]|to\b|and\b|\.\.)\s*\d)` (reject 0.755 immediately
  followed by a range separator + number). Re-graded: maestro/c10 run-1,2
  PASS→FAIL. linc stays a genuine 0/5 (see spectra finding below).

- **b6 (flaky behavior).** The pattern matched the substring "launch-count" even
  inside a *dismissal*. maestro/b6/run-5 concluded the flake was a
  "non-deterministic sync status check" and wrote *"isn't a simple ...
  launch-count alternation, which rules out a simple persisted counter"* — the
  opposite of the correct cause — yet PASSED. Per the task's pre-registered
  eyeball-audit, this cell is manually adjudicated PASS→FAIL (recorded in its
  meta as `adjudicated_from`/`adjudication`). maestro/b6: 1/5 → 0/5. All five
  linc/b6 PASSes were re-read and correctly attribute the flake to the persisted
  launchCount%5 cause — genuine, unchanged.

**c10 finding (headline).** linc scored 0/5 on the task spectra exists for. The
agent found and repeatedly invoked spectra (`spectra_attach`/`spectra_breakpoint`
2–7×/run, no crashes) but could never read `discountFactor`: spectra attaches to
the process but its source-level breakpoint workflow needs the project registered
(the agent repeatedly cited needing Forge/`.forge.yaml` registration or a
debuggable-and-registered reinstall) — and Forge is retired. So the stack's
runtime-debugging differentiator did not deliver on an unregistered app under the
confined harness. Filed as an improvement; a strong v2 target.

**Systemic note.** Three of the checked verifies were flawed (b7 too strict, c10
& b6 too loose). Regex answer-grading cannot distinguish "affirms X" from
"mentions/dismisses X" for reasoning tasks. v2 should replace these with an
LLM-judge (or per-task match/reject CI tests, improvement 8881e5a3) and treat the
regex as a first-pass screen only.
