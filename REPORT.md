# mobile-agent-bench — combined report (v1 + v2 + v3)

**Question:** driving an identical confined `claude-sonnet-5` agent, how do four
mobile-agent tool surfaces compare on a real Android app + Wear OS watch?

**Contestants (tool-under-test = the *only* capability the agent has):**
linc (nerve + crucible + spectra) · maestro · mobile-mcp · agent-device.

**Fixtures & method:** BenchTarget (Jetpack Compose). 10 tasks × 5 runs × 4
tools = 200 cells per grid. This report covers **three complete 200-cell grids**:
- **v1** (frozen at tag `v1-prereg`, Pixel 8 Pro + Pixel Watch 2, published
  with linc losing its marquee task `c10` at 0/5),
- **v2** (frozen at tag `v2-prereg`, byte-identical tasks/prompts to v1 after
  the two v1-identified P0 defects were fixed), and
- **v3** (frozen at tag `v3-prereg`, [`PREREGISTRATION-v3.md`](PREREGISTRATION-v3.md),
  Samsung Galaxy S24 `SM-S921U` + Galaxy Watch7 `SM-L300` on Android 16 / SDK 36):
  a rematch against upgraded competitor releases (`maestro 2.11.0`,
  `@mobilenext/mobile-mcp 1.0.10`, `agent-device 0.21.27`) and the frozen `linc`
  stack (`linc-nerve==0.1.0` from PyPI `LincForge/nerve@5477863`, plus git-pinned
  `crucible@cf04279` and `spectra@c471dad`) on a hybrid 10-task suite
  (`tasks_v3/`): 4 byte-identical v1/v2 anchors (`b5`, `b6`, `c9`, `c10`) + 6
  unseen zero-pilot tasks (`a5`, `a6`, `b9`, `b10`, `c11`, and the `b11` Wear OS
  capability row), scored once on the frozen stack with zero post-fix re-runs.

Every deviation from any pre-registration is recorded with receipts in
[`AMENDMENTS.md`](AMENDMENTS.md). Earlier grids remain published in full;
newer grids do not overwrite them.

---

## Disclosure — read this before the numbers

**This benchmark is authored by the people who build one of the contestants.**
The harness, the tasks, the target app, and this report were written by LINC
Innovations, the vendor of the `linc` stack (nerve/crucible/spectra). It is a
vendor-authored benchmark that names competitors, and the v1→v2 improvement
documented below was produced by the same vendor fixing its own tool between
runs. You should apply the skepticism that setup deserves.

What makes the result checkable rather than merely asserted:

1. **Pre-registration (commitment device).** Each grid was committed and tagged
   before any comparative cell ran ([`PREREGISTRATION.md`](PREREGISTRATION.md),
   [`PREREGISTRATION-v2.md`](PREREGISTRATION-v2.md),
   [`PREREGISTRATION-v3.md`](PREREGISTRATION-v3.md)) — tasks, prompts, verify
   patterns, model, devices, budgets, and exact stack pins/SHAs. Any later
   change is an amendment in [`AMENDMENTS.md`](AMENDMENTS.md) and voids every
   row it touches. Nothing is quietly edited.
2. **Published losses.** v1 shipped with linc scoring 0/5 on c10 — the one
   task its debugger uniquely exists for — the least efficient column on the
   grid (7 timeouts), and a falsified pre-registered expectation (b8 was
   predicted linc-exclusive; all four tools passed it). Those numbers are
   still published and are reproduced below.
3. **Disclosed interference — including in the vendor's favor and against
   it.** v1 recorded three confinement errata; v2 caught four interference
   classes before publication, one of which voided a cell that had *passed*;
   v3 ran with 0 locked-device cells (`device_locked_pre/post` recorded per
   cell) and symmetric per-cell `logcat -b all -c` + UiAutomation hygiene.
4. **Everything is re-runnable.** The harness, task files (`tasks/`,
   `tasks_v3/`), target-app source, adapters, and sanitized transcripts
   (`results/`, `results_v2/`, `results_v3/`) are published. Every figure traces
   to a stored raw run log.

The strongest criticism of v2 (that the vendor fixed defects on tasks it had
already seen, while competitors ran on older versions) motivated **v3**:
upgraded competitor baselines, 6 unseen zero-pilot tasks, dual pre-registered
reporting (both the 7-task UI + logcat phone subset and the full 9-task phone
aggregate including JDWP tasks `c10`/`c11`), and a strict score-once rule.

---

## TL;DR

- **On the 7-task UI + logcat phone subset (`n=35`, excluding JVM debugger tasks
  `c10` and `c11`), `linc` and Callstack's `agent-device 0.21.27` match at
  34/35 (97.1%):** `1` win (`b5`: `5/5` vs `4/5`), `1` loss (`b6`: `4/5` vs `5/5`),
  and `5` ties at `5/5` (`a5`, `a6`, `b9`, `b10`, `c9`), ahead of `mobile-mcp
  1.0.10` (`18/35 = 51.4%`) and `maestro 2.11.0` (`14/35 = 40.0%`).
- **Per-task efficiency on those 7 shared tasks splits cleanly between wall time
  and token cost:** `agent-device 0.21.27` is faster at the per-task median on
  **5 of 7 tasks** (`64.1s` vs `80.6s` pooled median; `20` vs `21` turns), while
  `linc` is faster on **2 of 7** (`b5`, `b6`) and uses fewer uncached tokens at
  the median on **6 of 7 tasks** (`2.60M` vs `3.95M` total uncached tokens;
  `$34.22` vs `$47.93` total spend, or **`$1.01` vs `$1.41` per successful
  completion**).
- **The 22-point gap on the 9-task phone aggregate (`linc` 44/45 = 97.8% vs
  `agent-device` 34/45 = 75.6%) is a capability boundary, not a UI/logcat
  performance gap:** it comes entirely from `c10` and `c11`, which require
  inspecting local variables inside a running JVM stack frame (`linc-spectra`
  goes `10/10`, though every run hit a 10s tap timeout + Android ANR dialog while
  the UI thread was paused at the breakpoint; `agent-device` and `maestro` go
  `0/10`; `mobile-mcp` goes `2/10` by curve-fitting 7 rounded UI totals on `c10`).
- **On the 3 UI-only phone tasks (`a5, a6, c9`, `n=15`)** — the subset where
  `maestro` has every required primitive (no logcat or JDWP needed) — `linc`,
  `agent-device`, and `mobile-mcp` score **15/15 (100%)**, and `maestro 2.11.0`
  scores **13/15 (86.7%)** under strict regex grading (**14/15 = 93.3%** when
  `maestro/a6/run-2`'s contrastive answer mention is adjudicated as a pass).
- **On the `b11` Wear OS capability row (`n=5`, Galaxy Watch7):** `linc`
  (`50.8s` median), `maestro 2.11.0` (`61.0s`), and `agent-device 0.21.27`
  (`62.5s`) all score **5/5 (100%)**; `mobile-mcp 1.0.10` scores **4/5 (80%)**
  (watch display dimmed to ambient mode mid-flow in `run-4`).

> **What this benchmark does and does not show**
> - **Does show:** How four confined MCP tool surfaces behave across 600
>   reproducible runs (`v1`, `v2`, `v3`) on deterministic UI, logcat, Wear OS,
>   and JVM runtime-inspection tasks, with raw sanitized transcripts for every
>   cell.
> - **Does not show:** Generalization across arbitrary third-party apps or other
>   LLM families. It tests **one Jetpack Compose target app (`BenchTarget`)** and
>   **one pinned model (`claude-sonnet-5`)**; the task suite was authored by the
>   `linc` vendor; `linc-crucible` includes vendor-tuned MCP tool descriptions
>   whereas competitors ran with their stock shipped tool schemas; and with 5
>   repeated runs per task, single-cell differences (`5/5` vs `4/5`) are within
>   run-to-run noise.

---

## Scoreboard

### v3 (`v3-prereg`; 45 scored phone cells/tool + `b11` watch capability row)

Tasks are grouped below by **required tool capability** so capability boundaries
(`logcat` in Tier B; `JDWP` debugger in `c10`/`c11`) are visually distinct from
UI automation performance:

| task | tier | type | capability required | linc (`0.1.0`) | agent-device (`0.21.27`) | mobile-mcp (`1.0.10`) | maestro (`2.11.0`) |
|------|------|------|---------------------|----------------|--------------------------|-----------------------|--------------------|
| `a5` (deep-link / clipboard) | A | unseen | UI + deep-link | **5/5** | **5/5** | **5/5** | **5/5** |
| `a6` (multi-device ambiguity) | A | unseen | UI + device target | **5/5** | **5/5** | **5/5** | 4/5 *(5/5 adj.)* |
| `c9` (seeded defect ship-gate) | C | anchor | UI exploration | **5/5** | **5/5** | **5/5** | 4/5 |
| **3-TASK UI-ONLY SUBSET (`n=15`, exploratory)** | A, C | **UI only** | **UI only** | **15/15 (100%)** | **15/15 (100%)** | **15/15 (100%)** | **13/15 (86.7%)** *(14/15 adj.)* |
| `b5` (conditional crash triage) | B | anchor | UI + crash logcat | **5/5** | 4/5 | 2/5 *(3/5 adj.)* | 0/5 |
| `b6` (flaky sync counter) | B | anchor | UI + app logcat | 4/5 | **5/5** | 1/5 | 1/5 |
| `b9` (silent feature-flag gate) | B | unseen | UI + warn logcat | **5/5** | **5/5** | 0/5 | 0/5 |
| `b10` (main-thread stall audit) | B | unseen | UI + warn logcat | **5/5** | **5/5** | 0/5 | 0/5 |
| **7-TASK UI+LOGCAT SUBSET (`n=35`, pre-reg)** | A–C | **UI+logcat** | **UI + logcat** | **34/35 (97.1%)** | **34/35 (97.1%)** | 18/35 (51.4%) | 14/35 (40.0%) |
| *Cell-level 95% Wilson CI (`n=35`)* | — | — | — | *`[85.5%, 99.5%]`* | *`[85.5%, 99.5%]`* | *`[35.6%, 67.0%]`* | *`[25.6%, 56.4%]`* |
| `c10` (runtime variable inspect) | C | anchor | UI + JDWP locals | **5/5** | 0/5 | 2/5 *(UI math)* | 0/5 |
| `c11` (swallowed exception state) | C | unseen | UI + JDWP locals | **5/5** | 0/5 | 0/5 | 0/5 |
| **9-TASK PHONE TOTAL (`n=45`, pre-reg)** | A–C | **all phone** | **UI + logcat + JDWP** | **44/45 (97.8%)** | 34/45 (75.6%) | 20/45 (44.4%) | 14/45 (31.1%) |
| *Cell-level 95% Wilson CI (`n=45`)* | — | — | — | *`[88.4%, 99.6%]`* | *`[61.3%, 85.8%]`* | *`[30.9%, 58.8%]`* | *`[19.5%, 45.7%]`* |
| **4-TASK UNSEEN UI+LOGCAT (`n=20`, `a5,a6,b9,b10`, expl.)** | A–B | **unseen** | **UI + logcat** | **20/20 (100%)** | **20/20 (100%)** | 10/20 (50.0%) | 9/20 (45.0%) |
| **5-TASK UNSEEN PHONE (`n=25`, `a5,a6,b9,b10,c11`, pre-reg)** | A–C | **unseen** | **UI + logcat + JDWP** | **25/25 (100%)** | 20/25 (80.0%) | 10/25 (40.0%) | 9/25 (36.0%) |
| **4-TASK ANCHOR SUBSET (`n=20`, `b5,b6,c9,c10`, pre-reg)** | B–C | **anchors** | **UI + logcat + JDWP** | **19/20 (95.0%)** | 14/20 (70.0%) | 10/20 (50.0%) | 5/20 (25.0%) |
| `b11` (Wear OS capability row, `n=5`, pre-reg) | B | unseen (watch) | Wear OS UI | **5/5 (100%)** | **5/5 (100%)** | 4/5 (80%) *(5/5 adj.)* | **5/5 (100%)** |

*Statistical note on confidence intervals:* The Wilson 95% intervals above
measure **repeat-run binomial variance across `n=35` or `n=45` cells on these
fixed tasks**, not generalization across arbitrary tasks. Because cells are
clustered in 5-run groups across `K=7` (or `K=9`) tasks, task-level variance
dominates; within any single task (`n=5`), `5/5` (`95% CI [56.6%, 100%]`) vs
`4/5` (`[37.6%, 96.4%]`) and `1/5` vs `0/5` are indistinguishable from single-run
noise. Full v3 analysis: [`docs/v3-deep-dive.md`](docs/v3-deep-dive.md).

#### Sensitivity / adjudication table (judgment-call cells in v3)

All primary tables report strict automated harness grading. Three cells in v3
involved non-capability judgment calls or environmental factors; scoring all
three leniently changes no tool ranking on any subset:

| Cell | Strict automated | Lenient / adjudicated | What happened | Impact on tool total (strict → lenient) |
|---|---|---|---|---|
| `maestro/a6/run-2` | FAIL | PASS | Agent found `PHONE-NODE-742` on the phone after screenshotting the watch and wrote *"confirmed distinct from the smartwatch (which showed WATCH-NODE-999)"*, tripping the negative lookahead `(?!.*WATCH-NODE-999)`. | `maestro` 9-task: `14/45 → 15/45` (`31.1% → 33.3%`); 3-task UI-only: `13/15 → 14/15` (`86.7% → 93.3%`) |
| `mobile-mcp/b5/run-1` | FAIL (900s timeout) | Excluded or PASS | Ran in Wave 1 before per-cell `adb logcat -b all -c` was added; `mobile_list_crashes` saw an earlier cell's `Item 037` crash entry right after tapping `Item 001` and spent the remaining budget testing `Item 001..012` (`run-2..5` went `2/4` with clean buffers). | `mobile-mcp` 9-task: `20/45 → 20/44 (45.5%)` or `21/45 (46.7%)` |
| `mobile-mcp/b11/run-4` | FAIL | PASS | Galaxy Watch7 screen dimmed to ambient mode mid-flow on run 4; `mobile-mcp` has no wake/stayon primitive (`run-1,2,3,5` all passed). | `mobile-mcp` `b11` watch row: `4/5 → 5/5 (100%)` |

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

linc's single miss in both v2 (`b6/run-5`) and v3 (`b6/run-4`) is on `b6`: in v3
`b6/run-4`, the agent passed the package name (`tag='dev.lincforge.benchtarget'`)
to `nerve_logcat`, got 0 lines, and hypothesized a random startup draw instead
of the persisted launch counter.

### Cross-grid summary (`v1` vs `v2` vs `v3`)

Because `v3` changed the task mix (replacing the saturated Tier A tasks `a1–a3`
and `b7` with unseen tasks `a5, a6, b9, b10, c11`), upgraded all competitor
versions, and moved from Pixel 8 Pro (Android 14/15) to Galaxy S24 (Android 16),
overall grid percentages across `v2` and `v3` are not direct longitudinal
deltas. Only the **4 byte-identical anchor tasks (`b5`, `b6`, `c9`, `c10`)**
share identical prompts and verification predicates across all three grids:

| Grid / Subset | Hardware & OS | `linc` | `agent-device` | `mobile-mcp` | `maestro` |
|---|---|---|---|---|---|
| **v1** — 9-task phone (`n=45`) | Pixel 8 Pro (Android 14/15) | 33/45 (73.3%) | 32/45 (71.1%) | 25/45 (55.6%) | 26/45 (57.8%) |
| **v2** — 9-task phone (`n=45`) | Pixel 8 Pro (Android 14/15) | **44/45 (97.8%)** | 32/45 (71.1%) | 28/45 (62.2%) | 20/45 (44.4%) |
| **v3** — 9-task phone (`n=45`) | Galaxy S24 (Android 16) | **44/45 (97.8%)** | 34/45 (75.6%) | 20/45 (44.4%) | 14/45 (31.1%) |
| **v3** — 7-task UI+logcat (`n=35`) | Galaxy S24 (Android 16) | **34/35 (97.1%)** | **34/35 (97.1%)** | 18/35 (51.4%) | 14/35 (40.0%) |
| **4 shared anchors (`b5,b6,c9,c10`) in v2 (`n=20`)** | Pixel 8 Pro | **19/20 (95%)** | 9/20 (45%) | 8/20 (40%) | 4/20 (20%) |
| **4 shared anchors (`b5,b6,c9,c10`) in v3 (`n=20`)** | Galaxy S24 | **19/20 (95%)** | 14/20 (70%) | 10/20 (50%) | 5/20 (25%) |

On the 4 byte-identical anchors (`b5, b6, c9, c10`), the only statistically
significant single-task shift between v2 and v3 (Fisher's exact test `p = 0.0079`)
is `agent-device` on `c9` (`0/5` in v2 → **`5/5` in v3** under `0.21.27` on Galaxy S24).
Task files: [`tasks/`](tasks/) (v1/v2) and [`tasks_v3/`](tasks_v3/) (v3).

## Efficiency

### v3 per-task and aggregate efficiency (`n=35` UI+logcat subset & `n=45` 9-task phone grid)

Because pooled medians across a bimodal task suite (40s Tier A tasks vs 500s
Tier C tasks) are sensitive to task mix, the table below reports **both** the
pooled efficiency metrics and the **head-to-head per-task median wins** across
the 7 shared UI+logcat tasks (`a5, a6, b5, b6, b9, b10, c9`), alongside **total
API spend** and **cost per successful completion (`$/pass`)**:

| tool | med wall (`n=45` / `n=35`) | faster task medians (`7` UI+logcat tasks) | med uncached tok (`n=45` / `n=35`) | total uncached tok (`n=45` / `n=35`) | lower tok medians (`7` UI+logcat tasks) | total spend (`n=45` / `n=35`) | cost / pass (`n=45` / `n=35`) | timeouts (`n=45`) |
|------|----------------------------|-------------------------------------------|------------------------------------|--------------------------------------|-----------------------------------------|-------------------------------|-------------------------------|-------------------|
| linc (`0.1.0`) | **100.2s** / 80.6s | 2 / 7 (`b5, b6`) | **38.5k** / 57.6k | **2.95M** / **2.60M** | **6 / 7** (`a5,a6,b5,b6,b10,c9`) | **$37.50** / **$34.22** | **$0.85** / **$1.01** | **0** |
| agent-device (`0.21.27`) | 140.7s / **64.1s** | **5 / 7** (`a5,a6,b9,b10,c9`) | 122.3k / **54.7k** | 5.31M / 3.95M | 1 / 7 (`b9`) | $58.50 / $47.93 | $1.72 / $1.41 | **0** |
| maestro (`2.11.0`) | 172.4s / 181.1s | — | 80.6k / 86.6k | 3.88M / 3.22M | — | $34.56 / $29.61 | $2.47 / $2.12 | **0** |
| mobile-mcp (`1.0.10`) | 508.6s / 508.6s | — | 126.7k / 166.8k | 6.85M / 5.68M | — | $34.64 / $27.95 | $1.73 / $1.55 | 13 |

### v2 (`n=45` scored phone cells)

| tool | med wall | med uncached tok | med turns | med $/task | timeouts | solved-unfinalized |
|------|----------|------------------|-----------|------------|----------|--------------------|
| linc | **138s** | 41.3k | **26** | $0.57 | **0** | 0 |
| maestro | 145s | 42.5k | 25 | $0.47 | 1 | 0 |
| mobile-mcp | 172s | **29.6k** | 40 | $0.46 | 1 | 0 |
| agent-device | 161s | 82.6k | 40 | $1.08 | 2 | 1 |

v1, for contrast: linc 198s / 65.2k / 39 turns / $0.64 / **7 timeouts** ·
agent-device 233s / 77.9k / 62 turns / $1.19 / 3 · maestro 103s / 45.2k / 17
turns / $0.45 / 1 · mobile-mcp 117s / 29.2k / 28 turns / $0.49 / 1.

**v1's verdict — "linc is the most capable and the least efficient" — was
superseded once element extraction was fixed (`nerve #105`).** In v1, nerve
returned an empty UI-element tree on every linc run (`element_count: 0`, while
competitors extracted a populated tree 10/10 on the identical device+app),
forcing the agent into screenshot-only vision. That tax produced the 2× wall
time, the turn count, and the 7 timeouts — 5 of which *already contained the
full ground-truth answer in-transcript* (solved, but out of budget). With
element extraction fixed, `linc` recorded **0 timeouts across 100 consecutive
v2+v3 cells**.

In v3, comparing the two co-leaders on the 7 shared UI+logcat tasks (`34/35`
each):
- **Wall time favors `agent-device 0.21.27` on 5 of 7 tasks:** `agent-device` posts
  lower median wall times on `a5` (`40.9s` vs `58.3s`), `a6` (`34.3s` vs `43.7s`),
  `b9` (`47.8s` vs `76.0s`), `b10` (`57.6s` vs `67.1s`), and `c9` (`444.6s` vs
  `581.6s`), giving it a faster pooled 35-cell median (`64.1s` vs `80.6s`, `20` vs
  `21` median turns). `linc` is faster on `b5` (`304.7s` vs `322.5s`) and `2×`
  faster on `b6` (`232.1s` vs `470.6s`).
- **Token efficiency and dollar cost favor `linc` on 6 of 7 tasks:** `linc` uses
  fewer uncached tokens at the per-task median on `a5`, `a6`, `b5`, `b6`, `b10`,
  and `c9` (all except `b9`: `57.6k` vs `52.2k`), resulting in **34% fewer total
  uncached tokens** (`2.60M` vs `3.95M`) and **29% lower API cost per successful
  completion** (`$1.01/pass` vs `$1.41/pass` on the 7-task subset; `$0.85/pass`
  vs `$1.72/pass` across the 9-task phone grid). Note that the pooled 35-cell
  median uncached token column (`54.7k` for `agent-device` vs `57.6k` for `linc`)
  reverses the 6-of-7 per-task direction because the 18th sorted cell in each
  35-cell pool falls on `b9` (`52.2k` vs `57.6k`) — an example of Simpson's
  paradox in pooled multi-task medians.

Grid reproduction cost (`claude-sonnet-5` API spend): v1 **$216** (200 cells);
v2 **$209.02** (200 cells); v3 **$168.55** (200 cells: linc `$38.34`, maestro
`$35.14`, mobile-mcp `$35.66`, agent-device `$59.41`).

## What changed between the grids

### v2 → v3 (`v3-prereg` freeze)

Everything below landed **before** the `v3-prereg` tag (`2dc566d`) and is
documented in [`PREREGISTRATION-v3.md`](PREREGISTRATION-v3.md):

1. **Upgraded competitor releases & frozen `linc` stack:**
   - `linc`: `linc-nerve==0.1.0` installed from the public PyPI wheel
     (`LincForge/nerve@5477863`, wheel
     `sha256:747798cf8c869e4e0f6d49426faada97221cfd55e70fef540afa3fe2d949ca19`),
     paired with git-pinned `linc-crucible@cf04279` (one commit past v2's
     `a717296`, adding preflight/B2B packaging docs; no benchmark-task logic
     changes) and `linc-spectra@c471dad` (two commits past v2's `badcee7`:
     auto-detaching `spectra_method_locals` after capture so the paused target
     process resumes automatically, and MCP tool annotations).
   - `maestro`: upgraded `2.5.0` → **`2.11.0`**.
   - `@mobilenext/mobile-mcp`: upgraded `0.2.2` → **`1.0.10`** (which adds
     `mobile_get_device_logs` and `mobile_list_crashes`).
   - `agent-device`: upgraded `0.12.2` → **`0.21.27`**.
2. **Hybrid 10-task suite (`tasks_v3/`):**
   - **4 byte-identical v1/v2 anchors** (`b5`, `b6`, `c9`, `c10` — enforced by
     `test_all_committed_v3_tasks_load_and_anchors_are_byte_identical`).
   - **6 unseen zero-pilot tasks** (`a5` deep-link/clipboard/back-stack, `a6`
     multi-device ambiguity, `b9` silent feature-flag gate, `b10` main-thread
     stall audit, `c11` swallowed exception state, and `b11` Wear OS Burst-mode
     capability row). Target-app surfaces were unit-tested via `./gradlew test`
     and `adb` reset commands were smoke-checked before freeze, with zero prior
     LLM agent runs on any of the 4 stacks.
3. **v3 harness hardening & execution order (applied symmetrically to all 4 tools):**
   - **Wave execution order:** Runs executed in 5 interleaved waves (`run-1`
     through `run-5`), iterating through tasks `a5..c11` in deterministic tool
     order (`linc → maestro → mobile-mcp → agent-device`) with full per-cell
     package/state reset between cells.
   - **Pre/post lock-screen guard (`device.is_device_locked`):** every cell
     verifies the target device is unlocked before launch and records
     `device_locked_pre` and `device_locked_post` in `meta.json` (`0/200`
     locked cells across v3).
   - **Per-cell logcat ring-buffer hygiene (`adb logcat -b all -c`):** clears
     `main`, `system`, `events`, and `crash` buffers before every cell so an
     earlier cell's crash (`b5`) or diagnostic log (`b9`/`b10`) cannot leak into
     a subsequent tool's `mobile_list_crashes` or `logcat` read.

### v1 → v2 (`v2-prereg` freeze)

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

Budget unchanged: 900s (600s for Tier A); a timeout remains FAIL for every
scored metric.

## Findings

### v3 Rematch — What Changed on Unseen Tasks & Upgraded Competitors

Full analysis in [`docs/v3-deep-dive.md`](docs/v3-deep-dive.md). Summary of the
four primary findings:

1. **On the 7-task UI + logcat phone subset (`n=35`), `agent-device 0.21.27`
   and `linc` match on completion (`34/35 = 97.1%` each).** Under `0.21.27` on
   Galaxy S24, `agent-device` went `5/5` on `c9` (up from `0/5` in v2) and
   scored `5/5` on `a5`, `a6`, `b6`, `b9`, `b10`, and `c9` (`4/5` on `b5`),
   posting faster per-task median wall times on 5 of the 7 tasks (`64.1s` vs
   `80.6s` pooled median), while `linc` posted lower per-task median uncached
   tokens on 6 of the 7 tasks (`2.60M` vs `3.95M` total uncached tokens;
   `$1.01/pass` vs `$1.41/pass`).
2. **Why `@mobilenext/mobile-mcp 1.0.10` unlocked `b6` (`0/5` → `1/5`) yet
   timed out `10/10` on `b9` and `b10`:** v1.0.10's new `mobile_get_device_logs`
   tool invokes `logcat -v threadtime,year -T 1` without `-d` (directly observed
   in the `adbd` log line captured inside
   `results_v3/mobile-mcp/b10/run-1/transcript.jsonl`), which starts streaming
   from the last 1 line of historical logcat and waits for `limit` matching lines
   to arrive. Because the synchronous `Log.w` lines in `b9` (`Run Health Check`)
   and `b10` (`Compact Local DB`) are emitted inside the button `onClick`
   handler *before* the subsequent `mobile_get_device_logs` tool call opens its
   logcat stream (and with no per-call timeout when a `message=` filter matches
   zero future lines), the tool call blocks until the harness kills the run at
   900s. By contrast, `linc-nerve` (`nerve_logcat`) and `agent-device` (`logs`)
   dump the historical ring buffer (`logcat -d`), going `10/10` each across `b9`
   and `b10`.
3. **`c10` (`5/0/2/0`) vs `c11` (`5/0/0/0`) — algebraic curve-fitting vs
   runtime stack-frame inspection:** In `mobile-mcp/c10/run-4` (`579.1s`,
   `34,512` output tokens) and `run-5` (`855.0s`, `46,356` output tokens),
   `claude-sonnet-5` solved `c10` without a debugger by tapping `Apply Discount`
   across quantities `q = 1..7`, recording the 7 rounded integer UI totals
   `(9, 17, 25, 32, 39, 44, 50)`, and solving the 7 rounding intervals to
   recover `1 - 0.035q = 0.755` (`9.3×`–`12.5×` the output tokens and `6×`–`8.5×`
   the wall time of `linc`'s `100.2s` JDWP stack-frame read). On `c11`
   (`c11-caught-exception-state`), the swallowed `PromoExpiredException` catch
   block displays a static `"Promo code expired"` string and has no UI-observable
   channel by design for `auditToken` (`PROMO-BENCH26-7956`) or `rebateCents`
   (`1355`): `linc` went **5/5 (`119.5s` median)** while `agent-device`,
   `mobile-mcp`, and `maestro` went **0/15 combined**.
4. **Score-once `linc` defects surfaced in v3 (disclosed, zero re-runs):**
   Scoring the frozen `linc` stack once surfaced two concrete defects in `linc`'s
   own column that are left unscored/unpatched in `results_v3/`:
   - **`nerve_logcat` package-name filter trap (caused `linc/b6/run-4` FAIL):**
     Across 16 calls in `b5`, `b6`, `b9`, `b10`, and `c9`, agents passed the
     package name (`tag='dev.lincforge.benchtarget'`) or a lowercase/message
     string to `nerve_logcat`'s `tag` parameter (`adb logcat -s <tag>`),
     receiving 0 lines; in `b6/run-4`, that caused the agent to abandon logcat
     and guess a random draw.
   - **UI-thread breakpoint suspension & ANR dialog on every `c10` and `c11` run:**
     Although `linc` passed `10/10` across `c10` and `c11`, arming
     `spectra_method_breakpoint` on a UI-triggered ViewModel method paused the
     app's main thread inside `onClick` while `nerve_tap` was still waiting for
     `adb shell input tap` to return. Every single `c10` and `c11` run hit a 10s
     `nerve_tap` read timeout (`{"error":"Tap failed: adb read timeout"}`) and
     triggered Android's 5s input-dispatch ANR dialog (`"Wait"`), which only
     cleared after `spectra_method_locals` auto-resumed the process.

### v2 Findings — `c10`, `c9`, Tier B, `a4`, and `b8`

#### c10 — the marquee flip (0/0/0/0 → 5/0/0/0 in v2)

v1: no tool could read the runtime `discountFactor` (0.755) from the running
process; linc invoked spectra hard (up to 19 attaches per run) and still
couldn't, because source breakpoints required a retired registration system.
That 0/5 was published as a loss with the root cause filed.

v2: linc 5/5 at a **122s median**. The transcripts show the same shape every
run: drive the UI to the exact state, arm `spectra_method_breakpoint` on
`CheckoutViewModel.applyDiscount` by name (zero-config, no source
registration), trigger the interaction, read locals, detach cleanly
(`spectra_sessions` → 0). Every competitor: 0/5 in v2.

#### c9 — ship-gate (linc 2/5 → 5/5; mobile-mcp 0/5 → 5/5 in v2; agent-device 0/5 → 5/5 in v3)

linc's v1 c9 losses were timeout conversions — the tier defect was localized
in-transcript but the vision-scrolling tax exhausted the budget. With elements
readable it finishes 5/5 at a 590s median in v2 (`581.6s` in v3). mobile-mcp's
jump to 5/5 in v2 (and 5/5 in v3) is its own: element tree plus methodical
screen-by-screen sweeps found both the export crash and the tier-propagation
bug reliably. maestro repeats its v1/v2/v3 strength (4/5 across all three grids).
agent-device's 0/5 in v1/v2 flipped to **5/5 in v3** (`0.21.27`).

#### Tier B — device observability still decides it

- **b6 (flake root-cause; ground truth is a persisted launch counter):** linc
  4/5 (v2 and v3) and agent-device 4/5 in v2 → **5/5 in v3**. In v2, maestro and
  mobile-mcp went 0/10 combined; in v3, each scored **1/5** (`mobile-mcp/b6/run-1`
  via `mobile_get_device_logs`; `maestro/b6/run-3` by tabulating 6 consecutive
  `clearState: false` launches and spotting runs 3 and 6 missing the button).
- **b7 (cold-start timing + variance, v1/v2):** linc and agent-device 5/5.
  mobile-mcp 0/5 — no shell surface for `am start -W`. maestro 1/5.
- **b5 (crash repro from a vague report):** linc 1/5 (v1) → **5/5** (v2 and v3).
  agent-device 5/5 (v1, v2) and 4/5 (v3). mobile-mcp 5/5 (v1) → 3/5 (v2) → 2/5
  (v3). maestro 0/5 across all three grids.

#### a4 (v2) & a6 (v3) — multi-device disambiguation

In v2 (`a4`), because `b8` ran first, the watch carried `BenchTarget`, turning
`a4` into an accidental multi-device test (`linc` 5/5, `mobile-mcp` 5/5,
`agent-device` 3/5, `maestro` 0/5). In v3 (`a6`), multi-device disambiguation
was pre-registered as an explicit task (`PHONE-NODE-742` vs `WATCH-NODE-999`):
`linc`, `mobile-mcp`, and `agent-device` all went **5/5**, and `maestro 2.11.0`
improved to **4/5** (in `a6/run-2`, `maestro` found `PHONE-NODE-742` on the
phone after screenshotting the watch first, and echoed `WATCH-NODE-999` in its
comparison sentence, tripping the negative lookahead).

#### b8 (v1/v2) & b11 (v3) — Wear OS capability rows (reported separately, never averaged)

- **v2 (`b8`, Pixel Watch 2):** linc 5/5 at 40.6s median · mobile-mcp 5/5 ·
  agent-device 4/5 · maestro 2/5.
- **v3 (`b11`, Galaxy Watch7 `SM-L300`):** linc **5/5** at **50.8s median**
  (fastest) · maestro **5/5** at 61.0s median · agent-device **5/5** at 62.5s
  median · mobile-mcp **4/5** at 98.2s median (watch display dimmed to ambient
  mode mid-flow in `run-4`).

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

### v3 — zero voided cells, one disclosed Wave-1 crash-buffer carry-over

All 200 v3 cells ran to completion with `device_locked_pre = false` and
`device_locked_post = false` (`0/200` locked cells) and zero mid-grid code
changes. One cross-cell state observation from Wave 1 is disclosed:

- **Cross-cell `logcat -b crash` carry-over on `mobile-mcp/b5/run-1`:** In Wave 1,
  `linc/b5/run-1` triggered the `Item 037` crash (`IllegalStateException`),
  which remained in Android's persistent `crash` ring buffer during
  `maestro/b5/run-1` (which cannot read logs) and into `mobile-mcp/b5/run-1`.
  When `mobile-mcp/b5/run-1` called `mobile_list_crashes` right after tapping
  `Item 001`, it saw the earlier `Item 037` crash entry and misattributed it to
  `Item 001`, spending the rest of its 900s budget re-testing `Item 001..012`.
  Per-cell `adb logcat -b all -c` hygiene was added for all subsequent cells
  (where `mobile-mcp` went `2/4` on `b5/run-2..5`), and per the pre-registered
  score-once rule, `mobile-mcp/b5/run-1` stands in `results_v3/` as ran.

## Per-cell detail

### v3 (`BENCH_RESULTS_DIR=results_v3 BENCH_TASKS_DIR=tasks_v3 uv run bench report`)

| tool | task | tier | runs | pass | solved-unfin | median wall s | median billed | median uncached | median output | wall stdev |
|---|---|---|---|---|---|---|---|---|---|---|
| agent-device | a5 | A | 5 | 5/5 | 0 | 40.9 | 290,711 | 33,395 | 1,523 | 17.1 |
| agent-device | a6 | A | 5 | 5/5 | 0 | 34.3 | 250,627 | 30,699 | 1,610 | 7.1 |
| agent-device | b10 | B | 5 | 5/5 | 0 | 57.6 | 498,075 | 44,932 | 2,492 | 9.0 |
| agent-device | b11 (capability row) | B | 5 | 5/5 | 0 | 62.5 | 365,034 | 28,143 | 2,305 | 9.2 |
| agent-device | b5 | B | 5 | 4/5 | 0 | 322.5 | 5,867,073 | 151,893 | 17,245 | 112.2 |
| agent-device | b6 | B | 5 | 5/5 | 0 | 470.6 | 7,814,409 | 202,675 | 27,296 | 78.2 |
| agent-device | b9 | B | 5 | 5/5 | 0 | 47.8 | 560,855 | 52,244 | 2,480 | 15.2 |
| agent-device | c10 | C | 5 | 0/5 | 0 | 268.7 | 2,418,531 | 149,000 | 15,709 | 65.4 |
| agent-device | c11 | C | 5 | 0/5 | 0 | 140.7 | 1,687,222 | 125,517 | 7,828 | 19.9 |
| agent-device | c9 | C | 5 | 5/5 | 0 | 444.6 | 15,506,543 | 238,210 | 24,572 | 68.4 |
| linc | a5 | A | 5 | 5/5 | 0 | 58.3 | 418,280 | 24,676 | 2,075 | 5.1 |
| linc | a6 | A | 5 | 5/5 | 0 | 43.7 | 255,203 | 20,286 | 1,581 | 4.4 |
| linc | b10 | B | 5 | 5/5 | 0 | 67.1 | 512,322 | 29,224 | 2,797 | 14.6 |
| linc | b11 (capability row) | B | 5 | 5/5 | 0 | 50.8 | 343,805 | 21,118 | 1,855 | 12.4 |
| linc | b5 | B | 5 | 5/5 | 0 | 304.7 | 6,261,414 | 128,556 | 15,454 | 54.3 |
| linc | b6 | B | 5 | 4/5 | 0 | 232.1 | 2,598,168 | 84,154 | 13,733 | 64.2 |
| linc | b9 | B | 5 | 5/5 | 0 | 76.0 | 637,237 | 57,579 | 3,219 | 17.3 |
| linc | c10 | C | 5 | 5/5 | 0 | 100.2 | 854,808 | 37,090 | 3,703 | 15.8 |
| linc | c11 | C | 5 | 5/5 | 0 | 119.5 | 817,245 | 36,661 | 5,173 | 6.6 |
| linc | c9 | C | 5 | 5/5 | 0 | 581.6 | 11,261,634 | 165,001 | 26,729 | 113.7 |
| maestro | a5 | A | 5 | 5/5 | 0 | 52.9 | 401,797 | 34,877 | 1,506 | 6.2 |
| maestro | a6 | A | 5 | 4/5 | 0 | 61.6 | 328,610 | 31,508 | 1,868 | 9.5 |
| maestro | b10 | B | 5 | 0/5 | 0 | 165.4 | 1,145,709 | 80,629 | 10,309 | 103.3 |
| maestro | b11 (capability row) | B | 5 | 5/5 | 0 | 61.0 | 215,166 | 15,772 | 1,422 | 4.8 |
| maestro | b5 | B | 5 | 0/5 | 0 | 298.5 | 2,931,775 | 125,853 | 13,649 | 92.8 |
| maestro | b6 | B | 5 | 1/5 | 0 | 218.3 | 1,178,377 | 86,595 | 12,663 | 149.7 |
| maestro | b9 | B | 5 | 0/5 | 0 | 223.5 | 1,605,632 | 101,354 | 13,168 | 68.4 |
| maestro | c10 | C | 5 | 0/5 | 0 | 230.7 | 853,855 | 83,657 | 12,884 | 62.7 |
| maestro | c11 | C | 5 | 0/5 | 0 | 72.1 | 267,501 | 41,772 | 3,837 | 5.4 |
| maestro | c9 | C | 5 | 4/5 | 0 | 327.9 | 6,742,018 | 178,488 | 16,598 | 95.9 |
| mobile-mcp | a5 | A | 5 | 5/5 | 0 | 60.6 | 472,961 | 29,700 | 2,227 | 4.7 |
| mobile-mcp | a6 | A | 5 | 5/5 | 0 | 34.7 | 199,276 | 17,890 | 1,320 | 3.1 |
| mobile-mcp | b10 | B | 5 | 0/5 | 0 | 900.0 | 3,953,449 | 232,787 | 503 | 0.0 |
| mobile-mcp | b11 (capability row) | B | 5 | 4/5 | 0 | 98.2 | 236,277 | 12,353 | 1,683 | 177.1 |
| mobile-mcp | b5 | B | 5 | 2/5 | 0 | 900.0 | 15,954,098 | 374,877 | 6,721 | 344.0 |
| mobile-mcp | b6 | B | 5 | 1/5 | 0 | 472.4 | 2,194,208 | 75,647 | 15,073 | 87.1 |
| mobile-mcp | b9 | B | 5 | 0/5 | 0 | 900.0 | 5,380,403 | 224,915 | 566 | 0.0 |
| mobile-mcp | c10 | C | 5 | 2/5 | 0 | 607.0 | 2,195,463 | 143,778 | 41,813 | 130.3 |
| mobile-mcp | c11 | C | 5 | 0/5 | 0 | 235.3 | 692,142 | 61,392 | 7,318 | 70.9 |
| mobile-mcp | c9 | C | 5 | 5/5 | 0 | 508.6 | 11,502,981 | 187,221 | 27,736 | 28.0 |

### v2 (`BENCH_RESULTS_DIR=results_v2`)

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
is the real signal**, as in v1 and v2. Deep-dive reports:
[`docs/v1-deep-dive.md`](docs/v1-deep-dive.md),
[`docs/v2-deep-dive.md`](docs/v2-deep-dive.md), and
[`docs/v3-deep-dive.md`](docs/v3-deep-dive.md).

## Limitations / threats to validity

Carried forward across all three grids:

- **Single model, single app.** One Compose app (`BenchTarget`), one model
  (`claude-sonnet-5`, invoked via `claude --model claude-sonnet-5` in Claude Code
  `2.1.296` with default CLI sampling parameters), across two physical device
  pairs (Pixel 8 Pro + Pixel Watch 2 in v1/v2; Samsung Galaxy S24 `SM-S921U` +
  Galaxy Watch7 `SM-L300` in v3). Generalization to third-party production apps,
  other UI toolkits, and other models remains open.
- **Clustered sample size (`K=9` tasks × `5` reps).** Each grid has 45 scored
  phone cells per tool, but those 45 cells are 5 repeated runs clustered within
  9 tasks. Between-task variance is much larger than within-task run variance;
  within a single task (`n=5`), `5/5` (`[56.6%, 100%]`) vs `4/5` (`[37.6%,
  96.4%]`) and `1/5` vs `0/5` are within single-run noise.
- **Regex answer-grading** cannot always distinguish "affirms X" from
  "mentions X in a comparison sentence" (e.g., `maestro/a6/run-2`, which found
  `PHONE-NODE-742` on the phone after screenshotting the watch and echoed
  `WATCH-NODE-999` by way of contrast, tripping the negative lookahead — shown
  in the Sensitivity / Adjudication table above). Frozen
  `match_samples`/`reject_samples` validate every pattern at load time.
- **Fixed 900s budget.** Unchanged across v1, v2, and v3 for comparability.
- **Confinement is a model of real usage, not real usage.** A real operator
  usually has a shell; this benchmark deliberately measures the *structured
  tool surface* alone.
- **Vendor authorship, tool-description tuning & task-selection asymmetry (v1–v3).**
  While v3 remediated v2's "take-home retest on seen tasks and older competitor
  versions" by upgrading every competitor to its latest release, introducing 6
  unseen zero-pilot tasks (`a5, a6, b9, b10, c11, b11`), and scoring the frozen
  `linc` stack once with zero post-fix re-runs, the unseen tasks were still
  authored by LINC engineers who know the capabilities of `linc-nerve` and
  `linc-spectra`, and `linc-crucible` includes vendor-authored MCP tool
  descriptions whereas competitors ran with their stock shipped tool schemas.
  That is why v3 leads with the **7-task UI + logcat phone subset (`n=35`, where
  `linc` and `agent-device 0.21.27` match at `34/35 = 97.1%`)** and the **3-task
  UI-only subset (`n=15`, where `maestro 2.11.0` scores `13/15` strict / `14/15`
  adjudicated)** alongside the 9-task aggregate.

## Verification & reproducibility checklist

- [x] **v1 (`results/`):** all 200 cells complete under `v1-prereg`, every
  published cell `Monitor=0`; errata #1–3 documented and remediated in
  [`AMENDMENTS.md`](AMENDMENTS.md); contaminated cells voided into
  `results_invalid/` and re-run.
- [x] **v2 (`results_v2/`):** all 200 cells complete under `v2-prereg` (stack
  pins `nerve@783fc88` / `spectra@badcee7` / `crucible@a717296`), four
  interference classes disclosed and voided pre-publication, per-cell hygiene
  and APK digest receipts in `meta.json`.
- [x] **v3 (`results_v3/`):** all 200 cells complete under `v3-prereg`
  (`2dc566d`; `linc-nerve==0.1.0` PyPI wheel
  `sha256:747798cf8c869e4e0f6d49426faada97221cfd55e70fef540afa3fe2d949ca19` +
  `crucible@cf04279` + `spectra@c471dad`; `maestro 2.11.0`;
  `@mobilenext/mobile-mcp 1.0.10`; `agent-device 0.21.27`), `0/200` locked-device
  cells (`device_locked_pre/post` verified), scored once with zero post-fix
  re-runs.
- [x] **Sanitization & test suite (`uv run pytest`):** 59 automated checks
  verifying APK digest pins, answer-verifier positive/negative samples, anchor
  task byte-identity (`v1/v2` ↔ `v3`), and zero leaked device serials or local
  hostnames across all 600 published cell transcripts.


