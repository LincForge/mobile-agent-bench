# LINC tools — improvement handoff (from mobile-agent-bench v1)

**Purpose:** hand a fresh **fable** session everything needed to implement the linc-tool
fixes the benchmark surfaced — no re-discovery required. Each item has: reactor ID,
priority, the **benchmark evidence** (impact), root cause, fix direction, and how to
**validate** (re-run the specific bench cells).

**Context in one paragraph.** mobile-agent-bench pits four mobile-agent tools
(linc = nerve+crucible+spectra, maestro, mobile-mcp, agent-device) driven by an
identical confined `claude-sonnet-5` agent against the BenchTarget Compose app on a
Pixel 8 Pro / Pixel Watch 2. v1 result: **linc is the most capable (73% completion,
dominates tier-B diagnostics) but the least efficient (~2× wall time, 7 timeouts vs 1).**
Two P0 defects gate linc, and both are proven by direct competitor comparison on the
*identical* device+app. Full analysis: `docs/v1-deep-dive.md`. Methodology &
integrity errata: `AMENDMENTS.md`.

---

## Priority order (by leverage)

1. **nerve element extraction** — `8bba730a` + root cause `280bbee7`  → unblocks the whole efficiency gap
2. **spectra runtime inspection** — `ab10e2d5` + prerequisites `3bee4d6c`, `8b9b0e86` + UX `79f596e0`  → unblocks c10, the marquee differentiator
3. Supporting nerve device-bench robustness (see "Secondary")

Do these **before** a v2 grid — they are the v2 blockers.

---

## P0-A · nerve is blind to UI elements on the bench  →  the efficiency gap

**Reactor:** `8bba730a` (linc-nerve, **critical**) — symptom; `280bbee7` (linc-nerve,
bug) — **almost certainly the root cause**. Treat as one work item.

**Benchmark evidence (impact):**
- `nerve_elements`/`nerve_state` returned `elements: [], element_count: 0` on **every**
  linc run across a1–a4, b5, b6, c9, c10. Max `element_count` across ALL linc
  transcripts = **0**. (Only b7, which reads logcat not the element tree, was immune.)
- On the **identical** Pixel 8 Pro + BenchTarget, competitors got a populated tree
  every time: **mobile-mcp 10/10, maestro 10/10** (a1+b5 sampled). → the defect is
  nerve's, not the app's.
- Consequence: linc runs **screenshot-only vision** every step. This is the mechanism
  behind linc's whole efficiency deficit:
  - A-tier tax: linc **30 turns / 135 s** vs maestro **12 turns / 82 s** for the same passing taps.
  - **5 of linc's 7 timeouts already had the full ground-truth answer in-transcript**
    (b5 run-1,2; c9 run-1,2,3) — linc *solved* the task but blew the 900 s budget
    vision-scrolling before finalizing. A fix plausibly recovers **b5 1→3/5** and
    **c9 2→5/5** with no capability change.

**Root cause (per `280bbee7`):** `uiautomator dump` gets **Killed** on BOTH bench
devices (Pixel 8 Pro and Pixel Watch 2, observed 2026-07-09). nerve's element/state
extraction appears to depend on that dump, so it returns empty. Competitors read the
**AccessibilityNodeInfo** tree via their own accessibility path, which works on the
same device — including Compose semantics.

**Fix direction:**
1. Stop relying solely on `uiautomator dump` for `nerve_elements`/`nerve_state`.
2. Read the a11y node tree directly (AccessibilityNodeInfo; Compose exposes semantics
   through it when the semantics tree is populated), or add a robust fallback path.
3. If a dump is unavailable, **say so** in the response — never return
   `element_count: 0` as if the screen were empty (silent-failure anti-pattern the
   nerve inbox flags repeatedly).

**Validate:** re-run `bench run --tool linc --task a1 --runs 2` and confirm
`element_count > 0` in the transcript; then re-run b5 and c9 and check whether the
solved-but-timed-out runs now finalize in-budget.

---

## P0-B · spectra can't do runtime inspection on an unregistered app  →  loses c10

**Reactor:** `ab10e2d5` (linc-spectra, **critical**, HEADLINE). Hard prerequisites on
the same host: `3bee4d6c` and `8b9b0e86`. Discoverability follow-up: `79f596e0`.

**Benchmark evidence (impact):**
- c10 (read runtime `discountFactor = 0.755`, unrecoverable from UI/logs — spectra's
  exact reason to exist) = **0/5 for linc** (and 0/0/0 across all tools under clean
  confinement).
- The confined agent **did** discover and hammer spectra (`spectra_attach` 7–19×/run,
  `spectra_breakpoint` 2–10×/run, no tool crashes) but never read the variable. Every
  run ended asking for a **debuggable-and-registered** build — the source-level
  breakpoint path needs Forge/`.forge.yaml` registration, and **Forge is retired**.

**Fix chain (order matters):**
1. `3bee4d6c` — `kotlin-debug-adapter` is **not installed on the Mac mini** (bench
   host) → `spectra_attach` fails "adapter not found". Install it and add an
   **adapter-presence health check at boot** (loud fail, not mid-engagement). Also fix
   the wrong repo URL in the error string (actual: `fwcd/kotlin-debug-adapter`).
2. `8b9b0e86` — `adb_list_jdwp_pids()` runs `adb jdwp` with `timeout=2`, but `adb jdwp`
   **never exits** (it streams), so the timeout fires every time → empty set →
   "Cannot find debuggable PID". Read partial output from `TimeoutExpired.output`, or
   `Popen`-stream and kill after first lines/deadline. (Manual `adb forward … jdwp` +
   jdb works, so the capability is intact — only discovery is broken.)
3. `ab10e2d5` — **decouple source-level breakpoints from Forge registration.** Resolve
   class/method → source via the connected DAP/JDWP + APK symbols directly; offer a
   zero-config "attach + breakpoint by fully-qualified method name + read locals" flow.
   If a debuggable build is genuinely required, **detect and say so up front.**
4. `79f596e0` (UX) — even when available, spectra was under-reached-for; sharpen tool
   descriptions to signal "use me to read runtime state not visible in UI/logs."

**Validate:** on a debuggable BenchTarget build, `spectra_attach` →
`spectra_breakpoint CheckoutViewModel.applyDiscount` → set qty 7, Apply discount →
`spectra_variables` reads `discountFactor = 0.755`. Then re-run
`bench run --tool linc --task c10 --runs 5`.

---

## Secondary · nerve device-bench robustness (surfaced adjacent, not v2 blockers)

These are open nerve items that the bench work corroborates; batch them if touching the
same code:
- `280bbee7` — `uiautomator dump` Killed on bench devices (folded into P0-A above).
- `8d140900` / `d1fe0658` / `fe7fbb9d` — emulator discovery + 0-byte-recording
  silent-successes (silent-failure family; same "never report success on empty" fix
  ethos as P0-A step 3).
- `44d68b62` — leaked UiAutomation across sessions hangs `am instrument`; detect + tell
  the caller to reboot.
- `2bb4eb80` — nightly BVT/Maestro jobs don't honor `nerve_pool` reservations (bench
  contamination risk; this benchmark independently hit device interference from
  `com.linc.daily-device-tests` — see `AMENDMENTS.md` interference audit).

---

## What v1 already proved works (don't "fix" these)

- **linc tier-B diagnostics** — b6 flaky root-cause **5/5**, b7 cold-start timing
  **5/5**: nerve's logcat/metrics/inspect are a real edge maestro (2/5, 0/5) and
  mobile-mcp (0/5, 0/5) lack. Highest raw completion (73%).
- **Wear OS** — b8 **5/5** for linc (and, honestly, for all three tools; the
  pre-registered "linc-exclusive" expectation did not hold — see `docs/v1-deep-dive.md`).

## For the fable session

- Repos: `~/projects/linc-nerve`, `~/projects/linc-spectra`. Bench harness + evidence:
  `~/projects/mobile-agent-bench` (transcripts under `results/linc/*/run-*/`).
- Start with **P0-A** (highest leverage, self-contained in nerve) then **P0-B**
  (spectra chain, order 1→4). Each has a concrete validate step above.
- Log work to reactor and mark the improvement IDs as you land fixes; a fair **v2**
  grid should be run only after P0-A and P0-B are in.
