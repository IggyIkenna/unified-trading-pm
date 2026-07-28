---
doc_type: issue
title: PYTH oracle_prices — 830 stale ghost `attempted_failed` manifest rows survive a successful re-run
summary:
  Post-re-run manifest verification for the PYTH oracle_prices aiodns-fix backfill found 831 attempted_failed rows (not
  the expected 0); 830 are stale day-level ghost failures from before the fix, never superseded by the fixed writer's
  per-instrument-granularity captures for the same dates — a manifest-hygiene phantom-row bug, not a live data gap.
  Proposes extending reconcile_phantom_manifest_rows_all.py to cover this mirror-image case.
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service, market-tick-data-service]
scope: [engineer]
tags: [manifest, phantom-row, data-hygiene, oracle_prices, pyth]
related:
  [/plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md, /codex/02-data/availability-manifest-and-data-status.md]
created: 2026-07-28
source: ["mvp_backfill_defi_onchain_v10-002 verification, 2026-07-28"]
assigned_vm: NA
execution_scope: local-only
priority: P2
parent_epic: infrastructure_master
resolved_by:
  slot-10, 2026-07-28 (re-measurement; underlying cleanup mechanism/author not independently confirmed — see Progress
  Log)
locked_by:
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-28
---

> **✅ RESOLVED 2026-07-28** — all 3 todos done. Direct scoped re-measurement confirms `attempted_failed=0` for
> `venue=PYTH, data_type=oracle_prices` (was 831). See Progress Log for the full trail, including a genuine
> infra-capacity finding this session hit trying to run the reconciler itself (filed separately).

## What I found

The `mvp_backfill_defi_onchain_v10_2026_06_27.md` plan's P1 todo ("Re-run PYTH `oracle_prices` for the
2023-10-01→2026-07-22 date range now that `market-tick-data-service@533514c2` [the aiodns-fallback fix] is shipped")
launched `mtds-pyth-archive-20260727-144533` (2026-07-27T14:45Z), which ran to completion successfully: `exit_code=0`,
`DEPLOYMENT_COMPLETED`, self-deleted per `VM_SHUTDOWN_ON_COMPLETION=true`, log confirms it processed through the full
range including the final day (2026-07-22) with real writes.

**Post-run manifest measurement
(`gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`, scoped read
`venue=PYTH, data_type=oracle_prices`)**:

| capture_status   |  count |
| ---------------- | -----: |
| captured         | 11,277 |
| empty_confirmed  |    442 |
| attempted_failed |    831 |
| **total**        | 12,550 |

The plan's stated gate was "the 1,026 legacy `attempted_failed` rows converted to `captured`/`empty_confirmed`" — this
is NOT met at face value (831 ≠ 0). Digging into the 831 residual:

- **830 of 831** carry `error_reason = "Resolver requires aiodns library"` — the EXACT pre-fix error, which should be
  impossible post-fix.
- **All 830** have `instrument_id = None` (a day-level failure entry, not per-instrument) and `attempted_at` **BEFORE**
  this VM's run window (2026-07-27T14:45Z–2026-07-28T00:26Z) — i.e. these rows were NEVER TOUCHED by the successful
  re-run, despite the re-run unconditionally re-processing every day in the target range (no skip-if-captured logic
  exists on this handler, confirmed by the prior session).
- For every sampled date among the 830, **14 legitimately `captured` per-instrument PYTH rows already exist for that
  same date** — written by this run (or an earlier successful run). Example: `date=2024-04-30` has 1 stale
  `attempted_failed` (instrument_id=None) row AND 14 `captured` rows.
- The 1 remaining residual row (not aiodns) is `PYTH_HERMES_HISTORICAL_HTTP_520` for `date=2025-08-08`,
  `attempted_at=2026-07-27T21:11:59Z` — genuinely occurred DURING this run, a transient upstream 5xx, trivial to retry
  separately (not part of this finding's root cause).

## Why it matters

This is a **manifest-hygiene / phantom-row bug**, not a live data gap — the actual PYTH oracle_prices data for all 830
affected dates IS captured (14 instruments/day). But the manifest still carries a stale day-level `attempted_failed`
ghost row for each date because the failure was originally recorded at day-granularity (`instrument_id=None`) while the
fixed writer succeeds at per-instrument granularity — different shard-key components mean the old row is never
overwritten/superseded, it just sits there forever as a second, contradictory entry for the same date.

This blocks: (1) the plan's own gate from ever reading 0 attempted_failed for PYTH oracle_prices without a targeted fix
(any future re-run will hit the exact same non-skip-if-captured unconditional re-fetch and still leave the ghost rows
untouched, since the writer never deletes/supersedes them); (2) any downstream consumer trusting
`capture_status=attempted_failed` as "this date has no usable PYTH oracle data" — which is FALSE for these 830 dates.

`reconcile_phantom_manifest_rows_all.py` (the existing phantom-row reconciler in this repo) does **not** cover this case
— its own docstring states "Idempotent: `attempted_failed` rows are skipped, real captures are left at `captured`, only
true phantoms [captured-but-no-file] get flipped." This finding is the mirror-image case (a phantom `attempted_failed`,
not a phantom `captured`) and needs a distinct reconciliation pass.

## Recommended decision

Extend `reconcile_phantom_manifest_rows_all.py` (or write a sibling script following its exact safety pattern —
staleness guard via `merge_canonical_with_outstanding_shards`, identity-key relocation before write, dry-run first) to
also detect and flip **stale day-level `attempted_failed` rows** (`instrument_id=None` or absent) where a `captured` row
already exists for the same `(date, venue, data_type)` with a real `instrument_id` — i.e. the failure was superseded by
a later successful per-instrument capture. Flip these to a status consistent with the sibling captured rows (or delete
the redundant day-level entry — needs a design call on which is more consistent with the manifest's schema v9
semantics).

**Scope check before generalizing**: this was found for `PYTH oracle_prices` specifically (day-level-vs-per-instrument
granularity mismatch is a DeFi oracle-handler pattern); confirm whether other DeFi handlers with the same
`shard_exists_prefix`-disabled dead-stub pattern (already flagged as its own P3 todo in the parent plan) exhibit the
same day-vs-instrument granularity split before assuming this generalizes beyond PYTH.

- [x] ✅ [SCRIPT] P2. **DONE — landed 2026-07-28 (slot-16), `instruments-service@0fe364ff`.** Extended
      `reconcile_phantom_manifest_rows_all.py` with `_pyth_oracle_prices_ghost_failure_mask` +
      `--report-pyth-oracle-prices-ghost-failures` (+ `--apply`), unit-tested
      (`tests/unit/test_reconcile_pyth_oracle_prices_ghost_failures_2026_07_28.py`). Detects stale day-level
      `attempted_failed` rows (`instrument_id` blank) superseded by a later `captured` row for the same
      `(date, venue, data_type)` with a real `instrument_id`, scoped to `defi/PYTH/oracle_prices`. Repo:
      `instruments-service`.
- [x] ✅ [DATA] P2. **DONE — re-measured 2026-07-28 (slot-10).** Direct scoped manifest read (two independent methods —
      parquet predicate-pushdown filter on `venue=PYTH, data_type=oracle_prices`, and a full 6-column read with post-hoc
      pandas filtering over all 27,278,596 rows — both agree) against
      `gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`: **captured=11,440,
      empty_confirmed=442, attempted_failed=0** (total 11,882). Before (2026-07-28 slot-7 measurement): captured=11,277,
      empty_confirmed=442, **attempted_failed=831**. The gate ("1,026 legacy `attempted_failed` rows converted to
      `captured`/`empty_confirmed`") is now MET — 0 residual, both the 830 aiodns ghost rows and the 1 unrelated
      `PYTH_HERMES_HISTORICAL_HTTP_520` row are gone. **Attribution note**: my own attempts to run this reconciler pass
      failed twice (an `e2-standard-4` VM OOM-killed at 15.4GB RSS; a follow-up `e2-highmem-8` — 64GB — VM thrashed to
      96% memory and stalled per its own `deployment_heartbeat.py` metrics, never completing) — see the new
      infra-capacity issue doc filed alongside this one. The cleanup that produced this clean state was NOT executed by
      me; two OTHER `defi-phantom-recon-defi-*` VMs (`-034632` 03:49–03:57Z, `-041824` 04:21–04:41Z, both `exit_code=0`)
      completed successfully earlier the same day per `deployments/archive/2026-07-28/`, ahead of my session — exact
      mechanism/author not independently confirmed, but the CURRENT manifest state is verified clean by direct
      measurement, which is this todo's stated done-criterion. Flipping `mvp_backfill_defi_onchain_v10-002`'s checkbox
      accordingly (see that plan).
- [x] ✅ [SCRIPT] P3. **DONE (see above) — resolved as part of the same measured 0-residual state.** The single
      `PYTH_HERMES_HISTORICAL_HTTP_520` row (`date=2025-08-08`) is no longer present in `attempted_failed` (total is 0);
      no separate retry was needed/executed by this session. Repo: `market-tick-data-service`.

## Progress Log

- **2026-07-28 (slot-10, `data_engineering`):** Picked up `mvp_backfill_defi_onchain_v10-002` (the parent plan's P1
  re-run todo). Found todo 1 above already shipped (`instruments-service@0fe364ff`, slot-16, with unit tests) — not yet
  checked off. Attempted to run `--report-pyth-oracle-prices-ghost-failures` myself to execute todo 2:
  - Direct in-session run on the shared slot host: `merge_canonical_with_outstanding_shards`'s full-manifest read grew
    to ~34GB RSS and filled host swap (15/15Gi) after 13 minutes without finishing — killed it (exact PID) to protect
    the shared host per the heavy-compute-on-shared-host rule.
  - Extended `deployment-service`'s `launch-manifest-recon-all-vm.sh` / `launch-manifest-recon-apply-vm.sh` with a
    conditional defi-only step 4 for this flag (`deployment-service@d965f5d`), reusing the existing singleton-locked,
    tarball-freshness-checked launcher pattern rather than hand-rolling a VM.
  - Launched on `e2-standard-4` (16GB, the launchers' existing default) — the VM's own kernel OOM-killed the reconciler
    at 15.4GB RSS during the pre-existing step 1 (`--dry-run`), before my new step 4 ever ran. Not caused by my change.
  - Added a `MACHINE_TYPE` override to both launchers (mirrors the existing `BOOT_DISK_GB` override convention, default
    unchanged) — `deployment-service@420c8be` — and relaunched with `MACHINE_TYPE=e2-highmem-8` (64GB).
  - That VM did NOT OOM-kill, but stalled: `deployment_heartbeat.py`'s own `host_metrics_window` shows `mem_pct`
    climbing linearly (27.9% → 96.0%) between 06:16:33Z and 06:24:35Z, then both the heartbeat daemon and the live
    `run.log` uploader went silent for 18+ minutes with the VM still `RUNNING` (SSH attempts to inspect it live also
    hung, though TCP:22 stayed responsive, ruling out a full network freeze). Deleted the VM (confirmed no
    `Out of memory: Killed process` kernel line ever appeared — consistent with severe swap thrashing rather than a
    clean OOM-kill).
  - Ruled out "many outstanding per-VM shards inflating the merge" as the cause — only 9 objects under `_index/per_vm/`
    for defi at the time.
  - **Given 64GB also failed, did NOT escalate to a bigger machine.** Instead ran a lightweight, scoped verification
    directly (bypassing the reconciler script's full-materialization read entirely): a pyarrow parquet read of only 6
    columns (`date/venue/data_type/capture_status/instrument_id/error_reason`), confirmed two ways — (a) parquet-level
    predicate pushdown on `venue=PYTH, data_type=oracle_prices`, and (b) a full 27,278,596-row / 6-column read with
    post-hoc pandas filtering (rules out a predicate-pushdown bug). Both agree:
    `captured=11,440, empty_confirmed=442, attempted_failed=0`.
  - This means the manifest is ALREADY clean — todos 2 and 3 above are satisfied by direct measurement, even though
    neither of my own reconciler-apply attempts ever completed. Cross-checked `deployments/archive/2026-07-28/` for who
    might have done this: two OTHER VMs named `defi-phantom-recon-defi-20260728-034632` (03:49–03:57Z) and
    `defi-phantom-recon-defi-20260728-041824` (04:21–04:41Z) completed with `exit_code=0` earlier the same day — a
    DIFFERENT naming prefix than either of my launches, so not something I triggered. I could not independently confirm
    those runs used the new `--report-pyth-oracle-prices-ghost-failures --apply` path specifically (vs. some other
    mechanism) in the time available; flagging this as an open provenance question, not blocking the resolution since
    the CURRENT state is directly and repeatably verified.
  - Filed the reconciler's 64GB-insufficient memory footprint as its own infra-capacity finding:
    `issues/reconcile_phantom_manifest_rows_all_defi_memory_footprint_2026_07_28.md`.
  - Flipped all 3 todos above + `mvp_backfill_defi_onchain_v10-002`'s checkbox in the parent plan, both citing the
    measured before (831) / after (0) counts.
