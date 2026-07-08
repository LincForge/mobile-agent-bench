# BenchTarget app — implementation plan (2026-07-08)

**Goal:** Implement `target-app/` to the FROZEN `target-app/SPEC.md` (pre-registration v1).
The spec is the contract — no redesign. Reactor goal `0da352dd`. /linc-circuit full mode
(Stage 1 satisfied by the frozen spec; council skipped by pre-registration design).

## Stack (matches LINC fleet, all locally installed)

Gradle 8.10.2 (wrapper copied from PrecisionLevel) · AGP 8.8.2 · Kotlin 2.3.20 +
`org.jetbrains.kotlin.plugin.compose` · JDK 17 (`/opt/homebrew/opt/openjdk@17`) ·
compileSdk/targetSdk 35, minSdk 24 (phone) / 30 (wear) · kotlinx-serialization-json 1.9.0 ·
Jetpack Compose (androidx BOM) on phone, Wear Compose 1.4.0 on watch.
`sdk.dir=/opt/homebrew/share/android-commandlinetools`.

Gradle build is rooted at `target-app/` (repo root stays a Python uv project).
Modules: `:app` (phone), `:wear` (watch). Both `applicationId dev.lincforge.benchtarget`.

## Key semantics locked during planning (spec + task-YAML cross-check)

- **state.json**: kotlinx-serialization, `encodeDefaults=false` + `explicitNulls=false`
  → single-line JSON, fields absent until first interaction. Harness greps use `": *"`
  (compact `":"` matches). Written to `getExternalFilesDir(null)/state.json` after every
  significant state change.
- **Flake (task 6)**: sync-init check reads the persisted counter **pre-increment** at
  cold start (`prior % 5 ∉ {2,4}` → show Retry sync), then the counter increments.
  From cleared data launches #1..#5 → decision values 0..4 → hidden on launches **#3
  and #5** exactly as the spec's operational line requires. state.json `launchCount`
  reports the post-increment total.
- **Crash (task 5)**: Detail "Export" on "Item 013" only → uncaught
  `IllegalStateException("export buffer not initialized")` thrown on main thread in the
  click handler → standard AndroidRuntime logcat signature.
- **Checkout (task 10)**: `discountFactor = 1.0 − min(q,10)×0.035` internal to
  `CheckoutViewModel.applyDiscount()`; at q=7 → 0.755, total `round(9.37×7×0.755)` = $50
  displayed whole-dollar. Factor never in UI/log/state.json (unit-tested absence).
- **Seeded flavor (task 9)**: product flavors `stock`/`seeded` (dimension `truth`),
  `BuildConfig.SEEDED` gates exactly two defects: (1) submit path drops the selected
  tier → always "Basic" in result line + `lastFormResult.tier`; (2) Submit is icon-only
  with null contentDescription. Same applicationId (installs replace; seeded only task 9).
- **Wear (task 8)**: title "BenchTarget", button "Ping", counter text `Pings: <n>`
  (verify regex `Pings:\s*3`), state-file analog on watch external files dir.
- **Labels frozen by task YAMLs**: Home nav = Catalog/Form/About/Checkout;
  Diagnostics shows `Build channel: BENCH-STABLE`; catalog "Item 001".."Item 100"
  zero-padded; form field "Name", switch "Subscribe", dropdown "Tier" {Basic,Pro,Max}
  default Basic, result `Registered <name> (<tier>, subscribed=<bool>)`.
- Log tag `BenchTarget` (transitions, submissions, sync-init decision at DEBUG);
  **no INTERNET permission**, no network.

## Tasks

1. **Scaffold** — wrapper + settings/root gradle + version catalog + `:app`/`:wear`
   skeletons; `./gradlew tasks` sanity. Commit.
2. **TDD core logic** (pure-Kotlin classes in `:app`, JVM unit tests, strict RED→GREEN):
   `BenchState` serializer · `CatalogItems` · `ExportPolicy` · `SyncPolicy` (pre-increment
   contract, 5-launch pattern) · `FormLogic` (stock + seeded) · `CheckoutLogic`
   (factor/rounding/no-leak). Commit per green cycle.
3. **Phone UI shell** — MainActivity, screen enum + BackHandler nav, 7 Compose screens
   wired to logic, `StateFileWriter`, `LaunchCounter` (SharedPreferences), flavors +
   BuildConfig.SEEDED, logging. Thin declarative layer (instrumented tests deferred to
   on-device verification per KMP tier table).
4. **Wear module** — Ping screen + state writer.
5. **Local verify (Stage 4 L1)** — `./gradlew clean test` (all unit tests) +
   `assembleStockDebug assembleSeededDebug :wear:assembleDebug`.
6. **Device verify** — bench phone (serial via `bench.local.yaml`): stock smoke (launch → state.json, Item 013
   crash signature in logcat, 5-cold-start flake pattern, checkout $50, factor absent
   from logcat); seeded: tier defect + a11y defect present. Bench watch (Pixel
   Watch 2, serial via fleet registry): Ping ×3 → `Pings: 3`.
7. **CI (Stage 4 L2)** — add `.github/workflows/test.yml`: uv pytest (harness) +
   `gradle testStockDebugUnitTest testSeededDebugUnitTest :wear:assembleDebug
   assembleStockDebug assembleSeededDebug`. Branch `benchtarget-app` → PR → green → merge.
8. **Close (Stage 5)** — reactor note on `0da352dd`, session file update, learnings.
