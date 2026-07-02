# BenchTarget — target app specification (FROZEN at pre-registration v1)

All ten benchmark tasks run against **BenchTarget**, a purpose-built open-source
Android + Wear OS app that lives in this repo (`target-app/`). A purpose-built
target removes third-party app churn from the benchmark: anyone can build the
exact APK from source and reproduce every row.

This spec is part of the pre-registration freeze. The app implementation must
satisfy this spec **before any comparative run**; implementation details may
vary, but every behavior below (screens, labels, ground truths, state contract)
is locked. If the implementation is found to deviate from the spec after runs
begin, the affected rows are invalidated and re-run — the spec wins.

## Identity

- Package: `dev.lincforge.benchtarget` (phone), `dev.lincforge.benchtarget` Wear APK (watch)
- Single-activity Jetpack Compose app; Compose for Wear OS on the watch
- Build flavors: `stock` (tasks 1–8, 10) and `seeded` (task 9 only — contains
  the seeded defects below; never used for any other task)

## State contract (harness verification hook)

After every significant state change the app serializes its UI state to
`getExternalFilesDir(null)/state.json` (adb-readable without root at
`/sdcard/Android/data/dev.lincforge.benchtarget/files/state.json`), single-line
JSON:

```json
{"screen": "home|catalog|detail|form|about|diagnostics|checkout",
 "selectedItem": "Item 073" ,
 "lastFormResult": {"name": "...", "tier": "Basic|Pro|Max", "subscribed": true},
 "launchCount": 4}
```

Fields absent until first relevant interaction. The state file is a
**verification hook only** — task prompts never mention it, and agents are not
told it exists. An agent that discovers and edits it has cheated; transcripts
are published, so this is auditable.

## Screens (stock flavor)

1. **Home** — title "BenchTarget"; nav buttons: **Catalog**, **Form**, **About**, **Checkout**.
2. **Catalog** — lazy list of 100 items, "Item 001" … "Item 100" (three-digit,
   zero-padded), ~10 visible per screen. Tap → Detail.
3. **Detail** — header = item name; body text "Catalog entry for <name>.";
   button **Export**.
   - **Crash ground truth (task 5):** on "Item 013" ONLY, tapping **Export**
     throws `IllegalStateException("export buffer not initialized")` (uncaught
     → process crash, standard AndroidRuntime logcat signature).
4. **Form** — text field "Name", switch "Subscribe", exposed dropdown "Tier"
   {Basic, Pro, Max} (default Basic), button **Submit** → result text
   `Registered <name> (<tier>, subscribed=<true|false>)` + `lastFormResult`.
5. **About** — static text + button **Diagnostics** (Home → About → Diagnostics
   = the 3-deep navigation path).
6. **Diagnostics** — text `Build channel: BENCH-STABLE`; a "Sync status" card.
   - **Flake ground truth (task 6):** the card's **Retry sync** button renders
     only when `launchCount % 5 ∉ {2, 4}` at cold start (`launchCount` is a
     persisted counter incremented every cold start, reset by `pm clear`).
     I.e. starting from cleared data, launches #3 and #5 are missing the
     button — "passes 3/5". The flake source an agent must identify: the
     button's presence depends on the **persisted launch counter** (a
     launch-count-conditional initialization skip in the sync component), not
     timing, network, or randomness.
7. **Checkout** — quantity stepper (1–10, default 1), base price $9.37/unit,
   button **Apply discount**, then total displayed rounded to WHOLE dollars
   (no cents — deliberately lossy so the factor below cannot be recovered by
   back-division from the UI: at quantity 7 the display is `$50`, and
   50 / 65.59 ≈ 0.762 ≠ the true factor).
   - **Runtime-state ground truth (task 10):** `CheckoutViewModel.applyDiscount()`
     computes an internal, never-displayed, never-logged
     `discountFactor = 1.0 − min(quantity, 10) × 0.035`.
     At quantity = 7: **0.755**. Total = round(9.37 × 7 × 0.755) = round(49.52) = $50.
   - The factor must not appear in logs, the state file, or any UI surface —
     obtaining it requires runtime inspection of the running process (or
     equivalent capability, e.g. pulling and decompiling the APK, which is a
     legitimate path and shows up in the transcript).

## Wear module

Single screen: title "BenchTarget", button **Ping**, counter text `Pings: <n>`;
state file analog on the watch's external files dir. (Capability row — task 8.)

## Seeded flavor (task 9 only) — defects, FROZEN

Built from the same source with flavor `seeded`. Exactly two seeded defects:

1. **Functional:** the Form's Tier dropdown selection is not propagated — the
   result line and `lastFormResult.tier` always say `Basic` regardless of the
   selected tier. (User-visible correctness bug; ship-blocking.)
2. **Accessibility:** the Form's Submit button has no accessible
   label/contentDescription (icon-only in this flavor).

Ground truth verdict for "should this ship?": **NO** — with the tier
propagation bug as the primary, ship-blocking finding.

## Logging

The app logs with tag `BenchTarget` (screen transitions, form submissions,
sync-init decisions at DEBUG). No network access. No analytics. `INTERNET`
permission absent.
