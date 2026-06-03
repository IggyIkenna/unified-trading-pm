---
title: "Shared git stash pile archived + cleared — confirmation window before final purge"
created: 2026-06-01
source:
  - unified-trading-pm/.git (shared common dir — stash ref visible to all slot worktrees)
parent_epic: infrastructure_master
priority: P3
status: active
locked_by: live-defi-rollout
locked_since: 2026-06-01
estimate_calibrated_ai_days: 0.4
estimate_class: infra
---

# Shared git stash pile — archived + cleared (2026-06-01)

## What I found

`git stash list` in `unified-trading-pm` was **91 deep**. Stashes live in the shared common `.git`, so the pile was
visible to (and partly created by) every slot worktree + the main checkout — a mix of: autostash residue, `foreign-*`
reconciliation parks, other-slot WIP snapshots (`WIP on tab/ikennaigboaka/{2..8}`), and slot-1's own parks. **Not all
docs** — ~329 `.py` entries across the pile (QG checkers, manifest/audit/propagation scripts), incl. a few ~100-file
"stash-everything-before-rebase" snapshots.

## What I did

- Dropped 5 provably-safe (4 content-already-in-LDR + 1 empty).
- Archived the remaining **86 three ways** before clearing:
  - gc-proof refs `refs/stash-archive/0000..0085` (local, in shared repo)
  - portable bundle `.stash-archive-20260601/stash_pile.bundle` (8.2 MB, vs LDR)
  - `.stash-archive-20260601/manifest.txt` (index → sha → label) + `README.md`
- Verified round-trip restore (re-stored the 107-file code snapshot, confirmed, re-cleared). `git stash list` is now
  **0**.

## Why it matters

Zero data loss + fully reversible, but the archive refs are **local to this host's .git** (not pushed). Anyone who
parked WIP in the shared stash should confirm they don't need it restored before we purge the archive.

## Recommended decision / future check

- [ ] [INFRA] P3. After ~1 week (target **2026-06-08**), if no slot/operator has asked to restore anything from the
      stash archive, purge it:
      `git for-each-ref refs/stash-archive/ --format='%(refname)' | xargs -n1 git update-ref -d` then
      `rm -rf .stash-archive-20260601`. Recovery procedure until then is in `.stash-archive-20260601/README.md`. —
      ikenna-slot-1
