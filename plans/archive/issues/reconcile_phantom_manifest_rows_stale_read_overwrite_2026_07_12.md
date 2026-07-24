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
status: resolved
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
    plans/active/issues/defi_consolidator_scheduler_sigkill_unresolved_2026_07_10.md,
  ]
created: 2026-07-12
parent_epic: sports_master
priority: P1
source: sports_p2_history_reference_and_odds_2015_to_present-001 (slot-9, data_engineering)
assigned_vm: planning
resolved_by: slot-3, infra, 2026-07-13
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-13
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
- [x] [DATA] P2. ✅ **Audited other "read full manifest -> patch -> full re-upload" scripts** in instruments-service /
      unified-trading-library. Full enumeration + disposition:

      **FIXED this session** (highest-risk + actively-reused library entry points, same staleness guard as item #1 --
                                                                                          `merge_canonical_with_outstanding_shards`/`_read_and_merge_per_vm_shards` re-fetch immediately before the
                                                                                          write-back):
                                                                                          - `unified-trading-library/unified_trading_library/manifest_writer/_maintenance.py`: `purge_venue_before_date`
                                                                                            (fresh re-fetch + re-derived mask), `rebuild_manifest` (fresh re-fetch, drops any key another writer already
                                                                                            landed during the blob-listing walk), `emit_migration_manifest_updates` (fresh re-fetch + re-derived prune;
                                                                                            the docstring's prior "same GCS generation-match path... concurrent migration VMs are safe" claim was FALSE
                                                                                            for this step -- corrected in the write path), `rebuild_manifest_from_canonical_paths` (highest-risk site
                                                                                            found -- full-corpus GCS walk + blind full-replace write; now merges in fresh outstanding per-VM shard rows
                                                                                            immediately before writing). 2 new regression tests added to `tests/unit/test_manifest_v4_migration.py`
                                                                                            (`test_purge_venue_before_date_preserves_shard_landed_after_initial_read`,
                                                                                            `test_rebuild_from_canonical_paths_preserves_shard_landed_mid_walk`); full UTL suite green (4365 passed).
                                                                                          - `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`'s two sibling write paths named in this
                                                                                            todo's own filing (`_apply_delete_chain_level_defi_phantoms`, `_apply_delete_legacy_combined_venue_defi_phantoms`)
                                                                                            -- same fix pattern (re-fetch fresh + re-derive the delete predicate immediately before the write-back). New
                                                                                            regression test `test_chain_level_defi_delete_preserves_shard_landed_before_write`.

                                                                                          **NOT fixed -- documented (lower priority, out of this session's time budget)**:
                                                                                          - `unified-trading-library/unified_trading_library/manifest_writer/_queries.py::reconcile_manifest` -- same
                                                                                            class (slow per-row `list_blobs` existence-probe loop then blind write), but inside the explicitly-excluded
                                                                                            `manifest_writer/` package boundary named in this todo's own text. Flagged for awareness, not actioned.
                                                                                          - `instruments-service/scripts/migrate_leagues_kill_2026_05_07.py` and
                                                                                            `migrate_teams_cadence_2026_05_07.py`: log/comment text claims "canonical CAS" protection that does not
                                                                                            actually exist at the write site (`blob.upload_from_file` with no `if_generation_match`). Short window, low
                                                                                            urgency, but the misleading comment should be corrected or real CAS added if either script is ever re-run.
                                                                                          - **~45 additional one-off, dated `instruments-service/scripts/*.py` migration/cleanup scripts** share the
                                                                                            identical short-window "read canonical once -> fast boolean-mask patch -> `to_parquet` + upload, no re-merge"
                                                                                            template (e.g. `dedup_phantom_after_recovery.py`, `reconcile_attempted_failed_to_captured_2026_05_13.py`,
                                                                                            `purge_prediction_other_group_rows.py`, `flip_residual_attempted_failed_2026_06_29.py`,
                                                                                            `canonicalize_okx_margin_type_2026_07_09.py`, `reconcile_defi_ghost_venue_*_20260522.py`,
                                                                                            `dedup_defi_manifest_status_priority_2026_06_24.py`, and ~35 more -- full list in the audit sub-agent's
                                                                                            transcript, available on request). Per `/codex/06-coding-standards/script-homes.md`, these are one-off scripts
                                                                                            (most already executed against production and unlikely to be re-run) -- retrofitting all ~45 individually was
                                                                                            judged lower-value than the time cost this session; recommend a dedicated bulk-sweep task (mechanical:
                                                                                            s/raw read/`merge_canonical_with_outstanding_shards`/ before each write) only if/when one of these scripts is
                                                                                            actually re-run against a bucket with active concurrent writers.
                                                                                          - `split_prediction_by_market.py` already calls `read_availability_index` right before its write --
                                                                                            LOW RISK, no action needed.
                                                                                          - Scripts targeting per-day/venue-owned `instrument_availability/by_date/` shard catalogs (not the shared
                                                                                            canonical `_index/availability_index.parquet`) -- e.g. `canonicalize_binance_futures_delivery_catalog_2026_07_09.py`,
                                                                                            `canonicalize_bybit_kraken_futures_catalog_2026_07_09.py` -- DOCUMENTED as read-only/dry-run-safe: a much
                                                                                            smaller concurrent-writer collision surface than the shared canonical, different bug class, no action needed.
                                                                                          (repo: instruments-service, unified-trading-library)

- [x] [INFRA] P2. ✅ **Investigated why the sports bucket's manifest consolidator Cloud Run Job went stale for 20+
      minutes.** Both hypotheses in the todo's own framing are RULED OUT with hard evidence; root cause is a third thing
      -- an ~89-minute crash-loop, not a stuck execution or a scheduler gap:

      **RULED OUT -- scheduler-side gap**: `gcloud run jobs executions list` for
                                                                                      `uts-prod-manifest-consolidator-instruments-sports` shows the `*/1 * * * *` Cloud Scheduler cron fired
                                                                                      **every single minute without a single miss** from 06:44 through 08:13 UTC (86 consecutive invocations, one per
                                                                                      minute). The trigger never stopped.

                                                                                      **RULED OUT -- stuck/OOM'd execution**: every failing execution's `status.conditions` shows
                                                                                      `reason: "NonZeroExitCode"` / `"The container exited with an error."` (exit code 1) -- NOT `OOMKilled` / signal
                                                                                      137 (the CeFi dated-instrument-seeding OOM signature this doc's own SSOT describes). Each attempt (incl. the
                                                                                      `maxRetries: 1` retry) completed in 20-90s, far under the 1800s job timeout. The container is not hanging -- it
                                                                                      is actively cycling fail -> retry -> fail -> next-minute-refires, cleanly, every cycle.

                                                                                      **What actually happened**: 84 of ~86 executions in the 06:44-08:13 UTC window failed (only 5 succeeded:
                                                                                      07:02, 07:03, 07:28, 07:29, 07:30); canonical mtime was genuinely stuck at `07:03:42Z` per the parent finding's
                                                                                      polling. Every single failure's stderr traceback is byte-identical across all 84 executions:
                                                                                      `manifest_consolidator.py:587, in consolidate -> merge_result = _duckdb_consolidate_and_write(` -- i.e. the
                                                                                      exception is always raised inside the DuckDB incremental-merge call, on the SAME line, every time. The window
                                                                                      overlaps precisely with the footystats residual closer v1 (active through ~06:50 UTC) and v2 (07:03-07:15 UTC)
                                                                                      actively writing/replacing per-VM shard parquet files in this SAME bucket (per this doc's "What I found" #1-3
                                                                                      above) -- the leading hypothesis is contention between the consolidator's incremental shard-scan (list
                                                                                      "changed" shards, then open them in DuckDB) and the closer's shard churn (the v1->v2 shard-name handoff), though
                                                                                      the EXACT DuckDB exception type/message could not be recovered (see next finding) so this is circumstantial, not
                                                                                      proven. **Self-healed without operator intervention** -- 0 failures in the last 60 executions checked
                                                                                      (09:06-10:06 UTC), canonical mtime currently 2s old as of this investigation.

                                                                                      **Secondary finding -- why this produced ZERO alerts for 89 minutes** (the real "why didn't anyone catch this"
                                                                                      answer, filed as its own actionable todo below rather than fixed inline): the code's own exception handler DOES
                                                                                      fire correctly (`logger.exception()` + `log_event(MANIFEST_CONSOLIDATION_FAILED, severity="ERROR", details={"error":
                                                                                      f"{type(exc).__name__}: {exc}", ...})` at `manifest_consolidator.py:660-680`) and WOULD have carried the exact
                                                                                      exception type + message -- but `main()` (line 1929) wires `setup_events("manifest-consolidator", mode="batch",
                                                                                      sink=MockEventSink())`, a **no-op sink**, so that event is silently discarded on every single failure. This
                                                                                      directly contradicts this doc's own § "Liveness + health contract" claim that `MANIFEST_CONSOLIDATION_FAILED`
                                                                                      "is now emitted with severity=ERROR so the alert sink routes it." Additionally, the CLI's own stdout summary
                                                                                      line (`error={report.error_reason}`, which also carries the exact exception) is never captured by Cloud Logging
                                                                                      for this job at all (verified 0 stdout entries even for a confirmed-successful execution), and the dedicated
                                                                                      `uts-prod-consolidator-liveness-watchdog` job (which DOES monitor this bucket, confirmed via its `--buckets` arg
                                                                                      list, and runs every 2 min via its own Cloud Scheduler) produced zero stderr output during the incident despite
                                                                                      explicitly calling `logging.basicConfig(level=logging.INFO)` in its `__main__` -- its actual CONSOLIDATOR_DOWN
                                                                                      verdict could not be confirmed from Cloud Logging (verification recipe evidence:
                                                                                      `gcloud logging read` queries + `gcloud run jobs executions list/describe` transcripts available on request).
                                                                                      (repo: unified-trading-library)

- [x] [INFRA] P2. ✅ **Fix the manifest-consolidator alerting no-op found above**: `manifest_consolidator.py`'s CLI
      `main()` wired `setup_events(..., sink=MockEventSink())`, so `MANIFEST_CONSOLIDATION_FAILED` (severity=ERROR)
      never reached any real consumer despite the SSOT doc (`/codex/05-infrastructure/manifest-consolidator-ssot.md` §
      "Liveness + health contract") claiming it "routes to the alert sink." Confirmed via research-agent trace that
      wiring `GcsEventSink` alone would NOT have closed the loop: `alerting-service`'s `BatchEventReader` only runs
      under a manual `--mode batch` historical replay (not an always-on watchdog), reads a stale fixed filename that
      doesn't match `GcsEventSink`'s actual write path, and `"manifest-consolidator"` isn't even in its
      `_EVENT_SOURCE_SERVICES` tuple. The REAL live path is Pub/Sub: `alert_subscriber.py` subscribes to
      `lifecycle-events-sub`, and `consolidator_rules.py` already has severity-routed handlers for both
      `MANIFEST_CONSOLIDATION_FAILED` and `CONSOLIDATOR_DOWN` waiting -- confirmed against the working reference pattern
      already proven by deployment-service's `dp-fleet-monitor` CLI (`PubSubEventSink(topic="lifecycle-events")`). Wired
      both entrypoints named in this todo: `manifest_consolidator.py::main()` (was `MockEventSink()`/mode="batch") AND
      `consolidator_liveness.py::_main()`, which turned out to have an even worse variant of this bug -- it never called
      `setup_events()` at all, so every `log_event()` call raised `RuntimeError`, silently swallowed by
      `check_buckets()`'s broad except and force-set to `STATUS_OK` (a false negative masking a real outage, not just a
      dropped alert). 4 new regression tests (sink-wired-when-project-id-resolves + graceful-no-crash-when-it-doesn't,
      one pair per entrypoint). Full `quality-gates.sh` green. (repo: unified-trading-library@bf6fb9c3)
- [x] [INFRA] P2. ✅ **Redeployed the manifest-consolidator + consolidator-liveness-watchdog Cloud Run images** carrying
      `unified-trading-library@bf6fb9c3`. Confirmed `bf6fb9c3` an ancestor of the latest published UTL base image
      (`111592eb`, digest `sha256:dcb4892d...`); bumped MTDS's `Dockerfile` `ARG BASE_IMAGE_DIGEST` to it
      (`market-tick-data-service@491862ed`; a concurrent slot had already independently fixed an unrelated pip-audit
      `click` CVE blocking the QG green-tree gate, rebased cleanly on top). Cloud Build auto-rebuilt MTDS's own image
      off the LDR push (`f062e0f9`, digest `sha256:dc9a7a34...`). Redeployed all **34**
      `uts-prod-manifest-consolidator-*` Cloud Run jobs (the fleet has grown past the "~10" this todo was scoped against
      — Phase D expansion since filing) + `uts-prod-consolidator-liveness-watchdog` via
      `gcloud run jobs update --image=...:latest` (forces re-resolution; a job otherwise pins the digest it last
      resolved at deploy time). Verified: all 34 jobs' latest executions now run images built after `dc9a7a34` (none
      stuck on the pre-fix digest). Side effect of the redeploy actually working: the watchdog's newly-live alerting
      immediately surfaced 3 genuinely-DOWN buckets on its very next cycles (previously silently masked as OK by the
      exact bug this fix closes) -- 2 are false-positives against deliberately-PAUSED legacy buckets (noted, not
      separately filed), 1 (`market-data-tick-defi-prd`) is a real, already-tracked, still-unresolved P1 incident --
      appended fresh corroborating evidence (today's `latest.json` `error_reason: "locked"` + a live-observed
      two-consecutive-SIGKILL lock cycle) to the existing
      `plans/active/issues/defi_consolidator_scheduler_sigkill_unresolved_2026_07_10.md` rather than duplicate-filing.
      (repo: market-tick-data-service@491862ed)

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
- **2026-07-12 (slot-7, data_engineering)** -- Item 2 closed. Research-agent audit enumerated ~50 sites across both
  repos sharing the read-once-write-back pattern. Fixed the highest-risk/actively-reused ones: UTL's
  `manifest_writer/_maintenance.py` (`purge_venue_before_date`, `rebuild_manifest`, `emit_migration_manifest_updates`,
  `rebuild_manifest_from_canonical_paths`) shipped as `unified-trading-library@21f6e208` (2 new regression tests, full
  suite green); the reconciler's two sibling delete functions
  (`_apply_delete_chain_level_defi_phantoms`/`_apply_delete_legacy_combined_venue_defi_phantoms`) shipped as
  `instruments-service@8160f705` (1 new regression test). Full enumeration + fix-vs-document disposition for the
  remaining ~45 one-off dated scripts recorded in the todo above. Both `quickmerge --agent` runs hit the same
  missing-`Quickmerge:`-trailer gap as item 1 (pre-committing before Pass-1 QG, per the documented recipe, leaves
  quickmerge's own commit step with nothing to do) -- resolved via `git commit --amend` + QG re-run each time, same as
  item 1's workaround.
- **2026-07-12 (slot-5, infra)** -- Item 3 closed via `gcloud run jobs executions list/describe` + `gcloud logging read`
  forensics (non-snap SDK at `~/google-cloud-sdk/bin/gcloud` -- the `/snap/bin/gcloud` on this host is broken,
  `cap_dac_override` missing). Ruled out both hypotheses the todo posed (scheduler gap, stuck/OOM'd execution) with hard
  evidence; found the real cause is an 89-min crash-loop (06:44-08:13 UTC, 84/86 cycles failed, self-healed) whose exact
  DuckDB exception is unrecoverable because the container's own stderr traceback is identically truncated on every
  failure. Filed a NEW P2 todo for the concrete secondary finding: the consolidator CLI's `MockEventSink()` makes its
  `MANIFEST_CONSOLIDATION_FAILED` alert a no-op, contradicting this doc's own "routes to the alert sink" claim --
  explains why the 89-min incident paged nobody. No code shipped this session (the fix needs an alerting-service
  consumer-path confirmation first, per the findings-triage "ambiguous -> diagnose both sides, don't blind-fix" rule) --
  filed as a todo instead, target repo named.
- **2026-07-12 (slot-5, infra)** -- Item 4 closed. Dispatched a research sub-agent to confirm the real consumer path
  before touching the sink (per the todo's own explicit ask): `GcsEventSink` would NOT have closed the loop (no
  automatic consumer reads it; `alerting-service`'s `BatchEventReader` is a manual replay-only path with a stale
  filename convention and doesn't even list `manifest-consolidator` in its source tuple). The actually-working path is
  Pub/Sub -- `alert_subscriber.py` subscribes `lifecycle-events-sub`, and `consolidator_rules.py` already has
  severity-routed handlers built for both `MANIFEST_CONSOLIDATION_FAILED` and `CONSOLIDATOR_DOWN`. Wired
  `manifest_consolidator.py::main()` to `PubSubEventSink(topic="lifecycle-events")` (matching deployment-service's
  already-working `dp-fleet-monitor` reference pattern), and additionally found + fixed the SAME class of bug in
  `consolidator_liveness.py::_main()` (which the todo asked to "confirm") -- it had NO `setup_events()` call at all, a
  worse variant: `log_event()` raised every cycle, silently swallowed by `check_buckets()`'s broad except into a false
  `STATUS_OK`, masking real outages rather than just dropping an alert. 4 new regression tests, full `quality-gates.sh`
  green, shipped `unified-trading-library@bf6fb9c3`. Filed the image-rebuild + ~10-job redeploy as its own new P2 todo
  (deployment-service) since landing the source fix doesn't reach production until those Cloud Run jobs redeploy.
- **2026-07-12 (slot-5, infra)** -- Item 5 (the redeploy todo above) picked up, but NOT actionable yet: traced the full
  deploy-hygiene chain per `/codex/08-workflows/ci-cd-flow.md` -- the manifest-consolidator Cloud Run jobs run off
  `market-tick-data-service:latest` (which pins `unified-trading-library` by digest in its `Dockerfile`'s
  `ARG BASE_IMAGE_DIGEST`, confirmed current pin predates `bf6fb9c3`). `bf6fb9c3` has NOT yet reached
  `unified-trading-library`'s `main` -- it's sitting in an open auto-merge promote PR
  (`IggyIkenna/unified-trading-library#536`, opened 10:41 UTC, `mergeStateStatus=CLEAN`, `mergeable=MERGEABLE`, no
  native `autoMergeRequest` -- merges via the `*/15` v2-gated cron per CLAUDE.md, not something an agent should
  force-merge). Only once that PR lands does UTL's base-image publish + `update-dependency-version.yml`
  `repository_dispatch` fan-out bump MTDS's `BASE_IMAGE_DIGEST` -- THEN MTDS's own image rebuilds, and only THEN can the
  ~10 `uts-prod-manifest-consolidator-*` jobs + `uts-prod-consolidator-liveness-watchdog` actually be redeployed to a
  digest that contains the fix. Same class of premature-completion risk as item 3's gate (this session already caught
  once, on a different task) -- skipped rather than idle-wait 30-60+ min for an automated multi-stage
  promote/build/dispatch chain with zero agent action available in the interim. Re-dispatch once PR #536 has merged AND
  MTDS's `Dockerfile` `BASE_IMAGE_DIGEST` has been auto-bumped past the current
  `sha256:e353a755b05ad914acaff36449103da6c572b7d22ddb7c9983a773f35ac9b58f` pin.
- **2026-07-12 (slot-10, infra)** -- Re-dispatched to item 5; re-verified the same blocker fresh, still unmet, skipped
  rather than idle-wait, same conclusion as slot-5. `gh pr view 536 --repo IggyIkenna/unified-trading-library` shows
  `state=OPEN`, `mergedAt=null`, `mergeStateStatus=CLEAN`, `mergeable=MERGEABLE` -- unchanged from slot-5's reading.
  Directly confirmed via `git merge-base --is-ancestor bf6fb9c3 origin/main` on a freshly-fetched
  `unified-trading-library` clone: **NO** -- `bf6fb9c3` is still not an ancestor of `main`. MTDS's `Dockerfile`
  `ARG BASE_IMAGE_DIGEST` is still pinned to the same pre-fix digest
  (`sha256:e353a755b05ad914acaff36449103da6c572b7d22ddb7c9983a773f35ac9b58f`), byte-identical to slot-5's reading. Zero
  agent action is available here -- force-merging an auto-merge promote PR ahead of its `*/15` v2-gated cron would
  violate the CI-verification HARD RULE (never force-merge a promotion PR); the fix must land via the normal promote →
  base-image-publish → `repository_dispatch` digest-bump → MTDS rebuild chain before this todo's own redeploy step
  becomes real. `skip-current-task`'d rather than poll-wait 15-30+ min on external CI/promote state. No repo code commit
  this entry (read-only re-verification; this plan-doc edit ships via the PM `docs(plans):` carve-out).
- **2026-07-13 (slot-3, infra)** -- Item 5 (final) closed. PR #536 had since merged (`2026-07-12T11:20:20Z`);
  re-verified `bf6fb9c3` present on UTL's currently-published base image (`111592eb`, built off `main`) and bumped
  MTDS's `Dockerfile` digest pin to it (`market-tick-data-service@491862ed`). Redeployed the full **34**-job
  consolidator fleet (grew from the ~10 this todo was originally scoped against) + the watchdog; verified every job's
  latest execution now runs a post-fix image. See the checkbox above for the full account, including the two downstream
  findings the now-live alerting immediately surfaced (1 real still-open P1 incident, corroborating evidence appended to
  its existing issue doc; 2 watchdog false-positives against paused legacy buckets, noted inline). All 5 todos in this
  issue doc are now closed.
