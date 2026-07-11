# mobile-agent-bench v1 — deep-dive findings (partial: a1–c10, 3 tools)

_Scope: linc / maestro / mobile-mcp on the stock+seeded phone grid (a1–c10),
claude-sonnet-5, Pixel 8 Pro, under hardened confinement (post errata #1–3).
agent-device column and b8 (watch capability) pending. All cells verified
`Monitor=0` (no shell escape)._

## Scoreboard (adjudicated)

| task | linc | maestro | mobile-mcp | note |
|------|------|---------|------------|------|
| a1–a4 | 5/5 | 5/5 | 5/5 | pure UI interaction — everyone passes |
| b5 | 1/5 | 0/5 | **5/5** | crash-repro-from-vague-report |
| b6 | **5/5** | 0/5 | 0/5 | flaky-behavior root cause |
| b7 | **5/5** | 2/5 | 0/5 | cold-start timing + variance |
| c9 | 2/5 | **4/5** | 0/5 | seeded ship-gate (tier defect) |
| c10 | 0/5 | 0/5 | 0/5 | runtime `discountFactor` (needs debugger) |

Completion (45 cells/tool): **linc 73%**, maestro 58%, mobile-mcp 56%.

## Efficiency (the other axis)

| tool | med wall | med uncached tok | med turns | med cost | timeouts |
|------|----------|------------------|-----------|----------|----------|
| linc | 198s | 65k | 39 | $0.64 | **7** |
| maestro | 103s | 45k | 17 | $0.45 | 1 |
| mobile-mcp | 117s | 29k | 28 | $0.49 | 1 |

**linc is the most capable and the least efficient** — highest completion, but ~2×
wall time, most turns, most timeouts, highest $/task.

## Root cause: nerve is blind to Compose UI elements (improvement `8bba730a`, P0/v2-blocker)

`nerve_elements`/`nerve_state` returned `elements: [], element_count: 0` on the
BenchTarget (Jetpack Compose) app in **every** linc run across a1–a4,b5,b6,c9,c10
(max element_count across all linc transcripts = **0**). On the identical app,
**mobile-mcp 10/10 and maestro 10/10** extracted a populated element tree. This
isolates the defect to nerve: it does not surface the Compose semantics /
AccessibilityNodeInfo tree that the competitors read.

Consequence: linc's agent runs **screenshot-only vision** on every step. This is the
mechanism behind the entire efficiency gap:
- **A-tier tax:** even where linc passes 20/20, it uses **30 turns/135s** vs maestro
  **12 turns/82s** for the same taps.
- **Timeout conversion (the sharp finding):** **5 of linc's 7 timeouts already
  contained the full ground-truth answer in-transcript** (b5 run-1,2; c9 run-1,2,3)
  — the agent *solved* the task but exhausted the fixed 900s budget vision-scrolling
  before finalizing. b5 especially: finding "Item 013" in a list without an element
  tree took 200–245 turns; mobile-mcp reads the list directly and finishes → 5/5.

The 900s budget is pre-registered and fair (competitors finish inside it), so the
scored 73% stands. But the diagnostic shows linc's *true* capability is higher and
gated on efficiency, not understanding. A v2 with the element fix would plausibly
recover b5 (1→3/5) and c9 (2→5/5) purely from finishing in-budget.

## Where each tool genuinely wins

- **linc** — behavioral/diagnostic tier B (b6 flaky root-cause 5/5, b7 timing 5/5):
  device observability (logcat/metrics/inspect via structured MCP) is a real edge the
  others lack. Highest raw completion.
- **maestro** — fast, and best on the c9 ship-gate (4/5) reasoning; weak on tier B
  diagnostics (needs the device-log depth it doesn't expose). NB: its v1-contaminated
  b5 3/5 and c10 jdb-pass were a raw-adb/jdb shell escape (erratum #3), now 0/5.
- **mobile-mcp** — cheapest, aces b5 (5/5) via a clean element tree + logcat; thin
  elsewhere.

## c10 — nobody solved runtime inspection (spectra improvement `ab10e2d5`)

c10 = 0/0/0. It needs the running `discountFactor` (0.755), reachable only by a
debugger or APK decompile. linc invoked spectra hard (7–19 `spectra_attach`/run) but
could never read the value: spectra attaches but its source-level breakpoint workflow
needs the project registered (Forge/`.forge.yaml`) — and Forge is retired. The stack's
runtime-debug differentiator did not deliver on an unregistered app under confinement.
The one maestro "pass" was the erratum-#3 raw-`jdb` escape (voided).

## v2 targets (priority order)

1. **`8bba730a`** nerve Compose element extraction — highest leverage; would cut
   linc's turns/timeouts and likely flip b5/c9. Hard prerequisite for a fair v2.
2. **`ab10e2d5`** spectra attach-without-Forge-registration — unlocks c10, the task
   the stack uniquely exists for.
3. Consider (v2 pre-registration, not a mid-grid change): whether 900s is the right
   budget or whether to also report "solved-but-unfinalized" as a distinct outcome.
