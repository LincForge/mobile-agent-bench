# Pre-registration — mobile-agent-bench v3

**Frozen at tag `v3-prereg` — before any v3 comparative run.**

v3 is a third-wave comparative evaluation of four mobile MCP tool stacks
(`linc`, `maestro`, `mobile-mcp`, `agent-device`) against their current
primary-sourced versions on a **hybrid 10-task suite** (`tasks_v3/`):
**4 longitudinal anchors** carried over byte-for-byte from v1/v2 (`b5`, `b6`,
`c9`, `c10`), plus **6 unseen tasks** (`a5`, `a6`, `b9`, `b10`, `b11`, `c11`)
designed after all four contestant stacks were frozen.

This document, the task files under `tasks_v3/`, the tool adapters under
`tools/`, the target-app spec (`target-app/SPEC.md`), the pinned stack
versions/digests, and the pinned model are frozen as of the `v3-prereg` git tag
and pushed to `origin` before Cell 1 executes. Any later change is an
**amendment** in `AMENDMENTS.md` and invalidates every row it touches. v1
(`results/`) and v2 (`results_v2/`) remain immutable; v3 rows land under
`results_v3/`.

## Authorship, conflict-of-interest, and zero-pilot disclosure

- **Authorship & conflict of interest:** `mobile-agent-bench`, `BenchTarget`,
  and the `linc` stack (`linc-nerve`, `linc-crucible`, `linc-spectra`) are
  authored by the same team (`LincForge`). Because a first-party benchmark
  cannot claim blind authorship of `BenchTarget`, every safeguard below is
  designed to make the evaluation **externally auditable and mechanically
  reproducible**:
  1. **Chronological freeze before unseen task design:** All three `linc`
     components were committed/published **before** the 6 unseen v3 tasks were
     designed (`linc-nerve==0.1.0` published to PyPI from `5477863` on
     2026-10-12; `linc-crucible@cf04279` and `linc-spectra@c471dad` committed
     prior to v3 task authoring on 2026-10-13).
  2. **Zero pilot or calibration runs:** **Zero** agent runs (pilot, smoke, or
     calibration) were executed on any of the 6 unseen tasks (`a5`, `a6`, `b9`,
     `b10`, `b11`, `c11`) on **any** of the four stacks prior to tagging
     `v3-prereg`. `BenchTarget` v3 features were verified exclusively via deterministic
     Kotlin JUnit tests (`./gradlew test`) and static regex sample tests
     (`pytest`).
  3. **Competitor-favorable unseen tasks:** Two of the six unseen tasks were
     specifically designed to test flagship capabilities shipped by competitors
     since v2: `b9` (`silent-error-log-attribution`) directly tests
     `@mobilenext/mobile-mcp@1.0.10`'s new `mobile_get_device_logs` tool, and
     `a6` (`multi-device-disambiguation`) directly tests
     `agent-device@0.21.27`'s `#1880` multi-device selection safety.

## Contestants and symmetric version pins (primary-sourced 2026-10-13)

| Stack | Version | Integrity Pin / Digest | Key upstream changes since v2 (2026-07) |
|---|---|---|---|
| `linc` | `linc-nerve==0.1.0`, `linc-crucible==0.1.0`, `linc-spectra==0.1.0` | PyPI wheel `linc_nerve-0.1.0-py3-none-any.whl` `sha256:747798cf8c869e4e0f6d49426faada97221cfd55e70fef540afa3fe2d949ca19` (`LincForge/nerve@5477863`); `linc-crucible@cf04279`; `linc-spectra@c471dad` | `linc-nerve` published on PyPI (`linc-device-kit==1.0.0`, `linc-cli-kit==0.1.3`); `crucible` and `spectra` at current `main` commits. |
| `maestro` | `2.11.0` (up from `2.6.1`) | `mobile-dev-inc/Maestro` tag `cli-2.11.0` (released 2026-09-29) | Per-flow output bundle with manifest, device logs, and crash/ANR reports (`2.7.0`); `childOf` hierarchy fix (`2.8.0`); empty input `hint` vs `text` fix (`2.9.0`). |
| `mobile-mcp` | `1.0.10` (up from `0.0.60`) | npm `@mobilenext/mobile-mcp@1.0.10` tarball `shasum:91e354a4b27440a2b3da4f8ebeff31e9962440c2` (`mobile-next/mobile-mcp` tag `1.0.10`, released 2026-10-11; `mobilecli@1.0.19`) | Native Go backend (`mobilecli`), new `mobile_get_device_logs` tool, `mobile_batch_commands`, `@ref` clicking/long-pressing, compact element list. |
| `agent-device` | `0.21.27` (up from `0.18.1`) | npm `agent-device@0.21.27` tarball `shasum:5ec1d7a62925f65c59d482a200e3d937541e1871` (`callstackincubator/agent-device` tag `v0.21.27`, released 2026-10-12) | `#1880` device-selection safety (identity conflicts and multi-device ambiguity fail explicitly instead of retargeting), request-bound daemon, `--text-stdin` on `fill`. |

- **Pinned agent harness & model:** `Claude Code 2.1.296` with `--model claude-sonnet-5` (resolved model snapshot ID recorded in every run's `transcript.jsonl` `system/init` event), `--permission-mode bypassPermissions`, `--strict-mcp-config`, and identical confinement flags across all four stacks.

## Sandbox isolation and between-cell hygiene

1. **Filesystem & tool confinement (`mobile_agent_bench/agent.py`):**
   - Every agent subprocess spawns in an empty neutral working directory
     (`/tmp/mobile-agent-bench-cwd`) outside the repository.
   - `--disallowedTools` blocks raw shell escape hatches (`Bash(adb*)`,
     `Bash(*adb *)`, `Bash(nerve*)`, `Bash(maestro*)`, `Bash(agent-device*)`,
     etc.) and path-guards `Read`, `Glob`, and `Grep` against reading the
     benchmark repo, `target-app/` source, or `tasks_v3/` YAML files.
   - Answer keys (`PHONE-NODE-742`, `4720`, `time-west-2`, `1850`,
     `IndexRebuilder`, `AUD-4-BENCH26-8419`) do not appear in any task prompt.
2. **Between-cell device hygiene (`mobile_agent_bench/device.py`):**
   - Before every cell, `clear_uiautomation_holders` force-stops all known
     `UiAutomation`-holding packages (`dev.mobile.maestro`,
     `com.github.uiautomator[.test]`, `io.appium.uiautomator2.server[.test]`,
     `com.callstack.agentdevice.{snapshothelper,multitouchhelper}`) and kills any
     orphaned `shell`-uid `app_process` server.
   - `ensure_pinned_app` verifies the MD5 digest of the installed `base.apk`
     against the repo-built artifact and reinstalls on mismatch.
   - `reset_app_state` executes the task's `reset` steps (`wake`, `home`,
     `force-stop`, `clear-data`).
   - `is_device_locked` verifies via `dumpsys window` that the keyguard/lockscreen
     is inactive (`device_locked_pre: false` in `meta.json`) and refuses to
     start a cell on a locked device.

## The 10-task v3 suite (`tasks_v3/`) and capability matrix

9 scored phone tasks (`45` runs/tool) + 1 Wear OS capability row (`b11`, `5`
runs/tool, reported separately and never averaged into phone means) = **200 runs
total** (`N = 5` per cell, interleaved round-robin across tools:
`linc -> maestro -> mobile-mcp -> agent-device`).

| Task | Tier | Kind | Verify | Timeout | Documented path: `linc` | Documented path: `maestro` | Documented path: `mobile-mcp` (`1.0.10`) | Documented path: `agent-device` (`0.21.27`) |
|---|---|---|---|---|---|---|---|---|
| `a5` `longpress-context-archive` | A | Unseen | `shell` (`state.json`) | 600s | `nerve_long_press` -> menu -> confirm | `run_flow` (`longPressOn`) -> menu -> confirm | `mobile_long_press_at` / `@ref` -> menu -> confirm | `longpress` / `press` -> menu -> confirm |
| `a6` `multi-device-disambiguation` | A | Unseen | `answer` | 600s | `nerve_discover` + `serial` param | `list_devices` + `device_id` param | `mobile_list_available_devices` + `device` param | `devices` + explicit target (`#1880`) |
| `b5` `crash-repro-evidence` | B | Anchor | `answer` | 900s | UI nav + `nerve_logcat` / `spectra` | UI nav + `2.7.0+` flow crash/device log bundle | UI nav + `mobile_get_device_logs` (`1.0.10`) | UI nav + `logs` |
| `b6` `flaky-behavior-investigation` | B | Anchor | `answer` | 900s | Cold-start loop + `nerve_logcat` | Cold-start loop (`launchApp: stopApp: true`) + UI/logs | Cold-start loop + `mobile_get_device_logs` (`1.0.10`) | Cold-start loop (`open`/`close`) + `logs` |
| `b9` `silent-error-log-attribution` | B | Unseen | `answer` | 900s | UI tap + `nerve_logcat` | UI tap + flow device log bundle (`2.7.0+`) | UI tap + `mobile_get_device_logs` (`1.0.10`) | UI tap + `logs` |
| `b10` `main-thread-stall-isolation` | B | Unseen | `answer` | 900s | UI taps + `nerve_logcat` / wall timing | UI taps + flow timing / device logs | UI taps + `mobile_get_device_logs` (`1.0.10`) | UI taps + `logs` / timing |
| `b11` `wearos-mode-switch-ping` *(capability row)* | B | Unseen | `answer` | 900s | Wear UI inspect + tap (`SM-L300`) | Wear UI inspect + `run_flow` (`SM-L300`) | Wear UI inspect + tap (`SM-L300`) | Wear UI snapshot + `press` (`SM-L300`) |
| `c9` `seeded-defect-ship-gate` | C | Anchor | `answer` | 900s | `crucible` / exploratory UI verification | Exploratory UI verification (`Form` Tier dropdown) | Exploratory UI verification (`Form` Tier dropdown) | Exploratory UI verification (`Form` Tier dropdown) |
| `c10` `runtime-state-inspection` | C | Anchor | `answer` | 900s | `spectra_method_breakpoint` + `spectra_method_locals` | No built-in debugger (structural capability gap) | No built-in debugger (structural capability gap) | No built-in debugger (structural capability gap) |
| `c11` `runtime-promo-signature` | C | Unseen | `answer` | 900s | `spectra_method_breakpoint` + `spectra_method_locals` | No built-in debugger (structural capability gap) | No built-in debugger (structural capability gap) | No built-in debugger (structural capability gap) |

## Analysis plan, dual reporting, and symmetric rerun policy

1. **Deterministic mechanical grading (zero human/LLM judgment):**
   - Every task is graded automatically by `mobile_agent_bench/agent.py`
     (`verify_task`): `a5` checks `state.json` via `adb shell`; the 9 `answer`
     tasks apply their pre-registered case-insensitive `DOTALL` regex to
     `final_answer_text(transcript.jsonl)`. All 9 regexes are validated at
     schema load time against frozen `match_samples` and `reject_samples`.
   - Any timed-out run (`wall_time_s >= timeout_s`) is scored **FAIL**; if its
     verifier passes or its answer pattern appears in assistant text prior to
     timeout, `solved_unfinalized: true` is recorded diagnostically and never
     counted as a `PASS`.
2. **Dual headline reporting (full 9-task phone grid AND 7-task UI/logcat subset):**
   - Because `c10` and `c11` require JVM/ART runtime local-variable inspection
     (a capability only `linc-spectra` provides natively among the four MCP
     stacks), `REPORT.md` v3 will report **both**:
     - **Full 9-task scored phone aggregate (`45` runs/tool)** across Tiers A+B+C.
     - **7-task UI + logcat phone aggregate (`35` runs/tool, excluding `c10` and `c11`)**, where all four stacks have a documented path to completion.
     - **4-anchor vs. 5-unseen-phone breakdown**, plus Wilson 95% confidence
       intervals alongside raw pass counts so `N = 5` per-cell granularity is
       not over-interpreted.
   - Note on longitudinal anchors (`b5`, `b6`, `c9`, `c10`): comparisons between
     v2 and v3 anchor scores are descriptive (as device hardware moved from
     Pixel 8 Pro / Android 15 to Galaxy S24 / Android 16 and all four tool
     stacks upgraded simultaneously).
3. **Symmetric no-tuning and invalidity rule:**
   - **No stack (`linc`, `maestro`, `mobile-mcp`, or `agent-device`) may be
     patched, re-pinned, or re-configured after `v3-prereg` is tagged.** Any
     defect discovered in `linc` or in a competitor during v3 execution stands
     as scored in `results_v3/`.
   - A run may be invalidated and re-executed **only** if a script-verifiable
     host/device infrastructure fault occurs (`device_locked_pre == True`,
     `device_locked_post == True`, `DeviceError` / ADB transport disconnect, or
     host power/network drop), and every such event must be logged in
     `AMENDMENTS.md` with the preserved raw artifact.

## Devices and execution window

- **Primary phone:** **Samsung Galaxy S24 (`SM-S921U`)**, Android 16 (SDK 36,
  build `BP4A.251205.006`).
- **Primary watch (`b11` capability row, plus attached distractor during `a6`):**
  **Samsung Galaxy Watch7 (`SM-L300`)**, Wear OS 6 / Android 16 (SDK 36, build
  `BP2A.250325.020`).
- Runs execute outside the `03:15–06:00 PT` host maintenance window.

## Frozen SHA-256 manifest (`tasks_v3/` and pinned APKs)

```text
998b97aeeddb87c6c16e93ab93338e6917645efd9a692b6ada60044c0fc7cc66  tasks_v3/a5-longpress-context-archive.yaml
5bc34371fff540dd71ac20f5420ef0790c5f9201178c00ac55c3ac36608c855e  tasks_v3/a6-multi-device-disambiguation.yaml
55d25f8fc8dc4b300c9509e6e77e7ec70a26c0d1d7661d31df834a42411b9786  tasks_v3/b10-main-thread-stall-isolation.yaml
27828aee88db6488b12448434c2fde70e7368d0b68ca3014a82a134746399a0b  tasks_v3/b11-wearos-mode-switch-ping.yaml
a603ae75d8a6bb781f0f87be982e9a4b087c61e3d521eb983dcaee075705108a  tasks_v3/b5-crash-repro.yaml
351d6e7f37320d1c6b886653cc070c01365ac897ec0bb58606668400217b7a43  tasks_v3/b6-flake-investigation.yaml
e3a5301dcbffca18262eb63b27e0796a2316a9a8d7ae7d360c8da38fffdaae5e  tasks_v3/b9-silent-error-log-attribution.yaml
a9f0343acd3c1287657c4fdf04e776fd29d6b5e782c11f88c182f682667837b4  tasks_v3/c10-runtime-state.yaml
a97b80c3d3daa00a5b55cf27ddc82aa5c3344c9039869a369ddddd3244086ed1  tasks_v3/c11-runtime-promo-signature.yaml
212edcda539c2ed6ae0dfeca77a6eb8444db1fe6c365ed0c5feca170961d5556  tasks_v3/c9-ship-gate.yaml
ffc2259f604d5af7b31206b56da9f39a8cc5cf01dd54c82e6fbc15be14fd7332  target-app/app/build/outputs/apk/stock/debug/app-stock-debug.apk
b16deb7f50cd74273dd9baece53f384466d010756e5a5c9628941746d98f7a6b  target-app/app/build/outputs/apk/seeded/debug/app-seeded-debug.apk
09287a53d02c708d815103d0de684003307e2b38be6863b5a4c0444da91f3158  target-app/wear/build/outputs/apk/debug/wear-debug.apk
```
