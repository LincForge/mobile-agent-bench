#!/bin/bash
# Comparative-campaign driver (resume-safe; bench skips existing meta.json).
# Serial-free by design — supply devices via env so no serial is committed:
#   export PHONE=<scored phone serial>          # also set as device_serial in bench.local.yaml
#   export BENCH_WATCH_SERIAL=<wear serial>      # from LINC device-fleet.yaml
#   scripts/run_campaign.sh all                  # phase 1 (phone-stock) -> 2 (c9 seeded) -> 3 (b8 watch)
# Phones: a1-a4,b5-b7,c10 (stock) + c9 (seeded). Watch: b8. Run from repo root on the bench host.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
export JAVA_HOME="${JAVA_HOME:-/opt/homebrew/opt/openjdk@17}"
PHONE="${PHONE:?export PHONE=<scored phone serial>}"
WATCH="${BENCH_WATCH_SERIAL:?export BENCH_WATCH_SERIAL=<wear serial>}"
RUNS="${RUNS:-5}"
PKG=dev.lincforge.benchtarget
STOCK=target-app/app/build/outputs/apk/stock/debug/app-stock-debug.apk
SEEDED=target-app/app/build/outputs/apk/seeded/debug/app-seeded-debug.apk
log(){ echo "[$(date +%H:%M:%S)] $*"; }
seg="${1:-all}"

phase1(){
  export BENCH_DEVICE_SERIAL="$PHONE"
  log "PHASE1 (phone-stock, dev=$PHONE): ensure STOCK apk (only on scored phone)"
  adb -s "$PHONE" install -r "$STOCK" >/dev/null 2>&1 || { adb -s "$PHONE" uninstall $PKG >/dev/null 2>&1; adb -s "$PHONE" install "$STOCK" >/dev/null; }
  for t in a1 a2 a3 a4 b5 b6 b7 c10; do log "PHASE1 task=$t"; uv run bench run --tool all --task "$t" --runs "$RUNS"; done
}
phase2(){
  export BENCH_DEVICE_SERIAL="$PHONE"
  log "PHASE2 (c9 seeded ship-gate, dev=$PHONE): install SEEDED"
  adb -s "$PHONE" uninstall $PKG >/dev/null 2>&1 || true; adb -s "$PHONE" install "$SEEDED" >/dev/null
  uv run bench run --tool all --task c9 --runs "$RUNS"
  log "PHASE2: restore STOCK"; adb -s "$PHONE" uninstall $PKG >/dev/null 2>&1 || true; adb -s "$PHONE" install "$STOCK" >/dev/null
}
phase3(){
  export BENCH_DEVICE_SERIAL="$WATCH"
  log "PHASE3 (b8 wear capability row, dev=watch)"
  uv run bench run --tool all --task b8 --runs "$RUNS"
}

case "$seg" in
  1) phase1 ;; 2) phase2 ;; 3) phase3 ;; all) phase1; phase2; phase3 ;;
  smoke) export BENCH_DEVICE_SERIAL="$PHONE"; uv run bench run --tool all --task a1 --runs 1 ;;
  *) echo "usage: PHONE=.. BENCH_WATCH_SERIAL=.. $0 [smoke|1|2|3|all]"; exit 1 ;;
esac
log "SEGMENT '$seg' COMPLETE"; uv run bench report || true
