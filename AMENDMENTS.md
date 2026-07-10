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
