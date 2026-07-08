# BenchTarget device verification — 2026-07-08 (pre-run gate)

SPEC.md requires the implementation to satisfy the frozen spec **before any
comparative run**. Sweep executed on the bench (mini), stock + seeded debug
APKs @ branch `benchtarget-app`, driven via adb/uiautomator (element-based
taps, no coordinates hardcoded against a device model).

| Ground truth | Device | Result |
|---|---|---|
| state.json initial contract (`{"screen":"home","launchCount":1}` after pm clear + launch) | Galaxy S10e | PASS |
| a2 verify cmd (exact YAML shell): name/tier=Pro/subscribed=true greps | Galaxy S10e | PASS |
| a3 verify cmd (exact YAML shell): screen=detail + selectedItem=Item 073 (deep scroll) | Galaxy S10e | PASS |
| a1/a4 labels: Home nav Catalog/Form/About/Checkout; `Build channel: BENCH-STABLE` | Galaxy S10e | PASS |
| b5 crash: Item 013 Export → `FATAL EXCEPTION: main` / `java.lang.IllegalStateException: export buffer not initialized`, process dies; no other item crashes (unit-tested all 99) | Galaxy S10e | PASS |
| b6 flake: from pm clear, launches #1–5 → Retry sync visible Y/Y/N/Y/N (3/5); logcat `SyncComponent init: launchCount=<0..4> skip=<pattern>` | Galaxy S10e | PASS |
| c10: quantity 7 → `Total: $50`; `0.755`/`discountFactor` absent from logcat and state.json | Galaxy S10e | PASS |
| c9 seeded defect 1: Tier Pro selected → `Registered Avery Quinn (Basic, subscribed=true)`, state tier=Basic | Galaxy S10e | PASS |
| c9 seeded defect 2: Submit = `android.widget.Button` with `text=""`, `content-desc=""` (no accessible label) | Galaxy S10e | PASS |
| b8 wear: launch, Ping ×3 → `Pings: 3` (matches `Pings:\s*3`); watch state-file analog written | Pixel Watch 2 | PASS |

Bench left in stock state (stock reinstalled on S10, `pm clear` run — launch
counter zeroed).

Notes for the harness:
- The wear APK's launcher activity is `dev.lincforge.benchtarget/.wear.MainActivity`
  (namespace differs from applicationId). Launch via LAUNCHER intent/monkey, not a
  hardcoded `.MainActivity` component.
- Unit suite: 21 tests × stock/seeded app variants + 2 wear tests, all green
  (`./gradlew test`).
