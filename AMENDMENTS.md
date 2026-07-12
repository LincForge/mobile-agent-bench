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

## 2026-07-10 — ERRATUM #2: Read-of-source confinement hole (closed) + c9 pre-fix

**Read hole.** `Read` was allowed so tools could hand the agent screenshot
*paths* (in /tmp), but nothing restricted WHERE it read. No-search (no
Bash/Grep/Glob) blocked repo *discovery*, but a lucky absolute-path guess
defeated it. Blast radius across the whole grid (audited every non-sandbox Read):
- **maestro/c10/run-5** guessed the real path
  `…/mobile-agent-bench/target-app/…/CheckoutViewModel.kt`, read the source, and
  computed the frozen 0.755 from the formula — a genuine ground-truth leak. VOID.
- **linc/c10/run-5** guessed *wrong* paths (`/forge/BenchTarget/…`,
  `/lincforge/BenchTarget/…`) → reads failed → obtained nothing (0/5 genuine).
- Everything else was a tool reading its OWN logs/config (agent-device
  `.agent-device/…/app.log`, maestro `.maestro/*`) or `/dev/null` — not ground
  truth. **a1–b7 are clean.**

**Fix.** `agent.ensure_confinement()` writes a PreToolUse Read-guard hook into the
agent cwd (a separate process the agent can't disable). It denies Read of paths
matching `mobile-agent-bench|target-app|/src/(main|test)/|\.kt$|\.java$|SPEC\.md$`
while leaving screenshots (`.png` in /tmp) and tool logs readable — fair to every
tool. Validated end-to-end: a live confined agent's source Read was denied and it
refused to route around the guard. Unit-tested (`test_read_guard_*`).

**Action.** The entire c10 row was voided to `results_invalid/c10-erratum2/` and
is being re-run under the hook (so no c10 transcript carries even a leak
*attempt*). a1–b7 are NOT re-run: the hook is a no-op for cells that never
attempted a source read, and all of a1–b7 were audited clean — so their results
are identical with or without it.

## 2026-07-10 — c9 verify pre-fixed (before any c9 cell ran)

Pre-testing c9's pattern (the lesson from b7/c10/b6) found a latent false positive:
the alternation included bare `block`, which matched "**block**ing" inside a SHIP
verdict ("no blocking issues, SHIP" false-PASSED the ship-gate). Dropped bare
`block`/`not ready`; kept explicit DO-NOT-SHIP forms + no-go. No c9 cell had run,
so nothing was re-graded — a clean pre-emptive grader fix.

## 2026-07-10 — ERRATUM #3: Monitor shell-escape (confinement bypass) + affected rows re-run

**The hole.** `CONFINE_DISALLOWED_TOOLS` denied the shell/fs/web/subagent built-ins
(Bash, Grep, Glob, Task, …) but **not the harness orchestration surface** — and the
built-in **`Monitor`** tool takes a `command` field and runs **arbitrary shell** in a
background loop (`persistent:true` spawns a background task whose output the agent
then Reads). Confined agents used `Monitor` to run raw `adb logcat`, `adb shell
pidof`, and `adb forward`+**`jdb`** (a Java debugger) — e.g. `maestro/c10/run-3`
attached jdb to the running process, hit a breakpoint in
`CheckoutViewModel.applyDiscount()`, and read `discountFactor = 0.755` directly.
This bypasses the tool-under-test entirely (the exact adb-bypass the confinement
existed to prevent) and, because `Monitor` can also `cat`, structurally defeats the
erratum-#2 Read-guard. All three tool columns' agents had `Monitor`.

**Blast radius (measured, not assumed).** Parsed every transcript for `Monitor`
tool_use whose `command` ran a device shell. All 61 `Monitor` calls were adb-family
(none `cat` source, so the Read-guard was not defeated *in practice*).
`ScheduleWakeup`/`TaskCreate` do **not** exec (no `command` field; they only carried
adb strings as prompt/description text). **8 of 120 completed cells** actually ran
the escape:

| task | linc | maestro | mobile-mcp |
|------|------|---------|------------|
| b5   | 0/5  | **3/5** | 0/5 |
| b7   | **1/5** | **1/5** | **2/5** |
| c10  | 0/5  | **1/5** | 0/5 |

(a1–a4, b6, and all unlisted cells: **0** Monitor-shell calls.)

**Fix.** Every non-device built-in is now denied — the orchestration surface
(`Monitor`, `ScheduleWakeup`, `Task*`), cron, worktree, MCP-resource, plan, notify,
`Workflow`, `Skill`, `SendMessage`, `AskUserQuestion`, `Artifact`. Only `Read`
(path-guarded, erratum #2), `ToolSearch` (loads deferred MCP schemas), and the
tool-under-test's MCP surface remain. Unit-tested (`test_build_command_confines…`
now asserts `Monitor`/`ScheduleWakeup`/`TaskCreate`/`Workflow`/… are denied).

**Remediation (CEO decision 2026-07-10 — "affected rows only").** The 112 cells
with zero Monitor-shell calls are *positively certified* clean (no shell output
existed to influence the answer) and are **confinement-invariant** — they stand.
Voided to `results_invalid/erratum3/` and re-run under the fixed confinement:
- **b7 — all three tools** (all were contaminated) → 15 runs.
- **maestro/b5** (linc/b5, mobile-mcp/b5 were clean → stand) → 5 runs.
- **maestro/c10** (linc/c10, mobile-mcp/c10 were clean → stand) → 5 runs.

Clean cells of a partially-contaminated task keep their v1 results because they
provably never invoked the removed tools (v1 outcome ≡ v3 outcome for them). This is
the third confinement erratum (source-read hole #2, shell-escape #3); v2 starts from
this hardened baseline.

**Outcome (re-run complete, every re-run cell verified `Monitor=0`).** Removing the
shell escape changed exactly the cells that had leaned on it — and left the
legitimately-earned results untouched:

| cell | v1 (contaminated) | v3 (clean) | reading |
|------|-------------------|-----------|---------|
| linc/b7        | 5/5 | **5/5** | unchanged — linc's cold-start timing came from nerve's MCP (metrics/logcat) all along |
| maestro/b7     | 2/5 | **2/5** | unchanged — its passes used Maestro's own force-stop+timing |
| mobile-mcp/b7  | 1/5 | **0/5** | its lone pass had used a Monitor `adb` shell |
| maestro/b5     | 3/5 | **0/5** | maestro's flaky-behavior detection was *entirely* raw `adb logcat` via Monitor; with no shell it scores 0 (one run hit the 900s timeout) |
| maestro/c10    | jdb 0.755 | **0/5** | the sole pass was the raw-`jdb` breakpoint read; gone |

Net: maestro's apparent strength on b5/c10 was borrowed from a raw adb/jdb shell,
not from Maestro. linc's numbers were escape-independent (it solved via nerve's
structured surface), so they held. The published v1 grid uses these v3 numbers for
b5(maestro)/b7(all)/c10(maestro); the other cells were certified escape-free.

## 2026-07-11 — cross-tool UiAutomation contamination vector disclosed (no verdicts changed) + per-cell hygiene added

**The vector.** Post-grid root-cause work on linc's element blindness (P0-A,
fixed in linc-nerve#105 @`e46a225`) found that a **leaked `dev.mobile.maestro`
instrumentation driver** — left alive on the bench phone by grid cells of a
*competing* tool column — holds the device's single UiAutomation connection,
making the system SIGKILL every subsequent `uiautomator dump` ("Killed",
rc 137). The v1 reset steps (`force-stop <app>`, `clear-data`, `home`, `wake`)
only touch the app under test, so a driver leaked by one cell survived into
later cells: a cross-tool contamination vector created by the harness's own
grid, not by any tool under test.

**Effect on v1 (disclosure, no re-grade).** Every v1 linc transcript shows
`element_count: 0`; the leaked-holder condition was found live on the bench
during post-grid diagnosis and dump recovery was reproduced by force-stopping
the driver. The environmental trigger does not excuse the scored failure —
nerve converting a failed dump into a silent empty tree was a genuine tool
defect (a robust tool must surface or heal the conflict, as its competitors'
drivers implicitly do by re-acquiring UiAutomation) — so **all v1 verdicts
stand as recorded**. But the efficiency/latency readings for affected linc
cells (e.g. a1 median 135 s vs ~34 s post-fix) should be read with the
environmental factor in mind.

**Fix (v2-forward).** The harness now runs a **per-cell UiAutomation-holder
hygiene step** before every run, for every tool identically: exact-name match
of running processes against a known-driver allowlist (`dev.mobile.maestro`,
uiautomator2/appium servers — never the similarly-named Pixel Watch companion
app) → `am force-stop` each → record the result as
`uiautomation_holders_cleared` in the run meta, so v2 cell provenance shows a
clean device at cell start. Unit-tested (`tests/test_device.py`); improvement
`9c816108`.

## 2026-07-10 — device-interference audit (no cells voided) + scheduled job neutralized

**Trigger.** The CEO glimpsed the SniperPulse home screen on the scored Pixel
during the c10 window and flagged possible interference from another session or
automation — a benchmark-integrity concern (a foreign app in the foreground
mid-run would disrupt the agent's BenchTarget interaction).

**Investigation.** Two questions: (1) did any *completed* run capture foreign
foreground contamination, and (2) what launched SniperPulse.

1. **Transcript classification.** Grepped every `results/` transcript for
   `sniperpulse` and classified each hit by context. **35 transcripts mention it;
   0 show it as a foreground/resumed activity** — every mention is inside a
   device/app-enumeration tool result (`nerve_apps` / `mobile_list_apps` listing
   *installed* packages; SniperPulse is installed on this shared dev device, so
   it appears in any package dump). Benign enumeration, not contamination. The
   three c10 re-run transcripts likewise show `foreground_sniper=none`.

2. **Source of the sighting.** The launchd job `com.linc.daily-device-tests`
   (`StartCalendarInterval` 05:00 local) runs a crucible **BVT** pass that builds
   and launches apps — including SniperPulse — on the physical fleet. Its logs
   show it fired **once today, 05:00–05:13 local (12:00–12:13 UTC)**, leaving
   SniperPulse on-screen afterward. The c10 re-runs ran **14:31–14:37 UTC** —
   ~2.5 h later, **zero temporal overlap**. The CEO saw the *residue* of the
   05:13 job, cleared by the first c10 `reset` (`force-stop`). It also plausibly
   explains the two earlier "external kills" (BVT grabbing the device / issuing
   force-stops mid-run), though those cells were re-run regardless.

**Conclusion — no cell voided.** No completed transcript carries foreground
contamination; the only fire today did not overlap any run. Nothing to void.

**Neutralization (going forward).** `com.linc.daily-device-tests` was booted out
of the user launchd domain (`launchctl bootout gui/$UID/…`) so it cannot fire at
05:00 during the remaining grid — critical because the agent-device column runs
unattended and could span 05:00. The plist is left in place; re-enable after the
grid with `launchctl bootstrap gui/$UID ~/Library/LaunchAgents/com.linc.daily-device-tests.plist`.
Exclusive scored-device access is now the standing condition for the rest of v1.

## 2026-07-11 — v2 precondition amended: phone keeps its keyguard (CEO decision, before any v2 row)

`PREREGISTRATION-v2.md` froze the device precondition as "lock-free (no secure
keyguard)". The bench phone is a personal device and the CEO decided to keep
its PIN. Amended precondition, effective before any v2 comparative row ran:

- The CEO unlocks the phone at the start of each run session; the harness
  operator sets `svc power stayon usb` for the duration, so the screen never
  sleeps and the keyguard never re-engages mid-grid, and restores
  `svc power stayon false` afterwards.
- A cell that encounters `deviceLocked=1` (dumpsys trust) is invalid and
  re-runs after re-unlock — a locked screen blinds every tool identically,
  so this is a no-row condition, not a FAIL.

**No rows affected** — no v2 comparative cell had run when this was amended.
The same-day pipeline smoke (throwaway a1 cell + APK digest-pin swap exercise,
results outside `results_v2/`, unpublished) validated hygiene → pin → reset →
verify end-to-end on the unlocked phone: a1 PASS 36 s, seeded/stock swap
installed+verified, idempotent re-check clean.

## 2026-07-11 — v2 run window widened to 2026-07-11 → 2026-07-20 (no rows had run)

`PREREGISTRATION-v2.md` set the comparative-run window at 2026-07-13 →
2026-07-20; the 07-13 start was chosen only for phone-unlock uncertainty. The
watch became run-ready on 07-11 (back on adb, no keyguard) and b8 needs no
phone, so the window START moves to 2026-07-11. The hard stop is unchanged.
**No rows affected** — no v2 comparative cell had run when this was amended.
b8 genuineness condition at run start: BenchTarget installed ONLY on the watch
(phone off-bench; verified absent from both other attached devices).

## 2026-07-11 — phone-grid false start voided (31 cells, none published) + environment controlled

The first phone-grid launch (21:51–23:47 local) was stopped and its 31 cells
deleted before any publication. Two harness-side contaminations, both fixed
before relaunch (23:54):

1. **Operator device reservation blocked the linc column (0/7).** The grid
   operator had reserved the bench phone in `nerve_pool` (10 h, to shield the
   grid from the 05:00 nightly device job). The linc cells' own nerve server
   honors that same reservation ledger, so every linc agent saw the phone as
   held by another session and refused to drive it — transcripts show the
   agent declining to "preempt that other active session's device
   reservation". Harness-inflicted; competitors don't read `nerve_pool`, so
   only linc was handicapped. Fix: reservation released; the nightly job was
   instead neutralized for the grid window via `launchctl bootout` (the exact
   v1 mechanism, re-enabled after the grid).
2. **Non-benchmark devices confused maestro (1/7).** Two Samsung devices
   (o1-project residents, one still carrying the retired "LINC Bench Probe"
   app) were attached alongside the benchmark pair; maestro burned full 600 s
   budgets enumerating and exploring them. v1's grid ran with only the
   benchmark devices attached. Fix: the Samsungs were physically unplugged;
   the grid environment is now exactly the pre-registered device set (Pixel
   8 Pro + Pixel Watch 2). mobile-mcp and agent-device passed their false-start
   cells despite the noise; their cells were voided anyway so every published
   v2 phone row runs under identical conditions.

**No published row is affected** — the false-start cells never left the bench
host. The b8 capability column (published earlier the same day) ran on the
watch under its own disclosed conditions and stands. First relaunch cell:
linc/a1/run-1 PASS 43.8 s, confirming cause (1).
