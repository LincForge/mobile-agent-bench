# LINC tools — pre-v2 improvement program (evaluated inventory)

_Compiled 2026-07-11 by the nerve/spectra P0-fix session. Every improvement and
learning the v1 benchmark surfaced across the linc stack (nerve / crucible /
spectra) plus the harness itself, each reality-checked against current code.
Reactor program: see `linc-tools-v2-readiness` (DRAFT under Ark) — approval =
the WIP-cap slot decision._

## Status legend

- **FIXED** — landed on main, live-verified on the bench
- **OPEN/v2** — must land (or be pinned in the pre-registration) before a fair v2
- **OPEN/debt** — real, but does not gate v2; normal producer-lane routing
- **N/A-v2** — unrelated to the bench

---

## 1 · The two P0s (both FIXED, 2026-07-11)

### P0-A `8bba730a` + `280bbee7` — nerve blind to UI elements → FIXED (linc-nerve #105, main `e46a225`)

**Corrected root cause.** Not Compose: a **leaked UiAutomation holder** (maestro's
`dev.mobile.maestro` instrumentation driver, left alive by grid cells) makes the
system SIGKILL every subsequent `uiautomator dump` (`Killed`, rc 137). nerve
converted that failure into `elements: [], element_count: 0` — silent-empty.
Fix: typed `UiHierarchyUnavailableError` (a failed dump can never read as an
empty screen), self-heal (force-stop allowlisted leaked drivers + one retry),
`elements_error` surfaced through nerve_state/nerve_diff, annotate paths degrade
to the raw frame.

**Bench validation (results_v2validation/, nerve pinned `e46a225`):**
a1 **PASS ×2 at ~34 s** (v1 linc median 135 s, ~4×), `nerve_elements` returning
populated trees (counts 20/11/6/8; v1 max across ALL linc transcripts was 0),
zero `elements_error`.

### P0-B `ab10e2d5` + `3bee4d6c` + `8b9b0e86` + `79f596e0` — spectra runtime inspection → FIXED (linc-spectra #35, main `f9dddb7`)

Four stacked defects, all landed:
1. `8b9b0e86` — `adb jdwp` streams forever; `timeout=2` always fired and discarded
   the partial output → PID discovery returned `{}` on every call. Now recovers
   PIDs from `TimeoutExpired.output`.
2. `3bee4d6c` — **corrected**: the adapter WAS installed (`~/tools/...`); discovery
   missed it only when `LINC_HOME` was set (state-dir redirect applied to a tool
   path). Real-home fallback + boot health check in `spectra bellows` + correct
   repo URL (`fwcd/kotlin-debug-adapter`).
3. **New bug found beneath** — the attach handshake hardcoded exception filters
   `["uncaught","caught"]`; ktda declares `"C"/"U"` and rejected the request →
   every attach died even past (1)/(2). Now arms only adapter-declared
   default-true filters; optional-request errors are best-effort.
4. `ab10e2d5` — DAP line breakpoints only bind against **real local source
   files** (synthetic/stub/basename paths verify but never fire — tested live
   three ways), so the Forge-registration gap is structural to the DAP path.
   New **zero-config flow**: `spectra_method_breakpoint` (jdb method-entry
   breakpoint by fully-qualified name — no sources, no line numbers) +
   `spectra_method_locals` (step-and-snapshot locals, one-shot). Non-debuggable
   builds detected and reported up front. `79f596e0` addressed via tool
   descriptions ("read runtime state not visible in UI/logs").

**Live c10 validation:** arm `CheckoutViewModel.applyDiscount` by name → UI to
qty 7 → Apply discount → harvest **`discountFactor = 0.755`** (+ `totalDollars
= 50`, per-line snapshots). Bench-cell re-runs in `results_v2validation/`.

---

## 2 · Remaining OPEN items, evaluated

### nerve

| id | finding | verdict |
|---|---|---|
| `44d68b62` | leaked UiAutomation also hangs `am instrument` (crucible BVT path) | **OPEN/v2-adjacent** — the elements() self-heal covers the dump path only; re-scope to the instrument path. Detection recipe now exists (ps allowlist + `dumpsys accessibility` "Ui Automation" line) |
| `2bb4eb80` | nightly device jobs don't honor `nerve_pool` reservations | **OPEN/v2** — v1 had to manually neutralize `daily-device-tests`; v2 grid integrity wants a real reservation↔cron handshake |
| `7f08981e` | bench watch secure keyguard blocks readiness gate | **OPEN/v2 (CEO physical)** — watch is also currently OFF adb (puck re-seat). b8 re-runs blocked on physical action; standing lock-free ask per playbook |
| `8d140900` `d1fe0658` `fe7fbb9d` | emulator discovery + 0-byte-recording silent successes | **OPEN/debt** — same silent-failure family as P0-A step 3; bench uses physical devices, so not v2 gates |
| `901fb6ef` `e3c5e20a` `eef2295e` `e834d647` `3bad56a7` `fd1f5353` `efa24d1c` | scrcpy S10e, screenrecord encoding, topology, multitouch, iOS MJPEG, thread plumbing, file size | **N/A-v2** |

### spectra (new, from the fix session itself)

| id | finding | verdict |
|---|---|---|
| `0950f809` | ktda `setExceptionBreakpoints` broken upstream (rejects its own declared ids; partial arming floods suspend-all stops) → crash→attach exception workflow unavailable via DAP | **OPEN/debt** — worked around in #35; options: upstream fix, pinned patched build, or jdb `catch` route |
| `fc9b7c3c` | ktda `verified: true` is meaningless (verifies breakpoints that can never bind) | **OPEN/debt** — doc/detection fix; cost v1 agents real turns |

### crucible

No grid-surfaced defects. (c9's 2/5 was reasoning/efficiency, not a crucible
failure; open crucible inbox items are general debt — deployer CRAP, BVT
consolidation, lock drift — none v2-gating.)

### bench harness (v2 pre-registration inputs)

| id | finding | verdict |
|---|---|---|
| `9c816108` | **per-cell UiAutomation-holder hygiene** — v1's own maestro cells created the condition that blinded nerve; cross-tool contamination vector. Consider a v1 AMENDMENTS note | **OPEN/v2 (required)** |
| `9b6a0ba5` + `2d884371` | **per-task APK install/verify + variant pinning** — c10 needs the debuggable build; a wrong app (linc-bench probe APK) was found installed; reset never verifies the install | **OPEN/v2 (required)** |
| `a283910e` | pin stack SHAs in pre-registration | **OPEN/v2 (required)** — pin nerve `e46a225`, spectra `f9dddb7` (+ crucible SHA at freeze) |
| `8881e5a3` `ffb4ada1` | verify-regex tested against sample answers; reasoning-task adjudication limits | **OPEN/v2 (required)** |
| `ca4499a4` | sanitizer must cover enumerated serials, not just the redact list | **OPEN/v2** |
| `5e37e19d` | report uncached/output token columns | **OPEN/v2 (report)** |
| `f6932211` | Read path confinement | already fixed (erratum #2) — dismiss at triage |
| deep-dive §v2 | report "solved-but-unfinalized" as a distinct outcome vs 900 s budget | **OPEN/v2 (design decision at pre-reg)** |

---

## 3 · Program shape (lane routing per knowledge-source contracts)

- **Reactor program** `linc-tools-v2-readiness` (DRAFT under Ark) = the strategic
  umbrella + v2 gate. Approval doubles as the Goldratt WIP-slot decision.
- **Bounded fixes** (44d68b62 instrument path, 2bb4eb80 reservation handshake,
  harness hygiene/install-verify/sanitizer/report items) route as
  **producer-lane GitHub issues** at /triage — no per-issue reactor shadows.
- **CEO/physical**: watch puck re-seat + lock-free standing state (b8 lane).
- **v2 pre-registration** consumes §2's "required" rows as its checklist; fresh
  pre-reg only after the program's fix items land.
