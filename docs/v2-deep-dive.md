# mobile-agent-bench v2 — deep-dive findings (complete grid)

_Scope: full pre-registered v2 grid (200/200 rows) — linc / maestro / mobile-mcp /
agent-device on a1–c10 + the b8 watch capability row, claude-sonnet-5, Pixel 8 Pro
+ Pixel Watch 2, protocol frozen at tag `v2-prereg` (stack pins: nerve `783fc88`,
spectra `badcee7`, crucible `a717296`). All amendments disclosed in AMENDMENTS.md;
every voided cell was caught and re-run before publication._

## Scoreboard (harness-verified, 45 scored cells/tool; b8 reported separately)

| task | linc | maestro | mobile-mcp | agent-device | note |
|------|------|---------|------------|--------------|------|
| a1–a3 | 15/15 | 15/15 | 15/15 | 15/15 | pure UI — table stakes for everyone |
| a4 | **5/5** | 0/5 | **5/5** | 3/5 | became a device-disambiguation test (see below) |
| b5 | **5/5** | 0/5 | 3/5 | **5/5** | crash-repro (v1: linc 1/5) |
| b6 | **4/5** | 0/5 | 0/5 | 4/5 | flake root-cause — launch-counter ground truth |
| b7 | **5/5** | 1/5 | 0/5 | **5/5** | cold-start timing + variance |
| c9 | **5/5** | 4/5 | **5/5** | 0/5 | seeded ship-gate (v1: linc 2/5) |
| c10 | **5/5** | 0/5 | 0/5 | 0/5 | **runtime inspection — linc exclusive** |
| **total** | **44/45 (98%)** | 20/45 (44%) | 28/45 (62%) | 32/45 (71%) | v1: 73 / 58 / 56 / 71 % |
| b8 (cap row) | 5/5 | 2/5 | 5/5 | 4/5 | watch; reported separately, never averaged |

linc's sole miss: b6 run-5, an honest analytic near-miss (concluded a sync-state
mechanism instead of the launch counter; adjudicated against the transcript).

## Efficiency (medians over scored cells)

| tool | wall | uncached tok | turns | cost | timeouts | solved-unfin |
|------|------|--------------|-------|------|----------|--------------|
| linc | **138s** | 41.3k | **26** | $0.57 | **0** | 0 |
| maestro | 145s | 42.5k | 25 | $0.47 | 1 | 0 |
| mobile-mcp | 172s | **29.6k** | 40 | $0.46 | 1 | 0 |
| agent-device | 161s | 82.6k | 40 | $1.08 | 2 | 1 |

**v1's central caveat is gone.** v1 linc was "most capable, least efficient" — 198s
median (~2× competitors), 39 turns, 7 timeouts, $0.64. v2 linc is most capable AND
fastest, with the fewest turns and **zero timeouts** (was 7). The nerve
element-extraction fix (#105) converted v1's vision-scrolling waste directly into
completed work, exactly as the v1 deep-dive predicted. mobile-mcp remains the
cheapest per token; agent-device's token-saving headline claim inverts here — it is
the most expensive column on every token axis ($1.08, 82.6k uncached, 2 timeouts).

## c10 — the marquee flip (0/0/0/0 → 5/0/0/0)

v1: no tool could read `discountFactor` (0.755) from the running process. v2: linc
5/5 at a **122s median** — the agent drives the UI to the exact state, arms
`spectra_method_breakpoint` on `CheckoutViewModel.applyDiscount` by name
(zero-config, no source registration), triggers the interaction, and harvests
locals (transcripts also show clean detach hygiene, `spectra_sessions` → 0).
Every competitor: 0/5 — agent-device's transcripts conclude the value is
unreachable ("no observation tool exists to read that internal variable");
maestro/mobile-mcp back-divide the rounded UI total and land on ~0.76 or a hedged
range the amended grader correctly rejects. This is the row the LINC stack
uniquely exists for, and it is now uniquely linc's.

## c9 — ship-gate (linc 2/5 → 5/5)

linc's v1 losses here were timeout conversions (solved in-transcript, budget
exhausted); with the element fix it finishes at 590s median and localizes the tier
defect 5/5. mobile-mcp jumped 0/5 → 5/5 — its element tree plus methodical
screen-by-screen sweeps found the export crash AND the tier bug reliably this
time. agent-device 0/5 is task-shaped: its verdicts fixate on Wear-class concerns
and secondary defects without localizing the tier-propagation bug the gate is
scored on. maestro 4/5 repeats its v1 strength (good judgment once it can see).

## Tier B — device observability still decides it

- **b6 (flake root-cause):** the ground truth is a persisted launch counter.
  linc 4/5 and agent-device 4/5 (+1 solved-unfinalized — it found the counter and
  died at the budget); maestro and mobile-mcp 0/10 combined — both concluded
  "conditional sync-state UI / timing" because neither can read logcat or app
  state deeply enough to find the counter. Same failure text in both columns.
- **b7 (cold-start discipline):** linc and agent-device 5/5. mobile-mcp 0/5 — no
  shell surface for `am start -W`, so it asks permission to estimate instead of
  measuring. maestro 1/5 — measures a UI-visible proxy with polling overhead.
- **b5 (crash repro):** linc 1/5 → **5/5** — the v1 element-blindness tax
  (200-turn list hunts) is gone. agent-device stays strong (5/5); mobile-mcp
  regressed 5/5 → 3/5; maestro 0/5 (cannot reach the crash evidence).

## a4 — an accidental (and kept) finding: device disambiguation

Because the b8 column ran first, the watch legitimately carries BenchTarget, so
"launch BenchTarget and describe its first screen" now requires knowing WHICH
device you're driving. linc and mobile-mcp: 5/5. maestro: 0/5 — its driver
defaults to the first adb device (the watch) and its agent described the watch's
Ping screen in every run. agent-device: 3/5 — two runs did the same
("locked by an existing session named 'watch'" → described the watch). The
condition was identical for every tool and is disclosed; it stays as a real-world
multi-device finding rather than an amendment.

## b8 (watch capability row)

linc 5/5 @ 40.6s (fastest, tightest variance) · mobile-mcp 5/5 · agent-device 4/5
(interaction done, never quoted the frozen counter text) · maestro 2/5 (driver
connection/targeting struggles in the multi-device environment). v1's corrected
expectation holds: Wear interaction is not linc-exclusive, but linc is the only
stack that is both perfect and fast on it.

## Integrity ledger (what the wave-2 harness work caught)

Four interference classes were caught, voided pre-publication, and disclosed —
none reached a published row:

1. **Operator reservation** blocked the linc column only (its own nerve honors
   the `nerve_pool` ledger) — 31 false-start cells voided; nightly neutralized
   via launchctl instead.
2. **Orphaned UiAutomation registration** (agent-device helper surviving a
   mid-cell abort as an anonymous shell-uid `app_process`) zeroed maestro's
   relaunched column — 24 cells voided; hygiene now kills the holder class
   before every cell (#14).
3. **Interactive BVT** stole the foreground mid-cell — exactly one cell voided
   (it had PASSED; fairness cuts both ways), logcat receipts preserved.
4. **Secure-lock window** (personal-device PIN re-engaged as the phone was
   picked up) — four b5 cells voided as no-rows per the keep-PIN amendment and
   re-run; the transcript-level lock audit that found them is now part of
   close-out.

Per-cell receipts (hygiene log, APK digest pin, solved-unfinalized flag) made
every one of these mechanically detectable. The digest pin also silently healed
the stock/seeded flavor swap 20 times across c9/c10 without a single wrong-variant
cell.

## Lessons learned (operational)

- **Never reserve the bench device during a grid** — the stack-under-test honors
  the same reservation ledger. Grid protection is procedural (neutralize cron,
  no interactive device sessions) until nerve grows owner-passthrough
  (improvement `bbb8d0b6`).
- **After any grid abort, sweep before diagnosing**: purge the in-flight cell
  (unsanitized transcript), kill shell-uid `app_process` orphans, clear adb
  forwards. An orphaned UiAutomation registration fails asymmetrically (dumps
  work, registrations die) and masquerades as one tool's weakness.
- **Audit transcripts for environment encounters at close-out** — the lock-window
  cells were found by grepping transcripts for keyguard/PIN language, not by any
  harness signal. v3 should detect `deviceLocked` in-harness per cell.
- **nerve leaks adb port forwards** per streaming session (improvement
  `29d723d7`, high) — ~230 stale forwards accumulated in one night.

## v3 candidates (priority order)

1. **In-harness lock detection** — record `dumpsys trust` per cell in meta;
   auto-void no-rows instead of post-hoc transcript audits.
2. **Reservation owner-passthrough** (nerve) + crucible reservation checks
   (`bbb8d0b6`) — make grid protection structural, not procedural.
3. **nerve forward-leak fix** (`29d723d7`) and payload trimming (the token-
   efficiency improvement filed at wave 1) — linc's uncached median (41k) can
   close on mobile-mcp's 29.6k.
4. **Multi-device as a first-class dimension** — a4/b8 showed device
   disambiguation separates the field; the bench's standing S24 makes a
   deliberate 3-device tier worth pre-registering.
5. **b6-class depth tasks** — the observability gap (logcat/app-state reach) is
   the widest durable moat; more tasks should probe it.
