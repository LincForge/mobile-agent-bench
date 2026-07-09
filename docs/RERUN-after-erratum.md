# Clean re-run runbook (after the 2026-07-08 harness erratum)

The first campaign was voided — see `results_invalid/ERRATUM.md`. The harness now
**confines each agent to the tool-under-test** (fix landed 2026-07-09). This is
the runbook for the clean re-run. Run it on the bench host (the mini) where the
devices live.

## What changed in the harness

`build_command` now passes `--disallowedTools` (see `agent.py`
`CONFINE_DISALLOWED_TOOLS`) and runs the agent from a neutral cwd (`AGENT_CWD`,
outside the repo). Isolation standard (CEO decision 2026-07-09, "allow Read,
block shell + search"):

- **Denied:** Bash, Grep, Glob, Write/Edit, WebFetch/WebSearch, Task/Agent — i.e.
  no shell (no direct `adb`, no `find`), no filesystem search/enumeration, no web.
- **Allowed:** the tool-under-test's `mcp__*` tools, `ToolSearch` (loads the
  deferred MCP schemas), and `Read` (tools that return a screenshot *file path*
  need it; without Bash/Grep/Glob the agent can't discover the repo, so
  SPEC.md/source stay unreachable).

Verify after any change: `uv run pytest -q` (the `test_build_command_confines_*`
test + the topology scanner must pass).

## Device preconditions (IMPORTANT — enforce before every phase)

The app must exist **only on the scored device**, or a confined agent can still
*launch* it on the wrong device (it can't install/uninstall anymore, but it can
launch what's already there):

- Phone phases (1 & 2): BenchTarget present **only** on the scored phone
  (Pixel 8 Pro). Uninstall from every other attached device first.
- Watch phase (3): the current wear build present on the Pixel Watch 2 (its
  launcher is `.wear.MainActivity`; a stale build exposing `.MainActivity` fails
  to launch — reinstall `target-app/wear/build/outputs/apk/debug/wear-debug.apk`
  if needed).

`bench.local.yaml` (gitignored) sets `device_serial` to the scored phone; the b8
task overrides to the watch. Supply serials via env for the driver.

## Run it

```bash
export PHONE=<scored phone serial>          # from bench.local.yaml device_serial
export BENCH_WATCH_SERIAL=<wear serial>      # from LINC device-fleet.yaml
uv sync
scripts/run_campaign.sh all                  # phase 1 (phone-stock) -> 2 (c9 seeded) -> 3 (b8 watch)
uv run bench report
```

Resume-safe: existing `meta.json` cells are skipped, so a kill/restart continues.
Full grid = 10 tasks x 4 tools x 5 = 200 runs, ~$140, ~10h (tier-B/C have
600–900s timeouts; competitor time-outs count as FAIL by design).

## Watch for (from the voided run's transcripts + the confined smoke)

- **agent-device on Compose:** its uiautomator a11y snapshot fails on the Compose
  target (17/17 in the smoke); it falls back to reading screenshot files. Expect
  weaker/ slower agent-device rows — a genuine, reportable tool finding, not a
  harness bug.
- **crucible / spectra barely invoked:** in the voided run the agent used nerve
  for everything (crucible 0x, spectra ~6x). With Bash removed the agent can no
  longer read source/logcat for the c9/c10 answers — this run is the real test of
  whether it reaches for crucible (ship-gate) / spectra (runtime state). Filed:
  reactor improvements on linc-crucible/linc-spectra/linc-nerve.
- **Never commit while a run is in flight** — a run's transcript is sanitized only
  at its end; the topology scanner (`uv run pytest`) will trip on an in-flight raw
  transcript. Commit results only at a quiescent point (campaign paused/done).

## After the grid

1. `uv run bench report` (per-device via `BENCH_RESULTS_DIR`).
2. Operational-proof stats (doc 044 §5): gateway API + overmann/minos history.
3. Optional S10 cross-device addendum: `PHONE=<s10> BENCH_RESULTS_DIR=results_s10
   scripts/run_campaign.sh all` (disclosed as post-registration).
4. Nothing publishes without CEO sign-off (doc 044 §6 gate).
