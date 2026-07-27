---
doc_type: issue
title: quickmerge.sh --agent --files errors on a fully-committed pure-deletion commit
summary: >-
  When every path passed to `--files` is a deletion that has already been fully committed (not just staged),
  `quickmerge.sh` exits 1 with "No valid paths from --files. Nothing to commit." instead of falling through to its own
  existing "already committed, ahead of main — proceeding to push + PR" handling. A one-line ADDED_ANY==0 guard blocks
  the sibling code path from ever being reached.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [quickmerge, tooling-gap, ci-cd, worker-lifecycle]
related: []
created: 2026-07-26
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
drift_direction: worsening-slowly
depends_on: []
source:
  [
    "Found 2026-07-26 (slot-7, backend_engineer) while shipping sports_satellite_ao_dispatch_batch5_2026_07_26.md's T6.8
    residual todo — two pure-deletion commits (market-tick-data-service, instruments-service) both hit this.",
  ]
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
---

# quickmerge.sh --agent --files errors on a fully-committed pure-deletion commit

## What I found

Worked a todo that deletes several files (dead one-off scripts). Followed the standard worker flow exactly: `git rm`
each file, `git commit`, `bash scripts/quality-gates.sh --no-fix` (green, sentinel written matching the new HEAD), then
`bash scripts/quickmerge.sh "msg" --agent --files '<the deleted paths>'`.

`quickmerge.sh` exited 1:

```
[repo] ⚠️  Path not found (and not tracked): <path1>
[repo] ⚠️  Path not found (and not tracked): <path2>
...
[repo] ❌ No valid paths from --files. Nothing to commit.
```

**Root cause** (`unified-trading-pm/scripts/quickmerge.sh` around line 1553-1584): the `--files` staging loop only
recognizes two states per path — (1) `[ -e "$f" ]` true (file exists on disk, new/modified content to add), or (2)
`git ls-files --error-unmatch -- "$f"` succeeds (file still present in the INDEX but missing from the worktree — an
_unstaged_ deletion, e.g. a plain `rm` without `git rm`). Neither matches a path that was `git rm`'d **and already
committed**: the file is gone from the worktree, the index, AND `HEAD~0`'s tree is already updated — so
`git ls-files --error-unmatch` correctly reports "not tracked" (it never was, post-commit). This sets `ADDED_ANY=0` for
every such path, hitting the early `exit 1` at line 1569-1571.

The exact handling this SHOULD fall into already exists two lines later — the `git diff --cached --name-only` empty
branch (line 1573-1584) checks `AHEAD_COUNT` against `origin/main` and prints "No uncommitted changes in --files paths;
branch is N commit(s) ahead of main — changes already committed. Proceeding to push + PR." That branch is provably
correct for this exact scenario (a clean, fully-committed-ahead tree) — it's just unreachable because the `ADDED_ANY==0`
guard exits first.

**Reproduced twice this session** (market-tick-data-service, instruments-service), same failure mode both times, worked
around by including one unchanged tracked file (e.g. `README.md`) in `--files` alongside the deleted paths — that
satisfies `ADDED_ANY=1` (the unchanged file gets a no-op `git add`), so execution reaches the
`git diff --cached --name-only`-empty check, which then correctly falls through to "already committed, ahead —
proceeding to push + PR" and ships cleanly. Not a hack: it's the tool's own designed fallback, just reached via a side
door.

## Why it matters

Any worker following the documented flow literally (`git rm` several files → commit → QG →
`quickmerge --agent --files '<paths>'`) will hit this every time the commit is a **pure deletion** (no modified/added
files in the same commit). The workaround (padding `--files` with an unrelated unchanged file) is non-obvious and easy
to get wrong (e.g. accidentally including a file that _does_ have unrelated local changes would silently pull those into
the commit — the opposite of what `--agent --files` scoping exists to prevent). Worth a proper one-line fix rather than
relying on every worker rediscovering the padding trick.

## Recommended decision

- [ ] [SCRIPT] P3. In `unified-trading-pm/scripts/quickmerge.sh`, when the `--files` staging loop's `ADDED_ANY` stays 0
      (line ~1569), check `AHEAD_COUNT=$(git rev-list origin/main..HEAD --count)` before exiting — mirror the existing
      `git diff --cached --name-only`-empty branch immediately below it (line ~1573-1584): if `AHEAD_COUNT -gt 0`, print
      the same "already committed, ahead of main — proceeding to push + PR" message and fall through instead of
      `exit 1`. (repo: unified-trading-pm)
