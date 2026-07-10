# c10 voided — erratum #2 (Read-of-source confinement hole), 2026-07-10

These c10 cells were run BEFORE the PreToolUse Read-guard landed. One
(maestro-c10/run-5) read app source via a guessed absolute path and computed the
frozen answer — a ground-truth leak. The whole c10 row is voided here for audit
and re-run cleanly under the guard. Kept per the CEO "preserve voided data"
precedent. Incomplete (killed-mid-run) cells were deleted before archiving. See
AMENDMENTS.md 2026-07-10.
