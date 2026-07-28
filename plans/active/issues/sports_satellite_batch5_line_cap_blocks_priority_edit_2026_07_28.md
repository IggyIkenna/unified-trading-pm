---
doc_type: issue
title: sports_satellite_ao_dispatch_batch5 is over the 1000-line hard cap, blocking its priority-resort edit
summary:
  Discovered applying the 2026-07-28 priority-resort — sports_satellite_ao_dispatch_batch5_2026_07_26.md is already 1002
  lines (over the 1000-line hard cap) BEFORE the resort touched it, so `check_line_caps.sh` blocked staging its 1-line
  `priority:` edit. Excluded from that commit; left at its current priority pending the standard line-cap remediation
  (extract closed Progress Log sections into an archive-bound history doc, per plan_line_cap_remediation_2026_07_23.md's
  precedent). SECOND COLLISION 2026-07-28 (same day, operator-gate retag pass) — the same file also carries 2
  now-resolved `[OPERATOR]` gates (the A2 purge todo, the sports_reference_v1_archive delete todo) that the retag
  workflow could not land for the same reason — file already over cap before any new content. Reverted that edit too
  rather than force it over cap further; bumped priority since this has now blocked two independent fixes in one day.
status: open
nature: process
asset_group: [sports]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-hygiene, line-cap, priority]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md,
    /codex/11-project-management/plan-priority-tier-and-dispatch-ordering.md,
  ]
created: "2026-07-28"
parent_epic: sports_master
source:
  Discovered mid-commit applying the 2026-07-28 priority-resort delta set; not fixed inline to avoid scope creep on that
  commit.
execution_scope: local-only
assigned_vm: NA
priority: P1
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
---

# sports_satellite_ao_dispatch_batch5 is over the 1000-line hard cap

## Todos

- [ ] [SCRIPT] P2. Extract the oldest fully-closed dated Progress Log section(s) from
      `plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md` into an archive-bound
      `sports_satellite_ao_dispatch_batch5_history_2026_07.md` (`status: complete`, `nature: record`, 0 open todos)
      under `plans/archive/2026_07/`, leaving a one-line pointer behind, until the live doc is back under 1000 lines.
      Then flip its `priority:` from `P1` to `P2` per the 2026-07-28 resort (it is 21/23 top-level todos done, a
      corpus-hygiene AO-dispatch-batch satellite per that resort's carve-out logic, same as its sibling batches).
      Definition of done:
      `bash scripts/plan-hygiene/check_line_caps.sh plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md`
      reports the file within cap, and its `priority:` reads `P2`.
- [ ] [SCRIPT] P1. Once the file is back under cap (prior todo), retag its 2 now-resolved `[OPERATOR]` gates: the A2
      dead-dimension manifest-purge todo (→ `[DATA]`, citing the already-shipped features-service@d564bf6f delete) and
      the `sports_reference_v1_archive`/`--drop-stale` delete todo (→ `[DATA]`/`[SCRIPT]`, citing the extended §3a
      reversibility carve-out — fresh-check `gcs_bucket_soft_delete_retention_seconds()` on both target surfaces,
      combined with the already-shipped twin-verification + dry-run at `market-tick-data-service@236d945e`/`@08439787`).
      Definition of done: both todos read a non-`[OPERATOR]` tag with the citation inline.
