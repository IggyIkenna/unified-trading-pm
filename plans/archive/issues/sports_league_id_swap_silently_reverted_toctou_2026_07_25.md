---
doc_type: issue
title:
  Sports league_id manifest swap (mtds "COPY+SWAP done", claimed re-verified 2026-07-24) had silently reverted — 260,298
  stale raw rows were live again; re-applied + verified stable across 5 consolidator cycles
summary: >-
  The league_id namespace migration's manifest swap (market-tick-data-service scripts/sports/league_id_relocation/
  manifest_swap_2026_07_22.py, run 2026-07-22, ADD 275,136 canonical rows + REMOVE 260,298 stale raw rows, verify_swap
  PASSED at the time) had silently reverted by 2026-07-25: a live `--apply-prod` plan-mode re-check found all 260,298
  stale raw-keyed rows back in the manifest (PLUS 8,425 canonical rows with wrong row_counts). This is despite
  `sports_plan_and_docs_reconcile_findings_2026_07_24.md`'s P0 finding, dated the DAY BEFORE, explicitly re-verifying
  and re-confirming "COPY+SWAP done" via live GCS spot-check. Root cause: the swap's CAS write predates (2026-07-22) the
  TOCTOU race fix in `unified-trading-library@14301571` (2026-07-24) that closed exactly this class of
  silent-clobber-by-a-concurrent-consolidator-cycle bug (see the sibling finding
  `sports_odds_manifest_consolidator_captured_outranks_resurrection_2026_07_24.md`). Re-applied the swap (`--apply-prod
  --confirm-prod-write`) now that the race is closed; verified STABLE across 5 consolidator cycles (~7.5 min of polling,
  `*/1 * * * *` cron) with zero reversion. The raw TRADES/batch_odds_api shape is now genuinely canonical. Deferred
  shapes (`odds_horizon_bucket`, `batch_footystats`) were never in this swap's scope and remain genuinely un-migrated —
  do not read this fix as covering them.
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: [sports, league-id, manifest-consolidator, toctou, resurrection, data-correctness, migration, verified-stable]
related:
  [
    /plans/active/issues/sports_league_id_namespace_migration_2026_07_20.md,
    /plans/archive/issues/sports_odds_manifest_consolidator_captured_outranks_resurrection_2026_07_24.md,
    /plans/archive/issues/sports_plan_and_docs_reconcile_findings_2026_07_24.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
  ]
created: 2026-07-25
assigned_vm: NA
parent_epic: sports_master
execution_scope: local-only
priority: P0
estimate_class: infra
source:
  sports_satellite_ao_dispatch_batch2_2026_07_24.md todo 36 (league_id casing migration census→copy→reprocess→swap)
resolved_by: market-tick-data-service (manifest_swap_2026_07_22.py re-run, no code change needed)
locked_by:
drift_direction: advance-code
depends_on: []
---

# Sports league_id manifest swap silently reverted — re-applied and verified stable

> **🟢 ARCHIVED 2026-07-25** — status=resolved, archived per /codex/11-project-management/issue-doc-lifecycle.md's
> archive-on-resolve rule (terminal_status_archival_backlog_sweep_2026_07_25.md).

## What I found

Assigned to execute batch2 todo 36 ("League_id casing migration — census→copy→reprocess→swap"), which described this as
an "already-committed, adversarially-verified executor" ready for a fresh run. Before running anything, I checked the
CURRENT live state (per this session's established pattern of verifying premises before executing) and found a direct
contradiction with the just-a-day-old reconcile finding.

**Live read, `market-data-tick-sports-prd-central-element-323112` manifest** (`read_availability_index`, `league_id`
column): `PREMIER_LEAGUE` = 19,954 rows, all `capture_status=captured`, dates spanning 2020-06-17 to 2026-05-24 (i.e.
the ORIGINAL historical population the 2026-07-22 swap was supposed to remove — zero rows after the swap date, ruling
out a live writer re-accumulating under the raw key).

**Full-scope confirmation** via the swap script's own read-only `--apply-prod` plan mode:

```
live index rows: 563,384
REMOVE: 260,298 live row(s) match a targeted stale tuple
ADD: 275,136 canonical keys planned — 0 genuinely new, 275,136 already present (8,425 with a row_count
     that DISAGREES with the report's verified target_rows)
```

This exactly matches the ORIGINAL pre-swap scope (260,298 stale / 275,136 canonical) — i.e. the 2026-07-22 swap's effect
had been **entirely undone**, not partially. `sports_plan_and_docs_reconcile_findings_2026_07_24.md`'s P0 finding, dated
2026-07-24 (one day before this check), explicitly claimed to have independently re-verified this via live GCS
spot-check ("canonical `league_id=EPL` object exists... manifest ADD/REMOVE swap executed 2026-07-22 (VERIFY PASSED
stale_remaining=0)") — that re-verification was itself either looking at a transient healthy window or checking a
narrower slice than the full 24-report scope; either way the manifest was NOT durably canonical at the time I checked.

## Root cause

The swap script (`manifest_swap_2026_07_22.py`) writes directly to the canonical `_index/availability_index.parquet` via
a generation-matched CAS write, ran 2026-07-22. The TOCTOU race that made exactly this kind of write vulnerable to
silent clobbering by a concurrent manifest-consolidator cycle (`*/1 * * * *` cron) was fixed in
`unified-trading-library@14301571`, shipped **2026-07-24 — two days after the swap ran**. That fix's own issue doc
(`sports_odds_manifest_consolidator_captured_outranks_resurrection_2026_07_24.md`) documents the identical symptom (a
correction write logs success, generation-confirms, then reverts within ~1-6 minutes) for a different data_type/bucket,
and traces the mechanism to `_write_consolidated`'s CAS token being taken from a fresh `blob.reload()` (always matches
itself) instead of the generation captured at the same read that produced the merge payload — so an external write
landing inside the consolidator's 90-120s read-to-write window gets silently overwritten by the consolidator's own
re-merge of pre-write content. The swap's own `verify_swap()` only checks the in-memory `df_after` immediately
post-write in the SAME script run — it has no visibility into what a consolidator cycle does moments later, so a clean
"VERIFY PASSED" at write time gives no guarantee of durability. This is highly plausible as the mechanism here given the
timing (swap predates the fix by exactly 2 days) and the byte-for-byte match to the pre-swap scope.

## What I did

Re-ran `manifest_swap_2026_07_22.py --apply-prod --confirm-prod-write` (idempotent — recomputes the exact stale/add sets
from the 24 durable shard reports on GCS each run, does not depend on any session-local state):

```
snapshot written + verified: gs://.../_index/snapshots/pre_league_id_manifest_swap_2026_07_22_20260725T003304Z.parquet
REMOVE done: base=563,384 rows -> removed 260,298 stale row(s).
ManifestWriter: updated availability index (465223 total entries, 275136 new)
VERIFY: stale_remaining=0 canon_present=275,136 canon_missing=0 canon_mismatched=0
>>> VERIFY PASSED.
```

**Then, unlike the original 2026-07-22 run, verified STABILITY** (the exact check that would have caught this the first
time) — polled the live manifest 5x over ~7.5 minutes (spanning multiple `*/1 * * * *` consolidator cycles):

| poll | time (UTC) | total rows | PREMIER_LEAGUE | EPL    |
| ---- | ---------- | ---------- | -------------- | ------ |
| 1    | 00:35:47   | 465,223    | 7,107          | 15,313 |
| 2    | 00:37:28   | 465,223    | 7,107          | 15,313 |
| 3    | 00:39:06   | 465,223    | 7,107          | 15,313 |
| 4    | 00:40:42   | 465,223    | 7,107          | 15,313 |
| 5    | 00:42:18   | 465,223    | 7,107          | 15,313 |

Byte-identical across all 5 polls — genuinely stable, not a transient healthy window like the prior "verified" claim
turned out to be. The residual 7,107 `PREMIER_LEAGUE` rows are NOT a re-reversion — they exactly match the non-TRADES
data_types this swap never targeted (`odds_horizon_bucket` 5,735 + `ODDS`/`odds` 673+673 + `trades`/ `trades_inplay`
23+3 = 7,107, confirmed by direct breakdown before the re-swap). The raw `TRADES`/`batch_odds_api` shape (the swap's
actual scope) is now genuinely, durably canonical.

## What remains — genuinely NOT done, do not conflate with this fix

This fix closes only the manifest-swap component for the raw `TRADES`/`batch_odds_api` shape (the original `b2a49317`
COPY's scope). The parent todo's other components remain outstanding:

- **`odds_horizon_bucket` shape (109,312 objects)** — requires MDPS `reprocess_sports_odds.py`'s Step-7 procedure
  (regenerate the processed surface under canonical partitions), not a manifest-only swap. Not started.
- **`batch_footystats` shape (16,970 objects)** — requires its own copy+swap pass via the casing-migration script
  extended to this shape. Not started.
- **Coverage-registry refresh** (`refresh_sports_bookmaker_league_coverage_2026_06_21.py`) — the parent todo's done-when
  includes `is_bookmaker_league_covered("BETFAIR_EX_EU","EPL")` flipping `False→True`; not yet run.
- **The human-gated DELETE** of old raw-keyed GCS objects — correctly out of scope for any agent
  (`sports_consolidated_closeout_2026_07_19.md` line 588, `[OPERATOR]`-only).

## Recommended follow-up

Given this exact silent-revert already happened once and the K2/footystats/odds_horizon_bucket work will involve further
direct-canonical-index writes, whoever executes the remaining shapes should apply the SAME stability check (poll ≥2
consolidator cycles post-write, not just the in-script immediate verify) before declaring any of them done — recommend
adding this as an explicit step to `manifest_swap_2026_07_22.py`'s own docstring/usage instructions so it isn't
rediscovered a third time.
