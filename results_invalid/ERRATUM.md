# ERRATUM — results_invalid/ is a VOIDED run (do not use)

**Date:** 2026-07-08
**Status:** All runs under `results_invalid/` are INVALID and must not be cited,
reported, or published. They are retained only as an audit trail of a harness
defect found mid-campaign.

## What was wrong

The harness fairness invariant (see `mobile_agent_bench/agent.py` docstring:
*"the MCP surface is the only capability"*) was **not enforced**. The agent was
launched with:

```
claude -p <prompt> --model <m> --mcp-config <tool> --strict-mcp-config \
  --output-format stream-json --verbose --dangerously-skip-permissions
```

`--strict-mcp-config` restricts only which **MCP servers** load. It does **not**
remove Claude Code's built-in tools (`Bash`, `Read`, `Grep`, `Glob`, `Write`,
`WebFetch`, …). With `--dangerously-skip-permissions` and the working directory
set to the repo root, every agent therefore had a full shell on the host, inside
the benchmark repo.

## Measured contamination (all 175 completed runs scanned)

| tool | runs | used built-in Bash/Read/Grep | ran `adb` directly via Bash | read app source / ground-truth |
|---|---|---|---|---|
| agent-device | 45 | 45 | 34 | 17 |
| linc | 45 | 45 | 16 | 12 |
| maestro | 45 | 33 | 31 | 15 |
| mobile-mcp | 40 | 17 | 14 | 10 |

Consequences that void the data:
1. **Tool bypass** — 95 runs shelled out to `adb` directly, so the "tool-under-test
   comparison" partly measured raw `adb`, not the MCP stack.
2. **Ground-truth leakage** — 54 runs read `SPEC.md` / app source (which contain
   the frozen answers: the crash string, `discountFactor = 0.755`, etc.), so
   answer-verified passes may reflect *reading the answer*, not device operation.
   This is the likely cause of the implausibly clean b5/b6/b8 5/5 sweeps.
3. **Wrong-device operation** — agent-device `find`-ed the stock APK on disk and
   `install`ed it onto non-target devices (the S10), after which agents drove the
   wrong device. (Also breaks the seeded-only premise of c9.)

## The fix (applied before the clean re-run)

- Confine the agent to **only** the tool-under-test's MCP tools (+ the loader),
  disallowing all built-in filesystem/shell/web tools.
- Launch the agent in a **neutral working directory outside the repo**, so no
  source or ground-truth is reachable even by accident.
- Disclosed as a pre-registration erratum; the frozen task suite / metrics /
  pass-criteria are unchanged — only the (buggy) agent-isolation plumbing.

The valid dataset lives in `results/` after the clean re-run.
