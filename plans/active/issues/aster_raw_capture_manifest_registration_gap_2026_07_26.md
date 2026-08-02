---
doc_type: issue
title: ASTER raw-trade capture — manifest shows near-total expected_unattempted despite real files on disk
summary: >-
  Discovered while scoping cefi_satellite_ao_dispatch_batch1-001 (extend MDPS candle-building to the 4 on-chain-perp
  CeFi venues). The cefi manifest shows ASTER at 487,191 MTDS rows: 486,890 expected_unattempted, 300 attempted_failed
  (2026-07-24..07-25), and exactly 1 captured row (2026-07-11, one instrument) across the full 2024-01-01..2026-07-25
  range. This contradicts the archived aster_capture_broken_coverage_and_completeness_2026_07_20.md's "🟢 RESOLVED —
  verified with real data" banner. A direct GCS listing shows the opposite of what the manifest claims: real,
  many-instrument raw_tick_data parquet files exist for day=2026-07-20 (written 2026-07-20/21) under
  pipeline_mode=batch_aster, and derived processed_candles/ files (timeframe=15s/1m, unregistered — 0 MDPS manifest rows
  for ASTER at all) exist for the same day. So real trade data IS landing on disk; the manifest is not reflecting it as
  captured — a registration gap, not (necessarily) a fetch failure.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library, deployment-service]
scope: [engineer]
tags: [aster, manifest, capture-status, phantom-registration, data-correctness]
related:
  [
    /plans/archive/issues/aster_capture_broken_coverage_and_completeness_2026_07_20.md,
    /plans/active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md,
    /plans/active/aster_and_cefi_rolling_adv_feature_2026_07_21.md,
    /plans/archive/2026_07/cefi_satellite_ao_dispatch_batch1_2026_07_25.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.5
assigned_role: data_engineering
drift_direction: advance-code
source: >-
  Discovered 2026-07-26 while working cefi_satellite_ao_dispatch_batch1-001 (slot 6). Direct manifest read
  (unified-trading-library read_availability_index over market-data-tick-cefi-prd-central-element-323112) + direct GCS
  listing (gcloud storage ls, scoped single-prefix reads, no whole-corpus walk) — evidence below.
locked_by:
locked_since:
resolved_by:
depends_on: []
context_scope:
  [
    market-tick-data-service/market_tick_data_service/cli/handlers/onchain_perp_batch_handler.py,
    unified-trading-library/unified_trading_library/manifest_writer/_writer.py,
    /plans/archive/2026_07/cefi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/archive/issues/defi_fold_manifest_registration_pending_2026_07_21.md,
  ]
---

# ASTER raw-trade capture — manifest registration gap

## What I found

1. **Manifest read** (`read_availability_index('market-data-tick-cefi-prd-central-element-323112', ...)`, filtered
   `service_name == 'market-tick-data-service'` + `venue == 'ASTER'`): 487,191 rows total —
   `expected_unattempted=486,890`, `attempted_failed=300` (dates 2026-07-24..2026-07-25 only), `captured=1` (date
   2026-07-11, `instrument_id=ASTER:PERPETUAL:BTC@LIN`, `written_at=2026-07-13T07:36:41Z`). The `expected_unattempted`
   rows span the full `2024-01-01..2026-07-21` range — i.e. per the manifest, ASTER's raw trade capture has essentially
   **never run** historically and has been failing outright for the last 2 days.
2. **Direct GCS listing** (scoped single-prefix reads, not a corpus walk) shows the opposite:
   - `raw_tick_data/by_date/day=2026-07-20/pipeline_mode=batch_aster/asset_group=cefi/venue=ASTER/ instrument_type=perpetual/data_type=trades/`
     contains real per-instrument parquet files (verified ≥10 distinct instruments — `0G-USDT@LIN`, `1000BONK-USDT@LIN`,
     `1000FLOKI-USDT@LIN`, `1000PEPE-USDT@LIN`, etc.), 7-27KB each, `updated` timestamps 2026-07-20T21:06Z /
     2026-07-21T02:08Z — plausible real trade data, not empty placeholders.
   - `processed_candles/by_date/day=2026-07-20/pipeline_mode=batch_aster/` contains derived candles at `timeframe=15s`
     and `timeframe=1m` (data_type=trades, instrument_type=PERPETUAL, venue=ASTER) — someone/ something already ran MDPS
     candle-building against this raw data. **Zero of these candle rows are registered in the manifest either** (0
     `market-data-processing-service` rows for ASTER in the cefi index).
3. **This contradicts** `plans/archive/issues/aster_capture_broken_coverage_and_completeness_2026_07_20.md`'s own
   closing banner: "🟢 RESOLVED 2026-07-25 — ACKED-INTO-CODE — all fix items (A/B/C/D/GAP-4) shipped + verified with
   real data in all 3 repos". That doc's "verified with real data" claim does not match what the manifest shows today, 1
   day later.

## Why it matters

- Per-asset_group coverage/completeness reporting (data-status pages, the daily digest, any consumer keying off
  `capture_status`) is currently reading ASTER as ~0% captured when real data physically exists — an under-count, not an
  over-count, so it's less likely to trigger existing "empty/failed" alerting but will silently starve any downstream
  consumer that reads the MANIFEST rather than GCS directly (e.g. MDPS's own `_get_tradable_instruments` path, feature
  backfills gated on manifest freshness, the ADV reader scaffolded in
  `aster_and_cefi_rolling_adv_feature_2026_07_21.md`).
- It blocks `cefi_satellite_ao_dispatch_batch1-001`'s ASTER leg specifically: that todo's "Done when" requires "a
  manifest-verified backfill covers each venue's full already-captured raw-trade range" — for ASTER, the manifest does
  not currently reflect the real captured range, so a manifest-based scoping of the backfill range would be wrong (it
  would think almost nothing has been captured and either skip real data or attempt to re-capture already-present data).
- The un-registered `processed_candles/` output for ASTER (found already on disk, day=2026-07-20, 15s/1m only, no
  manifest rows) is orphaned work from an unknown prior run — worth registering (or re-running with the writer) rather
  than silently leaving as a manifest-invisible artifact.

## Recommended decision

- **[DATA] P0.** Root-cause why ASTER's `record_captured`/`record_failed` manifest writes for the raw-trade adapter are
  not landing (or are landing then being lost/overwritten) despite the adapter clearly writing real parquet to GCS.
  Candidate angles: a raw-write path that bypasses `ManifestWriter` entirely (a direct `upload_bytes` without the paired
  `record_captured` call), a per-VM shard whose manifest rows never got consolidated, or an exception swallowed after
  the GCS upload but before the manifest write. Repo: market-tick-data-service.
- **[DATA] P1.** Once the writer-path is fixed, either (a) re-run a manifest-only reconciliation pass that registers the
  ALREADY-WRITTEN 2026-07-20/21 raw files + their derived candles as `captured` (idempotent, no re-fetch), or (b) if
  root-causing shows the files are somehow suspect, re-run the fetch for that narrow window. Prefer (a) unless the
  root-cause investigation finds a correctness problem with the existing files.
- **[DATA] P2.** Once ASTER's manifest correctly reflects its real captured range,
  `cefi_satellite_ao_dispatch_ batch1-001`'s ASTER leg (MDPS candle backfill) can be scoped correctly and re-attempted;
  until then it is carved out of that todo's initial delivery (see that plan's Progress Log / evidence for the
  carve-out).

## Todos

- [x] [DATA] P0. **Root-cause ASTER's manifest registration gap** — why `record_captured`/`record_failed` writes for the
      raw-trade adapter aren't landing despite real parquet on GCS (see "Recommended decision" above); this blocks
      `cefi_satellite_ao_dispatch_batch1-001`'s ASTER leg. — ✅ **market-tick-data-service@7a730cd6**. Root cause:
      `OnchainPerpBatchHandler.process()` constructs its `ManifestWriter` with no `per_vm_shards` argument, so it
      resolves from the ambient `MANIFEST_PER_VM_SHARDS` env var (default `False`). The dedicated fleet launcher
      (`launch-cefi-hl-aster-historical-backfill.sh`) sets that var, but the 2026-07-20/21 raw files were produced by an
      ad-hoc/manual invocation (no matching VM was ever found running — see "What I found" above — and both `accd8aa4`
      ASTER rate-limit fix and `aa72787b` row_key fix landed the SAME day, consistent with a manual verification run
      during that debugging session) that did not inherit the env var. Without it, every manifest write falls back to
      the legacy single-blob generation-match CAS path, which — on the cefi bucket's large/hot canonical index —
      exhausts its 15-retry budget without completing (identical mechanism to
      `/plans/archive/issues/defi_fold_manifest_registration_pending_2026_07_21.md`, confirmed via
      `unified-trading-library`'s `_write_to_gcs`/`_drain` code + docstrings). The raw parquet write
      (`PartitionedTickWriter`) is a fully independent path, so it succeeds regardless — explaining real data on disk
      with zero manifest registration. `.add()`'s legacy ingest path does NOT hit the separate `MalformedRowKeyError`
      `chain=""` bug `aa72787b` fixed (that bug only affects `record_empty`/`record_failed`'s `row_key` builder, which
      `.add()` bypasses entirely) — confirmed NOT a contributing factor for the captured-row gap specifically. Fix:
      hardcoded `per_vm_shards=True` on the handler's `ManifestWriter` construction (matching the existing safety-net
      pattern already used by `rebuild_sports_manifest_v9.py` /
      `recover_tradfi_chain_manifest_registration_2026_07_22.py`), so future runs of this handler register correctly
      regardless of the invoking environment. QG green (7403 passed, 2 pre-existing unrelated failures fixed as a
      repo-blocker per RULES.md §4b — `test_reprocess_bulk_tardis_derivative_ticker_funding_timestamp_2026_07_28.py`
      broke after `unified-api-contracts@ee7cb341` registered "coinbase"; another slot landed an equivalent fix
      concurrently, reconciled via merge).
- [x] [DATA] P1. Once the writer-path fix is deployed, re-run a manifest-only reconciliation pass that registers the
      ALREADY-WRITTEN 2026-07-20/21 raw files + their derived `processed_candles/` as `captured` (idempotent, no
      re-fetch) — mirrors the recipe in `/plans/archive/issues/defi_fold_manifest_registration_pending_2026_07_21.md`.
      Repo: market-tick-data-service. — ✅ **market-tick-data-service@9415ef7a**. Live-verified 2026-07-28: the daily
      ASTER capture had already self-healed MOST of the 2026-07-19..07-22 window post-fix (07-21/07-22 fully `captured`;
      candles for 07-20/07-21 already registered by MDPS on 07-27). The residual registration gap was exactly 8 (date,
      instrument) cells — real raw parquet on GCS, manifest still `attempted_failed` (4 on 07-19:
      BANK/ESPORTS/MERL/XAN-USDT@LIN; 4 on 07-20: BANK/DOGS/MMT/WET-USDT@LIN). New one-off
      `register_aster_onchain_perp_manifest_gap_2026_07_28.py` (dry-run/--apply, targeted GCS listing + slim manifest
      diff, additive `ManifestWriter.add(per_vm_shards=True)` mirroring `OnchainPerpBatchHandler._record_captured`'s
      exact field shape) registered all 8 — verified via a same-instance-identity read showing gap 8→0. Candle side
      needed no code change (already correctly registered). 9 new unit tests; QG green (sentinel=HEAD, 7414+ passed).
- [x] [DATA] P2. **DONE 2026-08-02 (slot-8, data_engineering).** Once ASTER's manifest correctly reflects its real
      captured range, re-scope `cefi_satellite_ao_dispatch_batch1-001`'s ASTER leg (MDPS candle backfill) — it was
      carved out of that plan's initial delivery pending this fix. — Re-verified the manifest fix live (fresh filtered
      `read_availability_index` read, not trusting the 2026-07-28 claim): ASTER's real raw-trade capture range is
      genuinely reflected now — 246,778 `captured` rows for `market-tick-data-service`/ASTER spanning
      `2023-07-22..2026-08-02` (vs. the original near-total `expected_unattempted` state), `trades` specifically
      `captured 2024-01-01..2026-07-27` (112,303 rows), only 4,209 `attempted_failed` remaining. MDPS candle
      registration for ASTER, by contrast, was still only 4 rows (`2026-07-20..2026-07-21` — the P1 fix's orphan
      registration), confirming the carve-out's premise: real captured range now known, candle backfill was still
      unscoped. Re-scoped and **launched** the same proven recipe from `cefi_satellite_ao_dispatch_batch1_2026_07_25.md`
      todo 1 (HYPERLIQUID/LIGHTER-ZKSYNC/EXTENDED-STARKNET): `market-data-processing-service` code tarball was one
      commit stale (republished via `create-code-tarballs.sh --include market-data-processing-service`, confirmed fresh
      on re-dry-run), then launched `mdps-backfill-cefi-20260802-140125` (SPOT `e2-standard-8`,
      `deployment-service/scripts/vm/launch-mdps-backfill-vm.sh --data-types trades --venues ASTER cefi 2024-01-01     2026-08-01 full`)
      — scoped to ASTER's genuine captured raw-trade range. STARTED confirmed <60s (task PID 8727 launched within the
      VM's setup script); **verified real progress, not fire-and-forget**:
      `vm-logs/mdps-backfill-cefi-20260802-140125/PROGRESS.json` shows
      `{"last_completed_date":"2024-01-01",     "monotonic":true}` within ~1 minute of task start — genuine per-date
      candle output, not a hang. The backfill continues running independently (multi-day range, same as the sibling
      venues' precedent — not waited-on to full completion in this session). Follow-up (verification + manifest
      registration of the newly-written candles) is a new todo below, per the findings-closure discipline. No code
      change was needed (pure re-scope + launch).

- [ ] [DATA] P2. **Follow-up from the P2 re-scope above.** Verify `mdps-backfill-cefi-20260802-140125` (ASTER MDPS
      candle backfill, `2024-01-01..2026-08-01`) reaches completion (check `PROGRESS.json`'s `last_completed_date`
      advances to the end date, or the VM's exit code/heartbeat goes terminal), then run the additive manifest
      reconciliation merge the launcher itself reminds to run post-backfill (NEVER
      `rebuild_manifest_from_canonical_paths` — that wholesale-replaces the bucket's whole manifest index and would
      delete this bucket's raw-tick rows, per
      `/plans/active/issues/rebuild_manifest_from_canonical_paths_prefix_scoped_wipe_2026_07_27.md`):
      `merge_manifest_from_canonical_paths('market-data-tick-cefi-central-element-323112',     service_name='market-data-processing-service', prefix='processed_candles/by_date')`.
      Repo: market-data-processing-service / unified-trading-library. **Done when**: a fresh `read_availability_index`
      read shows `market-data-processing-service` rows for ASTER spanning materially more than the current 2 days, and
      the VM's terminal status (exit_code / heartbeat) is confirmed, not assumed.

## Progress Log (2026-07-26)

- Root-caused + fixed todo 1 (P0). See the todo's own evidence line for the full mechanism. Shipped
  `market-tick-data-service@7a730cd6`. P1 (register the already-written 2026-07-20/21 data) and P2 (re-scope the
  `cefi_satellite_ao_dispatch_batch1-001` ASTER leg) are queued as separate todos above, not yet started.

## Progress Log (2026-07-28)

- Closed todo 2 (P1). See the todo's own evidence line for the full mechanism + verification. Shipped
  `market-tick-data-service@9415ef7a`. P2 (re-scope `cefi_satellite_ao_dispatch_batch1-001`'s ASTER leg) remains — not
  started this session.

## Progress Log (2026-08-01)

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).

## Progress Log (2026-08-02)

- Closed todo 3 (P2, the re-scope). Re-verified the manifest fix live, re-scoped and launched the ASTER MDPS candle
  backfill (`mdps-backfill-cefi-20260802-140125`), confirmed genuine progress. See the todo's own evidence line for full
  detail. A new follow-up todo (verify completion + additive manifest reconciliation) is queued above — the backfill is
  multi-day and continues running independently, not waited-on to completion this session.

## Not yet checked (deliberately out of scope for this discovery pass)

- Whether the SAME registration gap affects other CeFi venues beyond the 4 on-chain-perp ones this session was scoped to
  (a broader per-venue capture_status sweep would need a dedicated audit pass, not a corpus walk from here).
- Whether the un-registered `processed_candles/` ASTER output (15s/1m only) was produced by a human/agent test run or a
  since-removed cron; no currently-running GCE VM was found producing it (checked `gcloud compute instances list` at
  discovery time — only unrelated `mdps-backfill-tradfi-*` VMs were running).
