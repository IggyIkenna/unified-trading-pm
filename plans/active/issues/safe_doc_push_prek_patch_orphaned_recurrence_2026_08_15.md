---
doc_type: issue
title: safe-doc-push orphaned prek patch — recurrence of an archived issue class
summary: >-
  A safe-doc-push.sh run (slot-14, 2026-08-15) queued 287s behind another slot's push, landed cleanly, but exited
  non-zero with an ORPHANED PREK PATCH warning for /home/ubuntu/.cache/prek/patches/1786775660293-50536.patch — a
  467-file "context-scout" context_scope refresh sweep whose content is confirmed genuinely missing from the working
  tree (not just redundant). Same failure signature as the archived 2026-08-09 issue, so this is a recurrence, not a
  first occurrence.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao, tooling, data-loss-risk, safe-doc-push, prek]
related:
  - /plans/archive/2026_08/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md
  - /plans/active/infra_consolidated_closeout_2026_07_25.md
created: 2026-08-15
author: unknown
priority: P2
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
assigned_role: infra
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
locked_by:
resolved_by:
depends_on: []
source:
  - "observed during a routine plan checkbox-flip push, slot-14, 2026-08-15"
---

# safe-doc-push orphaned prek patch — recurrence of an archived issue class

## What happened

During a `bash scripts/dev/safe-doc-push.sh` run (slot-14, 2026-08-15, shipping the
`uac_data_type_validity_combinator_fragmentation_2026_07_07.md` checkbox flip), the push queued 287s behind another
slot's push, then succeeded (`885870a603 -> live-defi-rollout`) but exited non-zero (exit 9) with:

```
⚠️  ORPHANED PREK PATCH(ES) DETECTED after this run's push succeeded
   - /home/ubuntu/.cache/prek/patches/1786775660293-50536.patch
```

This is the exact failure signature previously tracked and CLOSED at
`/plans/archive/2026_08/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md` — i.e. it is a
**recurrence**, not a first occurrence. The prior fix did not fully close the gap (or a new trigger path exists,
possibly specific to long push-queue waits — this run queued 287s, well past typical contention).

## Evidence

- `/home/ubuntu/.cache/prek/patches/1786775660293-50536.patch` — mtime 2026-08-15 06:34, 467 files changed (1920
  insertions / 167 deletions). Content is a "context-scout" automated `context_scope` refresh sweep across
  `plans/active/*.md` — NOT my session's content (my session only touched one file, already confirmed landed at
  `git show HEAD:plans/active/issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md`).
- Confirmed genuinely missing, not just redundant:
  `grep "context-scout 2026-08-15" plans/active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md`
  (the patch's first hunk) — **zero hits** in the current working tree. The context-scout sweep's work was never
  committed anywhere and is ONLY recoverable from this patch file.
- My own change is unaffected: `git rev-list --count origin/live-defi-rollout..HEAD` = 0, `git status --porcelain`
  empty, `unified-api-contracts@d27d29f0c9` + PM `885870a603` both landed correctly.

## Why this is BLOCKED-OPERATOR-DECISION, not something I fixed myself

- I don't own the context-scout sweep's content and can't confirm it's still current (its own timestamps are 2026-08-15
  06:34; today's session is later the same day — plausible staleness risk on some of the 467 files if their
  `context_scope` has since been touched by other sessions).
- 467-file blast radius is too large for me to unilaterally `git apply` + ship without the owning session's context, per
  the workspace's findings-triage rule (big/cross-repo → notify operator, don't silently fix).
- Not deleting the patch file — per the prior issue doc's own instruction, it must not be removed until its content is
  confirmed safe/recovered.

## Recommendation

1. Whoever owns/dispatches the "context-scout" role should
   `git apply --check /home/ubuntu/.cache/prek/patches/1786775660293-50536.patch` to confirm it still applies cleanly,
   then apply + ship via `safe-doc-push.sh` if the content is still current.
2. Root-cause the recurrence: the prior fix (archived issue, closed 2026-08-10) evidently doesn't cover the
   long-push-queue-wait path (this run queued 287s before acquiring the push slot) — re-open or link a new investigation
   against `scripts/dev/safe-doc-push.sh`'s prek stash/restore lifecycle under queue contention.

## Todos

- [ ] [OPERATOR] P2. **Recover or confirm-stale the orphaned context-scout patch** —
      `/home/ubuntu/.cache/prek/patches/1786775660293-50536.patch` (467 files, `context_scope` refresh sweep). Apply via
      the owning role/session if still current; else document as intentionally superseded and clear it. (repo:
      unified-trading-pm)
- [ ] [SCRIPT] P2. **Root-cause why `safe-doc-push.sh`'s prek patch restore can still fail under a long (287s-observed)
      push-queue wait**, despite the 2026-08-09 fix — reopen or extend
      `/plans/archive/2026_08/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md`'s
      investigation for this trigger path. (repo: unified-trading-pm)
