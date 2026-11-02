---
linc-agent-version: 1
type: project
---

# Mobile Agent Bench — Project Instructions

Benchmark harness comparing mobile-automation tool stacks (LINC nerve/crucible/spectra,
mobile-mcp, agent-device, …) driving agents against the BenchTarget app on the physical
device bench. Scored device: Pixel 8 Pro (pre-registered); results in `BENCH_RESULTS_DIR`.

## Operational Notes

<!-- BEGIN AUTO-GENERATED FROM joey.db — do not edit between markers -->
- **Meta's Anthropic-compatible POST /v1/messages endpoint returns HTTP 400 on container, inference_geo, stop_sequences, top_k, and thinking.type="disabled"; a native /v1/responses MCP loop replaying reasoning.encrypted_content avoids HTTP 400s and cuts Claude Code's ~18k-token per-turn system prompt overhead.** <!-- rule_id: c887e8a3-40ba-4420-86d1-9107a805e7d0 h:3b9f208b8379 -->
- **Tool stacks enumerate ALL connected adb devices, not just BENCH_DEVICE_SERIAL — every fleet serial must be on the bench.local.yaml redact list or sibling serials leak into transcripts.** <!-- rule_id: 1ad4d377-c962-45c6-b391-f0f5e977b532 h:e1f8d3c2a97f -->
- **Bench 'uncached tokens' = cache_creation + input + output, and cache_creation DOMINATES — every mid-run ToolSearch schema load rewrites the prompt-cache prefix, so tool-description weight multiplies across the run. Vision tokens ≈ (w*h)/750: a 488x1080 PNG ≈ 702 tok/image vs mobile-mcp's 177x395 ≈ 93.** <!-- rule_id: d61df570-0510-4e71-9469-0536494b0bd2 h:1ce9e928c23c -->
- **A column's pass rate is not evidence an agent used a new tool: Muse Spark never called nerve_ground in 12 linc-sam runs because uiautomator bounds still located the unlabeled Submit. To measure a new capability, remove the fallback from the task set, and show grounding via the CLI overlay in outward captions.** <!-- rule_id: ea012291-3232-492f-b043-2c73f4c81b93 h:22c011a9edac -->
- **The frozen `linc` column runs the PyPI linc-nerve 0.1.0 venv (~/.linc/mab-v3-nerve-pypi), NOT the live ~/projects/linc-nerve clone: new nerve features reach bench cells only through an addendum column (BENCH_TOOLS_DIR=tools_addendum).** <!-- rule_id: 06d57120-992f-4877-9784-a1271a4776b0 h:cd83d08299d8 -->
- **Agents pick their device via nerve_discover and task prompts name none: on a 7-device host a Muse c9 cell drove the Pixel 8 Pro (stock APK) instead of the reset S24. Run every agent cell with the target as the only phone attached (plus the watch only for a6/b11). Accept a cell only if meta.json device.model matches and the run-start `adb devices` count is 1; the Muse transcript has no tool_result records, so also check the &lt;REDACTED-n&gt; device ids in transcript+stderr.** <!-- rule_id: 07d4d847-2c0e-4f4b-9718-92bc86e72da8 h:91708e891539 -->
- **Don't re-add java-kotlin to CodeQL default setup — target-app is a seeded/defective benchmark target with no testClasses task, and this repo is Python-primary.** <!-- rule_id: 9137b710-0f44-41b5-8c1a-77b9aba26373 h:7875785d8fe2 -->
- **Comparative-grid hygiene: NEVER nerve_reserve the bench device during a grid (the linc column's own nerve honors the pool and self-blocks) — neutralize the nightly with launchctl bootout instead. Interactive crucible BVT ignores nerve_pool, so do no interactive device work during a grid. After any abort run the full sweep: delete the in-flight run dir, kill shell-uid app_process orphans holding UiAutomation, clear adb forwards. Save logcat ActivityTaskManager interference receipts before the ring buffer rolls.** <!-- rule_id: 32229dce-8b0d-4f9e-8c59-ac2c731bc3ab h:09475ac8f0d3 -->
- **Confining a headless `claude -p` agent must deny the harness orchestration surface (Monitor, Task*, Schedule*, Cron*, Skill, SendMessage, Worktree, etc.), not just Bash/fs/web — Monitor takes a `command` field and runs arbitrary shell in a loop, bypassing the tool-under-test.** <!-- rule_id: 77b09891-506a-41fc-ac1b-e9cb52192030 h:ef324ad26dd8 -->
- **The no-internal-topology pytest is strongest only on a maintainer machine (redact patterns come from gitignored bench.local.yaml) — CI green does NOT prove committed docs are serial-free; run pytest locally after writing any doc that references devices.** <!-- rule_id: 587cfff3-1ceb-46ec-b60e-96f8090739ce h:2a09177dd532 -->
- **The wear APK launcher activity is dev.lincforge.benchtarget/.wear.MainActivity (module namespace ≠ applicationId) — launch via LAUNCHER intent/monkey, never a hardcoded .MainActivity component.** <!-- rule_id: ba04850b-9e54-486e-9e32-6197698330de h:5f39a7464b4a -->
- **Never run pytest or commit while a `bench run` is in flight — the repo topology scanner reads the not-yet-sanitized in-flight transcript and trips on raw serials; commit only at quiescent points.** <!-- rule_id: a7be529b-10bd-4048-a474-64867910f4fc h:de8c80c601ce -->
- **A headless benchmark agent with Bash + the repo as cwd silently bypasses the tool-under-test (runs adb directly, reads ground truth from SPEC.md/source), voiding the comparison — block shell+search; a screenshot-Read is fine since without enumeration the agent can't discover the repo path.** <!-- rule_id: 06af7cdb-22e7-4f7b-be54-1002fe029315 h:af921c112c7f -->
- **`claude -p --strict-mcp-config` restricts ONLY MCP servers, NOT Claude Code built-in tools (Bash/Read/Grep/Glob) — for real tool-isolation also pass --disallowedTools AND run the agent from a neutral cwd outside the repo.** <!-- rule_id: e59e3ba9-f1fb-48e1-a8f7-f96a6b172209 h:cd5f827f31ec -->
- **A new agent runner must not add a turn cap the baselines lacked: meta_agent MAX_TURNS=40 cut c9 off at 131 s of 900 s (Claude used 101-165 turns) and graded a mid-task sentence. The wall-clock timeout must bind, and a cap cut-off must not write a result record.** <!-- rule_id: 28117ea5-c152-496c-b9d1-046e59d285ff h:8b32c0734ece -->
- **When the CEO asks to 'improve as we discover' during a benchmark, freeze the vendor's stack at pre-registration and score the headline only on that frozen version; report any post-fix grid separately, so the result is not open to the 'tuned on seen tasks' objection.** <!-- rule_id: 6ad6144c-06b2-4294-b010-441455cc1d28 h:a6a55804c49e -->
<!-- END AUTO-GENERATED FROM joey.db -->
