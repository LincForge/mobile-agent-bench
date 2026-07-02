# Week-1 smoke verification (2026-07-01)

One-off, by-hand smoke of each stack before the pre-registration freeze.
Smokes are NOT benchmark rows: they ran against the Android Settings app on a
secondary bench device (Samsung Galaxy S10e, SM-G970U, Android 12), not the
pinned Pixel 8 Pro, and produce no scored data. Purpose: prove each tool is
installed in its vendor-recommended configuration and can drive a real device
before the task suite froze.

| Stack | Version | Smoke | Result |
|---|---|---|---|
| Maestro MCP | CLI 2.6.1 (Java 17) | flow: launchApp Settings + assertVisible "Connections" | PASS |
| agent-device | 0.18.1 (Node 26) | `open com.android.settings` + `snapshot -i` (@eN refs returned) | PASS |
| mobile-mcp | @latest (0.0.60) | end-to-end headless `claude -p` (pinned model, strict MCP): launch Settings, list elements | PASS — also validated the full harness invocation path and usage-accounting shape |
| LINC nerve | daemon 1.0 | scrcpy stream on Pixel 8 Pro: 10 frames @1080 decoded, live frame pulled, stream stopped | PASS (fairness rule: streaming enabled) |

Notes:
- nerve's scrcpy stream does NOT work on the S10e (scrcpy-server 3.3.4 crashes
  device-side: "stack corruption detected"); it works on the pinned Pixel 8 Pro.
  Tracked upstream; irrelevant to benchmark rows (all phone rows run on the Pixel),
  disclosed here for completeness.
- agent-device addresses devices by display name ("SM G970U"), not serial —
  harness adapter note for week 2.
- mobile-mcp smoke cost $0.21 on the pinned model — a full 200-run grid is
  plausibly ~$40-80 at tier-A complexity; tier B/C runs will cost more.
