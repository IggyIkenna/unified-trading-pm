---
doc_type: issue
title: DeFi fold (2026-07-21) — 648 canonical twins written but manifest rows not yet registered
summary:
  The 2026-07-21 defi dex_pools/lending_indices fold wrote 648 canonical OBJECTS (verified) but did not register
  availability-manifest rows for them. The consolidator merges record_captured per-VM shards — it does NOT re-derive
  rows from raw GCS objects — so the folded twins do not yet appear as captured in the coverage manifest. A standalone
  register pass via DefiManifestRecorder did not flush cleanly in a script context (no partial write occurred). This is
  a coverage-reporting gap, not data loss — the objects exist and the depth-provider reads them directly.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags: [defi, fold, manifest, record-captured, consolidator, honest-coverage, dex-pools, solana]
related:
  [
    defi_dex_pools_delete_order_stale_2026_07_20.md,
    data_pipeline_reconciliation_skill_2026_07_20.md,
    ../../codex/05-infrastructure/manifest-consolidator-ssot.md,
    ../../codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-21
last_updated: 2026-07-21
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: found while executing the D3 fold + manifest step, 2026-07-21
depends_on: []
---

# DeFi fold (2026-07-21) — canonical objects written, manifest rows pending

> **State:** the DATA migration is COMPLETE and verified (648 legacy-only twins written; KAMINO-vault 0→513, SOLEND
> 0→59, KAMINO-lending 0→44, RAYDIUM 100→132). The legacy `dex_pools/`+`lending_indices/` prefixes now have canonical
> twins for every cell → the delete is SAFE (human-only). What remains is registering the manifest rows so the folded
> twins show `captured` in the coverage surface. **No data is at risk; no partial manifest write occurred.**

## The mechanism finding (corrects a stale assumption)

The fold script's docstring claimed "the manifest is re-derived from GCS by the standard consolidator." **That is
wrong.** `unified_trading_library.manifest_consolidator.consolidate(bucket)` lists + merges the
`_index/per_vm/*.parquet` shards written by `record_captured` — it does **not** scan raw `raw_tick_data/` objects (that
would be the banned whole-corpus walk). So an objects-only fold leaves **no** manifest representation.

## The correct registration recipe (verified in dry-run: 714 rows)

Register one `record_captured` row per folded instrument at the per-pool grain (bare address, lowercased — the grain the
live `dex_pools_handler` and the address-keyed enumerator both use), then consolidate:

- `DefiManifestRecorder(catalogue_bucket=<market-data-tick-defi bucket>, target_day=date(2026,4,14), handler_label="dex_pools")`
- per instrument:
  `recorder.record_captured(venue=<PROTO>, chain="SOLANA", data_type="dex_pool_state"|"lending_indices", row_count=<n>, pipeline_mode=derive_pipeline_mode_for_row(<PROTO>,"defi",<dt>), instrument_type="solana_amm_pool"|"solana_vault"|"solana_lending", instrument_id=<address>.lower(), attempted_at=datetime(2026,4,14,tzinfo=UTC), source="onchain_subgraph")`
- `recorder.close()`, then `python -m unified_trading_library.manifest_consolidator --bucket <bucket>`.
- Scope: the 4 subsets with new writes (KAMINO-vault 513, KAMINO-lending 44, SOLEND 59, RAYDIUM 98 = 66 idempotent
  refresh + 32 new). SKIP ORCA (0 new — all 14,094 pre-existing, already registered by the live writer). Dry-run
  confirmed **714** rows.

## The blocker (why it is not done inline)

A standalone `DefiManifestRecorder`/`ManifestWriter(batch_size=1)` register pass did not flush a `_index/per_vm/` shard
in a plain-script context (the process reached storage/validation init, then exited without persisting — no output, no
shard, **no partial write**). The recorder is coupled to the live handler's async flush discipline. It was **not** worth
risking a flaky prod manifest write at the tail of the migration, so it is filed here as a bounded follow-up rather than
forced.

## Todos

- [ ] 1. [DATA] P1. Diagnose why the standalone `DefiManifestRecorder`/`ManifestWriter(batch_size=1)` register pass does
      not flush a `_index/per_vm/` shard from a plain script (buffer/flush/async-context coupling); either fix the
      standalone path or run the registration through the live handler flush discipline.
- [ ] 2. [DATA] P1. Register the 714 rows per the recipe above (dry-run first — it prints the per-cell counts), then run
      the consolidator over the defi market-data bucket; verify the folded cells show `captured` for `day=2026-04-14`
      (KAMINO/SOLEND/32-Raydium flip from `expected_unattempted` → `captured`).
- [ ] 3. [REVIEW] P1. Correct the fold script's MANIFEST docstring (it wrongly says the consolidator re-derives from
      objects) — or delete the one-off script once the legacy prefixes are deleted (human-only) and this is resolved.

## Alternative

Re-running the DeFi capture for `day=2026-04-14` (KAMINO/SOLEND/RAYDIUM) through the **live handler** would register the
manifest correctly (the handler's `record_captured` path works) — but defi capture is currently STOPPED, and the fold
already created the objects, so the register-pass path above is cheaper.
