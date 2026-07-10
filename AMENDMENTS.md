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
