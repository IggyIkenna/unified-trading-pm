---
doc_type: issue
title:
  reconcile_phantom_manifest_rows_all.py reads canonical without a staleness check, then blind-overwrites it -- can
  silently discard already-consolidated OR pending per-VM-shard progress
summary: |
  While closing sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md item #5 (footystats history ->
  zero-missing), running `scripts/reconcile_phantom_manifest_rows_all.py --asset-group sports --data-types
  MATCHES,PREDICTIONS,ODDS --apply` (instruments-service) briefly reverted ~2.5 hours of already-completed backfill
  progress in the canonical `availability_index.parquet` for the sports bucket. Root cause: the reconciler reads the
  canonical blob via a plain `pd.read_parquet`, patches a small number of rows in memory, then re-uploads the WHOLE
  dataframe via `df.to_parquet` -- with no staleness check against the manifest consolidator, and no re-merge of any
  per-VM shards written since its read. This is the SAME lost-update bug CLASS already fixed in
  `manifest_consolidator_cas_retry_lost_update_race_2026_07_08.md` (unified-trading-library@75e59a89), but that fix
  lives inside `_write_consolidated()`'s CAS-retry loop -- a completely different write path from this reconciler
  script, which was never covered. Caught only because this session independently re-verified the footystats gate via
  a manual canonical+shard merge rather than trusting a single read; a less careful flip would have shipped a false
  "gate met" claim.
status: open
nature: process
asset_group: [sports]
stage: [data]
repos: [instruments-service, unified-trading-library]
scope: [engineer]
tags: [manifest, manifest-consolidator, data-correctness, phantom-reconciler, race-condition, sports, footystats]
related:
  [
    plans/active/issues/manifest_consolidator_cas_retry_lost_update_race_2026_07_08.md,
    plans/active/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md,
  ]
created: 2026-07-12
parent_epic: sports_master
priority: P1
source: sports_p2_history_reference_and_odds_2015_to_present-001 (slot-9, data_engineering)
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-12
---

## What I found

Timeline, all UTC 2026-07-12, sports bucket (`instruments-store-sports-prd-central-element-323112`):

1. ~03:57-06:50 -- slot-6's inherited `footystats_residual_closer_2026_07_12.py` ran to completion (282 dates,
   `raised=0`), writing its progress to per-VM shard `_index/per_vm/footystats-residual-closer-20260712.parquet`.
2. ~06:53-07:03 -- I independently re-verified the gate via a manual merge (canonical + that per-VM shard, using
   `unified_trading_library.manifest_writer._read_index._merge_shard_frames`, the SAME dedup logic the
   reader/consolidator use) and found the gate genuinely still had a small fresh residual: 2,168 `PREDICTIONS` rows, all
   `written_at=2026-06-28T21:31:49Z` -- debris from the already-known "IS enumerate overwrite" regression event (this
   plan's own top banner), never previously caught for footystats PREDICTIONS specifically.
3. 07:03-07:15 -- ran a v2 closer pass to force-refetch that fresh residual. Completed clean
   (`processed=282, raised=0`). Its shard (`footystats-residual-closer-20260712-v2.parquet`) held 21,823 entries.
4. ~07:03:42 -- **canonical `availability_index.parquet` was last (re)written around this time and then went STALE for
   an extended period** -- confirmed by polling its GCS mtime every 30s for 3+ minutes (06:54-06:57) with zero change,
   then again later finding it still stuck at 07:03:42 as of 07:26. The `manifest-consolidator-ssot.md` documents a
   `*/1 * * * *` Cloud Scheduler cadence for this job; going 20+ minutes without a canonical update while per-VM shards
   existed is itself anomalous and NOT investigated further this session (flagged as todo #3 below).
5. 07:26 -- ran
   `scripts/reconcile_phantom_manifest_rows_all.py --asset-group sports --data-types MATCHES,PREDICTIONS,ODDS --dry-run`
   (a routine, previously-safe operation -- the SAME tool already used earlier in this plan for footystats ODDS todo #7
   without incident) to check for phantom-captured rows. It read the canonical directly via `pd.read_parquet` (no
   `read_availability_index()`, no staleness guard, no per-VM-shard merge) -- i.e. it read the STALE 07:03:42 snapshot,
   which predates BOTH the v1 and v2 closer runs' consolidation.
6. 07:28 -- ran the same command with `--apply`. It found "2 phantom captures" (real, evidenced), patched those 2 rows
   in the STALE dataframe, and re-uploaded the FULL 4,914,272-row dataframe as the new canonical
   (`Uploading reconciled manifest ... Done.`).
7. **Result: the canonical now reflected the PRE-v1-closer state for footystats PREDICTIONS/ODDS/MATCHES**
   (`expected_unattempted`: MATCHES 30, PREDICTIONS 4,543, ODDS 990 -- byte-identical to my very first baseline read at
   05:06 UTC, before either closer ran) -- silently discarding ~2.5 hours of genuine, already-completed backfill work
   from the canonical's perspective. The v2 closer's per-VM shard (`...-v2.parquet`) had ALSO disappeared from
   `_index/per_vm/` by this point (consumed by a consolidator cycle at some point, contents unclear whether merged
   before or lost alongside this overwrite -- not disambiguated).
8. Confirmed this was a MANIFEST-only regression, not real data loss: the actual captured parquet files for the
   force-refetched dates were still present on GCS (e.g.
   `sports_reference/by_date/day=2019-01-22/pipeline_mode=batch_footystats/entity=footystats_predictions/fetched_at_hour=2026-07-12T07/`
   exists). Recovered by re-running the closer twice more (v3, then a tiny targeted 4-date force-refetch script) --
   cheap because the underlying data already existed, so these were mostly fast preflight-skip/re-confirm passes, not
   real re-fetches. Final gate independently re-verified clean via manual canonical+shard merge:
   MATCHES/PREDICTIONS/ODDS all `expected_unattempted=0` within SSOT-expected leagues, 0 blank-reason.

**Root cause**: `scripts/reconcile_phantom_manifest_rows_all.py` (instruments-service) reads the canonical blob with a
plain `pd.read_parquet(...)` -- see its own docstring: "this reconciler reads the manifest via `pd.read_parquet` and
modifies a small fixed set of columns ... at the specified row indices, then writes back via `df.to_parquet`". This is a
completely SEPARATE write path from `unified_trading_library.manifest_consolidator._write_consolidated()`, which is
where `manifest_consolidator_cas_retry_lost_update_race_2026_07_08.md`'s P0 fix (unified-trading-library@75e59a89)
landed. That fix re-reads + re-merges the canonical on every `PreconditionFailed` CAS retry -- but this reconciler never
goes through `_write_consolidated()` at all, has no CAS/generation check, and has no staleness guard comparable to
`read_availability_index()`'s `MANIFEST_CONSOLIDATED_STALENESS_SEC` gate. Any bulk "read canonical -> patch N rows ->
re-upload the whole dataframe" tool is exposed to this same class of bug whenever canonical is stale relative to
outstanding per-VM shard writes -- which is exactly the state the consolidator being stuck 20+ minutes (finding #2
below) puts a bucket into routinely.

## Why it matters

1. **Silent regression of real backfill work.** This is not a cosmetic manifest-accounting bug -- it silently reverted
   the summary state for a genuine, expensive backfill (hours of real footystats API calls) back to its pre-work state.
   Anyone trusting the manifest without independent re-verification (the normal, faster path) would have flipped
   `sports_p2` item #5's checkbox on a FALSE "gate met" claim, or conversely re-launched an unnecessary duplicate
   backfill VM believing the gate still failed.
2. **The existing CAS-retry fix does NOT cover this tool.**
   `manifest_consolidator_cas_retry_lost_update_race_2026_07_08.md` is fully closed (all todos [x]) under the belief the
   lost-update race is fixed fleet-wide; this finding shows the SAME failure mode still exists in a widely-used adjacent
   tool (`reconcile_phantom_manifest_rows_all.py` is the standard tool for CeFi/DeFi/Sports/TradFi/Prediction
   phantom-row cleanup per its own `--asset-group` choices -- cross-cutting, not sports-specific).
3. **The manifest consolidator being stuck 20+ minutes is itself unexplained** and directly created the stale-read
   window that made this reconciler run dangerous -- worth its own investigation regardless of the reconciler fix, since
   a `*/1` cron going dark for 20+ min on a bucket suggests either a Cloud Run Job failure/backlog or a misconfigured
   trigger, not routine lag.

## Recommended decision

- [x] [CODE] P1. ✅ **Add a staleness guard to `reconcile_phantom_manifest_rows_all.py` before its bulk write-back** --
      implemented option (b) via a new shared helper. Added
      `unified_trading_library.manifest_writer.merge_canonical_with_outstanding_shards(client, bucket, index_blob=None)`
      — reads the canonical blob fresh + merges every outstanding `_index/per_vm/` shard (no cache, no staleness gate;
      distinct from `read_availability_index()`, which is the cached hot-path reader). Both the reconciler's initial
      read AND a fresh re-read immediately before `Uploading reconciled manifest` now go through this helper.
      Phantom/unphantom row sets are relocated onto the freshly re-merged frame by identity key
      (`_row_identity_cols`/`_relocate_indices_by_identity`, mirroring `_merge_shard_frames`'s dedup key) before the
      flip is applied, since positional indices don't survive a re-merge. Regression test
      (`test_write_back_preserves_shard_written_during_audit`) simulates a per-VM shard write landing mid-audit (via a
      wrapped `_audit_generic`) and asserts the final canonical still contains that shard's row AND the genuine phantom
      is still correctly flipped. 4 new UTL unit tests cover the helper directly (canonical+shard merge, canonical-only,
      custom `index_blob` override, empty-when-nothing-exists). Full `quality-gates.sh` green on both repos. (repo:
      unified-trading-library@737a52be, instruments-service@0f7bd460)
- [ ] [DATA] P2. **Audit other "read full manifest -> patch -> full re-upload" scripts** in instruments-service /
      unified-trading-library for the same pattern (grep for `to_parquet` writes to `_index/availability_index.parquet`
      paths outside `manifest_consolidator.py` / `manifest_writer/`) -- enumerate and either fix or document as
      "read-only / dry-run-safe only" (repo: instruments-service).
- [ ] [INFRA] P2. **Investigate why the sports bucket's manifest consolidator Cloud Run Job went stale for 20+ minutes**
      (canonical `availability_index.parquet` stuck at generation `2026-07-12T07:03:42Z` with per-VM shards outstanding,
      confirmed via repeated GCS mtime polling through at least 07:26) despite the documented `*/1 * * * *` Cloud
      Scheduler cadence -- check Cloud Run Job execution logs / Cloud Scheduler trigger history for this window; rule
      out a stuck/OOM'd execution vs. a scheduler-side gap (repo: deployment-service, or wherever the consolidator job's
      infra lives).

## Progress Log

- **2026-07-12 (slot-9, data_engineering)** -- Filed while closing `sports_p2_history_reference_and_odds` item #5. See
  "What I found" for the full timeline + recovery. No code fix attempted in this session (out of this task's craft scope
  / time budget) -- filed with concrete, actionable todos for a future dispatch.
- **2026-07-12 (slot-7, data_engineering)** -- Item 1 closed. Shipped `unified-trading-library@737a52be` (new
  `merge_canonical_with_outstanding_shards` helper + 4 unit tests, full `quality-gates.sh` green) then
  `instruments-service@0f7bd460` (reconciler wired to the helper on both the initial read and pre-write re-merge,
  identity-key relocation, regression test). While shipping, hit + root-caused an unrelated repo-wide
  instruments-service QG-red (`instruments_service_cefi_golden_bitfinex_futures_drift_2026_07_12.md`, consolidated with
  a concurrent slot-6 duplicate filing) and a separate pre-existing hardcoded-project-ID lint violation (fixed
  trivially, `instruments-service@7c186174`) -- both blocked `quickmerge --agent`'s green-sentinel requirement for this
  repo and were resolved before shipping. Items 2 and 3 remain open (P2, different craft scope/repo) -- not actioned
  this session.
