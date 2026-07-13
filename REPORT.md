# mobile-agent-bench — combined report (v1 + v2)

**Question:** driving an identical confined `claude-sonnet-5` agent, how do four
mobile-agent tool surfaces compare on a real Android app + Wear OS watch?

**Contestants (tool-under-test = the *only* capability the agent has):**
linc (nerve + crucible + spectra) · maestro · mobile-mcp · agent-device.

**Fixtures & method:** BenchTarget (Jetpack Compose) on a Pixel 8 Pro; Pixel
Watch 2 for b8. 10 tasks × 5 runs × 4 tools = 200 cells per grid. This report
covers **two complete grids**: **v1** (frozen at tag `v1-prereg`, published
with linc losing its marquee task) and **v2** (a full re-run under a fresh
pre-registration frozen at tag `v2-prereg`, after the v1-identified defects
were fixed). Prompts and verify patterns were **byte-identical** between the
grids. Every deviation from either pre-registration is recorded with receipts
in [`AMENDMENTS.md`](AMENDMENTS.md). v1 results remain published as v1; v2
does not overwrite them.

---

## Disclosure — read this before the numbers

**This benchmark is authored by the people who build one of the contestants.**
The harness, the tasks, the target app, and this report were written by LINC
Innovations, the vendor of the `linc` stack (nerve/crucible/spectra). It is a
vendor-authored benchmark that names competitors, and the v1→v2 improvement
documented below was produced by the same vendor fixing its own tool between
runs. You should apply the skepticism that setup deserves.

What makes the result checkable rather than merely asserted:

1. **Pre-registration.** Each grid was frozen before any comparative cell ran
   ([`PREREGISTRATION.md`](PREREGISTRATION.md),
   [`PREREGISTRATION-v2.md`](PREREGISTRATION-v2.md)) — tasks, prompts, verify
   patterns, model, devices, budgets, and (in v2) the exact stack SHAs. Any
   later change is an amendment in [`AMENDMENTS.md`](AMENDMENTS.md) and voids
   every row it touches. Nothing is quietly edited.
2. **Published losses.** v1 shipped with linc scoring 0/5 on c10 — the one
   task its debugger uniquely exists for — the least efficient column on the
   grid (7 timeouts), and a falsified pre-registered expectation (b8 was
   predicted linc-exclusive; all four tools passed it). Those numbers are
   still published and are reproduced below.
3. **Disclosed interference — including in the vendor's favor and against
   it.** v1 recorded three confinement errata; v2 caught four interference
   classes before publication, one of which voided a cell that had *passed*.
   See the integrity ledger.
4. **Everything is re-runnable.** The harness, task files, target-app source,
   adapters, and sanitized transcripts are published. Every figure in this
   report traces to a stored raw run log.

The strongest criticism of v2 is stated plainly in
[Limitations](#limitations--threats-to-validity): the vendor fixed defects on
tasks it had already seen, and competitors were not offered the same
remediation cycle.

---

## TL;DR

- **The arc:** v1 published linc as *most capable, least efficient, and 0/5 on
  its marquee task* (c10 runtime inspection — 0/5 for every tool). The two
  root causes were filed as P0 improvements, fixed, pinned, and the identical
  200-cell grid re-ran under a fresh pre-registration.
- **v2 completion (45 scored cells/tool):** **linc 44/45 (98%)** ·
  agent-device 32/45 (71%) · mobile-mcp 28/45 (62%) · maestro 20/45 (44%).
  v1 was linc 73% · agent-device 71% · maestro 58% · mobile-mcp 56%.
- **v1's central caveat is void.** linc went from 198s median / 39 turns /
  7 timeouts to **138s / 26 turns / 0 timeouts** — most capable *and* fastest.
  The mechanism is a single fix: nerve's UI-element blindness.
- **c10 flipped from 0/0/0/0 to 5/0/0/0.** linc reads the runtime
  `discountFactor` at a zero-config method breakpoint, 5/5 at a 122s median;
  every competitor still scores 0/5.
- **Competitors keep real wins:** mobile-mcp is the cheapest per uncached
  token (29.6k median) and jumped c9 from 0/5 to 5/5; maestro's c9 ship-gate
  judgment (4/5) held; agent-device matched linc on b5 and b7 (5/5 each).
- **The honest caveat:** the fixes that produced the v2 delta were aimed at
  tasks the vendor had already seen fail. The tasks and prompts were frozen
  and byte-identical — but linc's engineers knew what was on the test.
  Weight the delta accordingly (see Limitations).

---

## Scoreboard

### v2 (adjudicated; 45 scored cells per tool, b8 excluded)

| task | linc | maestro | mobile-mcp | agent-device |
|------|------|---------|------------|--------------|
| a1–a3 | 15/15 | 15/15 | 15/15 | 15/15 |
| a4 | **5/5** | 0/5 | **5/5** | 3/5 |
| b5 | **5/5** | 0/5 | 3/5 | **5/5** |
| b6 | **4/5** | 0/5 | 0/5 | 4/5 |
| b7 | **5/5** | 1/5 | 0/5 | **5/5** |
| c9 | **5/5** | 4/5 | **5/5** | 0/5 |
| c10 | **5/5** | 0/5 | 0/5 | 0/5 |
| **TOTAL** | **44/45 (98%)** | 20/45 (44%) | 28/45 (62%) | 32/45 (71%) |
| b8 (capability row) | 5/5 | 2/5 | 5/5 | 4/5 |

*b8 = Wear OS capability row; reported separately, never averaged (pre-reg).*

linc's single miss is b6 run-5 — an honest analytic near-miss: the agent
concluded a sync-state mechanism rather than the persisted launch counter, and
was adjudicated FAIL against the transcript.

### v1 → v2 delta (same tasks, same prompts, same devices, same model)

| | linc | maestro | mobile-mcp | agent-device |
|---|------|---------|------------|--------------|
| v1 completion | 73% | 58% | 56% | 71% |
| v2 completion | **98%** | 44% | 62% | 71% |
| notable flips | b5 1/5→5/5 · c9 2/5→5/5 · c10 0/5→5/5 | a4 5/5→0/5 (device disambiguation) · b7 2/5→1/5 | c9 0/5→5/5 · b5 5/5→3/5 | c9 stays 0/5 · a4 5/5→3/5 |

Task descriptions: a1 launch-navigate-assert · a2 form-fill-submit · a3
scroll-to-item-tap · a4 screenshot-describe · b5 crash-repro-evidence · b6
flaky-behavior-investigation · b7 coldstart-timing-variance · b8
wearos-launch-interact (capability row) · c9 seeded-defect-ship-gate · c10
runtime-state-inspection. Task files: [`tasks/`](tasks/).

## Efficiency (v2, medians over scored cells)

| tool | med wall | med uncached tok | med turns | med $/task | timeouts | solved-unfinalized |
|------|----------|------------------|-----------|------------|----------|--------------------|
| linc | **138s** | 41.3k | **26** | $0.57 | **0** | 0 |
| maestro | 145s | 42.5k | 25 | $0.47 | 1 | 0 |
| mobile-mcp | 172s | **29.6k** | 40 | $0.46 | 1 | 0 |
| agent-device | 161s | 82.6k | 40 | $1.08 | 2 | 1 |

v1, for contrast: linc 198s / 65.2k / 39 turns / $0.64 / **7 timeouts** ·
agent-device 233s / 77.9k / 62 turns / $1.19 / 3 · maestro 103s / 45.2k / 17
turns / $0.45 / 1 · mobile-mcp 117s / 29.2k / 28 turns / $0.49 / 1.

**v1's verdict — "linc is the most capable and the least efficient" — is now
void, and the mechanism is known.** In v1, nerve returned an empty UI-element
tree on every linc run (`element_count: 0`, while competitors extracted a
populated tree 10/10 on the identical device+app), forcing the agent into
screenshot-only vision. That tax produced the 2× wall time, the turn count,
and the 7 timeouts — 5 of which *already contained the full ground-truth
answer in-transcript* (solved, but out of budget). With element extraction
fixed (nerve #105), that vision-scrolling waste became completed work: 0
timeouts, fewest turns, fastest median wall. mobile-mcp remains the cheapest
column per uncached token. agent-device is the most expensive on every token
axis ($1.08, 82.6k uncached) and carries the grid's only solved-but-unfinalized
run (b6 — it found the launch counter and hit the budget).

Grid spend: v1 **$216** (200 cells); v2 **$209.02** (200 cells; 4 cells lack
cost data in meta and are excluded from the median-cost column — n=43–45 per
tool).

## What changed between the grids

Everything below landed **before** the `v2-prereg` freeze and is pinned there.
Prompts and verify patterns were byte-identical to v1; **no verify pattern
changed for v2** (task files gained only the `app.apk` digest pin and frozen
grader samples).

**The two LINC-stack P0 fixes (the vendor fixing its own tool — see
Disclosure and Limitations):**

- **nerve `783fc88`** — #105 typed UI-dump failures + self-heal of leaked
  UiAutomation holders (the v1 element blindness: a failed `uiautomator dump`
  was silently converted into an empty tree; the environmental trigger was a
  leaked competitor driver holding the device's single UiAutomation
  connection, but a robust tool must surface or heal that conflict, so the v1
  verdicts stood); #107 `ensure_ready` leaked-UiAutomation gate.
- **spectra `badcee7`** — #35 runtime inspection end-to-end: PID discovery,
  adapter discovery, attach handshake, and **zero-config method breakpoints**
  (v1's c10 failure: source-level breakpoints required Forge project
  registration, and Forge is retired); #37 jdb exception catchpoints + honest
  breakpoint warnings.
- crucible `a717296` — tool-description improvements only; no grid-surfaced
  defect was found in crucible.

The linc column ran from dedicated pin worktrees at those SHAs for the entire
grid. Competitors ran in their vendor-recommended configuration, exactly as in
v1, with installed versions recorded per run.

**Harness-integrity hardening (applied identically to every tool):**

1. **Per-cell UiAutomation hygiene** — known holder drivers force-stopped
   before every cell, logged to meta (closes the v1 cross-tool contamination
   vector; also removes the pre-warmed-helper advantage agent-device's own
   leftovers previously conferred).
2. **Per-task APK digest pinning** — installed `base.apk` md5 verified against
   the repo-built artifact before every cell; reinstall on mismatch. This
   silently healed the stock/seeded flavor swap 20 times across c9/c10 with
   zero wrong-variant cells.
3. **Grader sample validation** — every answer pattern carries frozen
   `match_samples`/`reject_samples` validated at load time through the same
   predicate that grades runs; the three v1 grader flaws are frozen as
   regression samples.
4. **Serial sanitizer covers enumerated serials**, not just the configured
   bench serial.
5. **Token medians at full granularity** — billed / uncached / output broken
   out per cell.
6. **Solved-but-unfinalized flag** — a timed-out run whose verification would
   have passed is mechanically flagged as a separate diagnostic column, never
   counted toward completion (pre-registered; motivated by v1's 5-of-7
   solved-then-timed-out linc cells).

Budget unchanged: 900s (600s for a1–a4); a timeout remains FAIL for every
scored metric.

## Findings

### c10 — the marquee flip (0/0/0/0 → 5/0/0/0)

v1: no tool could read the runtime `discountFactor` (0.755) from the running
process; linc invoked spectra hard (up to 19 attaches per run) and still
couldn't, because source breakpoints required a retired registration system.
That 0/5 was published as a loss with the root cause filed.

v2: linc 5/5 at a **122s median**. The transcripts show the same shape every
run: drive the UI to the exact state, arm `spectra_method_breakpoint` on
`CheckoutViewModel.applyDiscount` by name (zero-config, no source
registration), trigger the interaction, read locals, detach cleanly
(`spectra_sessions` → 0). Every competitor: 0/5. agent-device's transcripts
conclude the value is unreachable ("no observation tool exists to read that
internal variable"). maestro and mobile-mcp back-divide the rounded UI total
and land on ~0.76 or a hedged range that the amended grader correctly rejects
(a bare `0.755` inside a disclaimed range is not an obtained value — see the
2026-07-10 amendment). c10 is the task the LINC stack was built for; in v2 it
is the only column that completes it.

### c9 — ship-gate (linc 2/5 → 5/5; mobile-mcp 0/5 → 5/5)

linc's v1 c9 losses were timeout conversions — the tier defect was localized
in-transcript but the vision-scrolling tax exhausted the budget. With elements
readable it finishes 5/5 at a 590s median. mobile-mcp's jump to 5/5 is its
own: element tree plus methodical screen-by-screen sweeps found both the
export crash and the tier-propagation bug reliably. maestro repeats its v1
strength (4/5 — sound ship/no-ship judgment once it can see the state).
agent-device's 0/5 is task-shaped rather than mechanical: its verdicts fixate
on Wear-class concerns and secondary defects without localizing the
tier-propagation bug the gate is scored on.

### Tier B — device observability still decides it

- **b6 (flake root-cause; ground truth is a persisted launch counter):** linc
  4/5 and agent-device 4/5 (+1 solved-unfinalized — it found the counter and
  died at the budget). maestro and mobile-mcp: 0/10 combined — both concluded
  "conditional sync-state / timing" because neither surface reads logcat or
  app state deeply enough to find the counter. The failure text is nearly
  identical in both columns.
- **b7 (cold-start timing + variance):** linc and agent-device 5/5. mobile-mcp
  0/5 — no shell surface for `am start -W`, so its agent asks permission to
  estimate instead of measuring. maestro 1/5 — it measures a UI-visible proxy
  with polling overhead.
- **b5 (crash repro from a vague report):** linc 1/5 → **5/5** — v1's
  200-turn element-blind list hunts are gone. agent-device stays strong (5/5,
  as in v1). mobile-mcp regressed 5/5 → 3/5. maestro 0/5 — it cannot reach
  the crash evidence without a log surface (its v1 3/5 here was a
  shell-escape artifact, corrected in erratum #3; see the integrity ledger).

### a4 — an accidental (and kept) finding: device disambiguation

Because the b8 column ran first, the watch legitimately carries BenchTarget,
so "launch BenchTarget and describe its first screen" now requires knowing
*which* device you're driving. linc and mobile-mcp: 5/5. maestro: 0/5 — its
driver defaults to the first adb device (the watch) and its agent described
the watch's Ping screen in every run. agent-device: 3/5 — two runs did the
same. The condition was identical for every tool and is disclosed; it stays as
a real-world multi-device finding rather than an amendment.

### b8 — Wear OS capability row (reported separately, never averaged)

linc 5/5 at 40.6s median (fastest, tightest variance) · mobile-mcp 5/5 ·
agent-device 4/5 (interaction completed, but the run never quoted the frozen
counter text) · maestro 2/5 (driver connection/targeting struggles in the
multi-device environment). v1's corrected expectation holds: Wear interaction
is **not** linc-exclusive — the original pre-registered claim that it was is
falsified and stays falsified. linc is the only column that scores 5/5 at the
fastest median wall time on the row.

## Integrity ledger

Fairness cuts both ways in this section: interference was found that hurt the
vendor's column, that hurt competitors' columns, and — in one case — that
coincided with a cell *passing*. All of it was voided or disclosed before
publication. Full entries with receipts: [`AMENDMENTS.md`](AMENDMENTS.md).

### v1 — three confinement errata (all remediated before publication)

1. **nerve pin.** The pre-registration hadn't pinned the linc stack's SHA; two
   nerve commits landed mid-grid. The remaining cells were run against nerve
   pinned to the SHA the early cells used (`bb02ff1`), keeping all 200 cells
   uniform; the improvements were deferred to v2 so the delta could be
   published cleanly instead of moving the target mid-measurement.
2. **Read-of-source hole.** A path-unrestricted `Read` let one maestro run
   guess the target-app source path and compute the answer from the formula —
   a genuine ground-truth leak. The cell was voided, a PreToolUse Read-guard
   (denying source paths, allowing screenshots/tool logs) was added, and the
   whole c10 row re-ran under it. Notably, a linc run guessed *wrong* paths
   and obtained nothing — its 0/5 was genuine.
3. **Monitor shell-escape.** The built-in `Monitor` tool ran arbitrary shell,
   letting confined agents bypass the tool-under-test with raw `adb` and even
   `jdb`. Blast radius was measured per-transcript, not assumed: 8 of 120
   completed cells had used the escape; they were voided and re-run under the
   closed confinement, and the 112 zero-shell cells were positively certified
   clean. The re-run corrected maestro's numbers specifically: **b5 3/5 →
   0/5** (its flake detection had been entirely raw `adb logcat`), **c10's
   sole pass → 0/5** (a raw-`jdb` breakpoint read), mobile-mcp b7 1/5 → 0/5.
   linc's b7 5/5 was unchanged — its timing came from nerve's structured
   surface all along. Every published v1 cell is verified `Monitor=0`.

v1 also disclosed, post-grid, the **cross-tool UiAutomation contamination
vector**: a leaked competitor driver held the device's single UiAutomation
connection, which is what starved nerve's element dumps. The v1 verdicts stood
anyway — nerve silently swallowing the failure was a genuine tool defect —
but the finding produced both the nerve fix and the v2 per-cell hygiene step.

### v2 — four interference classes, all caught and voided pre-publication

None reached a published row. Per-cell receipts (hygiene log, APK digest pin,
solved-unfinalized flag, meta provenance) made every one mechanically
detectable.

1. **Operator reservation (hurt linc only).** The grid operator had reserved
   the bench phone in `nerve_pool` to shield the grid — and the linc column's
   own nerve honors that same reservation ledger, so every linc agent refused
   to drive a device it saw as held by another session. 31 false-start cells
   voided (competitors' passing cells voided too, so every published row runs
   under identical conditions). The same false start also had two
   non-benchmark Samsung devices attached, which burned maestro's budgets on
   enumeration; they were physically unplugged before relaunch.
2. **Orphaned UiAutomation holder (zeroed maestro's column).** An anonymous
   shell-uid `app_process` — agent-device's snapshot helper, orphaned when the
   false-start grid was killed mid-cell — held a UiAutomation registration
   that blocked every subsequent registration while passive dumps kept
   working. Every relaunched maestro cell failed fast; 24 cells voided as
   environmental, not tool behavior. Hygiene now kills the holder class
   (including anonymous shell-uid orphans by pid) before every cell, for
   every tool.
3. **Interactive BVT stole the foreground mid-cell.** An unrelated session's
   device test drove the bench phone for ~3 minutes during c9. Exactly one
   cell overlapped: maestro/c9/run-4 — **it had PASSED**, and was voided and
   re-run anyway per the no-foreground-contamination standard. The published
   run-4 is the clean re-run. Logcat receipts preserved; neighboring cells
   verified clean by timestamp.
4. **Secure-lock window.** The personal device's PIN re-engaged for ~20
   minutes as the phone was picked up before a pause; the close-out transcript
   audit found four consecutive b5 cells (one per tool) that hit the locked
   device. Per the pre-declared keep-PIN amendment these are no-rows — a
   locked screen blinds every tool identically — and all four were re-run
   unlocked. Two other lock-language hits were adjudicated and stand
   (documented per-cell in the amendment).

## Per-cell detail (harness `bench report` output, `BENCH_RESULTS_DIR=results_v2`)

| tool | task | tier | runs | pass | solved-unfin | median wall s | median billed | median uncached | median output | wall stdev |
|---|---|---|---|---|---|---|---|---|---|---|
| agent-device | a1 | A | 5 | 5/5 | 0 | 64.8 | 830,908 | 50,829 | 2,346 | 70.0 |
| agent-device | a2 | A | 5 | 5/5 | 0 | 132.6 | 1,965,504 | 87,937 | 4,693 | 17.5 |
| agent-device | a3 | A | 5 | 5/5 | 0 | 164.0 | 1,660,186 | 69,766 | 5,556 | 65.7 |
| agent-device | a4 | A | 5 | 3/5 | 0 | 27.6 | 167,393 | 14,416 | 1,135 | 3.2 |
| agent-device | b5 | B | 5 | 5/5 | 0 | 674.5 | 10,004,661 | 178,836 | 27,037 | 157.0 |
| agent-device | b6 | B | 5 | 4/5 | 1 | 541.2 | 9,246,478 | 172,773 | 22,735 | 202.1 |
| agent-device | b7 | B | 5 | 5/5 | 0 | 136.1 | 610,491 | 30,582 | 4,610 | 47.6 |
| agent-device | b8 (capability row) | B | 5 | 4/5 | 0 | 100.1 | 735,834 | 22,361 | 4,115 | 33.6 |
| agent-device | c9 | C | 5 | 0/5 | 0 | 355.2 | 3,002,126 | 81,056 | 14,521 | 144.1 |
| agent-device | c10 | C | 5 | 0/5 | 0 | 226.6 | 2,310,014 | 83,840 | 5,904 | 326.2 |
| linc | a1 | A | 5 | 5/5 | 0 | 123.6 | 816,642 | 38,515 | 5,573 | 39.6 |
| linc | a2 | A | 5 | 5/5 | 0 | 138.7 | 1,041,567 | 39,123 | 5,552 | 61.8 |
| linc | a3 | A | 5 | 5/5 | 0 | 88.4 | 712,935 | 30,103 | 3,893 | 24.7 |
| linc | a4 | A | 5 | 5/5 | 0 | 26.9 | 214,042 | 21,086 | 1,112 | 4.1 |
| linc | b5 | B | 5 | 5/5 | 0 | 494.3 | 6,624,239 | 120,198 | 17,198 | 75.6 |
| linc | b6 | B | 5 | 4/5 | 0 | 359.4 | 3,167,774 | 78,578 | 15,060 | 57.2 |
| linc | b7 | B | 5 | 5/5 | 0 | 134.4 | 920,412 | 41,315 | 6,116 | 31.0 |
| linc | b8 (capability row) | B | 5 | 5/5 | 0 | 40.6 | 330,473 | 19,491 | 1,451 | 7.1 |
| linc | c9 | C | 5 | 5/5 | 0 | 590.5 | 7,850,006 | 113,626 | 20,561 | 123.3 |
| linc | c10 | C | 5 | 5/5 | 0 | 122.2 | 731,092 | 25,274 | 4,029 | 25.0 |
| maestro | a1 | A | 5 | 5/5 | 0 | 127.6 | 752,373 | 38,937 | 4,643 | 26.1 |
| maestro | a2 | A | 5 | 5/5 | 0 | 237.6 | 1,546,835 | 81,273 | 7,739 | 103.4 |
| maestro | a3 | A | 5 | 5/5 | 0 | 144.6 | 585,476 | 36,681 | 4,565 | 41.4 |
| maestro | a4 | A | 5 | 0/5 | 0 | 31.9 | 119,775 | 9,964 | 774 | 1.6 |
| maestro | b5 | B | 5 | 0/5 | 0 | 709.6 | 3,833,941 | 124,833 | 24,840 | 106.3 |
| maestro | b6 | B | 5 | 0/5 | 0 | 353.4 | 1,866,124 | 81,226 | 12,846 | 38.7 |
| maestro | b7 | B | 5 | 1/5 | 0 | 48.6 | 119,518 | 21,847 | 3,089 | 90.3 |
| maestro | b8 (capability row) | B | 5 | 2/5 | 0 | 169.5 | 211,083 | 20,245 | 2,056 | 73.1 |
| maestro | c9 | C | 5 | 4/5 | 0 | 706.3 | 4,261,985 | 155,397 | 20,462 | 155.5 |
| maestro | c10 | C | 5 | 0/5 | 0 | 70.4 | 187,762 | 22,468 | 3,277 | 39.9 |
| mobile-mcp | a1 | A | 5 | 5/5 | 0 | 96.6 | 424,761 | 17,549 | 4,304 | 17.0 |
| mobile-mcp | a2 | A | 5 | 5/5 | 0 | 194.9 | 1,245,513 | 37,577 | 7,305 | 32.2 |
| mobile-mcp | a3 | A | 5 | 5/5 | 0 | 166.9 | 837,709 | 22,135 | 6,164 | 81.8 |
| mobile-mcp | a4 | A | 5 | 5/5 | 0 | 24.1 | 112,322 | 5,267 | 717 | 3.5 |
| mobile-mcp | b5 | B | 5 | 3/5 | 0 | 536.4 | 8,128,952 | 158,730 | 14,393 | 292.1 |
| mobile-mcp | b6 | B | 5 | 0/5 | 0 | 237.0 | 1,175,413 | 37,935 | 10,729 | 82.1 |
| mobile-mcp | b7 | B | 5 | 0/5 | 0 | 75.0 | 202,765 | 20,772 | 5,284 | 72.9 |
| mobile-mcp | b8 (capability row) | B | 5 | 5/5 | 0 | 74.1 | 418,731 | 13,882 | 2,779 | 6.1 |
| mobile-mcp | c9 | C | 5 | 5/5 | 0 | 843.7 | 12,387,902 | 139,129 | 28,586 | 140.8 |
| mobile-mcp | c10 | C | 5 | 0/5 | 0 | 107.0 | 388,628 | 18,373 | 4,810 | 16.5 |

The "median billed" column is cache-inflated (cache reads compound with
turns × context) and misleading as an efficiency signal; **"median uncached"
is the real signal**, as in v1. The v1 per-cell table remains in the v1
report (git history) and its analysis in
[`docs/v1-deep-dive.md`](docs/v1-deep-dive.md); v2 analysis in
[`docs/v2-deep-dive.md`](docs/v2-deep-dive.md).

## Limitations / threats to validity

Carried forward from v1, all still true:

- **Single model, single app, single device pair.** One Compose app on one
  Pixel 8 Pro (+ one Pixel Watch 2), one model (`claude-sonnet-5`).
  Generalization to other apps, UI toolkits, OEMs, and models is unproven.
- **Regex answer-grading** cannot distinguish "affirms X" from "mentions X"
  for reasoning tasks. v2 added frozen match/reject samples validated at load
  time and kept eyeball adjudication as the backstop for c-tier and b6, but
  the planned LLM-judge does not exist yet.
- **Fixed 900s budget.** Unchanged from v1 for comparability. v2's
  solved-but-unfinalized flag makes the timeout-conversion failure mode
  visible for every tool identically, but a timeout is still a scored FAIL.
- **Confinement is a model of real usage, not real usage.** A real operator
  usually has a shell; this benchmark deliberately measures the *structured
  tool surface* alone.

New, v2-specific, and the most important one:

- **The vendor fixed defects on tasks it had already seen — competitors got
  no remediation cycle.** The v1→v2 linc delta (73% → 98%, 7 timeouts → 0,
  c10 0/5 → 5/5) was produced by LINC engineers who had read every v1
  transcript, targeting exactly the failures this grid measures. The tasks
  and prompts were byte-identical to v1 and frozen at `v2-prereg`, no verify
  pattern changed, and the fixes are general product changes shipped in the
  public tools rather than task-specific patches. But it is still,
  structurally, a take-home retest: maestro, mobile-mcp, and agent-device were run
  as-shipped both times, and their vendors were not invited to fix their v1
  failure modes first. Two things would remediate this: (a) an **independent
  re-run** of the published harness by someone with no stake in the result,
  and (b) a **v3 with new tasks the vendor has not seen**, graded under the
  same discipline. Until one of those exists, read the v2 delta as "the
  vendor can fix what this benchmark measures," not "the vendor
  generalizes."

## What's next (v3 candidates)

From [`docs/v2-deep-dive.md`](docs/v2-deep-dive.md), in priority order:

1. **In-harness lock detection** — record `dumpsys trust` per cell in meta and
   auto-void no-rows, replacing post-hoc transcript audits.
2. **Reservation owner-passthrough** (nerve) + crucible reservation checks —
   make grid protection structural rather than procedural.
3. **nerve forward-leak fix + payload trimming** — linc's 41.3k uncached
   median can close on mobile-mcp's 29.6k.
4. **Multi-device as a first-class dimension** — a4/b8 showed device
   disambiguation separates the field; a deliberate 3-device tier is worth
   pre-registering.
5. **More b6-class depth tasks** — the observability gap (logcat / app-state
   reach) produces the largest and most consistent separation between the
   columns, and is currently sampled by a single task.
6. **Unseen tasks and/or an independent re-run** — the validity remediation
   named in Limitations; arguably the highest-value item on this list.

## CEO publish gate

- [x] v1: all 200 cells complete, every published cell `Monitor=0`; errata
  #1–3 documented and remediated; contaminated cells voided/re-run
- [x] v2: all 200 cells complete under the `v2-prereg` freeze (stack pins
  nerve `783fc88` / spectra `badcee7` / crucible `a717296`)
- [x] v2 integrity ledger disclosed — four interference classes caught and
  voided pre-publication (including one cell that had passed); per-cell
  hygiene/pin receipts in every published row's meta
- [x] Grader discipline: no verify pattern changed for v2; frozen
  match/reject samples validate at load; c-tier and b6 adjudications
  recorded per-cell
- [x] Vendor conflict and the v2-specific validity threat stated in the body,
  not a footnote
- [x] **CEO sign-off to publish externally** — granted 2026-07-13: publish v1
  and v2 together, as one document. The v1 loss is load-bearing evidence, not
  a preamble to the v2 result.
- [ ] Mechanics of publication (repo visibility, announcement) — tracked
  separately; this report is the artifact, not the act
- [ ] v3 gated on a fresh pre-registration (candidate list above)
