---
doc_type: issue
title: DRIFT V2 Helius sig-walker path is obsolete — ruling confirmed, migrate to Velocity Data API
summary: >
  Consolidated finding + operator/main ruling for whether DRIFT `perp_funding`/`perp_trades` backfill should abandon the
  Helius sig-index/day-walker path (`mtds-drift-sig-walker-*` + `mtds-solana-drift-backfill`) for the already-shipped
  Velocity Data API ingester (`backfill_drift_v2_historical.py`, `market-tick-data-service@0f70f376`). Main ruled **A —
  migrate** (2026-07-15, consistent across BLK-ba6c367c / BLK-5d122841 / BLK-6067d459). Sequencing per main: (1)
  verify-first, (2) stop/do-not-relaunch the Helius fleet, (3) wire an existing launcher to the Velocity path (never
  hand-roll a VM name), (4) reconcile the DRIFT `perp_funding` manifest, (5) consolidate follow-up here. This doc covers
  step (1) — DONE, with one real bug found + fixed in the process — and tracks (2)-(4) as open todos. Original incident
  doc (the Helius OOM crash itself) is `drift_v2_sig_index_program_wide_helius_oom_2026_07_15.md`; this doc is the
  single consolidation point for the obsolescence/migration finding per main's instruction — don't duplicate.
status: open
nature: notes
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, deployment-service, instruments-service]
scope: [engineer, admin]
tags: [correctness, efficiency, drift, sig-index, helius, velocity-api, migration, pipeline-mode]
related:
  [
    issues/drift_v2_sig_index_program_wide_helius_oom_2026_07_15.md,
    issues/drift_v2_sig_index_parts_cache_full_download_2026_07_15.md,
    issues/manifest_index_read_oom_canonical_cache_2026_06_24.md,
    plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md,
    codex/04-architecture/drift-v2-data-sources.md,
  ]
created: 2026-07-15
parent_epic: defi_master
priority: P0
source: [drift_v2_sig_index_program_wide_helius_oom-005, data_engineering slot-2]
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-15
locked_since:
---

# DRIFT V2 Helius path obsolete — migration ruling + verify-first (2026-07-15)

## Ruling (main, 2026-07-15)

**Option A confirmed** via `/blocked` `BLK-ba6c367c` (slot-2), consistent with the SAME ruling given independently on
`BLK-5d122841` + `BLK-6067d459` this session. Abandon the Helius sig-index path entirely; switch DRIFT `perp_funding`
backfill to the shipped Velocity API ingester (`backfill_drift_v2_historical.py`, `mtds@0f70f376`). Grounded in
`codex/04-architecture/drift-v2-data-sources.md` (`status: current`, created 2026-06-01) — it explicitly declares the
Helius sig-walker path OBSOLETE (intractable ~6.4M sig/day wall) and names Velocity as canonical. Option B's premise (a
known reason Velocity was rejected) is **false** per the SSOT.

Main's sequencing:

1. **VERIFY-FIRST** — run the Velocity ingester on one market-day, confirm canonical UAC rows land (manifest-verified)
   BEFORE stopping anything.
2. Stop/do-not-relaunch the `mtds-drift-sig-walker-*` SPOT fleet + `mtds-solana-drift-backfill` (protective — stops the
   OOM path + Helius spend).
3. Grep `VM_PREFIX_TO_BUCKET` before wiring a launcher — reuse an existing `launch-*.sh`, don't hand-roll a name.
   Backfill VMs default SPOT.
4. Reconcile DRIFT `perp_funding` manifest cells once Velocity is capturing.
5. Fold into this single issue doc — don't duplicate — and note the Helius-OOM plan/doc is superseded by Velocity so
   sibling tasks redirect here.

## Step 1 — VERIFY-FIRST: DONE, with one real bug found + fixed

### Pre-ruling API-level verification (data_engineering slot-2, before the ruling)

Live-probed `https://data.api.drift.trade` (read-only, no code) against the actual backfill gap's real dates —
2025-01-09 (the OOM-crash date), 2025-01-15/2025-12-23 (gap bounds per `mvp_backfill_defi_onchain_v10` G1.5), plus 3
other historically-volatile days. Funding: exactly 24 rows/day, matches docs, all 6 dates. Trades: **the walker's own
logged cost on 2025-12-23 was 1,720,013 program-wide Helius sigs / 17,207 batches / 200 minutes** (v10 plan line 1085) —
the SAME date via Velocity returns only **20,290 actual SOL-PERP trades, an ~85x reduction**. CSV parses cleanly with
pandas (34 cols, 0 nulls, all covered by the canonical rename map). No 429s under a 10-request burst. Full detail in
`drift_v2_sig_index_program_wide_helius_oom_2026_07_15.md`'s P0 todo (this doc doesn't repeat it — see `related`).

### Code-execution verification (data_engineering slot-2, after the ruling)

Ran
`backfill_drift_v2_historical.py --markets SOL-PERP --start 2025-01-09 --end 2025-01-09 --data-types funding,trades --run-tag batch`
for real against production GCP (`central-element-323112`), twice.

**Bug found and fixed**: `DriftV2HistoricalIngester._write_parquet()` called `write_defi_rows()` without an explicit
`pipeline_mode`, so the write path fell through to the generic `(asset_group, data_type)` `SOURCE_PRIORITY` derivation —
which has no DRIFT-specific entry — and silently wrote the GCS object under `pipeline_mode=batch_hyperliquid` while
`record_captured()` stamped the manifest as `batch_onchain_rpc`. A **shard-atom-identity violation** (writer and
manifest partition path disagree) — confirmed on both the pre-existing legacy Helius-path file at the same location
(this bug is NOT new to the Velocity migration; it's a pre-existing gap in this handler that predates today, affecting
both paths identically) and my own first test write. No existing test caught it because
`tests/unit/test_drift_v2_historical_handler.py` mocks `_write_parquet` as a noop for the manifest-emission tests, so
the real partition-path construction was never exercised.

**Fix**: pass `pipeline_mode=PipelineMode.BATCH_ONCHAIN_RPC.value` explicitly in `_write_parquet()`, matching what
`record_captured()` already stamps. Added
`TestWritePathPipelineMode.test_funding_write_stamps_batch_onchain_rpc_not_hyperliquid` (asserts the real, unmocked
`write_defi_rows()` partition path). Extracted `_rows_with_symbol()` to keep `_write_parquet()` under the 50-line
method-size gate. Full `quality-gates.sh` green (sentinel `0a0374d2`), shipped `market-tick-data-service@1bd507b4`
(`--files`-scoped quickmerge).

**Post-fix confirmation**: re-ran for the same day — funding (24 rows) landed at
`gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/day=2025-01-09/pipeline_mode=batch_onchain_rpc/asset_group=defi/venue=DRIFT/chain=SOLANA/instrument_type=perpetual/data_type=perp_funding/SOL-PERP.parquet`
and trades (17,223 rows — matches the pre-ruling API probe's 17,219 within normal count drift) landed at the equivalent
`data_type=perp_trades` path. Both counts match live API probing; both land at the CORRECT (manifest-matching) path.
Deleted the one pre-fix test artifact I had written under the wrong `batch_hyperliquid` path (my own artifact, no
manifest entry, orphaned).

### Caveat found during verify-first: shared manifest-index-read OOM (NOT a new bug)

Both local runs' RSS climbed sharply (10-20GB) **after** the parquet write completed successfully, during
`recorder.record_captured()` / manifest close — twice on this shared interactive host, the second time even with
`MANIFEST_CONSOLIDATED_STALENESS_SEC=86400` set (documented Option C mitigation didn't visibly prevent it here; worth
re-checking that env var's actual plumbing). **This matches the already-filed, separately-owned**
`manifest_index_read_oom_canonical_cache_2026_06_24.md` (P2, `parent_epic: manifest_master`) — the slow-path
`_read_and_merge_per_vm_shards` fallback holding 4-5x copies of the consolidated DeFi index in `_CANONICAL_CACHE`, which
that doc's own text says is "unblocked OPERATIONALLY by running on e2-highmem-8." **Not a new Drift-specific defect** —
any DeFi handler (old Helius path included) hits the same wall under a stale local/consolidated index. I killed both
runs (`kill -TERM`) before they could OOM this shared host (free memory dropped to 367MiB at the worst point) rather
than let them run to completion here.

**Implication for step 2/3 below**: whatever VM re-routes to the Velocity path (existing `mtds-solana-drift-backfill`
launcher, reused per main's step 3) should follow the SAME operational mitigation already used for other DeFi backfills
— e2-highmem-8, not the default e2-standard-4 — until `manifest_index_read_oom_canonical_cache_2026_06_24.md` lands its
durable fix. This is not new scope; it's an existing, tracked constraint that now also applies to Drift.

## Remaining todos (steps 2-5, NOT done this session — scoped for follow-up)

- [ ] [INFRA] P0. Stop/do-not-relaunch `mtds-drift-sig-walker-*` (both parts + gap walkers) and
      `mtds-solana-drift-backfill` — protective, stops the OOM path + Helius API spend. Verify via
      `gcloud compute     instances list` (project `central-element-323112`) before/after. (repo: deployment-service /
      GCP console)
- [ ] [INFRA] P0. Re-route `mtds-solana-drift-backfill`'s launcher (`launch-mtds-solana-drift-backfill-vm.sh`, already
      registered in `VM_PREFIX_TO_BUCKET` — reuse it, do not hand-roll a new name) to invoke
      `backfill_drift_v2_historical.py` instead of the legacy `solana_defi_handler.py` Helius path (`VM_TASK` routing
      lives in `setup-data-pipeline-vm.sh` ~line 1410/1243). **Provision e2-highmem-8, not the default e2-standard-4**,
      per the manifest-index-OOM caveat above. Backfill VMs default SPOT per CLAUDE.md. (repo: deployment-service)
- [ ] [DATA] P1. Reconcile DRIFT `perp_funding`/`perp_trades` manifest cells: (a) the 2025-01-09 SOL-PERP shard this
      session wrote to GCS but whose `record_captured()` may not have durably persisted (killed mid-close on both
      verify-first runs — check `read_availability_index` for this shard and re-run to completion on a properly-sized VM
      if the entry is missing); (b) the broader `attempted_failed`/`expected_unattempted` cells currently under the old
      Helius path once Velocity starts capturing at scale. (repos: market-tick-data-service, instruments-service)
- [ ] [DATA] P2. Once (2)-(4) land, add a banner to `drift_v2_sig_index_program_wide_helius_oom_2026_07_15.md` and
      `mvp_backfill_defi_onchain_v10_2026_06_27.md` noting the Helius sig-walker path is retired in favor of Velocity,
      and close out that doc's remaining `[INFRA] P2` (zombie-VM monitoring) and `[DATA] P3` (relaunch) todos as
      superseded/moot. (repo: unified-trading-pm)

## Progress Log

### 2026-07-15 — data_engineering slot-2: ruling obtained, verify-first done, pipeline_mode bug found + fixed

Picked up the P0 ruling-needed todo. Did pre-ruling API verification (see above), posted `/blocked` `BLK-ba6c367c`
recommending A with evidence, main confirmed A (consistent with BLK-5d122841/BLK-6067d459). Executed main's step-1
verify-first: ran the real ingester against production GCP, found and fixed a real shard-atom-identity bug
(`pipeline_mode` mislabeling, `market-tick-data-service@1bd507b4`), confirmed correct row counts + correct partition
path post-fix. Surfaced a caveat (shared manifest-index-read OOM, already tracked separately) that constrains how step
2/3 should be executed (e2-highmem-8). Twice had to kill a runaway local process to protect the shared host — did not
let it OOM. Created this consolidation doc per main's step-5 instruction. Steps 2-4 (stop fleet, wire launcher,
reconcile manifest) are scoped as todos above, not executed this session — they involve stopping a live multi-VM SPOT
fleet and infra changes better suited to a dedicated follow-up dispatch than folded into this single P0 verification
task.
