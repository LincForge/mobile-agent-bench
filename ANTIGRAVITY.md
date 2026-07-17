<!-- AUTO-GENERATED FROM LINC.md — DO NOT EDIT -->
<!-- LINC_CONTEXT_v1_hash:b651d00b096c -->


# Mobile Agent Bench — Project Instructions

Benchmark harness comparing mobile-automation tool stacks (LINC nerve/crucible/spectra,
mobile-mcp, agent-device, …) driving agents against the BenchTarget app on the physical
device bench. Scored device: Pixel 8 Pro (pre-registered); results in `BENCH_RESULTS_DIR`.

## Operational Notes

<!-- BEGIN AUTO-GENERATED FROM joey.db — do not edit between markers -->
- **A headless benchmark agent with Bash + the repo as cwd silently bypasses the tool-under-test (runs adb directly, reads ground truth from SPEC.md/source), voiding the comparison — block shell+search; a screenshot-Read is fine since without enumeration the agent can't discover the repo path.**
- **Comparative-grid hygiene: NEVER nerve_reserve the bench device during a grid (the linc column's own nerve honors the pool and self-blocks) — neutralize the nightly with launchctl bootout instead. Interactive crucible BVT ignores nerve_pool, so do no interactive device work during a grid. After any abort run the full sweep: delete the in-flight run dir, kill shell-uid app_process orphans holding UiAutomation, clear adb forwards. Save logcat ActivityTaskManager interference receipts before the ring buffer rolls.**
- **Confining a headless `claude -p` agent must deny the harness orchestration surface (Monitor, Task*, Schedule*, Cron*, Skill, SendMessage, Worktree, etc.), not just Bash/fs/web — Monitor takes a `command` field and runs arbitrary shell in a loop, bypassing the tool-under-test.**
- **Don't re-add java-kotlin to CodeQL default setup — target-app is a seeded/defective benchmark target with no testClasses task, and this repo is Python-primary.**
- **Never run pytest or commit while a `bench run` is in flight — the repo topology scanner reads the not-yet-sanitized in-flight transcript and trips on raw serials; commit only at quiescent points.**
- **The no-internal-topology pytest is strongest only on a maintainer machine (redact patterns come from gitignored bench.local.yaml) — CI green does NOT prove committed docs are serial-free; run pytest locally after writing any doc that references devices.**
- **The wear APK launcher activity is dev.lincforge.benchtarget/.wear.MainActivity (module namespace ≠ applicationId) — launch via LAUNCHER intent/monkey, never a hardcoded .MainActivity component.**
- **Tool stacks enumerate ALL connected adb devices, not just BENCH_DEVICE_SERIAL — every fleet serial must be on the bench.local.yaml redact list or sibling serials leak into transcripts.**
- **`claude -p --strict-mcp-config` restricts ONLY MCP servers, NOT Claude Code built-in tools (Bash/Read/Grep/Glob) — for real tool-isolation also pass --disallowedTools AND run the agent from a neutral cwd outside the repo.**
- **Bench 'uncached tokens' = cache_creation + input + output, and cache_creation DOMINATES — every mid-run ToolSearch schema load rewrites the prompt-cache prefix, so tool-description weight multiplies across the run. Vision tokens ≈ (w*h)/750: a 488x1080 PNG ≈ 702 tok/image vs mobile-mcp's 177x395 ≈ 93.**
<!-- END AUTO-GENERATED FROM joey.db -->
