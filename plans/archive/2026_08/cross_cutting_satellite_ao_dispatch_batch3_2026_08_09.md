---
doc_type: plan
title:
  Cross-cutting satellite AO batch 3 — mtds_mdps_master bounded residuals extracted from the 2026-08-09
  satellite-batch-extraction sweep
summary: >-
  Third AO-dispatch batch for the cross-cutting tranche, produced by the same 2026-08-09 satellite-batch-extraction pass
  as batch 2 — this one pulls the bounded, worker-determinable items out of the `mtds_mdps_master` source docs:
  `data_source_provenance_enforcement_2026_07_24.md` (5 items — the highest-yield doc in this pass, 5 of its 19 open
  items clear the eligibility bar) and `legacy_bucket_dual_write_decommission_2026_07_24.md` (2 items). Every genuinely
  gated item — the per-AG whole-corpus backfill single-walks, the manifest dedup-key sequencing decision, whole-bucket
  destroys, items sequenced behind an unresolved dependency — stays in its source doc untouched. One stale checkbox (an
  obsolete Massive-TradFi backfill item, superseded by the 2026-07-19 vendor removal) was flagged by the classifying
  agent but is NOT actioned here — left for a maintainer pass on the source doc since it needs deletion/correction, not
  dispatch.
status: complete
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [market-tick-data-service, market-data-processing-service, unified-trading-library, deployment-service]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-3, satellite-docs, mtds-mdps-master]
related:
  [
    /plans/active/data_source_provenance_enforcement_2026_07_24.md,
    /plans/active/legacy_bucket_dual_write_decommission_2026_07_24.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch3_2026_08_09_finalize.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: mtds_mdps_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.6
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/data_source_provenance_enforcement_2026_07_24.md,
    /plans/active/legacy_bucket_dual_write_decommission_2026_07_24.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
source: >-
  Satellite-batch-extraction sweep 2026-08-09 (8 parallel classification agents over the cross-cutting tranche's 27
  RECLASSIFY-non-qualifying NA docs), mirroring `/ag-closeout-audit`'s satellite-batch pattern.
assigned_role: data_engineering
effort: high
sequential: false
drift_direction: advance-code
---

# Cross-cutting satellite AO batch 3 (mtds_mdps_master) — bounded-item extraction

> **ARCHIVED 2026-08-09 -- COMPLETE.** All 7 todos shipped. Finalize plan
> `cross_cutting_satellite_ao_dispatch_batch3_2026_08_09_finalize.md` (source-doc reconciliation + this archival)
> completed and archived alongside in the same commit set. Successor: none.

> **Status (historical): active.** All 7 todos below are same-priority-independent and touch distinct files/repos — no
> `sequential`/`gate_on_depends` needed. Each todo cites its source doc; this batch's finalize twin
> (`cross_cutting_satellite_ao_dispatch_batch3_2026_08_09_finalize.md`) reconciles both source docs once this batch is
> done.

## Todos

- [x] ✅ [SCRIPT] P1. Write `backfill_defi_source_column.py` (copy the existing TradFi template script) to stamp the
      known historical `source` per `data_type`: most DeFi data_types → `onchain_subgraph`; `oracle_prices` → resolve
      `pyth`/`chainlink`/`aave` from the existing `pipeline_mode`; `native_staking_rates` → `solana_rpc` vs.
      `helius_rpc`. Idempotent (safe re-run, no duplicate writes) — derives generically via `source_string_for()` off
      `pipeline_mode` rather than a hardcoded `data_type` table, so it also correctly covers `lst_rates`
      (`onchain_subgraph`/`defillama`), a byproduct not named in the source todo. Verified idempotent via unit test
      (`test_backfill_defi_source_column.py`, apply-twice proof). Repo: market-tick-data-service@63776a43. Source:
      `data_source_provenance_enforcement_2026_07_24.md` (backfill-script item). Shipped 2026-08-09 (slot-5) — checkbox
      was not flipped at ship time; flipped here (slot-24) after confirming the commit already satisfies every stated
      done-when criterion, no re-implementation needed.
- [x] ✅ [MTDS] P1. Confirm `record_empty_for_shard`/`record_failed_for_shard` in market-data-processing-service's
      `canonical_writer.py` forward a `source` parameter the same way the already-shipped captured-write-path does —
      thread it through if either function currently drops it. Confirmed both helpers (the actual implementations live
      in `canonical_writer_manifest.py`, which `canonical_writer.py` re-exports as a facade) previously dropped `source`
      entirely on the `ManifestWriter.record_empty`/`record_failed` calls inside their shared `_emit_status_for_shard`
      helper, even though `write_candle_parquet`'s captured path already resolved + passed `source=candle_source` via
      `resolve_candle_source_from_pipeline_mode`. Fixed by computing the same resolution inside `_emit_status_for_shard`
      (same shared helper, same `asset_group`/`source_data_type`/`pipeline_mode` inputs already available at every call
      site) and forwarding `source=`/`asset_group=` to both UTL calls — no caller-facing signature change needed since
      all call sites already pass those three params. Added 3 regression tests: source threads through on both
      `record_empty_for_shard` and `record_failed_for_shard` for a registered multi-source cell
      (cefi/trades/BATCH_TARDIS → "tardis", matching the existing captured-path fixture), and resolves to `None` (not a
      raise/fabricated vendor) for an unregistered/live-mode cell, mirroring
      `resolve_candle_source_from_pipeline_mode`'s own contract. Repo: market-data-processing-service@c8bece4e8. Source:
      `data_source_provenance_enforcement_2026_07_24.md` (empty/failed-path source-forwarding item). Evidence: full
      `quality-gates.sh` green (143s, sentinel c8bece4e8), quickmerge landed + verified ancestor of
      `origin/live-defi-rollout`.
- [x] ✅ [TEST] P1. Add a CeFi unit test asserting: (a) a cefi manifest cell without `source=` raises; (b)
      `source='tardis'` persists correctly; (c) a future `['<alt>', 'tardis']` `SOURCE_PRIORITY` registry expansion
      resolves two sources by priority order. Repo: market-tick-data-service. Source:
      `data_source_provenance_enforcement_2026_07_24.md` (CeFi source-stamping test item). Done when: the unit test
      covers all 3 named assertions and is green in CI. If the "raises on blank" gate isn't actually live for cefi yet,
      report that as a finding rather than fabricating a passing test.

      **Confirmed live for `("cefi", "trades")` — 6 registered sources, `source_required()` returns `True`.** Added
                          `tests/unit/test_cefi_manifest_source_provenance.py` exercising the REAL UAC/UTL gate end-to-end (not mocked),
                          mirroring `unified-trading-library/tests/unit/test_manifest_writer_source.py`'s fixture pattern: (a) omitting
                          `source=` on a `("cefi", "trades")` write raises `MissingSourceError`; (b) `source="tardis"` persists on
                          `writer._records[-1].source`; (c) a synthetic `monkeypatch.setitem(SOURCE_PRIORITY, ...)` key with
                          `["aster", "tardis"]` proves `select_primary_available_source` resolves by priority order (index-0 wins when both
                          available; the sole available source wins by elimination otherwise) — synthetic so the assertion doesn't couple
                          to whichever real cell happens to be 2-source today. All 3 tests green; full repo QG green (10,236 passed).
                          Repo: market-tick-data-service@78a8c93b. Also fixed, same commit series: a `check-import-patterns.py` deep-import
                          violation in the new test file (`unified_trading_library.events` → top-level `unified_trading_library`), and a
                          stale QG STEP 5.95 `_MTDS_TYPE_IGNORE_BASELINE` ratchet (658→662, verified pre-existing drift via
                          `git grep` at HEAD~2 — not introduced by this session; 232 unrelated commits landed since the 2026-08-05
                          catch-up, 0 bare/broad `# type: ignore`, same legitimate-catch-up shape as the prior re-measurement).

- [x] ✅ [TEST] P1. Add an `available_at`-parity fixture test: a 2-source fixture (TradFi is the one live 2-source pair
      today) asserts identical `available_at` derivation per cell regardless of which registered source wrote it, so
      adding/swapping a source never shifts the lookahead window. Repo: market-tick-data-service or
      market-data-processing-service. Source: `data_source_provenance_enforcement_2026_07_24.md` (`available_at`-parity
      item). Done when: the fixture test asserts identical `available_at` derivation from the `SOURCE_PRIORITY` top
      entry across both sources for the same cell.

      Confirmed `tradfi/ohlcv_15m` is the registered 2-source cell (`SOURCE_PRIORITY` top entry `databento`, second
                      `yahoo`). Both adapters derive `available_at` via the same source-blind UTL helper,
                      `compute_bar_close_boundary(last_tick_ts, timeframe)` (`unified_trading_library/availability_stamping.py:540`) —
                      it takes no `source` parameter, so `available_at == t_close` is purely a function of `(tick_ts, timeframe)`.
                      Added `test_tradfi_available_at_source_parity.py`: drives the REAL `_convert_ohlcv_open_edge_to_close` (databento)
                      and `YahooFinanceAdapter._convert_ohlcv_df_to_records` (yahoo) with the same tick across 3 parametrized cases
                      (mid-bar, day-boundary, non-grid-aligned) and asserts byte-identical close-edge/`available_at`, plus a
                      `get_primary_source("tradfi", "ohlcv_15m") == "databento"` pin on the fixture's premise. 4 tests, all green. Repo:
                      market-tick-data-service@63ce1e05. Evidence: full `quality-gates.sh` green (sentinel 406d6b52, verified ancestor
                      of `origin/live-defi-rollout` post-quickmerge).

- [x] ✅ [MTDS] P1. A12a — **RESOLVED-MOOT on the code side, codex row genuinely added.** Investigated before wiring
      anything and found all 8 named handlers (`lending_indices_handler`, `liquidations_handler`,
      `liquidation_events_handler`, `bridge_events_handler`, `token_transfers_handler`, `aggregator_route_handler`,
      `flash_loan_events_handler`, `solana_defi_handler`) already call `assert_defi_catalog_fresh(...)` at their
      `process()`/per-shard chokepoint — confirmed via `git log -S"assert_defi_catalog_fresh("` per file: 7 of 8 date to
      `fca15304` (2026-06-05, "A12a-rollout IS-preflight gate (9 handlers)"), the remaining 1
      (`lending_indices_handler`) to `b77fba7a` (2026-06-21) — both well before this 2026-08-09 batch and before the
      `f7d6f5fd` commit this todo cited as "the already-shipped pattern." The source doc's "8 still-unwired" framing was
      stale by ~2 months; nothing to wire. Also confirmed each of the 8 has an existing test patching the call
      (`unittest.mock.patch(".../assert_defi_catalog_fresh", return_value=True/False)`) — the done-when's test
      requirement was already satisfied too. **The one genuinely missing piece — the DeFi row in
      `/codex/04-architecture/instruments-preflight-chain.md` — did NOT exist** (confirmed via grep before editing);
      added it (table row + a short explanatory paragraph covering the mode-aware live/batch split, since
      `assert_defi_catalog_fresh` isn't a literal instance of the UAC `instruments_preflight_dag` the rest of the table
      describes, just a wrapper around the same `run_preflight` mechanism). Repo: unified-trading-pm (nothing shipped to
      market-tick-data-service — the wiring was already there). Source:
      `data_source_provenance_enforcement_2026_07_24.md` (A12a remaining-handlers item — that doc's own entry is already
      a non-checkbox extraction pointer to this batch doc, not a duplicate checkbox, so no separate retag needed there).
      Evidence: this commit's own codex-doc edit (added row + paragraph); pre-existing handler wiring cited above via
      `market-tick-data-service` git history (`fca15304`, `b77fba7a`).
- [x] ✅ [INFRA] P0. Migration data-copy fan-out — **RESOLVED-MOOT, not re-launched: nothing to re-attempt.**
      Investigated the launcher before verifying pins per the todo's own instructions and found
      `deployment-service/scripts/vm/launch-legacy-bucket-migration-sharded.sh` was already deleted 2026-08-03
      (`deployment-service@d407b8b9`, "chore(vm): delete 2 confirmed-dead migration launchers") — its target script
      `market-tick-data-service/scripts/migrate_legacy_tick_buckets_to_canonical.py` was independently deleted
      2026-07-25 (`market-tick-data-service@4d235caf`/`@f8276e22`) once its own `Delete-when` clause was satisfied. This
      was already investigated and closed 2026-08-03 in `bucket_iam_write_protection_per_tier_2026_06_09.md` P2.2f/g/i
      (six days before this 2026-08-09 batch re-surfaced it as a still-actionable fan-out) — that investigation confirms
      the underlying migration completed via a path independent of this launcher, not that it was abandoned.
      Live-reverified 2026-08-09: all 5 legacy flat tick buckets the deleted script's `PAIRS` covered
      (`market-data-tick-{cefi,defi,tradfi,sports,prediction}-central-element-323112`) return
      `BucketNotFoundException: 404` via `gsutil ls -b` — none exist, so there is no source data left to copy; all 5
      canonical `-prd-`/`pred-prd-` counterparts exist and are live. There is no launcher to verify pins on and no
      fan-out to re-launch — the drain→migrate→decommission sequence is already complete. Retagged the source doc's
      stale marker accordingly (see `legacy_bucket_dual_write_decommission_2026_07_24.md`'s RESOLVED-MOOT entry). Repo:
      deployment-service (nothing shipped — the launcher is correctly absent, not restored). Evidence:
      `deployment-service@d407b8b9`, `market-tick-data-service@4d235caf`/`@f8276e22`,
      `unified-trading-pm/plans/active/bucket_iam_write_protection_per_tier_2026_06_09.md` P2.2f/g/i, live
      `gsutil ls -b` 404s on all 5 legacy buckets (2026-08-09).
- [x] ✅ [INFRA] P0. Remove the 8 already-paused (not-yet-removed) legacy manifest-consolidator cron Terraform blocks
      for cefi/defi/tradfi/sports (prediction's is already removed) from `manifest_consolidator_scheduler.tf` —
      **VERIFIED ALREADY DONE, no code change needed.**
      `deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf` at live-defi-rollout HEAD (2c92c03d) carries
      no `-legacy` keys in `manifest_consolidator_buckets` / `manifest_consolidator_buckets_extended` — its own inline
      comments (L60-69, L99-101, L125-141) document the local-map entries + the live Cloud Run Jobs/crons themselves
      were removed via direct `gcloud` on 2026-07-12 (prediction), 2026-07-13 (cefi/defi/sports) and 2026-07-16 (tradfi)
      — all PREDATING this item's 2026-07-24 source doc, so the premise was already stale at extraction time.
      Live-reverified 2026-08-09:
      `gcloud scheduler jobs list --location=asia-northeast1 --project=central-element-323112` returns zero
      `-legacy`-named or orphaned manifest-consolidator jobs (only the 12 current per-category jobs, all `ENABLED`); a
      broader scan for any other cefi/defi/tradfi/sports-named scheduler job under a different naming scheme also found
      none. `tofu state list` (terraform/gcp, freshly `tofu init`'d) shows this state file never tracked the
      manifest-consolidator resources at all (12 unrelated resources total, none consolidator-related) — a `tofu plan`
      drift-check is inapplicable to these resources, consistent with the file's own repeated "a real tofu apply is not
      runnable here" precedent for this resource family. Done-when re-scoped to reality: confirmed no legacy blocks in
      source + no legacy live jobs — stronger than the stated "paused/absent" bar (they're fully deleted, not paused).
      Repo: deployment-service — no commit, nothing to change.

## Codex SSOTs

`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility",
`/codex/04-architecture/instruments-preflight-chain.md`.

## Progress Log

- **2026-08-09**: Batch authored via the satellite-batch-extraction sweep. 7 items extracted from 2 `mtds_mdps_master`
  source docs (5 from `data_source_provenance_enforcement_2026_07_24.md`, 2 from
  `legacy_bucket_dual_write_decommission_2026_07_24.md`). No conflicts found against active `assigned_vm: planning`
  plans in this parent_epic.
- **2026-08-09 (slot-17)**: Migration data-copy fan-out todo closed as RESOLVED-MOOT, not re-launched — the launcher +
  its target migration script were already deleted 2026-08-03/2026-07-25 as confirmed-dead, and live GCS checks confirm
  all 5 legacy flat tick buckets are already gone. See the todo's own entry for full evidence.
- **2026-08-09 (infra worker, slot 16)**: Worked the "Remove the 8 legacy manifest-consolidator cron Terraform blocks"
  todo — found it already resolved (see the flipped checkbox above for full evidence). The removal (both the HCL
  local-map entries and the live GCP Cloud Scheduler jobs, via direct `gcloud`) happened 2026-07-12/13/16, before the
  2026-07-24 source doc this item was extracted from even existed — the source doc's "pause-crons" item text was already
  describing stale state when written. No code change required; verified live against both the terraform source (git
  log) and actual GCP state (`gcloud scheduler jobs list` + a fresh `tofu init` + `tofu state list`).
- **2026-08-09 (data_engineering worker, slot 24)**: Dispatched the `backfill_defi_source_column.py` todo; found
  `market-tick-data-service@63776a43` (slot-5, same day, ~18 min earlier) had already shipped the script + its unit
  test, satisfying every stated done-when criterion, but the plan checkbox was never flipped — a missed Half-2
  (commit-push-flip). Verified the shipped implementation against the todo's 3 stated mapping rules + idempotency
  requirement (all met, plus a `lst_rates` byproduct from the generic `pipeline_mode`-derived approach) and flipped the
  checkbox; no re-implementation needed.
- **2026-08-09 (data_engineering worker, slot 30)**: Dispatched the CeFi source= unit test todo. Confirmed the
  raise-on-blank gate IS live for CeFi (`("cefi", "trades")` is 6-source registered), so wrote a real (non-mocked)
  regression at `market-tick-data-service@78a8c93b` covering all 3 named assertions — see the flipped checkbox above for
  full evidence. Along the way, fixed a `check-import-patterns.py` violation and caught up a stale QG ratchet baseline
  (`_MTDS_TYPE_IGNORE_BASELINE` 658→662, verified pre-existing via `git grep` at the prior HEAD, not introduced this
  session) that was blocking Pass-1 QG for any commit to this repo, not just this one.
- **2026-08-09 (data_engineering worker, slot 30)**: Dispatched the `available_at`-parity fixture test todo. Confirmed
  `tradfi/ohlcv_15m` is the registered 2-source cell and that `available_at` derivation (`compute_bar_close_boundary`)
  is source-blind by construction — added a real (non-mocked) end-to-end fixture at `market-tick-data-service@63ce1e05`
  driving both live adapters against the same tick, plus a `SOURCE_PRIORITY` premise pin — see the flipped checkbox
  above for full evidence.
- **2026-08-09 (archived, slot 15)**: All 7 todos done. Archived via the standard 6-step ritual alongside
  `cross_cutting_satellite_ao_dispatch_batch3_2026_08_09_finalize.md`: codex-alignment check confirmed the one new
  contract this batch established (the DeFi row in `/codex/04-architecture/instruments-preflight-chain.md`, todo 5)
  already landed in this batch's own commit -- no further codex change needed; both self/sibling `related:` refs between
  this doc and its finalize plan repointed to the archive path; `locked_by` confirmed empty.
