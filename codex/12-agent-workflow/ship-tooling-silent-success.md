---
doc_type: codex-ssot
title: Silent success in ship tooling — why a green ship may have shipped nothing
summary: >-
  A ship script exiting 0 is NOT evidence that anything landed. Five distinct mechanisms measured on 2026-08-10 produced
  "success" while committing part of the change or none of it: an autostash guard quarantining the caller's own --files,
  a stash-then-fatal that never restored, isolated mode dropping file DELETIONS, `| tail` masking a non-zero exit, and a
  pre-reconcile quarantine reporting "No changes to commit". Each announced itself in a line nobody reads. This doc
  gives the one verification rule that catches all of them, and the diagnostic order for "my work vanished" — which is
  almost never a peer.
authoritative_for: [ship-verification, silent-success, vanished-work-diagnosis]
status: current
nature: guideline
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer]
tags: [quickmerge, safe-doc-push, autostash, verification, multi-agent]
related:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/12-agent-workflow/host-concurrency-and-commit-provenance.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-08-10
last_updated: "2026-08-10"
owner: infrastructure
last_reviewed: "2026-08-10"
code_refs:
  [
    unified-trading-pm/scripts/quickmerge.sh,
    unified-trading-pm/scripts/dev/safe-doc-push.sh,
    unified-trading-pm/scripts/dev/tree-wip-guard.sh,
  ]
referenced_by: []
---

# Silent success in ship tooling

## The one rule

**Verify a ship against `origin`, never against the ship command's exit code.**

```bash
git fetch -q origin "$BRANCH"
git show "origin/$BRANCH:<path>" | grep -qF '<a string your change introduced>' || echo "NOT LANDED"
```

Per _marker_, not per file: a partial commit lands the file while dropping the change you cared about. Measured
2026-08-10 — a ship reported `✅ post-push ancestry verified` and `EXIT=0` having committed one of four named files.
Ancestry verification is honest about the commit it made; it cannot tell you the commit contained what you asked for.

## Five measured ways a green ship shipped nothing

| mechanism                                                                            | what it printed                                |
| ------------------------------------------------------------------------------------ | ---------------------------------------------- |
| autostash guard quarantined the caller's own `--files` (argument-order bug)          | `No changes to commit`                         |
| STAGE 5 stashed the tree, hit a fatal, never restored                                | the fatal — then the NEXT ship looked complete |
| isolated mode skipped paths absent from the caller tree, so `git mv` lost its DELETE | `skipping copy: <path>`                        |
| `cmd \| tail -25` returned tail's status                                             | nothing — exit 0                               |
| pre-reconcile quarantine on a large stash pile                                       | `quarantined; the next pull will start clean`  |
| QG killed mid-run by the host RAM-pressure watchdog (2026-08-12)                     | `Re-gate hit ONLY the duration budget`         |

Every one of them logged what it was doing. The failure is not that the tools are silent; it is that the line is one of
several hundred and reads as routine.

**A sixth, and it is the CALLER's bug, not the tool's** (measured 2026-08-12, twice in one session). Backgrounding a
ship as:

```bash
bash scripts/quickmerge.sh ... > ship.log 2>&1; echo "EXIT=$?"
```

makes the backgrounded command's overall status that of the LAST command in the list — the `echo`, which is **always
0**. The harness then reports `completed (exit code 0)` no matter what quickmerge did. This is the same class as the
documented `cmd | tail` row above (status of the wrong process), but it survives the fix for that one, because there is
no pipe to notice. Both times the ship had genuinely not landed: once the QG was SIGTERM'd by `qg-governor-watchdog`
at >=75% host RAM (a peer slot was running two concurrent quickmerges), once a rebase conflict left the commit unpushed.

Use `set -o pipefail` and let the ship command BE the last command, or capture its status into a variable before echoing
anything. But the durable defence is the one rule above: **the exit code never proves a ship; only `origin` does.**
`git rev-list --count origin/<branch>..HEAD` and grepping the log for `CITE THIS` / `Landed on` cost one call and cannot
be fooled by any of the six.

## "My work vanished" — diagnostic order

On a shared checkout the instinct is _a peer reverted me_. Measured 2026-08-10: that was wrong at least four times out
of four. **Check these in order before blaming anyone:**

1. **`git stash list`** — look for `safety-snapshot:` / `quickmerge-<pid>` / `autostash` entries. The guards _park_
   work, they do not drop it. `git stash show -p 'stash@{N}' | grep -c '<your marker>'` finds which one holds it.
2. **The ship log** — grep it for `quarantin`, `Stashing changes`, `skipping copy`, `No changes to commit`. The reason
   is usually there verbatim.
3. **Your own retries** — each failed attempt can ADD a stash entry. The pre-reconcile quarantine fires at ≥10 entries,
   so a retry loop makes the next attempt _more_ likely to be eaten. A failure mode that worsens as you retry feels like
   an adversary; it is a threshold.
4. **Only then**, a peer.

## A backup taken at the wrong moment is worse than none

The workspace already requires backing up WIP before any git-touching command in a shared checkout
(`/codex/05-infrastructure/per-tab-worktrees.md`). Two refinements learned the hard way:

- **Verify the backup contains the change**, by marker, immediately after taking it. A backup taken _after_ a guard
  stashed the tree captures the already-stripped version and looks like insurance. That happened on 2026-08-10; recovery
  came from git's stash, not from the scratchpad copy.
- **Prefer a private worktree to a backup.** `git worktree add --detach "$TMPDIR/<name>/.tabs/<N>/<repo>" HEAD` gives an
  independent working tree that another session's `checkout`/`pull` cannot touch. Include the `.tabs/<N>/` segment so
  slot commit-attribution still derives correctly, and symlink the sibling repos next to it so `quality-gates.sh`'s
  `WORKSPACE_ROOT` derivation resolves.

## Restoring a backup can delete someone else's work

Before restoring a whole file from a backup, diff it against `origin` and read the **removals**:

```bash
git diff origin/<branch> -- <file> | grep '^-' | grep -v '^---'
```

If a removed line is not one your edit replaced, your backup predates a peer's change and restoring it wholesale reverts
them. Reset to `origin`'s version and re-apply only your own edit on top. This caught a near-miss on 2026-08-10 where
restoring `quickmerge.sh` would have deleted a peer's autostash chain-breaker.

## Ship-script defects are usually symmetrical — check the sibling

`safe-doc-push.sh` and `quickmerge.sh` share a design and drift apart silently. The isolated-mode dropped-DELETE bug was
fixed in one and left in the other the same day, and bit a real ship within the hour. **When you fix a defect in one
ship script, grep the other for the same shape before you move on.** The same applies within a file: the argument-order
bug had a correctly-called sibling function 65 lines below it, which is what pinned the intended contract.
