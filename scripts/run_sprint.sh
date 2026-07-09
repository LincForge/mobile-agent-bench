#!/bin/bash
# Sprint driver — run a chosen TOOL SUBSET over one segment, then stop at a clean
# quiescent point (so the scored device can come off the bench between sprints).
# Resume-safe: `bench` skips any cell that already has meta.json.
#
# Why this exists (vs run_campaign.sh): (1) per-tool control, so the fast tools
# (linc/maestro/mobile-mcp) can run in a short sprint while agent-device's slow
# deterministic-FAIL column runs unattended later; (2) enforces cross-device
# hygiene — the app is left on the SCORED device ONLY. The harness injects no
# ANDROID_SERIAL (tools self-discover the device), so app-location is the sole
# guard against wrong-device ops (the defect that voided the first campaign).
#
# Usage (serials via env — never committed):
#   export PHONE=<scored phone serial>          # also device_serial in bench.local.yaml
#   export WATCH=<wear serial>
#   TOOLS="linc maestro mobile-mcp" bash scripts/run_sprint.sh stock    # a1-a4,b5-b7,c10
#   TOOLS="linc maestro mobile-mcp" bash scripts/run_sprint.sh seeded   # c9 (seeded build)
#   TOOLS="linc maestro mobile-mcp" bash scripts/run_sprint.sh watch    # b8 (wear)
#   TOOLS="agent-device"            bash scripts/run_sprint.sh stock     # the slow column, alone
# Optional: RUNS (default 5), BENCH_RESULTS_DIR (default results; results_s10 for the S10 addendum).
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
export JAVA_HOME="${JAVA_HOME:-/opt/homebrew/opt/openjdk@17}"
PHONE="${PHONE:?export PHONE=<scored phone serial>}"
WATCH="${WATCH:-}"
TOOLS="${TOOLS:?export TOOLS=\"linc maestro mobile-mcp\" (or a single tool id)}"
RUNS="${RUNS:-5}"
PKG=dev.lincforge.benchtarget
STOCK=target-app/app/build/outputs/apk/stock/debug/app-stock-debug.apk
SEEDED=target-app/app/build/outputs/apk/seeded/debug/app-seeded-debug.apk
WEAR=target-app/wear/build/outputs/apk/debug/wear-debug.apk
log(){ echo "[$(date +%H:%M:%S)] $*"; }
seg="${1:?usage: TOOLS=.. PHONE=.. WATCH=.. $0 [stock|seeded|watch]}"

# Leave the app on $keep ONLY: uninstall from every other attached device.
hygiene(){
  local keep="$1"
  for s in $(adb devices | awk 'NR>1 && $2=="device"{print $1}'); do
    [ "$s" = "$keep" ] && continue
    if adb -s "$s" shell pm list packages 2>/dev/null | grep -q "$PKG"; then
      log "hygiene: uninstall $PKG from $s (not the scored device)"
      adb -s "$s" uninstall "$PKG" >/dev/null 2>&1 || true
    fi
  done
}

case "$seg" in
  stock)
    export BENCH_DEVICE_SERIAL="$PHONE"
    hygiene "$PHONE"
    log "install STOCK on scored phone $PHONE"
    adb -s "$PHONE" install -r "$STOCK" >/dev/null 2>&1 || { adb -s "$PHONE" uninstall "$PKG" >/dev/null 2>&1; adb -s "$PHONE" install "$STOCK" >/dev/null; }
    TASKS="a1 a2 a3 a4 b5 b6 b7 c10" ;;
  seeded)
    export BENCH_DEVICE_SERIAL="$PHONE"
    hygiene "$PHONE"
    log "install SEEDED on scored phone $PHONE"
    adb -s "$PHONE" uninstall "$PKG" >/dev/null 2>&1 || true; adb -s "$PHONE" install "$SEEDED" >/dev/null
    TASKS="c9" ;;
  watch)
    [ -n "$WATCH" ] || { echo "export WATCH=<wear serial> for the watch segment"; exit 1; }
    export BENCH_DEVICE_SERIAL="$WATCH"
    hygiene "$WATCH"
    log "ensure WEAR build on watch $WATCH (launcher .wear.MainActivity)"
    adb -s "$WATCH" install -r "$WEAR" >/dev/null 2>&1 || { adb -s "$WATCH" uninstall "$PKG" >/dev/null 2>&1; adb -s "$WATCH" install "$WEAR" >/dev/null; }
    TASKS="b8" ;;
  *) echo "usage: TOOLS=.. PHONE=.. WATCH=.. $0 [stock|seeded|watch]"; exit 1 ;;
esac

log "SPRINT seg=$seg tools=[$TOOLS] tasks=[$TASKS] runs=$RUNS results=${BENCH_RESULTS_DIR:-results}"
for tool in $TOOLS; do
  for t in $TASKS; do
    log "run tool=$tool task=$t"
    uv run bench run --tool "$tool" --task "$t" --runs "$RUNS"
  done
done
log "SPRINT seg=$seg tools=[$TOOLS] COMPLETE — quiescent point (device can come off the bench)"
