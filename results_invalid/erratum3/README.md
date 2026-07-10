# Voided by ERRATUM #3 (Monitor shell-escape) — 2026-07-10

These (tool,task) rows are voided because the `Monitor` built-in gave the confined
agent an arbitrary-shell escape (raw adb/jdb), bypassing the tool-under-test. See
`../../AMENDMENTS.md` (ERRATUM #3). Contaminated cells measured (Monitor ran a
device shell): maestro/b5 3/5, linc/b7 1/5, maestro/b7 1/5, mobile-mcp/b7 2/5,
maestro/c10 1/5. Whole rows voided for within-task confinement uniformity; the
clean cells of maestro-only tasks (linc/mobile-mcp b5,c10) were kept in `results/`
(they never invoked Monitor → confinement-invariant). Re-run under the fixed
confinement (all orchestration built-ins denied).
