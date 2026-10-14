# mobile-agent-bench v3 — deep-dive findings (complete 200-cell rematch)

_Scope: full pre-registered v3 grid (200/200 rows) — linc / maestro / mobile-mcp /
agent-device on a5, a6, b5, b6, b9, b10, c9, c10, c11 + the b11 Wear OS capability row,
claude-sonnet-5 (`Claude Code 2.1.296`), Samsung Galaxy S24 (`SM-S921U`, Android 16 / SDK 36)
+ Samsung Galaxy Watch7 (`SM-L300`, Wear OS 6 / Android 16 / SDK 36), protocol frozen at tag
`v3-prereg` (`PREREGISTRATION-v3.md`, commit `2dc566d`). Contestant versions: `linc-nerve==0.1.0`
from PyPI (`LincForge/nerve@5477863`), `linc-crucible@cf04279`, `linc-spectra@c471dad`;
`maestro 2.11.0`; `@mobilenext/mobile-mcp 1.0.10`; `agent-device 0.21.27`. Scored once on the
frozen stack with zero post-fix re-runs._

## Why v3 exists

v2's `Limitations` section named the structural validity threat of the v1→v2 arc:
the vendor had fixed defects on tasks (`a1–c10`) it had already seen fail, and
competitors (`maestro 2.5.0`, `mobile-mcp 0.2.2`, `agent-device 0.12.2`) were not
re-tested on newer upstream releases. v3 directly addresses that threat along three
axes:

1. **Upgraded competitor baselines:** `maestro` (`2.5.0` → `2.11.0`),
   `@mobilenext/mobile-mcp` (`0.2.2` → `1.0.10`, adding `mobile_get_device_logs`
   and `mobile_list_crashes`), and `agent-device` (`0.12.2` → `0.21.27`).
2. **Hybrid 10-task suite (`tasks_v3/`):** 4 byte-identical v1/v2 anchor tasks
   (`b5`, `b6`, `c9`, `c10`) to measure longitudinal competitor movement + 6
   unseen zero-pilot tasks (`a5`, `a6`, `b9`, `b10`, `c11`, and the `b11` Wear OS
   capability row) authored and frozen before any comparative cell ran.
3. **Score once on frozen stack ("improvements as we discover them"):** The `linc`
   column ran against the published PyPI `linc-nerve==0.1.0` wheel and pinned
   `crucible`/`spectra` SHAs, and was scored **once and only once**. Every `linc`
   defect or friction surfaced by the 200-cell run was routed into the improvement
   backlog without re-running the grid.

## Scoreboard (harness-verified, `BENCH_RESULTS_DIR=results_v3 BENCH_TASKS_DIR=tasks_v3`)

| task | tier | type | linc | agent-device (`0.21.27`) | mobile-mcp (`1.0.10`) | maestro (`2.11.0`) | note |
|------|------|------|------|--------------------------|-----------------------|--------------------|------|
| `a5` | A | unseen | **5/5** | **5/5** | **5/5** | **5/5** | deep-link / clipboard / back-stack recovery |
| `a6` | A | unseen | **5/5** | **5/5** | **5/5** | 4/5 | multi-device ambiguity (watch + phone on bus) |
| `b5` | B | anchor | **5/5** | 4/5 | 2/5 | 0/5 | crash repro from vague report (`Item 037`) |
| `b6` | B | anchor | 4/5 | **5/5** | 1/5 | 1/5 | flake root-cause (persisted launch counter mod 3) |
| `b9` | B | unseen | **5/5** | **5/5** | 0/5 | 0/5 | silent feature-flag gate (`DIAG_VERBOSE_V3=disabled`) |
| `b10` | B | unseen | **5/5** | **5/5** | 0/5 | 0/5 | main-thread stall audit (`Compact Local DB`, 420ms) |
| `c9` | C | anchor | **5/5** | **5/5** | **5/5** | 4/5 | seeded ship-gate (`Pro` → `Basic` tier truncation) |
| `c10` | C | anchor | **5/5** | 0/5 | 2/5 | 0/5 | runtime variable inspect (`discountFactor = 0.755`) |
| `c11` | C | unseen | **5/5** | 0/5 | 0/5 | 0/5 | swallowed exception state (`PROMO-BENCH26-7956`, `1355`) |
| **9-Task Phone Aggregate** | A–C | **45 cells/tool** | **44/45 (97.8%)** | **34/45 (75.6%)** | **20/45 (44.4%)** | **14/45 (31.1%)** | Wilson 95% CI: linc `[88.4%, 99.6%]` vs agent-device `[61.3%, 85.8%]` |
| **7-Task UI+Logcat Subset** | A–C | **35 cells/tool** (excl. `c10, c11`) | **34/35 (97.1%)** | **34/35 (97.1%)** | **18/35 (51.4%)** | **14/35 (40.0%)** | **Tied at 34/35 (97.1%)** between `linc` and `agent-device` |
| **5-Task Unseen Phone Subset** | A–C | **25 cells/tool** (`a5,a6,b9,b10,c11`) | **25/25 (100.0%)** | **20/25 (80.0%)** | **10/25 (40.0%)** | **9/25 (36.0%)** | zero-pilot unseen tasks |
| **4-Task Anchor Subset** | B–C | **20 cells/tool** (`b5,b6,c9,c10`) | **19/20 (95.0%)** | **14/20 (70.0%)** | **10/20 (50.0%)** | **5/20 (25.0%)** | byte-identical to v1/v2 |
| `b11` (capability row) | B | unseen (watch) | **5/5 (100%)** | **5/5 (100%)** | 4/5 (80%) | **5/5 (100%)** | Galaxy Watch7 (`SM-L300`); reported separately |

## Dual Aggregate Analysis (Pre-Registered)

Per `PREREGISTRATION-v3.md`, because `c10` and `c11` require JDWP runtime frame
inspection (`linc-spectra`), we report both the full 9-task phone aggregate and the
7-task UI + logcat phone subset side by side:

| Metric | Subset | `linc` | `agent-device` (`0.21.27`) | `mobile-mcp` (`1.0.10`) | `maestro` (`2.11.0`) |
|---|---|---|---|---|---|
| **Pass rate (cell-level 95% Wilson CI)** | 7-task UI+logcat (`n=35`, pre-reg) | **34/35 — 97.1%** (`[85.5%, 99.5%]`) | **34/35 — 97.1%** (`[85.5%, 99.5%]`) | 18/35 — 51.4% (`[35.6%, 67.0%]`) | 14/35 — 40.0% (`[25.6%, 56.4%]`) |
| **Pass rate (cell-level 95% Wilson CI)** | 9-task phone (`n=45`, pre-reg) | **44/45 — 97.8%** (`[88.4%, 99.6%]`) | 34/45 — 75.6% (`[61.3%, 85.8%]`) | 20/45 — 44.4% (`[30.9%, 58.8%]`) | 14/45 — 31.1% (`[19.5%, 45.7%]`) |
| **Pass rate** | 3-task UI-only (`n=15`, `a5,a6,c9`, expl.) | **15/15 — 100%** | **15/15 — 100%** | **15/15 — 100%** | **13/15 — 86.7%** *(14/15 adj.)* |
| **Pass rate** | 4-task unseen UI+logcat (`n=20`, `a5,a6,b9,b10`, expl.) | **20/20 — 100%** | **20/20 — 100%** | 10/20 — 50.0% | 9/20 — 45.0% |
| **Pass rate (cell-level 95% Wilson CI)** | 5-task unseen phone (`n=25`, `a5,a6,b9,b10,c11`, pre-reg) | **25/25 — 100.0%** (`[86.7%, 100.0%]`) | 20/25 — 80.0% (`[60.9%, 91.1%]`) | 10/25 — 40.0% (`[23.4%, 59.3%]`) | 9/25 — 36.0% (`[20.2%, 55.5%]`) |
| **Faster per-task median wall time** | 7 UI+logcat tasks | 2 / 7 (`b5, b6`) | **5 / 7** (`a5,a6,b9,b10,c9`) | — | — |
| **Pooled median wall time** | 9-task / 7-task | **100.2s** / 80.6s | 140.7s / **64.1s** | 508.6s / 508.6s | 172.4s / 181.1s |
| **Lower per-task median uncached tokens** | 7 UI+logcat tasks | **6 / 7** (`a5,a6,b5,b6,b10,c9`) | 1 / 7 (`b9`) | — | — |
| **Pooled median uncached tokens** | 9-task / 7-task | **38.5k** / 57.6k | 122.3k / **54.7k** | 126.7k / 166.8k | 80.6k / 86.6k |
| **Total uncached tokens** | 9-task / 7-task | **2.95M** / **2.60M** | 5.31M / 3.95M | 6.85M / 5.68M | 3.88M / 3.22M |
| **Median turns** | 9-task / 7-task | **22** / 21 | 27 / **20** | 57 / 72 | 24 / 27 |
| **Cost per successful completion (`$/pass`)** | 9-task / 7-task | **$0.85** / **$1.01** | $1.72 / $1.41 | $1.73 / $1.55 | $2.47 / $2.12 |
| **Total API spend** | 9-task / 7-task / all 50 | **$37.50** / **$34.22** / **$38.34** | $58.50 / $47.93 / $59.41 | $34.64 / $27.95 / $35.66 | $34.56 / $29.61 / $35.14 |
| **Timeouts (900s)** | 9-task (`n=45`) | **0** | **0** | 13 | **0** |

Two headlines emerge from the dual view:

1. **On UI + logcat tasks (`n=35`), `agent-device 0.21.27` and `linc` match on
   completion (`34/35 = 97.1%` each: 1 win, 1 loss, 5 ties).** Under `0.21.27` on
   Galaxy S24, `agent-device` went `5/5` on `c9` (up from `0/5` in v2) and scored
   `5/5` on `a5`, `a6`, `b6`, `b9`, `b10`, and `c9` (`4/5` on `b5`). Across those
   7 shared tasks, `agent-device` posts faster per-task median wall times on **5
   of 7 tasks** (`64.1s` vs `80.6s` pooled median; `20` vs `21` turns), while
   `linc` is faster on **2 of 7** (`b5`, `b6`) and posts lower per-task median
   uncached tokens on **6 of 7 tasks**, consuming **34% fewer total uncached
   tokens** (`2.60M` vs `3.95M`) and **29% lower API cost per successful
   completion** (`$1.01/pass` vs `$1.41/pass`).
2. **The 22-point gap on the full 9-task phone grid (`44/45` vs `34/45`) and the
   5-cell gap on the 5 unseen phone tasks (`25/25` vs `20/25`) are entirely a
   debugger capability boundary (`c10`, `c11`).** On the 4 non-debugger unseen
   phone tasks (`a5, a6, b9, b10`), both `linc` and `agent-device` score `20/20`.
   On `c10` and `c11`, which require reading local variables from a running JVM
   stack frame, `linc-spectra` goes `10/10` while `agent-device` and `maestro` go
   `0/10` (`mobile-mcp` goes `2/10` via algebraic curve-fitting on `c10`).

## Key Technical Findings by Task & Competitor

### 1. Why `@mobilenext/mobile-mcp 1.0.10` unlocked `b6` (`0/5` → `1/5`) yet timed out 10/10 on `b9` and `b10`

`@mobilenext/mobile-mcp 1.0.10` added two major observability tools over `0.2.2`:
`mobile_get_device_logs` and `mobile_list_crashes`. On `b5` (`run-2`, `run-3`),
`mobile_list_crashes` read the Android crash buffer directly after `Item 037`
threw `IllegalStateException: detail_Render_overflow: item=37`, solving `b5` in
`198.1s` (`run-2`). On `b6/run-1`, `mobile_get_device_logs` captured the
`SyncComponent init: launchCount=...` log line during cold launch (`1/5` PASS vs
`0/5` in v2).

Yet on `b9` (silent feature-flag gate) and `b10` (main-thread stall audit),
`mobile-mcp 1.0.10` hit the **900.0s timeout on all 10 runs (`0/10`)**. What is
directly observed in `results_v3/mobile-mcp/b10/run-1/transcript.jsonl` is the
`adbd` log line captured during an earlier unfiltered call:

```
adbd service requested 'shell,v2,TERM=dumb:export ANDROID_LOG_TAGS=''; exec logcat '-v' 'threadtime,year' '-T' '1''
```

and the subsequent filtered `mobile_get_device_logs(filter: ["message=blocked_ms"])`
call blocking until the harness killed the run at `900.0s`. Unlike `logcat -d`
(which dumps the historical ring buffer and exits immediately), `logcat -T 1`
starts streaming from the last 1 line of historical logcat and waits for `limit`
matching lines to arrive. Because the synchronous `Log.w` lines in `b9` (`Run
Health Check`) and `b10` (`Compact Local DB`) are emitted inside the button's
`onClick` handler *before* the subsequent `mobile_get_device_logs` tool call opens
its logcat stream (and with no per-call timeout when a `message=` filter matches
zero future lines), the call hangs until the cell budget expires. By contrast,
`linc-nerve` (`nerve_logcat`) and `agent-device` (`logs`) dump the historical
ring buffer (`logcat -d`), going `10/10` each across `b9` and `b10`.

### 2. `c10` vs `c11`: Algebraic curve-fitting vs runtime stack-frame inspection

On `c10` (`c10-runtime-variable-inspect`, v1/v2 anchor), `linc` set a zero-config
method breakpoint on `CheckoutViewModel.applyDiscount`, tapped `Apply Discount` at
quantity 7, and read `discountFactor = "0.755"` and `totalDollars = "50"` directly
from the paused JVM stack frame (`5/5`, `100.2s` median wall, `3,703` median output
tokens).

In `mobile-mcp/c10/run-4` (`579.1s`, `34,512` output tokens) and
`mobile-mcp/c10/run-5` (`855.0s`, `46,356` output tokens), `claude-sonnet-5`
passed `c10` (`2/5`) **without a debugger**: the agent tapped `Apply Discount` at
every quantity `q = 1..7`, recorded the 7 rounded integer UI totals
`(9, 17, 25, 32, 39, 44, 50)`, wrote out the 7 simultaneous rounding intervals
`9.37 × q × f(q) ∈ [total - 0.5, total + 0.5)`, and solved for the linear
coefficient `f(q) = 1 - 0.035q` → `f(7) = 0.755` (`9.3×`–`12.5×` the output tokens
and `6×`–`8.5×` the wall time of `linc`'s JDWP read).

`c11` (`c11-caught-exception-state`, unseen Tier C task) removes that indirect UI
inference path by design: entering `BENCH26` and tapping `Redeem` throws a
`PromoExpiredException` whose `catch` block displays a static `"Promo code expired"`
message for every input while holding `auditToken = "PROMO-BENCH26-7956"` and
`rebateCents = 1355` in local variables that have no UI-observable channel. On
`c11`, `linc` went **5/5 (`119.5s` median wall, `36.7k` median uncached tokens)**
via `spectra_method_breakpoint` + `spectra_method_locals` on
`CheckoutViewModel.redeemPromo`, while `agent-device`, `mobile-mcp`, and
`maestro` went **0/15 combined (`0/5` each)**.

### 3. `maestro 2.11.0`: Behavioural deduction on `b6` (`1/5`) and multi-device `a6` (`4/5` strict / `5/5` adjudicated)

- **`b6/run-3` (`PASS`, `218.3s`):** Although `maestro mcp` in `2.11.0` still exposes
  only 5 UI/flow tools (`list_devices`, `inspect_screen`, `run`, `take_screenshot`,
  `cheat_sheet`) and no logcat surface, in `b6/run-3` the agent executed 6
  consecutive cold launches using `launchApp: {clearState: false, stopApp: true}`,
  tabulated `"Retry sync"` presence across runs 1–6 (`present, present, absent,
  present, present, absent`), and deduced the modulo-3 (`every 3rd launch`) counter
  purely from the behavioural sequence (`1/5`).
- **`a6` (`4/5` strict / `5/5` adjudicated):** With both the Galaxy Watch7 and
  Galaxy S24 visible on the ADB bus, `maestro` passed 4 of 5 runs under strict
  regex grading. In `a6/run-2`, because `maestro`'s `list_devices` omits device
  form-factor/model metadata, the agent took screenshots of both devices (seeing
  `WATCH-NODE-999` on the watch and `PHONE-NODE-742` on the phone) and wrote:
  *"Found it on the Diagnostics screen: Node token: PHONE-NODE-742 ... confirmed
  distinct from the smartwatch (which showed WATCH-NODE-999)."* That contrastive
  mention tripped the pre-registered negative lookahead `(?!.*WATCH-NODE-999)`.
  By contrast, `linc` (`nerve_discover` returns `device_type: "phone"` vs
  `"watch"` and `model: "SM-S921U"` vs `"SM-L300"`), `agent-device`, and
  `mobile-mcp` went `5/5` without touching the watch.

### 4. `b11` Wear OS Capability Row (Galaxy Watch7 `SM-L300`)

On `b11` (toggling `Mode: Standard` → `Mode: Burst` and incrementing to
`Pings: 3 (Burst)` on the physical Galaxy Watch7), `linc` (`50.8s` median),
`maestro 2.11.0` (`61.0s` median), and `agent-device 0.21.27` (`62.5s` median)
all scored **5/5**. `mobile-mcp 1.0.10` scored **4/5 (`98.2s` median)**: in
`b11/run-4` (`494.9s`), the Galaxy Watch7's Wear OS screen timeout dimmed the
display to ambient mode mid-flow, and `mobile-mcp` had no wake/stayon primitive to
relight the watch screen — whereas `linc`'s `nerve_ensure_ready` automatically
applied `extend_timeout` and `stayon` on the watch (`5/5`, fastest median wall at
`50.8s`).

## LINC-Column Defects & Friction Surfaced by v3 (Disclosed, Not Re-Run)

Per the pre-registered v3 rule, the frozen `linc` stack was scored once (`44/45`
phone, `5/5` watch), and every `linc` defect or tool friction discovered across the
50 `linc` transcripts is left unpatched in `results_v3/` and documented below:

1. **`nerve_logcat` case-sensitive tag-only filter (root cause of `linc`'s sole
   failure, `linc/b6/run-4`):** Across 16 tool calls in `b5`, `b6`, `b9`, `b10`,
   and `c9`, agents passed the Android package name
   (`tag='dev.lincforge.benchtarget'`), a lowercase tag (`tag='benchtarget'`), or
   a message keyword (`tag='HealthCheck'`) to `nerve_logcat`'s `tag` parameter.
   Because `adb logcat -s <tag>` is strictly case-sensitive and tag-only, those
   calls returned `{"lines":[],"count":0}`. In `linc/b6/run-4`, after
   `nerve_logcat(tag='dev.lincforge.benchtarget')` returned 0 lines and an
   unfiltered 300-line dump scrolled past cold start, the agent abandoned logcat
   and guessed a random startup draw (`FAIL`). Planned fix: auto-detect package
   names (`"." in tag`) via `--pid=$(pidof <pkg>)`, fall back to case-insensitive
   substring matching when `-s <tag>` returns 0 lines, and add explicit `package`
   / `grep` parameters.
2. **UI-thread suspension & Android ANR dialog during `spectra_method_breakpoint`
   (`10/10` runs across `c10` and `c11`):** In all 10 `c10` and `c11` runs
   (`10/10 PASS`), arming `spectra_method_breakpoint` on a UI-triggered ViewModel
   method and then calling `nerve_tap` suspended the app's UI thread inside
   `onClick` before `adb shell input tap` returned. That caused `nerve_tap` to hit
   its 10s read timeout (`{"error":"Tap failed: adb read timeout"}`) and triggered
   Android's 5s input-dispatch ANR dialog (`"Wait"`), which cleared once
   `spectra_method_locals` resumed the process. Planned fix: add a background
   auto-collector thread in `spectra_method_breakpoint` that steps, snapshots
   locals, and resumes within ~200ms of breakpoint hit, plus accept `device` as an
   alias for `device_serial`.
3. **`nerve_logcat` temp-file indirection (`lines > 100`):** In 14 calls across
   `b5`, `b6`, `b9`, and `c9`, requesting `lines > 100` (e.g., `150`, `200`, `300`)
   caused `nerve_logcat` to write output to a temp file and return zero inline
   lines, costing an extra turn and ~30k cached tokens for `Read`. Planned fix:
   raise the inline threshold to ~250 lines and always include a 50-line
   `tail_lines` preview inline.
4. **`nerve_actionlog_start` default `deny_words` on bench devices (`"checkout"`):**
   In `c9/run-1`, `c9/run-2`, and `c9/run-4`,
   `nerve_actionlog_start(target_package='dev.lincforge.benchtarget')` enabled the
   default guarded-session `deny_words` list (which blocks tapping `"checkout"`),
   forcing the agent to restart `nerve_actionlog_start` with
   `deny_words='delete account'`. Planned fix: relax commercial purchase-label
   blocks by default on non-personal bench devices (`personal: false` in
   `devices.yaml`) or allow updating `deny_words` mid-session.
5. **Parameter aliases across `linc-nerve` and `linc-spectra`:** Accept `keycode`
   alias for `key` in `nerve_key`, accept `x1/y1/x2/y2` aliases for
   `start_x/start_y/end_x/end_y` in `nerve_swipe`, default `device` when only one
   device is online/reserved in `nerve_ensure_ready` / `nerve_launch` /
   `nerve_release`, clarify registered-route scope in `nerve_navigate`, and make
   `spectra_detach` idempotent when already auto-detached by
   `spectra_method_locals`.

