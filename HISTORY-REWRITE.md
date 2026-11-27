# History rewrite, 2026-11-26

On 2026-11-26 the full git history of this repo was rewritten once, with
`git filter-repo`, to remove personal data captured in run transcripts
(device identifiers, notifications, app lists, embedded screenshots). All
branches and tags were force-pushed.

What did not change:

- Harness and task files are byte-identical at every pre-registration tag.
  Comparing the trees of each tag before and after the rewrite, the only paths
  that differ are under the results directories (`results/`,
  `results_invalid/`, `results_s10/`, `results_v2/`, `results_v2validation/`,
  `results_v3/`) and four screen recordings (`recording-*.mp4`) that sat at
  the repo root from the v2 era and were removed.
- Commit author and committer dates are preserved.
- Tag names are unchanged.

What changed: every commit id. The tags map as follows.

| ref | old commit | new commit |
|---|---|---|
| `v1-prereg` | `c05c617821eb939ef2ffa4b2ec912005644f8658` | `499e10be2c10acdfafa3b14947d5c7424b245ea1` |
| `v2-prereg` | `602749063a121255e62cd8b60dec7a7265da0464` | `ec5292798ec66d77551503c3a16d824c413b567d` |
| `v3-prereg` | `2dc566d267e0fbd3485609770822e9e0f2d84816` | `ad9d24f46e335be0600fd1c6229b3b18b8444623` |
| `pre-hackathon-2026-10-26` | `5bb0ed5d7aecc1a3bf3268b0252011119669a939` | `dec0a8c22f9e8ad8c1a7f52f8edda349ea0d2d16` |
| `main` (at the rewrite) | `555369e6bf6deb3baffa56e2558dc7a577e012f2` | `eeb7e8680d65c0b7d3a1f3d80b8d8337fe26a1a1` |

The full old-to-new map for all commits is available on request (open an
issue).

Old ids still appear verbatim inside two raw agent transcripts under
`results_invalid/` (commands the agent ran); transcripts are kept as recorded.
