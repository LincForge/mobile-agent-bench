# mobile-agent-bench — v1 report

**Question:** driving an identical confined `claude-sonnet-5` agent, how do four
mobile-agent tool surfaces compare on a real Android app + Wear OS watch?

**Contestants (tool-under-test = the *only* capability the agent has):**
linc (nerve + crucible + spectra) · maestro · mobile-mcp · agent-device.

**Fixtures:** BenchTarget (Jetpack Compose) on a Pixel 8 Pro; Pixel Watch 2 for b8.
10 tasks × 5 runs × 4 tools = **200 cells**. Model `claude-sonnet-5`. Pre-registration
frozen at tag `v1-prereg`; every deviation is in `AMENDMENTS.md`.

---

## TL;DR

- **Completion (a1–c10, b8 excluded):** 🥇 **linc 73%** · 🥈 **agent-device 71%** ·
  maestro 58% · mobile-mcp 56%.
- **The device-observability tools win the diagnostic tier and lose on efficiency.**
  linc and agent-device dominate tier B (crash-repro, flaky root-cause, timing) but
  cost 2–4× the turns/wall/$ of maestro and mobile-mcp.
- **No tool solved runtime inspection (c10 = 0/0/0/0)** under clean confinement — the
  task linc's spectra uniquely exists for. It's unrealized for everyone → linc's to
  win in v2 if spectra is fixed.
- **linc's inefficiency has a single root cause:** nerve returns an empty UI-element
  tree on this device (0 elements every run; competitors 10/10), forcing vision-only
  operation. 5 of linc's 7 timeouts *already had the answer in-transcript* — solved,
  but out of time.
- **Integrity:** three confinement errata were caught and remediated mid-grid
  (documented); the published numbers are all from cells verified free of the shell
  escape (`Monitor=0`).

---

## Scoreboard (adjudicated)

| task | tier | linc | maestro | mobile-mcp | agent-device |
|------|------|------|---------|------------|--------------|
| a1–a4 | A | 5/5 | 5/5 | 5/5 | 5/5 |
| b5 | B | 1/5 | 0/5 | **5/5** | **5/5** |
| b6 | B | **5/5** | 0/5 | 0/5 | 3/5 |
| b7 | B | **5/5** | 2/5 | 0/5 | 4/5 |
| c9 | C | 2/5 | **4/5** | 0/5 | 0/5 |
| c10 | C | 0/5 | 0/5 | 0/5 | 0/5 |
| **completion** | | **73%** | 58% | 56% | 71% |
| b8 | B* | 5/5 | 5/5 | 5/5 | 5/5 |

*b8 = Wear OS capability row; reported separately, never averaged (pre-reg).*

**Per-tier:**
- **A (pure interaction):** linc 20/20 · agent-device 20/20 · maestro 20/20 · mobile-mcp 20/20 — solved by all.
- **B (diagnostics):** agent-device 12/15 · **linc 11/15** · mobile-mcp 5/15 · maestro 2/15.
- **C (reasoning/runtime):** maestro 4/10 · linc 2/10 · agent-device 0/10 · mobile-mcp 0/10.

## Ops-proof / efficiency (a1–c10; `uncached` = real signal, not cache-inflated total)

| tool | compl% | med wall | med uncached tok | med turns | med $/task | timeouts |
|------|--------|----------|------------------|-----------|-----------|----------|
| linc | 73% | 198s | 65,164 | 39 | $0.64 | **7** |
| agent-device | 71% | 233s | 77,892 | 62 | $1.19 | 3 |
| maestro | 58% | 103s | 45,188 | 17 | $0.45 | 1 |
| mobile-mcp | 56% | 117s | 29,241 | 28 | $0.49 | 1 |

Total grid spend (200 cells): **$216**. (Note: the harness `bench report` "median
tokens" column is `total_billed` ≈ cache_read — inflated by turns×context and
misleading; the table above uses `total_uncached`.)

## Per-cell detail (harness `bench report` output)

| tool | task | tier | runs | pass | median wall s | median tokens¹ | wall stdev |
|---|---|---|---|---|---|---|---|
| linc | a1 | A | 5 | 5/5 | 142.3 | 1,101,053 | 23.7 |
| linc | a2 | A | 5 | 5/5 | 190.5 | 1,500,657 | 60.3 |
| linc | a3 | A | 5 | 5/5 | 140.8 | 1,213,524 | 15.8 |
| linc | a4 | A | 5 | 5/5 | 25.7 | 236,265 | 6.2 |
| linc | b5 | B | 5 | 1/5 | 900.0 | 16,661,197 | 112.3 |
| linc | b6 | B | 5 | 5/5 | 335.0 | 3,439,710 | 67.5 |
| linc | b7 | B | 5 | 5/5 | 131.8 | 1,306,730 | 39.6 |
| linc | b8 (capability row) | B | 5 | 5/5 | 59.3 | 481,932 | 10.3 |
| linc | c9 | C | 5 | 2/5 | 900.0 | 22,349,883 | 64.4 |
| linc | c10 | C | 5 | 0/5 | 427.7 | 4,961,221 | 123.5 |
| agent-device | a1 | A | 5 | 5/5 | 132.3 | 1,151,253 | 21.2 |
| agent-device | a2 | A | 5 | 5/5 | 237.0 | 2,381,063 | 130.3 |
| agent-device | a3 | A | 5 | 5/5 | 226.8 | 2,724,271 | 10.5 |
| agent-device | a4 | A | 5 | 5/5 | 74.9 | 561,996 | 28.3 |
| agent-device | b5 | B | 5 | 5/5 | 620.2 | 9,602,877 | 93.2 |
| agent-device | b6 | B | 5 | 3/5 | 749.1 | 10,650,043 | 127.6 |
| agent-device | b7 | B | 5 | 4/5 | 139.9 | 834,308 | 37.2 |
| agent-device | b8 (capability row) | B | 5 | 5/5 | 91.6 | 576,226 | 34.0 |
| agent-device | c9 | C | 5 | 0/5 | 642.4 | 7,741,346 | 169.2 |
| agent-device | c10 | C | 5 | 0/5 | 430.7 | 2,886,249 | 270.2 |
| maestro | a1 | A | 5 | 5/5 | 51.9 | 454,795 | 40.1 |
| maestro | a2 | A | 5 | 5/5 | 93.8 | 733,611 | 8.6 |
| maestro | a3 | A | 5 | 5/5 | 100.8 | 485,385 | 59.0 |
| maestro | a4 | A | 5 | 5/5 | 38.6 | 218,227 | 2.4 |
| maestro | b5 | B | 5 | 0/5 | 464.7 | 2,716,955 | 205.5 |
| maestro | b6 | B | 5 | 0/5 | 266.7 | 2,335,598 | 45.0 |
| maestro | b7 | B | 5 | 2/5 | 53.1 | 130,425 | 110.3 |
| maestro | b8 (capability row) | B | 5 | 5/5 | 77.5 | 216,656 | 5.7 |
| maestro | c9 | C | 5 | 4/5 | 589.4 | 5,805,963 | 76.9 |
| maestro | c10 | C | 5 | 0/5 | 96.2 | 364,820 | 25.5 |
| mobile-mcp | a1 | A | 5 | 5/5 | 86.0 | 611,719 | 8.8 |
| mobile-mcp | a2 | A | 5 | 5/5 | 113.5 | 955,060 | 19.5 |
| mobile-mcp | a3 | A | 5 | 5/5 | 116.4 | 981,061 | 14.6 |
| mobile-mcp | a4 | A | 5 | 5/5 | 21.1 | 172,369 | 2.0 |
| mobile-mcp | b5 | B | 5 | 5/5 | 528.3 | 6,668,308 | 122.9 |
| mobile-mcp | b6 | B | 5 | 0/5 | 393.0 | 3,318,872 | 81.5 |
| mobile-mcp | b7 | B | 5 | 0/5 | 59.1 | 135,994 | 3.8 |
| mobile-mcp | b8 (capability row) | B | 5 | 5/5 | 87.0 | 506,154 | 17.1 |
| mobile-mcp | c9 | C | 5 | 0/5 | 562.2 | 5,339,506 | 165.0 |
| mobile-mcp | c10 | C | 5 | 0/5 | 169.5 | 1,354,356 | 104.7 |

¹ cache-inflated `total_billed`; use the uncached table above for efficiency.

## Findings

1. **linc is the most capable and least efficient.** #1 completion (73%), sole clean
   winner on b6 (flaky root-cause), 5/5 on b7 (timing) — but 2× wall, most turns, 7
   timeouts. agent-device is a near-tie (71%) and *beats* linc on b5.
2. **Root cause of linc's inefficiency — nerve is blind to UI elements here.**
   `nerve_elements`/`nerve_state` returned `element_count: 0` on **every** linc run;
   mobile-mcp and maestro got a populated tree 10/10 on the identical device+app. linc
   is forced into screenshot-only vision → the turn/latency/timeout tax. **5 of linc's
   7 timeouts already contained the full ground-truth answer** (b5×2, c9×3): solved,
   but out of budget. Filed `8bba730a` (nerve, critical); likely root cause `280bbee7`
   (`uiautomator dump` Killed on both bench devices).
3. **c10 = 0/0/0/0 — the runtime-inspection differentiator is unrealized.** linc's
   spectra was discovered and invoked hard (7–19 attach/run) but couldn't read
   `discountFactor` on an unregistered app (source breakpoints need Forge, retired).
   Filed `ab10e2d5` (spectra, critical) + prerequisites `3bee4d6c`, `8b9b0e86`, UX
   `79f596e0`. This is v2's marquee opportunity for linc.
4. **b8 (Wear OS): all four tools 5/5.** The pre-registered "linc-exclusive" expectation
   did not hold — an honest correction, not buried.
5. **maestro's raw numbers required a correction.** Its v1 b5 3/5 and a c10 pass came
   from a `Monitor`-tool shell escape (raw `adb`/`jdb`), not from Maestro; after closing
   the hole (erratum #3) and re-running, maestro/b5 → 0/5 and the c10 jdb-pass is gone.

## Integrity & confinement

- **Confinement:** the agent gets ONLY the tool-under-test's MCP surface — no
  Bash/fs/web/subagents, `--strict-mcp-config`, neutral cwd, a path-guarded `Read`.
- **Three errata, all documented in `AMENDMENTS.md` and remediated before publication:**
  #1 nerve pinned to a single SHA for the whole grid; #2 a `Read`-of-source hole closed
  (one contaminated cell voided); #3 the `Monitor` shell-escape closed (8 contaminated
  cells voided + re-run; 112 zero-shell cells positively certified). **Every published
  cell is verified `Monitor=0`.**
- **Grader discipline:** three verify patterns were found flawed (b7 too strict, c10/b6
  too loose) and corrected against pre-registered intent, then re-graded from frozen
  transcripts (never re-run). c9 passes were eyeball-adjudicated (all 6 genuinely
  localize the seeded tier defect).
- **Interference audit:** a scheduled device-test job (`daily-device-tests`) was found
  and neutralized for the grid; a transcript scan confirmed **no cell** was contaminated
  by foreground interference (all "sniperpulse" mentions were benign app-list
  enumeration).

## Filed improvements → v2 targets (priority order)

| id | tool | pri | impact | fix direction |
|----|------|-----|--------|---------------|
| `8bba730a` (+`280bbee7`) | nerve | P0 | the entire efficiency gap; flips b5/c9 timeouts | read AccessibilityNodeInfo directly / don't depend on killable `uiautomator dump` |
| `ab10e2d5` | spectra | P0 | unblocks c10 (0→win), the marquee differentiator | decouple source breakpoints from Forge; zero-config attach+break-by-method+read-locals |
| `3bee4d6c` | spectra | P1 | prerequisite — adapter missing on bench host | install kotlin-debug-adapter + boot health check |
| `8b9b0e86` | spectra | P1 | prerequisite — JDWP PID discovery broken | fix `adb jdwp` timeout=2 (it never exits) |
| `79f596e0` | spectra | P2 | agent under-reaches for spectra | sharpen tool descriptions |

Full implementation handoff: `docs/linc-tools-improvement-handoff.md`. Analysis:
`docs/v1-deep-dive.md`.

## Limitations / threats to validity

- **Single model, single app, single device.** One Compose app on one Pixel 8 Pro;
  generalization to other apps/UI toolkits/OEMs is unproven. (The nerve element gap may
  be device- or Compose-specific — `280bbee7` sees the dump killed on two devices.)
- **Regex answer-grading** cannot distinguish "affirms X" from "mentions X" for reasoning
  tasks; c-tier used eyeball adjudication as backstop. v2 should add an LLM-judge.
- **Fixed 900s budget** turns some linc *capability* into *timeout* (see finding 2).
  v2 should consider reporting "solved-but-unfinalized" as a distinct outcome.
- **Confinement is a model of, not identical to, real usage** (a real operator may have a
  shell). The benchmark measures the *structured tool surface*, deliberately.

## CEO publish gate

- [x] All 200 cells complete, every published cell `Monitor=0`
- [x] Errata #1–3 documented + remediated; contaminated cells voided/re-run
- [x] c-tier passes adjudicated; grader bugs fixed vs pre-registered intent
- [x] Improvements filed with benchmark-linked impact
- [ ] **CEO sign-off to publish externally** ← awaiting decision
- [ ] v2 gated on `8bba730a` + `ab10e2d5` landing (fresh pre-registration)
